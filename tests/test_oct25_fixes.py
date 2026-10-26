"""Fixes from Islombek's live test on Oct 25.

1. A lime (yellow-green) ball was "lost" when he asked for "green": green was hue 60 +- 10.
2. The owner chooses which way across the counting line is "in" (camera on either side of a door).
3. An unreachable robot camera said "This feature is not available"; now CAMERA_UNAVAILABLE."""
import cv2
import numpy as np

from koz.agent.loop import with_entry
from koz.agent.planner import colour_recipe, counter_recipe
from koz.blocks.color_finder import ColorFinder
from koz.blocks.line_counter import LineCounter, _cross
from koz.errors import CODES as ERROR_CODES
from koz.server import _data_ok


def finder(colour):
    return ColorFinder(next(b for b in colour_recipe(colour, "en")["blocks"]
                            if b["type"] == "color_finder")["settings"])


def ball(rgb):
    image = np.full((480, 640, 3), (180, 170, 200), np.uint8)
    cv2.circle(image, (480, 200), 60, rgb[::-1], -1)
    return image


def test_green_finds_lime_and_pure_green_balls_but_not_blue_or_red():
    for rgb in [(210, 235, 60), (190, 230, 50), (40, 200, 60)]:   # lime, yellow-green, green
        assert finder("green").find(ball(rgb)).label == "right"
    for rgb in [(40, 60, 220), (220, 30, 30)]:                      # blue, red
        assert finder("green").find(ball(rgb)).label == "lost"


def test_left_to_right_entry_swaps_the_line_and_the_counts():
    recipe = counter_recipe(False, "en")
    flipped = with_entry(recipe, "left_to_right")
    line = next(b for b in recipe["blocks"] if b["type"] == "line_counter")["settings"]["line"]
    new = next(b for b in flipped["blocks"] if b["type"] == "line_counter")["settings"]["line"]
    assert new == [line[1], line[0]] and line != new
    assert with_entry(recipe, "right_to_left") is recipe and with_entry(recipe, None) is recipe
    # someone walking left -> right: the default line calls it "exited", the flipped one "entered"
    left, right = (0.3, 0.5), (0.7, 0.5)
    assert _cross(*line, left) > 0 > _cross(*line, right)          # default: left side is "inside"
    assert _cross(*new, left) < 0 < _cross(*new, right)            # flipped: right side is "inside"


def test_start_job_accepts_entry_only_for_prompts_and_only_known_values():
    prompt = {"input": "prompt", "language": "en", "text": "count people"}
    assert _data_ok("start_job", {**prompt, "entry": "left_to_right"})
    assert _data_ok("start_job", {**prompt, "entry": "right_to_left"})
    assert _data_ok("start_job", prompt)
    assert not _data_ok("start_job", {**prompt, "entry": "up"})
    assert not _data_ok("start_job", {"input": "recipe", "recipe": {}, "entry": "left_to_right"})


def test_unreachable_camera_has_its_own_code():
    assert "CAMERA_UNAVAILABLE" in ERROR_CODES
