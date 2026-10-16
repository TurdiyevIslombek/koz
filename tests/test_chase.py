"""The fly-brain car job, from words to wheels (planner -> recipe -> agent -> runner -> motors).
Mock hardware: MockMotorLink for the board, EndlessCamera for the camera."""
import json

import cv2
import numpy as np
import pytest
from helpers import FULL_FRAME, Approve, EndlessCamera, FakeClock, FakeFaces

from koz.actions.motors import MockMotorLink
from koz.agent import Agent, FakePlanner, OllamaPlanner
from koz.agent import loop as agent_loop
from koz.agent import tuner
from koz.brains.flybrain.driver import BrainDriver
from koz.events import EventLog, new_id
from koz.local_setup import LocalSetup
from koz.recipe import check_recipe
from koz.server import Hub

CAR = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME, mount="moving", motor_cap=0.15)

CHASE = [("Chase the red ball", "en", "red"), ("Make the car follow the blue ball with the fly brain", "en", "blue"),
         ("Догони красный мяч", "ru", "red"), ("Qizil koptokni quv", "uz", "red"), ("Қизил тўпни қув", "uz", "red")]
FORBIDDEN = ["Chase the dog", "Chase my little brother", "Drive the car into the cat", "Догони его",
             "Mushukni quv", "Мушукни қув", "follow me"]


@pytest.mark.parametrize("sentence,language,colour", CHASE)
def test_chase_the_ball_becomes_the_fly_brain_car_recipe(sentence, language, colour):
    plan = FakePlanner().plan(sentence)
    assert (plan.job, plan.language) == ("chase_colour", language)
    recipe = check_recipe(plan.recipe).data
    assert recipe["brain"]["type"] == "flybrain" and {"type": "motors", "max_speed_ratio": 0.25} in recipe["actions"]
    assert [b["type"] for b in recipe["blocks"]] == ["privacy_guard", "face_blur", "color_finder"]
    assert "fly brain" in plan.message or "pashsha" in plan.message or "мухи" in plan.message


@pytest.mark.parametrize("sentence", FORBIDDEN)
def test_the_car_never_chases_people_or_animals(sentence):
    assert FakePlanner().plan(sentence).refusal == "MOTOR_TARGET_FORBIDDEN"


def test_finding_a_ball_is_still_not_driving():
    for sentence in ("Find the red ball", "track the green ball", "Qizil koptokni izla"):
        assert FakePlanner().plan(sentence).job == "find_colour"


def test_an_ai_planner_can_pick_the_car_job_too():
    reply = '{"job": "chase_colour", "colour": "green", "school": false, "refusal": null}'
    send = lambda method, path, body, timeout=None: (
        {"models": [{"name": "gemma4:e2b-it-qat"}]} if path == "/api/tags" else {"message": {"content": reply}})
    plan = OllamaPlanner(send=send).plan("drive to the green one")
    assert plan.job == "chase_colour" and check_recipe(plan.recipe).data["brain"]["type"] == "flybrain"


# --- the agent's check and adjustment for the car -------------------------------------------------

def observations(*targets):
    return [{"privacy": "approved", "target": t} for t in targets]


def test_chase_check_first_needs_the_ball_then_needs_it_in_the_middle():
    assert agent_loop.judge("chase_colour", observations("lost", "lost", "left"))[:2] == ("target_visible", "fail")
    assert agent_loop.judge("chase_colour", observations("left", "left", "left"))[:2] == ("target_centered", "fail")
    assert agent_loop.judge("chase_colour", observations("left", "center", "right"))[:2] == ("target_centered", "pass")


def test_not_centring_turns_the_brain_up_then_narrows_the_deadband():
    recipe = FakePlanner().plan("Chase the red ball").recipe
    changes = []
    for _ in range(4):
        change = tuner.propose(recipe, "target_centered", [])
        changes.append(change)
        recipe = check_recipe(tuner.apply(recipe, change)).data   # every adjustment passes the checks
    assert [(c["setting"], c["before"], c["after"]) for c in changes] == [
        ("brain.turn_gain", 1.0, 1.5), ("brain.turn_gain", 1.5, 2.0),
        ("brain.deadband", 0.1, 0.07), ("brain.deadband", 0.07, 0.04)]


# --- the agent drives the car (mock board) --------------------------------------------------------------

def ball_at(x):
    image = np.full((240, 320, 3), 120, np.uint8)
    cv2.circle(image, (x, 120), 22, (0, 0, 220), -1)
    return image


class CarRun:
    def __init__(self, image, armed=True):
        self.clock, self.events, self.opened = FakeClock(), [], 0
        self.link = MockMotorLink(armed=armed)
        self.agent = Agent(FakePlanner(), CAR, self._open, EventLog(self.events.append), clock=self.clock,
                           eval_seconds=1.5, motor_link=self.link,
                           models={"scene_checker": Approve(), "face_detector": FakeFaces(),
                                   "brain_driver": BrainDriver(seed=0)})
        self.image = image

    def _open(self):
        self.opened += 1
        return EndlessCamera(self.image, self.clock)


def test_not_armed_the_car_job_is_refused_before_the_camera_opens():
    run = CarRun(ball_at(160), armed=False)
    result = run.agent.run("Chase the red ball")
    assert (result.state, result.code, run.opened) == ("refused", "MOTOR_NOT_ARMED", 0)
    assert "ARM" not in run.link.sent


def test_a_ball_in_the_middle_passes_and_the_car_drives():
    run = CarRun(ball_at(160))
    result = run.agent.run("Chase the red ball")
    assert result.state == "running" and result.decisions[-1]["check"] == "target_centered"
    moves = [m for m in run.link.sent if m.startswith("M,")]
    assert moves and all(abs(int(v)) <= round(255 * 0.15) for m in moves for v in m[2:].split(","))
    result.runner.stop()
    assert run.link.sent[-2:] == ["STOP", "DISARM"]


def test_a_ball_that_never_gets_centred_turns_the_brain_up_then_stops():
    """The picture doesn't change here (no real car), so the ball stays on the left: the agent turns
    the brain up twice, then stops with ADJUSTMENT_LIMIT and the car is disarmed."""
    run = CarRun(ball_at(40))
    result = run.agent.run("Chase the red ball")
    assert (result.state, result.code) == ("held", "ADJUSTMENT_LIMIT")
    assert [(d["next"], d["change"] and d["change"]["setting"]) for d in result.decisions] == [
        ("adjust", "brain.turn_gain"), ("adjust", "brain.turn_gain"), ("stop", None)]
    assert run.link.sent[-1] == "DISARM" and run.link.state == 0
    revisions = [e for e in run.events if e["type"] == "recipe"]
    assert [r["data"]["recipe"]["brain"]["settings"]["turn_gain"] for r in revisions] == [1.0, 1.5, 2.0]


# --- the runner server: the web can't arm; a person on this computer can --------------------------------

def test_the_web_cannot_arm_but_a_person_here_can():
    clock, sent = FakeClock(), []
    link = MockMotorLink(armed=False)
    hub = Hub(CAR, lambda: EndlessCamera(ball_at(160), clock), FakePlanner(), deliver=sent.append, clock=clock,
              wall_clock=lambda: 1.76e9, eval_seconds=1.0, motor_link=link,
              models={"scene_checker": Approve(), "face_detector": FakeFaces(), "brain_driver": BrainDriver(seed=0)})

    def command(name, data, job_id=None):
        hub.handle(json.dumps({"v": 1, "type": "command", "command_id": new_id(), "session_id": hub.events.session_id,
                               "job_id": job_id, "trial_id": None, "expires_at": 1.76e9 + 10, "command": name,
                               "data": data}))

    command("arm_motors", {})                                     # no such command exists
    assert [e["data"]["code"] for e in sent if e["type"] == "command_result"] == ["INVALID_COMMAND"]
    job = new_id()
    command("start_job", {"input": "prompt", "language": "en", "text": "Chase the red ball"}, job)
    hub._thread.join(5)
    assert [e["data"]["code"] for e in sent if e["type"] == "fault"] == ["MOTOR_NOT_ARMED"] and "ARM" not in link.sent
    hub.arm_motors_by_hand()                                      # the A key / Enter on this computer
    assert link.sent == ["ARM"] and link.armed
    job = new_id()
    command("start_job", {"input": "prompt", "language": "en", "text": "Chase the red ball"}, job)
    import time
    deadline = time.monotonic() + 5
    while not any(m.startswith("M,") for m in link.sent) and time.monotonic() < deadline:
        time.sleep(0.01)
    command("stop_job", {}, job)
    hub._thread.join(5)
    assert any(m.startswith("M,") for m in link.sent) and link.sent[-1] == "DISARM"
