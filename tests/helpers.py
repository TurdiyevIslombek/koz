"""Test helpers: the recorded test video (input for the mock camera), fake clocks,
fake privacy checkers and fake face detectors. Used only by tests."""
import copy
from dataclasses import replace

import cv2
import numpy as np

from koz.privacy import PrivacyResult

WIDTH, HEIGHT, FPS = 320, 240, 10
FRAMES_PER_SCENE = 3
RED = (0, 0, 220)            # BGR
RED_PAST_ZERO = (40, 0, 230)  # hue about 175: red on the other side of OpenCV's hue circle
GREEN = (0, 200, 0)
BALL_RADIUS = 22

# (label color_finder should report, what to draw). 3 frames each.
SCENES = [
    ("left", ("ball", RED, 60)),
    ("center", ("ball", RED, 160)),
    ("right", ("ball", RED, 260)),
    ("lost", ("ball", GREEN, 160)),        # another colour is not the target
    ("lost", ("speck", RED, 160)),         # a 4x4 red speck is far below min_area_ratio
    ("left", ("ball", RED_PAST_ZERO, 60)),  # hue wrap-around still counts as red
]
LABELS = [label for label, _ in SCENES for _ in range(FRAMES_PER_SCENE)]

FULL_FRAME = (((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),)
LEFT_THIRD = (((0.0, 0.0), (0.33, 0.0), (0.33, 1.0), (0.0, 1.0)),)

LOCKED = [{"type": "privacy_guard", "settings": {}}, {"type": "face_blur", "settings": {}}]
COLOR_SETTINGS = {"hue_center": 0, "hue_half_width": 10, "saturation_min": 120,
                  "value_min": 80, "min_area_ratio": 0.01}


def record_test_video(path):
    """Write the test video as MJPEG, the same compression the ESP32-CAM streams."""
    rng = np.random.default_rng(7)
    ramp = np.linspace(100, 160, WIDTH, dtype=np.float64)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), FPS, (WIDTH, HEIGHT))
    assert writer.isOpened()
    for _, (kind, colour, x) in SCENES:
        for _ in range(FRAMES_PER_SCENE):
            grey = np.tile(ramp, (HEIGHT, 1)) + rng.normal(0, 8, (HEIGHT, WIDTH))
            frame = np.clip(np.dstack([grey, grey, grey]), 0, 255).astype(np.uint8)
            if kind == "ball":
                cv2.circle(frame, (x, HEIGHT // 2), BALL_RADIUS, colour, -1)
            else:
                frame[118:122, x - 2:x + 2] = colour
            writer.write(frame)
    writer.release()
    return path


def color_recipe(school=False, **settings):
    return {"version": 1, "language": "uz",
            "camera": {"source": "device_camera", "size": f"{WIDTH}x{HEIGHT}", "fps": FPS},
            "blocks": copy.deepcopy(LOCKED) + [{"type": "color_finder",
                                                "settings": {**COLOR_SETTINGS, **settings}}],
            "brain": {"type": "none"}, "actions": [{"type": "dashboard"}],
            "privacy": {"school": school}}


class FakeClock:
    def __init__(self, start=1000.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class TickingCamera:
    """Wraps a camera; moves the fake clock forward before each frame."""

    def __init__(self, camera, clock, seconds_per_frame):
        self.camera, self.clock, self.dt = camera, clock, seconds_per_frame
        self.capabilities = camera.capabilities

    @property
    def is_open(self):
        return self.camera.is_open

    def read(self):
        self.clock.advance(self.dt)
        return self.camera.read()

    def close(self):
        self.camera.close()


class StaleEveryOther(TickingCamera):
    """Every second frame arrives already 1 s old."""

    def read(self):
        frame = super().read()
        if frame is not None and frame.index % 2 == 1:
            frame = replace(frame, t=frame.t - 1.0)
        return frame


class Approve:
    def check(self, image):
        return PrivacyResult("approved")


class Refuse:
    def __init__(self, code):
        self.code = code

    def check(self, image):
        return PrivacyResult("blocked", self.code)


class Explode:
    def check(self, image):
        raise RuntimeError("model crashed")


class Sequence:
    """Returns the given results in order, one per scene check."""

    def __init__(self, *results):
        self.results = list(results)

    def check(self, image):
        return self.results.pop(0)


class SlowApprove:
    def __init__(self, clock, seconds):
        self.clock, self.seconds = clock, seconds

    def check(self, image):
        self.clock.advance(self.seconds)
        return PrivacyResult("approved")


class FakeFaces:
    """A face detector that 'finds' the given boxes and counts its calls."""

    def __init__(self, boxes=(), clock=None, seconds=0.0):
        self.boxes, self.clock, self.seconds = list(boxes), clock, seconds
        self.calls = 0

    def detect(self, image):
        self.calls += 1
        if self.clock is not None:
            self.clock.advance(self.seconds)
        return self.boxes


class BrokenFaces:
    def detect(self, image):
        raise RuntimeError("detector crashed")


def classroom_recipe(line=((0.5, 0.0), (0.5, 1.0)), school=True):
    return {"version": 1, "language": "ru",
            "camera": {"source": "device_camera", "size": f"{WIDTH}x{HEIGHT}", "fps": FPS},
            "blocks": copy.deepcopy(LOCKED) + [
                {"type": "person_detector", "settings": {"min_confidence": 0.5}},
                {"type": "line_counter", "settings": {"line": [list(line[0]), list(line[1])]}}],
            "brain": {"type": "none"}, "actions": [{"type": "dashboard"}], "privacy": {"school": school}}


def walker(start_x, end_x, frames, y=120, size=60):
    """Boxes (x0, y0, x1, y1) for one person walking in a straight line across `frames` frames."""
    step = (end_x - start_x) / (frames - 1)
    return [(start_x + i * step - size / 2, y - size, start_x + i * step + size / 2, y + size) for i in range(frames)]


class ScriptedPeople:
    """A person detector that 'finds' scripted boxes: frame n gets script[n] (a list of boxes)."""

    def __init__(self, script):
        self.script, self.calls = script, 0

    def detect(self, image, min_confidence):
        from koz.blocks import Person
        boxes = self.script[self.calls] if self.calls < len(self.script) else []
        self.calls += 1
        return [Person(tuple(map(float, b)), 0.9) for b in boxes]
