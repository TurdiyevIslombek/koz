"""The privacy guard's check (koz/privacy.py): object check (bed, toilet, sink), then the room
check, with stand-in models so each rule can be tried exactly."""
import numpy as np
import pytest

from helpers import FULL_FRAME, FakeClock, FakeFaces, TickingCamera, color_recipe
from koz.capture import FileCamera
from koz.events import EventLog
from koz.local_setup import LocalSetup
from koz.privacy import GuardCheck, PrivacyGate, PrivacyResult
from koz.recipe import check_recipe
from koz.runner import Runner
from koz.scene import CLASSES, NAMES, PlacesSceneChecker, decide

FRAME = np.full((240, 320, 3), 128, np.uint8)
CLASSROOM, KITCHEN, BATHROOM = NAMES.index("classroom"), NAMES.index("kitchen"), NAMES.index("bathroom")


def room(index, p=0.7):
    probabilities = np.full(CLASSES, (1 - p) / (CLASSES - 1))
    probabilities[index] = p
    return probabilities


class FakeScene:
    """Places365 stand-in: always the same room guesses."""
    judge = staticmethod(decide)
    top = staticmethod(PlacesSceneChecker.top)

    def __init__(self, probabilities, dark=False):
        self.p, self.dark = probabilities, dark

    def probabilities(self, image):
        return self.p

    def too_dark_or_flat(self, image):
        return self.dark


class FakeObjects:
    """NanoDet stand-in: check n sees script[n] (e.g. {"bed": 0.8})."""

    def __init__(self, *script):
        self.script, self.calls = list(script), 0

    def find(self, image):
        found = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        return found


def results(guard, n):
    return [guard.check(FRAME) for _ in range(n)]


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("name, code", [("bed", "PRIVATE_BEDROOM"), ("toilet", "PRIVATE_BATHROOM")])
def test_bed_or_toilet_seen_twice_stops_in_both_modes(strict, name, code):
    guard = GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({name: 0.8}), strict=strict)
    first, second = results(guard, 2)
    assert first == PrivacyResult("unknown", "PRIVACY_UNCERTAIN", seen=name, confirming=True)
    assert second == PrivacyResult("blocked", code, seen=name)


def test_seen_once_then_twice_not_is_not_a_stop():
    guard = GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"bed": 0.8}, {}, {}))
    assert [(r.state, r.confirming) for r in results(guard, 3)] == \
        [("unknown", True), ("unknown", True), ("approved", False)]


def test_two_of_the_last_three_checks():
    """Codex review: after seen, not seen, it must not resume before the third check."""
    guard = GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"bed": 0.8}, {}, {"bed": 0.8}))
    first, second, third = results(guard, 3)
    assert first.confirming and second.confirming
    assert third == PrivacyResult("blocked", "PRIVATE_BEDROOM", seen="bed")


def test_a_broken_object_check_is_a_failed_check_not_nothing_seen():
    class Broken:
        def find(self, image):
            raise ValueError("NanoDet output is not what the model gives")
    gate = PrivacyGate(GuardCheck(FakeScene(room(CLASSROOM)), Broken()))
    assert gate.admit(FRAME) == PrivacyResult("unknown", "PRIVACY_UNAVAILABLE")


def test_sink_stops_only_with_a_bathroom_like_room():
    bathroomish = room(BATHROOM, 0.35)
    bathroomish[KITCHEN] = 0.4   # top: kitchen, then bathroom
    guard = GuardCheck(FakeScene(bathroomish / bathroomish.sum()), FakeObjects({"sink": 0.6}))
    assert guard.check(FRAME) == PrivacyResult("blocked", "PRIVATE_BATHROOM", seen="sink")
    kitchen = GuardCheck(FakeScene(room(KITCHEN)), FakeObjects({"sink": 0.6}))
    assert kitchen.check(FRAME) == PrivacyResult("approved")


def test_darkness_comes_first():
    guard = GuardCheck(FakeScene(room(CLASSROOM), dark=True), FakeObjects({"bed": 0.9}))
    assert guard.check(FRAME) == PrivacyResult("unknown", "PRIVACY_UNCERTAIN")


def test_default_relies_on_objects_not_on_a_vague_room_guess():
    vague_bedroom = room(KITCHEN, 0.5)
    vague_bedroom[NAMES.index("bedroom")] = 0.15   # would stop the strict guard (top 5 above 0.10)
    vague_bedroom /= vague_bedroom.sum()
    strict = GuardCheck(FakeScene(vague_bedroom), FakeObjects({}), strict=True)
    desk = GuardCheck(FakeScene(vague_bedroom), FakeObjects({}))
    assert strict.check(FRAME).state == "blocked" and desk.check(FRAME).state == "approved"


def test_check_line_names_rooms_objects_and_result():
    guard = GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"bed": 0.83}))
    guard.check(FRAME)
    assert guard.line.startswith("check 1: room classroom 0.70")
    assert "| seen bed 0.83 -> unknown (confirming)" in guard.line


def test_gate_checks_again_on_the_next_frame_while_confirming():
    clock = FakeClock()
    gate = PrivacyGate(GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"bed": 0.8})), clock)
    assert gate.admit(FRAME).confirming
    assert gate.due()                              # not 10 s later: right away
    assert gate.admit(FRAME).state == "blocked"


def test_runner_holds_frames_while_confirming_then_stops(test_video):
    clock, sent = FakeClock(), []
    guard = GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"bed": 0.8}))
    faces = FakeFaces()
    runner = Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME),
                    TickingCamera(FileCamera(test_video, clock=clock), clock, 0.1), EventLog(sent.append),
                    scene_checker=guard, face_detector=faces, clock=clock)
    assert runner.run() == "refused"
    assert [e["data"] for e in sent if e["type"] == "fault"] == [{"code": "PRIVATE_BEDROOM", "effect": "off"}]
    assert faces.calls == 0 and guard.checks == 2   # no frame got past the guard
