"""Live test #4 target: Ko'z stops within 1 s after a toilet or bed comes into view.

Measured on recorded clips made from real Places365 photos (tests/places365_photos.txt):
2 s at a desk without a bed, then the camera turns to a bathroom with a toilet (or a
bedroom with a bed), as a quick cut or as a 1 s pan. The clip is MJPEG at 15 fps, like
the ESP32-CAM, and runs through the real runner with the real models. The clock moves
1/15 s per frame, so the delay is what a 15 fps camera would see; the printed processing
time per frame says whether a MacBook keeps up with that."""
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from helpers import FULL_FRAME, FakeClock, TickingCamera
from koz.blocks.person_detector import MODEL_PATH as NANODET_PATH
from koz.capture import FileCamera
from koz.events import EventLog
from koz.local_setup import LocalSetup
from koz.privacy import GuardCheck, PrivateObjects
from koz.recipe import check_recipe
from koz.runner import Runner
from koz.scene import MODEL_PATH, PlacesSceneChecker

HERE = Path(__file__).resolve().parent
PHOTOS = HERE / "fixtures" / "places365"
FPS, SIZE = 15, (640, 480)

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists() or not NANODET_PATH.exists() or not PHOTOS.exists(),
    reason="run scripts/fetch_models.py and scripts/fetch_test_photos.py first")


def frame(photo):
    return cv2.resize(cv2.imread(str(photo)), SIZE, interpolation=cv2.INTER_LINEAR)


@pytest.fixture(scope="module")
def scenes():
    """A desk the default guard runs at, a bathroom with a clear toilet, a bedroom with a clear bed."""
    scene, objects = PlacesSceneChecker(), PrivateObjects()

    def answer(image):
        guard = GuardCheck(scene, objects)
        result = guard.check(image)
        return guard.check(image) if result.confirming else result, guard.last_found

    def best(group, thing):
        scored = [(found.get(thing, 0), p) for p in sorted((PHOTOS / group).glob("*.jpg"))
                  for _, found in [answer(frame(p))]]
        return max(scored)[1]

    desk = next(p for p in sorted((PHOTOS / "desk").glob("*.jpg"))
                if (lambda r: r[0].state == "approved" and not r[1])(answer(frame(p))))
    return {"desk": frame(desk), "toilet": frame(best("bathroom", "toilet")), "bed": frame(best("bedroom", "bed"))}


def record(path, frames):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), FPS, SIZE)
    for f in frames:
        writer.write(f)
    writer.release()
    return path


def pan(a, b, steps):
    """The camera turning from view a to view b: b slides in from the right."""
    out = []
    for i in range(1, steps + 1):
        shift = round(SIZE[0] * i / steps)
        f = np.concatenate([a[:, shift:], b[:, :shift]], axis=1) if shift < SIZE[0] else b.copy()
        out.append(f)
    return out


class TimedCamera(TickingCamera):
    """Remembers when each frame arrived (on the fake 15 fps clock)."""

    def __init__(self, *args):
        super().__init__(*args)
        self.times = []

    def read(self):
        frame = super().read()
        if frame is not None:
            self.times.append(frame.t)
        return frame


def stop_delay(clip, appears_at, mount="fixed"):
    """Seconds from frame `appears_at` (the thing comes into view) to Ko'z stopping."""
    clock, faults = FakeClock(), []
    camera = TimedCamera(FileCamera(clip, clock=clock), clock, 1 / FPS)
    recipe = check_recipe({"version": 1, "language": "en", "camera": {"source": "device_camera", "size": "640x480", "fps": 15},
                           "blocks": [{"type": "privacy_guard", "settings": {}}, {"type": "face_blur", "settings": {}},
                                      {"type": "color_finder", "settings": {"hue_center": 0, "hue_half_width": 10,
                                                                            "saturation_min": 120, "value_min": 70,
                                                                            "min_area_ratio": 0.002}}],
                           "brain": {"type": "none"}, "actions": [{"type": "dashboard"}], "privacy": {"school": False}})
    runner = Runner(recipe, LocalSetup(True, FULL_FRAME, mount=mount), camera,
                    EventLog(lambda e: faults.append((clock(), e["data"])) if e["type"] == "fault" else None), clock=clock)
    started = time.perf_counter()
    runner.run()
    per_frame_ms = (time.perf_counter() - started) * 1000 / max(len(camera.times), 1)
    assert faults, "Ko'z never stopped"
    delay = faults[0][0] - (camera.times[0] + appears_at / FPS)   # negative: stopped before that frame
    print(f"stopped {delay:.2f} s after it came into view ({faults[0][1]['code']}); "
          f"guard: {runner.guard.line}; processing {per_frame_ms:.0f} ms per frame")
    return delay, faults[0][1]["code"]


@pytest.mark.parametrize("thing, code", [("toilet", "PRIVATE_BATHROOM"), ("bed", "PRIVATE_BEDROOM")])
@pytest.mark.parametrize("mount", ["fixed", "moving"])
def test_quick_turn_stops_within_one_second(scenes, tmp_path, thing, code, mount):
    clip = record(tmp_path / "turn.avi", [scenes["desk"]] * (2 * FPS) + [scenes[thing]] * (2 * FPS))
    delay, stopped_for = stop_delay(clip, appears_at=2 * FPS, mount=mount)
    assert stopped_for == code and delay <= 1.0


def test_slow_pan_stops_within_one_second_of_the_view(scenes, tmp_path):
    turning = pan(scenes["desk"], scenes["toilet"], FPS)        # a 1 s turn
    clip = record(tmp_path / "pan.avi", [scenes["desk"]] * (2 * FPS) + turning + [scenes["toilet"]] * (2 * FPS))
    delay, stopped_for = stop_delay(clip, appears_at=2 * FPS + FPS // 2)   # toilet view half in: "comes into view"
    assert stopped_for == "PRIVATE_BATHROOM" and delay <= 1.0
