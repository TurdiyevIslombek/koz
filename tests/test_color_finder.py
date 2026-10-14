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
