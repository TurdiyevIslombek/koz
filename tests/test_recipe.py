"""Recipe checks (CLAUDE.md rule 1): strict parsing, the contract schema, extra checks."""
import copy
import json

import pytest

from helpers import LOCKED, color_recipe
from koz.errors import KozError
from koz.recipe import CheckedRecipe, check_recipe, load_recipe, parse_recipe_text


def code_of(fn, *args, **kwargs):
    with pytest.raises(KozError) as caught:
        fn(*args, **kwargs)
    return caught.value.code


def changed(recipe, fn):
    recipe = copy.deepcopy(recipe)
    fn(recipe)
    return recipe


def test_good_recipe_passes_and_is_copied():
    recipe = color_recipe()
    checked = check_recipe(recipe)
    assert isinstance(checked, CheckedRecipe) and checked.school is False
    recipe["blocks"][2]["settings"]["hue_center"] = 90
    assert checked.data["blocks"][2]["settings"]["hue_center"] == 0


def test_recipe_text_round_trip():
    assert load_recipe(json.dumps(color_recipe())).data == color_recipe()
    assert load_recipe(json.dumps(color_recipe()).encode()).data == color_recipe()


@pytest.mark.parametrize("text", [
    '{"version": 1, "version": 1}',                 # duplicate key
    '{"x": NaN}', '{"x": Infinity}', '{"x": 1e999}',  # not finite
    b'{"x": "\xff"}',                               # invalid UTF-8
    "{" + " " * 17000 + "}",                        # over 16 KiB
    '{"x": ' + "[" * 13 + "]" * 13 + "}",           # nested too deep
    "[" * 15000,                                    # under 16 KiB but deeper than the parser allows
    "not json",
])
def test_strict_parsing_refuses(text):
    assert code_of(parse_recipe_text, text) == "INVALID_RECIPE"


@pytest.mark.parametrize("breaks", [
    lambda r: r.update(blocks=r["blocks"][1:]),                            # no privacy guard
    lambda r: r.update(blocks=[r["blocks"][1], r["blocks"][0], r["blocks"][2]]),  # wrong order
    lambda r: r["blocks"][1].update(settings={"strength": 0}),           # weaken the blur
    lambda r: r.update(blocks=[]),
])
def test_locked_blocks(breaks):
    assert code_of(check_recipe, changed(color_recipe(), breaks)) == "SAFETY_LOCKED"


MOTION = {"type": "motion_zone", "settings": {"rect": [0.1, 0.1, 0.9, 0.9], "pixel_delta": 25,
                                              "min_changed_ratio": 0.05}}


@pytest.mark.parametrize("breaks", [
    lambda r: r.update(url="http://evil.example"),
    lambda r: r["camera"].update(address="rtsp://evil.example"),
    lambda r: r["blocks"].append({"type": "face_recognition", "settings": {}}),
    lambda r: r["blocks"].append(copy.deepcopy(r["blocks"][2])),         # color_finder twice
    lambda r: r["blocks"].append({**MOTION, "settings": {**MOTION["settings"], "rect": [0.9, 0.1, 0.1, 0.9]}}),
    lambda r: r["actions"].append({"type": "alert", "template": "motion_detected"}),  # no motion_zone
    lambda r: r["blocks"][2]["settings"].update(hue_center=200),
    lambda r: r["blocks"][2]["settings"].update(hue_center="0"),
    lambda r: r["actions"].append({"type": "motors", "max_speed_ratio": 0.1}),
])
def test_invalid_recipes(breaks):
    assert code_of(check_recipe, changed(color_recipe(), breaks)) == "INVALID_RECIPE"


def test_block_order_is_checked():
    recipe = color_recipe()
    recipe["blocks"] = LOCKED + [copy.deepcopy(MOTION), recipe["blocks"][2]]   # motion_zone before color_finder
    assert code_of(check_recipe, recipe) == "INVALID_RECIPE"


def test_school_mode_allows_counts_only():
    assert code_of(check_recipe, color_recipe(school=True)) == "SCHOOL_COUNTS_ONLY"
    # A local school setting applies even when the recipe says it isn't a school.
    assert code_of(check_recipe, color_recipe(), local_school=True) == "SCHOOL_COUNTS_ONLY"
    bare = changed(color_recipe(school=True), lambda r: r.update(blocks=copy.deepcopy(LOCKED)))
    assert check_recipe(bare).school is True
    assert check_recipe(changed(bare, lambda r: r["privacy"].update(school=False)), local_school=True).school


def test_unbuilt_parts_are_refused_not_skipped():
    car = changed(color_recipe(), lambda r: r.update(
        brain={"type": "flybrain", "settings": {"turn_gain": 0.5, "deadband": 0.1}},
        actions=[{"type": "dashboard"}, {"type": "motors", "max_speed_ratio": 0.15}]))
    classroom = changed(color_recipe(school=True), lambda r: r.update(blocks=copy.deepcopy(LOCKED) + [
        {"type": "person_detector", "settings": {"min_confidence": 0.5}},
        {"type": "line_counter", "settings": {"line": [[0.5, 0.0], [0.5, 1.0]]}}]))
    farm = changed(color_recipe(), lambda r: r.update(
        blocks=copy.deepcopy(LOCKED) + [copy.deepcopy(MOTION)],
        actions=[{"type": "dashboard"}, {"type": "alert", "template": "motion_detected"}]))
    assert code_of(check_recipe, farm) == "UNSUPPORTED_CAPABILITY"   # motion zone and alerts: not built
    assert check_recipe(classroom).school is True   # person_detector + line_counter are built now
    assert check_recipe(car).data["brain"]["type"] == "flybrain"      # the fly brain + motors: built Oct 16


def test_errors_never_repeat_the_input():
    for recipe in (changed(color_recipe(), lambda r: r.update(url="http://evil.example")),
                   changed(color_recipe(), lambda r: r["blocks"][2]["settings"].update(hue_center="evil"))):
        with pytest.raises(KozError) as caught:
            check_recipe(recipe)
        assert "evil" not in str(caught.value)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_numbers_from_python_are_refused(bad):
    """Adjustments may build recipes in Python, skipping the text parser."""
    assert code_of(check_recipe, color_recipe(min_area_ratio=bad)) == "INVALID_RECIPE"
