"""Regression tests for Codex's motor safety review (.collab/reviews/motor-safety.md, Oct 16), one
section per finding. Each test was written first and failed on the code the review saw; the fix came
after. Mock hardware only: MockMotorLink, a fake serial port, fake cameras."""
import threading

import pytest
from helpers import FakeClock
from test_motors import FakePort

from koz.actions.motors import MotorsAction, SerialMotorLink
from koz.errors import KozError


# --- MS-3: a failed STOP skipped DISARM, said "disarmed" and let a new job drive without ARM ------------

class FlakyPort(FakePort):
    """A fake USB port whose writes of the listed lines fail (a cable that drops for a moment)."""

    def __init__(self):
        super().__init__()
        self.failing = set()

    def write(self, data):
        if data.decode().strip() in self.failing:
            raise OSError("injected USB write failure")
        super().write(data)


def armed_link(port, clock):
    link = SerialMotorLink(serial_port=port, clock=clock)
    link.arm_by_hand()
    link.handle_line("S,1,RUNNING,200")   # the board says: armed
    return link


def lines(port):
    return [w.strip() for w in port.written]


@pytest.mark.parametrize("failing", [{"STOP"}, {"DISARM"}, {"STOP", "DISARM"}])
def test_a_failed_stop_or_disarm_still_tries_the_other_and_locks_the_link(failing):
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    try:
        action = MotorsAction(link, .25, .2)
        action.drive((100, 100))
        port.failing = failing
        action.end()
        assert lines(port)[2:] == [line for line in ("STOP", "DISARM") if line not in failing]   # both tried
        assert action.status == "stop_commanded"            # never "disarmed" from a write that failed
        assert not link.armed and link.fault == "NO_LINK"   # latched, although the board's status is fresh
    finally:
        link.close()


def test_after_a_write_failure_only_a_person_can_make_it_drive_again():
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    try:
        MotorsAction(link, .25, .2).drive((100, 100))
        port.failing = {"STOP"}
        MotorsAction(link, .25, .2).end()
        port.failing = set()                     # the cable works again before the board's watchdog
        link.handle_line("S,1,RUNNING,200")      # and the board still says armed
        sent = len(port.written)
        with pytest.raises(KozError):
            MotorsAction(link, .25, .2).drive((100, 100))
        assert len(port.written) == sent         # nothing was sent: no new job without a new ARM
        link.arm_by_hand()                       # a person, on this computer
        link.handle_line("S,1,RUNNING,200")
        MotorsAction(link, .25, .2).drive((100, 100))
        assert lines(port)[-2:] == ["ARM", "M,20,20"]
    finally:
        link.close()


def test_a_reader_that_fails_means_no_link_at_once():
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    port.closed = True                           # the cable was pulled: readline() raises
    link._thread.join(1)
    assert link.fault == "NO_LINK" and not link.armed   # without waiting for the status to go stale
    with pytest.raises(KozError):
        MotorsAction(link, .25, .2).drive((100, 100))
    link.close()


def test_serial_writes_have_a_time_limit(monkeypatch):
    import serial
    opened = {}

    def fake_serial(*args, **kwargs):
        opened.update(kwargs)
        return FakePort()

    monkeypatch.setattr(serial, "Serial", fake_serial)
    link = SerialMotorLink("/dev/cu.fake")
    try:
        assert 0 < opened["write_timeout"] <= 0.25   # a blocked write can't hold up STOP / DISARM
    finally:
        link.close()


def test_threads_can_stop_while_another_drives():
    """The job thread drives while Stop arrives from the command thread: writes never interleave."""
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    try:
        action = MotorsAction(link, .25, .2)
        driver = threading.Thread(target=lambda: [action.drive((100, 100)) for _ in range(200)])
        driver.start()
        link.halt()
        driver.join(5)
        written = lines(port)
        stop = written.index("STOP")
        assert written[stop + 1] == "DISARM" and not any(w.startswith("M,") for w in written[stop:])
    finally:
        link.close()


# --- MS-1: a frame already in progress could drive after Stop was accepted ---------------------------

def test_an_ended_action_never_drives_even_before_the_board_reports_disarmed():
    from koz.actions.motors import MockMotorLink

    link = MockMotorLink(armed=True, delayed_status=True)   # DISARM sent, the board hasn't said so yet
    action = MotorsAction(link, .25, .2)
    action.end()
    action.drive((100, 100))
    assert link.sent == ["STOP", "DISARM"]


class Gate:
    """Holds the job thread at one point (a camera read or the brain) until the test releases it."""

    def __init__(self, active=True):
        self.active, self.entered, self.release = active, threading.Event(), threading.Event()

    def wait_here(self):
        if self.active:
            self.active = False
            self.entered.set()
            assert self.release.wait(5)


class StillBrain:
    """A brain that always says 'forward', optionally held at its first tick."""

    def __init__(self, gate=None):
        self.gate = gate

    def reset(self):
        pass

    def tick(self, *args, **kwargs):
        if self.gate is not None:
            self.gate.wait_here()
        return None, (100, 100)


def ball_in_the_middle():
    import cv2
    import numpy as np
    image = np.full((240, 320, 3), 120, np.uint8)
    cv2.circle(image, (160, 120), 22, (0, 0, 220), -1)
    return image


def car_hub(link, camera_gate=None, brain=None):
    import json

    from helpers import Approve, EndlessCamera, FakeFaces
    from test_motors import CAR_SETUP, car_recipe

    from koz.agent import FakePlanner
    from koz.events import new_id
    from koz.server import Hub

    class GatedCamera(EndlessCamera):
        def read(self):
            if camera_gate is not None:
                camera_gate.wait_here()
            return super().read()

    clock, delivered = FakeClock(), []
    hub = Hub(CAR_SETUP, lambda: GatedCamera(ball_in_the_middle(), clock), FakePlanner(), motor_link=link,
              clock=clock, wall_clock=lambda: 1000, deliver=delivered.append, eval_seconds=1.0,
              models={"scene_checker": Approve(), "face_detector": FakeFaces(), "brain_driver": brain or StillBrain()})
    job = new_id()

    def command(name, data):
        hub.handle(json.dumps({"v": 1, "type": "command", "command_id": new_id(), "session_id": hub.events.session_id,
                               "job_id": job, "trial_id": None, "expires_at": 1010, "command": name, "data": data}))

    command("start_job", {"input": "recipe", "recipe": car_recipe()})
    return hub, delivered, command


def stop_while_held(hub, link, command, gate):
    """Press Stop while the job thread is held at the gate; return what was sent from then on."""
    try:
        assert gate.entered.wait(5)
        command("stop_job", {})
        at_stop = len(link.sent)
        assert link.sent[at_stop - 2:at_stop] == ["STOP", "DISARM"]   # at once, not at the next frame
        gate.release.set()
        hub._thread.join(5)
        assert not hub._thread.is_alive()
        return link.sent[at_stop:]
    finally:
        gate.release.set()


def wait_for_running(delivered):
    import time
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if any(e["type"] == "status" and e["data"]["state"] == "running" for e in list(delivered)):
            return
        time.sleep(0.01)
    raise AssertionError("the job never reached running")


def test_stop_during_a_camera_read_while_trying_never_drives_after():
    from koz.actions.motors import MockMotorLink

    link, gate = MockMotorLink(armed=True, delayed_status=True), Gate()
    hub, _, command = car_hub(link, camera_gate=gate)
    after = stop_while_held(hub, link, command, gate)
    assert not any(line.startswith("M,") for line in after) and not link.armed


def test_stop_during_processing_while_trying_never_drives_after():
    from koz.actions.motors import MockMotorLink

    link, gate = MockMotorLink(armed=True, delayed_status=True), Gate()
    hub, _, command = car_hub(link, brain=StillBrain(gate))
    after = stop_while_held(hub, link, command, gate)
    assert not any(line.startswith("M,") for line in after) and not link.armed


def test_stop_during_a_camera_read_while_running_never_drives_after():
    from koz.actions.motors import MockMotorLink

    link, gate = MockMotorLink(armed=True, delayed_status=True), Gate(active=False)
    hub, delivered, command = car_hub(link, camera_gate=gate)
    wait_for_running(delivered)
    assert any(line.startswith("M,") for line in link.sent)   # it was driving
    gate.active = True
    after = stop_while_held(hub, link, command, gate)
    assert not any(line.startswith("M,") for line in after) and not link.armed


# --- MS-2: a failure while reporting a stop skipped the motor cleanup ----------------------------------

def failing_on(kind):
    def deliver(event):
        if kind == "any" or event["type"] == kind:
            raise RuntimeError("injected event delivery failure")
    return deliver


def raising(*args, **kwargs):
    raise RuntimeError("injected failure")


def must_be_armed_again(link):
    with pytest.raises(KozError) as error:
        MotorsAction(link, .25, .2).check()
    assert error.value.code == "MOTOR_NOT_ARMED"
    link.arm_by_hand()
    MotorsAction(link, .25, .2).check()


@pytest.mark.parametrize("failure", ["observation delivery", "fault delivery", "a listener", "camera close"])
@pytest.mark.parametrize("trigger", ["camera error", "privacy stop"])
def test_the_motors_stop_and_disarm_even_if_reporting_the_stop_fails(trigger, failure):
    from helpers import Refuse
    from test_motors import car_runner

    from koz.actions.motors import MockMotorLink

    link = MockMotorLink(armed=True, delayed_status=True)
    runner, _ = car_runner(link)
    assert runner.step() and any(line.startswith("M,") for line in link.sent)   # driving
    before = len(link.sent)
    if failure == "observation delivery":
        runner.events._sink = failing_on("observation")
    elif failure == "fault delivery":
        runner.events._sink = failing_on("fault")
    elif failure == "a listener":
        runner.events.listeners.append(failing_on("any"))
    else:
        runner.camera.close = raising
    if trigger == "camera error":
        runner.camera.read = raising
    else:
        runner._gate._checker = Refuse("PRIVATE_BATHROOM")
        runner._gate._checked_at -= 1
    assert runner.step() is False                    # it stops, and nothing escapes
    assert runner.state == "held"
    assert link.sent[before:][-2:] == ["STOP", "DISARM"] and not link.armed
    must_be_armed_again(link)


def test_hold_disarms_before_it_reports():
    from test_motors import car_runner

    from koz.actions.motors import MockMotorLink

    link = MockMotorLink(armed=True, delayed_status=True)
    runner, _ = car_runner(link)
    assert runner.step()
    runner.events._sink = failing_on("fault")
    with pytest.raises(RuntimeError):
        runner.hold("CHECK_FAILED")                  # the agent's own stop; its report fails
    assert link.sent[-2:] == ["STOP", "DISARM"] and not link.armed


def test_an_agent_callback_that_fails_still_stops_the_motors():
    from helpers import Approve, EndlessCamera, FakeFaces
    from test_motors import CAR_SETUP, car_recipe

    from koz.actions.motors import MockMotorLink
    from koz.agent import FakePlanner
    from koz.agent.loop import Agent
    from koz.events import EventLog

    link, clock = MockMotorLink(armed=True, delayed_status=True), FakeClock()
    agent = Agent(FakePlanner(), CAR_SETUP, lambda: EndlessCamera(ball_in_the_middle(), clock), EventLog(lambda e: None),
                  clock=clock, eval_seconds=1.0, on_frame=raising, motor_link=link,
                  models={"scene_checker": Approve(), "face_detector": FakeFaces(), "brain_driver": StillBrain()})
    with pytest.raises(RuntimeError):
        agent.run_recipe(car_recipe())
    assert link.sent[-2:] == ["STOP", "DISARM"] and not link.armed
    must_be_armed_again(link)


def test_a_job_thread_that_crashes_still_disarms():
    import json

    from helpers import Approve, EndlessCamera, FakeFaces
    from test_motors import CAR_SETUP

    from koz.actions.motors import MockMotorLink
    from koz.events import new_id
    from koz.server import Hub

    class CrashingPlanner:
        name = "crash"

        def plan(self, text):
            raise RuntimeError("injected planner crash")

    link, clock = MockMotorLink(armed=True, delayed_status=True), FakeClock()
    hub = Hub(CAR_SETUP, lambda: EndlessCamera(ball_in_the_middle(), clock), CrashingPlanner(), motor_link=link,
              clock=clock, wall_clock=lambda: 1000, models={"scene_checker": Approve(), "face_detector": FakeFaces()})
    hub.handle(json.dumps({"v": 1, "type": "command", "command_id": new_id(), "session_id": hub.events.session_id,
                           "job_id": new_id(), "trial_id": None, "expires_at": 1010, "command": "start_job",
                           "data": {"input": "prompt", "language": "en", "text": "chase the red ball"}}))
    hub._thread.join(5)
    assert link.sent[-2:] == ["STOP", "DISARM"] and not link.armed
