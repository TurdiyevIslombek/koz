"""Offline review probes: these assertions document CURRENT unsafe behavior, not acceptance tests.
No serial port, camera, network service or hardware is opened. See motor-safety.md.
"""
import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from helpers import Approve, EndlessCamera, FakeClock, FakeFaces, Refuse
from test_motors import CAR_SETUP, FakePort, ball_on_the_left, car_recipe, car_runner
from koz.actions.motors import MockMotorLink, MotorsAction, SerialMotorLink
from koz.agent import FakePlanner
from koz.events import new_id
from koz.server import Hub


class StillBrain:
    def reset(self):
        pass

    def tick(self, *args, **kwargs):
        return None, (100, 100)


def test_accepted_stop_allows_an_inflight_frame_to_drive():
    clock, link, delivered = FakeClock(), MockMotorLink(armed=True), []
    entered, release = threading.Event(), threading.Event()

    class WaitingCamera(EndlessCamera):
        def read(self):
            entered.set()
            assert release.wait(3)
            return super().read()

    hub = Hub(CAR_SETUP, lambda: WaitingCamera(ball_on_the_left(), clock), FakePlanner(),
              motor_link=link, clock=clock, wall_clock=lambda: 1000, deliver=delivered.append,
              models={"scene_checker": Approve(), "face_detector": FakeFaces(), "brain_driver": StillBrain()})
    job = new_id()

    def command(name, data):
        cid = new_id()
        hub.handle(json.dumps({"v": 1, "type": "command", "command_id": cid,
            "session_id": hub.events.session_id, "job_id": job, "trial_id": None,
            "expires_at": 1010, "command": name, "data": data}))
        return cid

    try:
        command("start_job", {"input": "recipe", "recipe": car_recipe()})
        assert entered.wait(3)
        cid = command("stop_job", {})
        assert next(e["data"]["result"] for e in delivered
                    if e["type"] == "command_result" and e["data"]["command_id"] == cid) == "accepted"
        before = len(link.sent)
        assert "STOP" not in link.sent and "DISARM" not in link.sent
        release.set()
        hub._thread.join(3)
        assert not hub._thread.is_alive()
        after = link.sent[before:]
        assert "M,20,20" in after
        assert after[-2:] == ["STOP", "DISARM"]
        print("accepted stop ->", after)
    finally:
        release.set()
        hub._thread.join(3)


def reporting_failed(_):
    raise RuntimeError("injected event delivery failure")


def test_fault_reporting_failure_skips_motor_cleanup():
    link = MockMotorLink(armed=True)
    runner, _ = car_runner(link)
    assert runner.step()
    before = len(link.sent)
    runner.events._sink = reporting_failed
    runner.camera.read = lambda: (_ for _ in ()).throw(RuntimeError("camera failed"))
    assert runner.step() is False and runner.state == "held"
    assert link.sent[before:] == [] and link.armed
    assert not runner._motors._ended
    print("fault + reporting failure -> held; cleanup commands:", link.sent[before:], "; armed:", link.armed)


def test_privacy_stop_reporting_failure_leaves_board_armed():
    link = MockMotorLink(armed=True)
    runner, _ = car_runner(link)
    assert runner.step()
    before = len(link.sent)
    runner.events._sink = reporting_failed
    runner._gate._checker = Refuse("PRIVATE_BATHROOM")
    runner._gate._checked_at -= 1
    assert runner.step() is False and runner.state == "held"
    assert link.sent[before:] == ["STOP"] and link.armed
    print("privacy + reporting failure ->", link.sent[before:], "; armed:", link.armed)


def test_ended_action_still_sends_drive_before_disarm_acknowledgement():
    class DelayedStatus(MockMotorLink):
        def disarm(self):
            self.sent.append("DISARM")  # real board status arrives asynchronously

    link = DelayedStatus(armed=True)
    action = MotorsAction(link, .25, .2)
    action.end()
    action.drive((100, 100))
    assert link.sent == ["STOP", "DISARM", "M,20,20"]
    print("ended action ->", link.sent)


def test_failed_stop_skips_disarm_and_allows_a_new_job_without_rearming():
    class FailedStopPort(FakePort):
        fail_stop = False

        def write(self, data):
            if self.fail_stop and data == b"STOP\n":
                raise OSError("injected transient USB write failure")
            return super().write(data)

    port, clock = FailedStopPort(), FakeClock()
    link = SerialMotorLink(serial_port=port, clock=clock)
    try:
        link.handle_line("S,1,RUNNING,200")
        action = MotorsAction(link, .25, .2)
        action.drive((100, 100))
        port.fail_stop = True
        action.end()
        assert action.status == "disarmed" and link.armed and link.fault is None
        assert port.written == ["M,20,20\n"]  # DISARM was never attempted
        port.fail_stop = False
        MotorsAction(link, .25, .2).drive((100, 100))
        assert port.written == ["M,20,20\n", "M,20,20\n"]  # no new human ARM
        print("failed STOP -> reported disarmed; new job sends:", port.written, "; link fault:", link.fault)
    finally:
        link.close()

