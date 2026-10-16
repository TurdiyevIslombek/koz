"""The motors action and the fly brain in the runner (koz/actions/motors.py; CLAUDE.md rule 11).
Mock hardware only: MockMotorLink stands in for the board, a fake port for the USB serial."""
import copy
import time

import cv2
import numpy as np
import pytest
from helpers import FULL_FRAME, Approve, EndlessCamera, FakeClock, FakeFaces, Refuse, Sequence, color_recipe

from koz.actions.motors import MockMotorLink, MotorsAction, SerialMotorLink
from koz.brains.flybrain.driver import BrainDriver
from koz.errors import KozError
from koz.events import EventLog
from koz.local_setup import LocalSetup
from koz.privacy import PrivacyResult
from koz.recipe import check_recipe
from koz.runner import Runner

CAR_SETUP = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME, mount="moving", motor_cap=0.2)


def car_recipe(ratio=0.25):
    recipe = color_recipe()
    recipe["brain"] = {"type": "flybrain", "settings": {"turn_gain": 1.0, "deadband": 0.1}}
    recipe["actions"] = [{"type": "dashboard"}, {"type": "motors", "max_speed_ratio": ratio}]
    return recipe


def ball_on_the_left():
    image = np.full((240, 320, 3), 120, np.uint8)
    cv2.circle(image, (50, 120), 22, (0, 0, 220), -1)
    return image


def car_runner(link, guard=None, camera=None, clock=None, **kwargs):
    clock = clock or FakeClock()
    events = []
    runner = Runner(check_recipe(car_recipe(**kwargs)), CAR_SETUP, camera or EndlessCamera(ball_on_the_left(), clock),
                    EventLog(events.append), scene_checker=guard or Approve(), face_detector=FakeFaces(),
                    clock=clock, motor_link=link, brain_driver=BrainDriver(seed=0))
    return runner, events


def moves(link):
    return [tuple(int(v) for v in line[2:].split(",")) for line in link.sent if line.startswith("M,")]


# --- MotorsAction -------------------------------------------------------------------------------

def test_speed_is_the_lower_of_the_recipe_and_the_local_cap():
    link = MockMotorLink(armed=True)
    action = MotorsAction(link, max_speed_ratio=0.25, local_cap=0.2)
    action.drive((255, -150))
    assert link.sent == ["M,51,-30"] and action.status == "enabled"   # x 0.2, not 0.25
    action.pause()
    assert link.sent[-1] == "STOP" and action.status == "stop_commanded"
    action.end()
    assert link.sent[-2:] == ["STOP", "DISARM"] and action.status == "disarmed"
    action.end()
    assert link.sent.count("DISARM") == 1


def test_a_disarmed_or_faulty_board_stops_the_job():
    with pytest.raises(KozError) as error:
        MotorsAction(MockMotorLink(), 0.25, 0.2).drive((100, 100))
    assert error.value.code == "MOTOR_NOT_ARMED"
    link = MockMotorLink(armed=True)
    link.trip("OBSTACLE")
    with pytest.raises(KozError) as error:
        MotorsAction(link, 0.25, 0.2).check()
    assert error.value.code == "MOTOR_SAFETY_STOP"
    link = MockMotorLink(armed=True)
    link.silent = True   # the board stopped talking
    with pytest.raises(KozError):
        MotorsAction(link, 0.25, 0.2).check()


def test_nothing_in_ko_z_arms_the_motors_except_a_person():
    """Contract 3: arming is a local human action. Only arm_by_hand() sends ARM, and only the
    terminal prompt and the runner window call it."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "koz"
    callers = sorted(str(p.relative_to(root)) for p in root.rglob("*.py") if "arm_by_hand(" in p.read_text())
    assert "actions/motors.py" in callers and set(callers) <= {"actions/motors.py", "server.py"}


# --- the serial link (a fake port) ----------------------------------------------------------------

class FakePort:
    def __init__(self, lines=(b"READY\n",)):
        self.incoming, self.written, self.closed = list(lines), [], False

    def readline(self):
        if self.closed:
            raise OSError("closed")
        if self.incoming:
            return self.incoming.pop(0)
        time.sleep(0.01)
        return b""

    def write(self, data):
        self.written.append(data.decode())

    def close(self):
        self.closed = True


def test_serial_link_reads_the_board_and_sends_the_protocol():
    port = FakePort()
    link = SerialMotorLink(serial_port=port)
    assert link.ready and not link.armed and link.fault is None
    link.arm_by_hand()
    link.drive(40, -20)
    link.stop()
    link.disarm()
    assert port.written == ["ARM\n", "M,40,-20\n", "STOP\n", "DISARM\n"]
    link.handle_line("S,1,RUNNING,120")
    assert link.armed and link.distance_cm == 120 and link.fault is None
    link.handle_line("S,0,OBSTACLE,22")
    assert not link.armed and link.fault == "OBSTACLE"
    link.handle_line("garbage,,")
    assert link.fault == "OBSTACLE"
    link.close()


def test_serial_link_says_no_link_when_the_board_goes_silent():
    clock = FakeClock()
    link = SerialMotorLink(serial_port=FakePort(), clock=clock)
    link.handle_line("S,1,RUNNING,100")
    assert link.armed
    clock.advance(0.6)
    assert link.fault == "NO_LINK" and not link.armed
    link.close()


def test_a_board_that_never_answers_is_a_safety_stop():
    with pytest.raises(KozError) as error:
        SerialMotorLink(serial_port=FakePort(lines=()), ready_timeout_s=0.2)
    assert error.value.code == "MOTOR_SAFETY_STOP"


# --- the runner with the fly brain and the motors ----------------------------------------------------

def test_without_a_motor_board_a_car_recipe_does_not_start():
    with pytest.raises(KozError) as error:
        car_runner(None)
    assert error.value.code == "UNSUPPORTED_CAPABILITY"


def test_not_armed_by_hand_means_nothing_moves():
    link = MockMotorLink(armed=False)
    runner, events = car_runner(link)
    assert runner.step() is False and runner.state == "refused" and runner.stop_reason == "MOTOR_NOT_ARMED"
    assert moves(link) == [] and "ARM" not in link.sent
    assert [e["data"]["code"] for e in events if e["type"] == "fault"] == ["MOTOR_NOT_ARMED"]


def test_armed_the_brain_turns_toward_the_ball_and_the_speed_stays_capped():
    link = MockMotorLink(armed=True)
    runner, events = car_runner(link)
    for _ in range(40):
        assert runner.step()
    sent = moves(link)
    assert len(sent) >= 35                                     # one command per approved frame
    assert all(abs(v) <= round(255 * 0.2) for move in sent for v in move)   # the lower cap: 0.2
    left, right = np.mean(sent[10:], axis=0)
    assert left < right                                        # ball on the left: it turns left
    status = [e for e in events if e["type"] == "status"][-1]["data"]
    assert status["motor"] == "enabled"
    assert all("wheel" not in str(e).lower() for e in events)  # wheel speeds never leave the computer
    runner.stop()
    assert link.sent[-2:] == ["STOP", "DISARM"] and runner.stop_reason == "stop_job"


def test_a_stale_frame_stops_the_motors_but_not_the_job():
    clock = FakeClock()

    class Stale(EndlessCamera):
        def read(self):
            frame = super().read()
            return frame if self.index != 6 else type(frame)(frame.image, frame.t - 1.0, frame.index)

    link = MockMotorLink(armed=True)
    runner, events = car_runner(link, camera=Stale(ball_on_the_left(), clock), clock=clock)
    for _ in range(8):
        runner.step()
    stale = next(i for i, line in enumerate(link.sent) if line == "STOP")
    assert link.sent[stale - 1].startswith("M,") and link.sent[stale + 1].startswith("M,")   # resumes after
    assert runner.state == "running" and "DISARM" not in link.sent


def test_a_privacy_stop_stops_and_disarms_the_car():
    link = MockMotorLink(armed=True)
    guard = Sequence(*[PrivacyResult("approved")] * 3 + [PrivacyResult("blocked", "PRIVATE_BATHROOM")])
    runner, events = car_runner(link, guard=guard)
    for _ in range(80):
        if not runner.step():
            break
    assert runner.state == "held" and runner.stop_reason == "PRIVATE_BATHROOM"
    assert link.sent[-2:] == ["STOP", "DISARM"] and link.state == 0
    assert [e for e in events if e["type"] == "status"][-1]["data"]["motor"] == "disarmed"


def test_a_board_fault_holds_the_job():
    link = MockMotorLink(armed=True)
    runner, events = car_runner(link)
    runner.step()
    link.trip("OBSTACLE")   # the board saw the wall (or the ball) closer than stop_cm and disarmed
    assert runner.step() is False and runner.state == "held" and runner.stop_reason == "MOTOR_SAFETY_STOP"
    assert [e["data"] for e in events if e["type"] == "fault"] == [{"code": "MOTOR_SAFETY_STOP", "effect": "held"}]


def test_the_motors_pause_while_the_privacy_guard_checks():
    link = MockMotorLink(armed=True)
    runner, _ = car_runner(link)
    runner.step()                                   # the first check, then approved and driving
    first_moves = len(moves(link))
    sent_before = len(link.sent)
    runner._gate._checked_at -= 1.0                 # the next frame is due a check
    runner.step()
    assert link.sent[sent_before] == "STOP" and len(moves(link)) == first_moves + 1   # stop, check, then drive


def test_school_mode_never_gets_motors():
    recipe = car_recipe()
    recipe["privacy"]["school"] = True
    with pytest.raises(KozError):
        check_recipe(copy.deepcopy(recipe))
