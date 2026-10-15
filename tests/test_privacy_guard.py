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
    assert guard.line.startswith("check 1 @ 0.0 s (room+objects): room classroom 0.70")
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


class CountingScene(FakeScene):
    def __init__(self, probabilities):
        super().__init__(probabilities)
        self.calls = 0

    def probabilities(self, image):
        self.calls += 1
        return self.p


def test_objects_every_check_room_every_three_seconds():
    """Live test #4: objects every 0.5 s, the room every 3 s (when the view stays still)."""
    clock, scene, objects = FakeClock(), CountingScene(room(CLASSROOM)), FakeObjects({})
    gate = PrivacyGate(GuardCheck(scene, objects, clock=clock), clock)
    for _ in range(int(4.0 / 0.1)):          # 4 s of frames at 10 fps
        gate.admit(FRAME)
        clock.advance(0.1)
    assert objects.calls == 8                 # every 0.5 s
    assert scene.calls == 2                   # at 0 s and at 3 s


def test_camera_moved_means_check_on_the_next_frame():
    clock, scene, objects = FakeClock(), CountingScene(room(CLASSROOM)), FakeObjects({})
    guard = GuardCheck(scene, objects, clock=clock)
    gate = PrivacyGate(guard, clock)
    gate.admit(FRAME)
    other_view = np.zeros((240, 320, 3), np.uint8)
    other_view[:, :160] = 230                 # a very different picture
    clock.advance(0.1)
    assert gate.due(other_view) is False      # moved, but only 0.1 s since the last check
    clock.advance(0.1)
    assert gate.due(FRAME) is False           # same view, 0.2 s later: not yet
    assert gate.due(other_view) is True       # the camera moved: check now
    gate.admit(other_view)
    assert objects.calls == 2 and scene.calls == 1   # the room waits: checked < 1 s ago
    clock.advance(1.0)
    gate.admit(other_view)                     # still on the new view, 1 s later: room checked again
    assert scene.calls == 2


def test_moving_car_does_not_check_on_every_frame():
    """On the car the view always changes, so only the 0.5 s schedule applies."""
    clock = FakeClock()
    gate = PrivacyGate(GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({}), clock=clock, watch_changes=False), clock)
    gate.admit(FRAME)
    clock.advance(0.1)
    assert gate.due(np.zeros((240, 320, 3), np.uint8)) is False


def test_check_line_says_how_long_after_first_seen_it_stopped():
    clock = FakeClock()
    guard = GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"toilet": 0.8}), clock=clock)
    guard.check(FRAME)
    clock.advance(0.07)
    assert guard.check(FRAME).state == "blocked"
    assert guard.stop_delay == pytest.approx(0.07)
    assert guard.line.endswith("-> blocked, 0.07 s after first seen")


def test_routine_checks_do_not_flip_the_status(test_video):
    """Contract 8.1 (agreed with Codex, Oct 15): 'checking' only before approval or while confirming."""
    clock, sent = FakeClock(), []
    runner = Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME),
                    TickingCamera(FileCamera(test_video, clock=clock), clock, 0.25), EventLog(sent.append),
                    scene_checker=GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({}), clock=clock),
                    face_detector=FakeFaces(), clock=clock)
    runner.run()   # 18 frames, 4.5 s: about 9 privacy checks
    states = [e["data"]["state"] for e in sent if e["type"] == "status"]
    assert "checking" not in states[1:]


def test_while_confirming_no_frame_is_shown_and_no_block_runs(test_video):
    clock = FakeClock()
    faces = FakeFaces()
    runner = Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME),
                    TickingCamera(FileCamera(test_video, clock=clock), clock, 0.05), EventLog(list().append),
                    scene_checker=GuardCheck(FakeScene(room(CLASSROOM)), FakeObjects({"bed": 0.8}, {}, {}), clock=clock),
                    face_detector=faces, clock=clock)
    runner.step()                              # bed seen once: confirming
    assert runner.preview is None and faces.calls == 0 and runner.state == "checking"
    runner.step()                              # not seen: still confirming (2 of 3 still possible)
    assert runner.preview is None and faces.calls == 0
    runner.step()                              # not seen again: approved, the frame is processed
    assert runner.preview is not None and faces.calls == 1 and runner.state == "running"
