"""Regression tests from live tests #1 and #2 (docs/TRIALS.md), on real photos, with the full
privacy guard (room check + object check):
- a bed or a toilet in view stops both modes, and no mode approves a dark frame;
- the default guard runs at a desk without a bed and in a kitchen with a sink, and lets
  through no more than 4 of 23 bathroom/bedroom photos (3 at the 0.40 limit; 4 since Oct 16 at 0.55);
- the strict guard (--strict) never approves a bathroom or a bedroom.

Photos: 71 from the Places365 validation set (MIT CSAIL), listed with their SHA-256 in
tests/places365_photos.txt. Their copyright belongs to their owners, so they are not in
git; scripts/fetch_test_photos.py downloads them."""
from pathlib import Path

import cv2
import numpy as np
import pytest

from koz.blocks.person_detector import MODEL_PATH as NANODET_PATH
from koz.privacy import GuardCheck, PrivateObjects
from koz.scene import MODEL_PATH, PlacesSceneChecker

HERE = Path(__file__).resolve().parent
PHOTOS = HERE / "fixtures" / "places365"
ROWS = [line.split() for line in (HERE / "places365_photos.txt").read_text().splitlines()
        if line and not line.startswith("#")]

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists() or not NANODET_PATH.exists() or not all((PHOTOS / g / n).exists() for g, n, _ in ROWS),
    reason="run scripts/fetch_models.py and scripts/fetch_test_photos.py first")


@pytest.fixture(scope="module")
def models():
    return PlacesSceneChecker(), PrivateObjects()


def judge(models, image, strict):
    """The guard's answer for one photo, as on a live camera: a fresh guard, and if it saw
    a bed or toilet once it checks the next frame (the same photo) before deciding."""
    guard = GuardCheck(*models, strict=strict)
    result = guard.check(image)
    if result.confirming:
        result = guard.check(image)
    return result, guard.last_found


def photos(group, change=None):
    for g, name, _ in ROWS:
        if g == group:
            image = cv2.imread(str(PHOTOS / g / name))
            yield name, change(image) if change else image


def first_frame(image):
    """What a camera's first frames look like: very dark, a little noise, a warm tint."""
    noise = np.random.default_rng(0).normal(0, 4, image.shape)
    return np.clip(image * 0.12 + noise + [2, 6, 10], 0, 255).astype(np.uint8)


@pytest.mark.parametrize("group", ["bathroom", "bedroom"])
def test_strict_guard_never_approves_a_bathroom_or_bedroom(models, group):
    approved = [name for name, image in photos(group) if judge(models, image, True)[0].state == "approved"]
    assert approved == []


@pytest.mark.parametrize("group", ["bathroom", "bedroom", "classroom", "shop", "desk", "kitchen"])
@pytest.mark.parametrize("strict", [False, True])
def test_dark_first_frames_are_never_approved(models, group, strict):
    approved = [name for name, image in photos(group, first_frame)
                if judge(models, image, strict)[0].state == "approved"]
    assert approved == []


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("group, thing, code", [("bedroom", "bed", "PRIVATE_BEDROOM"),
                                                ("bathroom", "toilet", "PRIVATE_BATHROOM")])
def test_a_bed_or_toilet_in_view_stops_both_modes(models, strict, group, thing, code):
    stopped = []
    for name, image in photos(group):
        result, found = judge(models, image, strict)
        if thing in found:
            assert (result.state, result.code, result.seen) == ("blocked", code, thing), name
            stopped.append(name)
    assert len(stopped) >= 5   # measured Oct 15: a bed in 7 of 11 bedrooms, a toilet in 7 of 12 bathrooms


def test_a_desk_without_a_bed_runs_by_default(models):
    ran = []
    for name, image in photos("desk"):
        result, found = judge(models, image, False)
        if "bed" in found:
            assert result.seen == "bed" and result.state == "blocked", name   # a desk in a bedroom, bed in view
        else:
            assert result.state == "approved", name
            ran.append(name)
    assert len(ran) >= 8   # measured Oct 15: 10 of 12 home-office photos have no bed in view


def test_a_kitchen_with_a_sink_runs_by_default(models):
    with_sink = []
    for name, image in photos("kitchen"):
        result, found = judge(models, image, False)
        assert result.state == "approved", name
        if "sink" in found:
            with_sink.append(name)
    assert with_sink   # Places365_val_00033751.jpg (a restaurant kitchen, sink 0.45)


def test_ordinary_places_are_still_approved_by_the_strict_guard(models):
    """Strict mode. So a guard that refuses everything can't pass by accident. Measured on Oct 15:
    9 of 11 classrooms and 7 of 12 shops approved; the rest were 'uncertain' (a safe stop)."""
    classrooms = [judge(models, image, True)[0].state for _, image in photos("classroom")]
    shops = [judge(models, image, True)[0].state for _, image in photos("shop")]
    print(f"approved: classrooms {classrooms.count('approved')}/{len(classrooms)}, "
          f"shops {shops.count('approved')}/{len(shops)}")
    assert classrooms.count("approved") >= len(classrooms) / 2
    assert shops.count("approved") >= 1


def test_default_limit_does_not_get_worse(models):
    """The honest limit of the default guard (live test #3): when no bed or toilet is visible
    and the room check isn't confident, it runs. Measured Oct 15 (sum limit 0.40): 3 of 23 private
    photos (a bathroom read as "closet 0.35", one as "bank_vault 0.69", a bedroom as "kennel/outdoor").
    Oct 16, sum limit raised to 0.55 (Islombek's decision, docs/TRIALS.md): 4 of 23; the new one is a
    bathroom read as "wet_bar 0.51, bathroom 0.35" (private rooms together 0.43).
    The strict guard (--strict) stops all 23."""
    approved = [name for group in ("bathroom", "bedroom") for name, image in photos(group)
                if judge(models, image, False)[0].state == "approved"]
    print(f"default mode approved {len(approved)} of 23 private photos: {approved}")
    assert len(approved) <= 4
