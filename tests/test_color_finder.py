"""color_finder on the recorded test video, read through the mock camera."""
import pytest

from helpers import COLOR_SETTINGS, FRAMES_PER_SCENE, LABELS, WIDTH
from koz.blocks import ColorFinder
from koz.capture import FileCamera


def frames(path):
    with FileCamera(path) as camera:
        while (frame := camera.read()) is not None:
            yield frame


def test_labels_on_recorded_video(test_video):
    finder = ColorFinder(COLOR_SETTINGS)
    assert [finder.find(f.image).label for f in frames(test_video)] == LABELS


@pytest.mark.parametrize("scene, expected_x", [(0, 60), (1, 160), (2, 260)])
def test_position(test_video, scene, expected_x):
    frame = list(frames(test_video))[scene * FRAMES_PER_SCENE]
    target = ColorFinder(COLOR_SETTINGS).find(frame.image)
    assert target.x == pytest.approx((expected_x + 0.5) / WIDTH, abs=0.02)
    assert target.y == pytest.approx(0.5, abs=0.02)
    assert 0.01 < target.area_ratio < 0.03


def test_lost_has_no_position(test_video):
    frame = list(frames(test_video))[3 * FRAMES_PER_SCENE]   # green ball
    target = ColorFinder(COLOR_SETTINGS).find(frame.image)
    assert (target.label, target.x, target.y, target.area_ratio) == ("lost", None, None, 0.0)


def test_settings_change_the_result(test_video):
    """The kind of change the agent's adjust step makes: a narrower hue range misses
    the red that sits past 0 on the hue circle."""
    frame = list(frames(test_video))[5 * FRAMES_PER_SCENE]
    assert ColorFinder(COLOR_SETTINGS).find(frame.image).label == "left"
    assert ColorFinder({**COLOR_SETTINGS, "hue_half_width": 2}).find(frame.image).label == "lost"


# --- "ball found" means a round blob of real size (Oct 15) ---------------------------------

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from pathlib import Path  # noqa: E402

from koz import policy  # noqa: E402

PLANNER_SETTINGS = {"hue_center": 0, "hue_half_width": 10, "saturation_min": 120, "value_min": 70,
                    "min_area_ratio": 0.002}   # what the planner asks for "red"
CLASSROOM = Path(__file__).parent / "fixtures" / "places365" / "classroom" / "Places365_val_00001389.jpg"
RED = (0, 0, 220)


def scene(draw, seed=1):
    """A 640 x 480 grey frame with sensor noise, one shape drawn, then JPEG-compressed like a camera."""
    rng = np.random.default_rng(seed)
    image = np.clip(np.full((480, 640, 3), 128.0) + rng.normal(0, 8, (480, 640, 3)), 0, 255).astype(np.uint8)
    draw(image)
    return cv2.imdecode(cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 60])[1], cv2.IMREAD_COLOR)


def shaded(image):   # lit from the left: the right side too dark to count
    cv2.circle(image, (320, 240), 40, RED, -1)
    yy, xx = np.mgrid[0:480, 0:640]
    image[((xx - 320) ** 2 + (yy - 240) ** 2 <= 1600) & (xx > 335)] = (0, 0, 60)


BALLS = {
    "ball": lambda i: cv2.circle(i, (320, 240), 40, RED, -1),
    "smallest ball the recipe allows (r 14)": lambda i: cv2.circle(i, (320, 240), 14, RED, -1),
    "ball with a highlight": lambda i: (cv2.circle(i, (320, 240), 40, RED, -1),
                                        cv2.circle(i, (305, 225), 10, (240, 240, 255), -1)),
    "ball a quarter hidden": lambda i: (cv2.circle(i, (320, 240), 40, RED, -1),
                                        cv2.rectangle(i, (340, 180), (400, 300), (128, 128, 128), -1)),
    "ball a third out of the frame": lambda i: cv2.circle(i, (627, 240), 40, RED, -1),
    "slightly blurred ball (1.3 : 1)": lambda i: cv2.ellipse(i, (320, 240), (52, 40), 0, 0, 360, RED, -1),
    "ball with its dark side lost": shaded,
}
NOT_BALLS = {
    "square": lambda i: cv2.rectangle(i, (280, 200), (360, 280), RED, -1),
    "2:1 rectangle": lambda i: cv2.rectangle(i, (260, 210), (380, 270), RED, -1),
    "triangle": lambda i: cv2.fillPoly(i, [np.array([(320, 190), (270, 280), (370, 280)])], RED),
    "long oval (1.6 : 1)": lambda i: cv2.ellipse(i, (320, 240), (64, 40), 0, 0, 360, RED, -1),
    "round but too small (r 6)": lambda i: cv2.circle(i, (320, 240), 6, RED, -1),
}


@pytest.mark.parametrize("name", BALLS)
def test_round_balls_are_found(name):
    assert ColorFinder(PLANNER_SETTINGS).find(scene(BALLS[name])).label != "lost"


@pytest.mark.parametrize("name", NOT_BALLS)
def test_patches_that_are_not_balls_are_lost(name):
    assert ColorFinder({**PLANNER_SETTINGS, "min_area_ratio": 0.001}).find(scene(NOT_BALLS[name])).label == "lost"


def test_minimum_size_is_fixed_in_code_not_only_in_the_recipe():
    assert policy.TARGET_MIN_RADIUS_PX >= 8   # the recipe's min_area_ratio can go down to 0.001 (77 px at 320 x 240)
    tiny = scene(lambda i: cv2.circle(i, (320, 240), 6, RED, -1))
    assert ColorFinder({**PLANNER_SETTINGS, "min_area_ratio": 0.001}).find(tiny).label == "lost"


@pytest.mark.skipif(not CLASSROOM.exists(), reason="needs scripts/fetch_test_photos.py")
def test_the_orange_lit_classroom_that_fooled_it_is_not_a_ball():
    """Oct 15: in this warmly lit classroom (Places365 val photo 1389), walls and desks are 'red'
    enough, and the biggest patch counted as the ball. They are big and ragged, not round."""
    room = cv2.resize(cv2.imread(str(CLASSROOM)), (640, 480))
    assert ColorFinder(PLANNER_SETTINGS).find(room).label == "lost"
    with_ball = room.copy()
    cv2.circle(with_ball, (520, 65), 30, RED, -1)   # a red ball in front of the blackboard
    target = ColorFinder(PLANNER_SETTINGS).find(with_ball)
    assert target.label == "right" and target.x == pytest.approx(520.5 / 640, abs=0.01)
