"""The runner on the recorded test video: fixed order, privacy fails closed, unknown is not 0."""
import threading
from dataclasses import replace

import numpy as np
import pytest

from helpers import (LABELS, FULL_FRAME, LEFT_THIRD, Approve, BrokenFaces, Explode, FakeClock,
                     FakeFaces, Refuse, Sequence, SlowApprove, StaleEveryOther, TickingCamera,
                     color_recipe)
from koz import policy
from koz.capture import FileCamera
from koz.errors import KozError
from koz.events import EventLog
from koz.local_setup import LocalSetup
from koz.privacy import FAILED, PrivacyGate, PrivacyResult
from koz.recipe import check_recipe
from koz.runner import Runner

ENVELOPE = {"v", "type", "session_id", "seq", "job_id", "trial_id", "revision", "minute", "data"}


def make(test_video, seconds_per_frame=1.0, camera_cls=TickingCamera, area=FULL_FRAME,
         clock=None, **runner_args):
    clock = clock or FakeClock()
    sent = []
    camera = camera_cls(FileCamera(test_video, clock=clock), clock, seconds_per_frame)
    runner = Runner(check_recipe(color_recipe()), LocalSetup(True, area), camera,
                    EventLog(sent.append), clock=clock, **runner_args)
    return runner, sent, clock


def of_type(sent, kind):
    return [e["data"] for e in sent if e["type"] == kind]


def states(sent):
    """Status states in order, with repeated heartbeats folded together."""
    result = []
    for status in of_type(sent, "status"):
        if not result or result[-1] != status["state"]:
            result.append(status["state"])
    return result


def test_runs_the_recipe_on_recorded_video(test_video):
    runner, sent, _ = make(test_video, scene_checker=Approve())
    assert runner.run() == "idle"
    assert [o["target"] for o in of_type(sent, "observation")] == LABELS
    assert states(sent)[:2] == ["checking", "running"] and states(sent)[-1] == "idle"
    assert all(set(e) == ENVELOPE and e["revision"] == 1 for e in sent)
    assert [e["seq"] for e in sent] == list(range(1, len(sent) + 1))
    assert all(o["coverage"] == "complete" and o["privacy"] == "approved" for o in of_type(sent, "observation"))
    status = of_type(sent, "status")[1]
    assert status["opencv_major"] == 5 and status["capabilities"] == ["recorded_fixture"]


def test_at_most_one_observation_per_second(test_video):
    runner, sent, _ = make(test_video, seconds_per_frame=0.1, scene_checker=Approve())
    runner.run()
    assert len(of_type(sent, "observation")) == 2   # 18 frames at 10 fps = 1.8 s


def test_without_the_scene_model_the_runner_refuses_to_start(test_video, tmp_path, monkeypatch):
    monkeypatch.setattr("koz.scene.MODEL_PATH", tmp_path / "missing.onnx")
    with pytest.raises(KozError) as caught:
        Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME), FileCamera(test_video),
               EventLog(list().append), face_detector=FakeFaces())
    assert caught.value.code == "PRIVACY_UNAVAILABLE"


def test_an_unavailable_check_lets_nothing_through(test_video):
    faces = FakeFaces()
    runner, sent, _ = make(test_video, scene_checker=Sequence(FAILED), face_detector=faces)
    assert runner.run() == "refused"
    assert of_type(sent, "fault") == [{"code": "PRIVACY_UNAVAILABLE", "effect": "off"}]
    assert of_type(sent, "observation")[0]["target"] == "unknown"
    assert of_type(sent, "status")[-1]["camera_on"] is False
    assert faces.calls == 0 and runner.preview is None   # no frame got past the gate


@pytest.mark.parametrize("checker, code", [
    (Refuse("PRIVATE_BATHROOM"), "PRIVATE_BATHROOM"),
    (Explode(), "PRIVACY_UNAVAILABLE"),
    (PrivacyResult, "PRIVACY_UNAVAILABLE"),   # not a checker at all
])
def test_private_or_broken_scene_check_refuses(test_video, checker, code):
    runner, sent, _ = make(test_video, scene_checker=checker, face_detector=FakeFaces())
    assert runner.run() == "refused"
    assert of_type(sent, "fault") == [{"code": code, "effect": "off"}]


def test_slow_scene_check_counts_as_failed(test_video):
    clock = FakeClock()
    runner, sent, _ = make(test_video, clock=clock, scene_checker=SlowApprove(clock, 6.0),
                           face_detector=FakeFaces())
    assert runner.run() == "refused"
    assert of_type(sent, "fault") == [{"code": "PRIVACY_UNAVAILABLE", "effect": "off"}]


def test_recheck_stops_a_running_job(test_video):
    checker = Sequence(PrivacyResult("approved"), PrivacyResult("blocked", "PRIVATE_BEDROOM"))
    half = policy.PRIVACY_RECHECK_S / 2
    runner, sent, _ = make(test_video, seconds_per_frame=half, scene_checker=checker, face_detector=FakeFaces())
    assert runner.run() == "held"   # frame 3 is one recheck interval after the first check
    assert of_type(sent, "fault") == [{"code": "PRIVATE_BEDROOM", "effect": "held"}]
    assert [o["target"] for o in of_type(sent, "observation")] == ["left", "left", "unknown"]
    assert of_type(sent, "observation")[-1]["unknown_reason"] == "PRIVATE_BEDROOM"
    assert states(sent) == ["checking", "running", "checking", "held"]   # the recheck is visible


def test_stale_frames_are_unknown_not_lost(test_video):
    runner, sent, _ = make(test_video, camera_cls=StaleEveryOther, scene_checker=Approve(),
                           face_detector=FakeFaces())
    assert runner.run() == "idle"   # stale frames pause outputs; they don't stop the job
    observations = of_type(sent, "observation")
    assert observations[0]["target"] == "left" and observations[0]["coverage"] == "complete"
    assert observations[1]["target"] == "unknown" and observations[1]["coverage"] == "gapped"
    assert [o["unknown_reason"] for o in observations[:3]] == [None, "FRAME_STALE", None]
    assert all(o["coverage"] == "gapped" for o in observations[1:])   # the gap stays recorded


def test_slow_processing_is_unknown(test_video):
    clock = FakeClock()
    runner, sent, _ = make(test_video, clock=clock, scene_checker=Approve(),
                           face_detector=FakeFaces(clock=clock, seconds=0.6))
    runner.run()
    assert {o["target"] for o in of_type(sent, "observation")} == {"unknown"}
    assert {o["unknown_reason"] for o in of_type(sent, "observation")} == {"OVERLOADED"}


def test_blur_failure_stops_the_job(test_video):
    runner, sent, _ = make(test_video, scene_checker=Approve(), face_detector=BrokenFaces())
    assert runner.run() == "held"
    assert of_type(sent, "fault") == [{"code": "BLUR_UNAVAILABLE", "effect": "held"}]
    assert of_type(sent, "observation")[-1]["unknown_reason"] == "BLUR_UNAVAILABLE"


def test_outside_the_allowed_area_is_black(test_video):
    runner, sent, _ = make(test_video, area=LEFT_THIRD, scene_checker=Approve(), face_detector=FakeFaces())
    runner.run()
    targets = [o["target"] for o in of_type(sent, "observation")]
    assert targets[:3] == ["left"] * 3          # the ball on the left is inside the allowed area
    assert targets[3:9] == ["lost"] * 6         # the balls in the middle and on the right are blacked out


@pytest.mark.parametrize("setup, code", [
    (LocalSetup(False, FULL_FRAME), "OWNERSHIP_REQUIRED"),
    (LocalSetup(True, ()), "ALLOWED_AREA_REQUIRED"),
    (LocalSetup(True, (((0, 0), (0.5, 0.5), (1, 1)),)), "ALLOWED_AREA_REQUIRED"),   # a line, no area
    (LocalSetup(True, (((0, 0), (2, 0), (0, 2)),)), "ALLOWED_AREA_REQUIRED"),       # outside the frame
    (LocalSetup(True, FULL_FRAME, school=True), "SCHOOL_COUNTS_ONLY"),             # local school flag
])
def test_local_setup_is_required(test_video, setup, code):
    with pytest.raises(KozError) as caught:
        Runner(check_recipe(color_recipe()), setup, FileCamera(test_video), EventLog(list().append),
               scene_checker=Approve(), face_detector=FakeFaces())
    assert caught.value.code == code


def test_only_checked_recipes_run(test_video):
    with pytest.raises(TypeError):
        Runner(color_recipe(), LocalSetup(True, FULL_FRAME), FileCamera(test_video), EventLog(list().append))


def test_preview_is_blurred_and_dropped_on_stop(test_video):
    runner, _, _ = make(test_video, scene_checker=Approve(), face_detector=FakeFaces([(100, 80, 60, 60)]))
    runner.step()
    assert runner.preview is not None
    assert len({tuple(p) for p in runner.preview[90:130, 110:150].reshape(-1, 3)}) <= 36
    runner.run()
    assert runner.preview is None


def test_status_heartbeat_every_second(test_video):
    runner, sent, _ = make(test_video, seconds_per_frame=0.25, scene_checker=Approve(), face_detector=FakeFaces())
    runner.run()   # 18 frames = 4.5 s
    assert 4 <= sum(s["state"] == "running" for s in of_type(sent, "status")) <= 5


class CrashOnSecondFrame(TickingCamera):
    def read(self):
        frame = super().read()
        if frame.index == 1:
            raise RuntimeError("camera unplugged")
        return frame


def test_unexpected_error_stops_the_job(test_video):
    runner, sent, _ = make(test_video, camera_cls=CrashOnSecondFrame, scene_checker=Approve(),
                           face_detector=FakeFaces())
    assert runner.run() == "held"
    assert of_type(sent, "fault") == [{"code": "INTERNAL_ERROR", "effect": "held"}]
    assert runner.camera.is_open is False and runner.preview is None
    assert of_type(sent, "observation")[-1]["target"] == "unknown"
    assert of_type(sent, "observation")[-1]["unknown_reason"] == "INTERNAL_ERROR"


def test_malformed_privacy_answer_fails_closed(test_video):
    class Garbled:
        def check(self, image):
            return PrivacyResult("unknown", [])
    runner, sent, _ = make(test_video, scene_checker=Garbled(), face_detector=FakeFaces())
    assert runner.run() == "refused"
    assert of_type(sent, "fault") == [{"code": "PRIVACY_UNAVAILABLE", "effect": "off"}]


def test_stuck_scene_check_times_out():
    release = threading.Event()

    class Stuck:
        def check(self, image):
            release.wait(10)
            return PrivacyResult("approved")
    try:
        gate = PrivacyGate(Stuck(), timeout_s=0.05)
        assert gate.admit(np.zeros((240, 320, 3), np.uint8)) == PrivacyResult("unknown", "PRIVACY_UNAVAILABLE")
    finally:
        release.set()


def test_preview_is_dropped_when_frames_are_stale(test_video):
    runner, _, _ = make(test_video, camera_cls=StaleEveryOther, scene_checker=Approve(), face_detector=FakeFaces())
    runner.step()
    assert runner.preview is not None
    runner.step()   # this frame is 1 s old
    assert runner.preview is None


def test_slow_frame_never_reaches_the_preview(test_video):
    clock = FakeClock()
    runner, _, _ = make(test_video, clock=clock, scene_checker=Approve(),
                        face_detector=FakeFaces(clock=clock, seconds=0.6))
    runner.step()
    assert runner.preview is None


def test_a_changed_checked_recipe_is_checked_again(test_video):
    checked = check_recipe(color_recipe())
    checked.data["camera"]["size"] = "800x600"   # above the resolution cap
    with pytest.raises(KozError) as caught:
        Runner(checked, LocalSetup(True, FULL_FRAME), FileCamera(test_video), EventLog(list().append),
               scene_checker=Approve(), face_detector=FakeFaces())
    assert caught.value.code == "INVALID_RECIPE"


def test_reason_changes_are_sent_at_once(test_video):
    """Every frame flips between stale and fresh, so every frame is sent, even at 10 fps."""
    runner, sent, _ = make(test_video, seconds_per_frame=0.1, camera_cls=StaleEveryOther,
                           scene_checker=Approve(), face_detector=FakeFaces())
    runner.run()
    reasons = [o["unknown_reason"] for o in of_type(sent, "observation")]
    assert reasons == [None, "FRAME_STALE"] * 9


class StaleFirstFrame(TickingCamera):
    def read(self):
        frame = super().read()
        return replace(frame, t=frame.t - 1.0) if frame is not None and frame.index == 0 else frame


def test_stale_before_the_first_privacy_check_says_frame_stale(test_video):
    runner, sent, _ = make(test_video, camera_cls=StaleFirstFrame, scene_checker=Approve(),
                           face_detector=FakeFaces())
    runner.step()
    first = of_type(sent, "observation")[0]
    assert (first["privacy"], first["target"], first["unknown_reason"]) == ("unknown", "unknown", "FRAME_STALE")


def test_classroom_counter_on_recorded_video(test_video):
    """School mode: one person walks right to left across the door line, another stays."""
    from helpers import ScriptedPeople, classroom_recipe, walker
    path = walker(260, 60, 18)
    stays = [(20, 60, 60, 180)] * 18
    clock = FakeClock()
    sent = []
    camera = TickingCamera(FileCamera(test_video, clock=clock), clock, 1.0)
    runner = Runner(check_recipe(classroom_recipe()), LocalSetup(True, FULL_FRAME, school=True), camera,
                    EventLog(sent.append), scene_checker=Approve(), face_detector=FakeFaces(),
                    person_detector=ScriptedPeople([[p, s] for p, s in zip(path, stays)]), clock=clock)
    assert runner.run() == "idle"
    last = of_type(sent, "observation")[-1]
    assert last["entered"] == {"state": "known", "value": 1, "reason": None}
    assert last["exited"]["value"] == 0 and last["occupancy"]["value"] == 2
    assert last["target"] is None   # no colour finder in this recipe
    assert all(s["school"] for s in of_type(sent, "status"))


def test_counts_become_unknown_with_the_reason(test_video):
    from helpers import ScriptedPeople, classroom_recipe
    clock = FakeClock()
    sent = []
    camera = StaleEveryOther(FileCamera(test_video, clock=clock), clock, 1.0)
    runner = Runner(check_recipe(classroom_recipe()), LocalSetup(True, FULL_FRAME), camera, EventLog(sent.append),
                    scene_checker=Approve(), face_detector=FakeFaces(), person_detector=ScriptedPeople([]),
                    clock=clock)
    runner.run()
    stale = of_type(sent, "observation")[1]
    assert stale["occupancy"] == stale["entered"] == {"state": "unknown", "value": None, "reason": "FRAME_STALE"}
    assert stale["unknown_reason"] == "FRAME_STALE"


def test_strict_mode_comes_from_local_setup(test_video):
    runner = Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME, strict=True),
                    FileCamera(test_video), EventLog(list().append), scene_checker=Approve(), face_detector=FakeFaces())
    assert runner.strict is True
    with pytest.raises(KozError) as caught:
        Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME, strict="yes"),
               FileCamera(test_video), EventLog(list().append), scene_checker=Approve(), face_detector=FakeFaces())
    assert caught.value.code == "INVALID_COMMAND"


@pytest.mark.skipif(not __import__("koz.scene", fromlist=["MODEL_PATH"]).MODEL_PATH.exists(),
                    reason="run scripts/fetch_models.py first")
def test_the_default_guard_gets_the_strict_setting(test_video):
    runner = Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME, strict=True),
                    FileCamera(test_video), EventLog(list().append), face_detector=FakeFaces())
    assert runner.guard.strict is True
    default = Runner(check_recipe(color_recipe()), LocalSetup(True, FULL_FRAME), FileCamera(test_video),
                     EventLog(list().append), face_detector=FakeFaces())
    assert default.guard.strict is False   # live test #3: run anywhere, stop on what you see
