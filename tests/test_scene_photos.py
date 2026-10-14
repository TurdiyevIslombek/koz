"""Regression test from live test #1 (docs/TRIALS.md): on real photos the privacy guard must
never approve a bathroom or a bedroom, and never approve a dark frame.

Photos: 46 from the Places365 validation set (MIT CSAIL), listed with their SHA-256 in
tests/places365_photos.txt. Their copyright belongs to their owners, so they are not in
git; scripts/fetch_test_photos.py downloads them."""
from pathlib import Path

import cv2
import numpy as np
import pytest

from koz.scene import MODEL_PATH, PlacesSceneChecker

HERE = Path(__file__).resolve().parent
PHOTOS = HERE / "fixtures" / "places365"
ROWS = [line.split() for line in (HERE / "places365_photos.txt").read_text().splitlines()
        if line and not line.startswith("#")]

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists() or not all((PHOTOS / g / n).exists() for g, n, _ in ROWS),
    reason="run scripts/fetch_models.py and scripts/fetch_test_photos.py first")


@pytest.fixture(scope="module")
def checker():
    return PlacesSceneChecker()


def answers(checker, group, change=None):
    """{photo: guard answer} for one group, optionally after changing each photo."""
    result = {}
    for g, name, _ in ROWS:
        if g == group:
            image = cv2.imread(str(PHOTOS / g / name))
            result[name] = checker.check(change(image) if change else image).state
    return result


def first_frame(image):
    """What a camera's first frames look like: very dark, a little noise, a warm tint."""
    noise = np.random.default_rng(0).normal(0, 4, image.shape)
    return np.clip(image * 0.12 + noise + [2, 6, 10], 0, 255).astype(np.uint8)


@pytest.mark.parametrize("group", ["bathroom", "bedroom"])
def test_no_bathroom_or_bedroom_is_ever_approved(checker, group):
    approved = [name for name, state in answers(checker, group).items() if state == "approved"]
    assert approved == []


@pytest.mark.parametrize("group", ["bathroom", "bedroom", "classroom", "shop"])
@pytest.mark.parametrize("workspace", [False, True])
def test_dark_first_frames_are_never_approved(group, workspace):
    """Even in an owner-confirmed workspace, a dark frame is never approved."""
    checker = PlacesSceneChecker(owner_workspace=workspace)
    approved = [name for name, state in answers(checker, group, first_frame).items() if state == "approved"]
    assert approved == []


def test_ordinary_places_are_still_approved(checker):
    """So a guard that refuses everything can't pass by accident. Measured on Oct 14:
    9 of 11 classrooms and 7 of 12 shops approved; the rest were 'uncertain' (a safe stop)."""
    classrooms = list(answers(checker, "classroom").values())
    shops = list(answers(checker, "shop").values())
    print(f"approved: classrooms {classrooms.count('approved')}/{len(classrooms)}, "
          f"shops {shops.count('approved')}/{len(shops)}")
    assert classrooms.count("approved") >= len(classrooms) / 2
    assert shops.count("approved") >= 1
