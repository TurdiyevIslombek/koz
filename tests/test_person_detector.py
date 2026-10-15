"""person_detector: reading NanoDet's output, the pinned model, and (optionally) a real person."""
from pathlib import Path

import numpy as np
import pytest

from koz.blocks import NanoDetPersons
from koz.blocks.person_detector import BINS, CLASSES, INPUT, MODEL_PATH, MODEL_SHA256, decode
from koz.capture import FileCamera
from koz.errors import KozError
from koz.pinned import require_pinned

PRIVATE_CLIP = Path(__file__).resolve().parent / "fixtures" / "private" / "face.mp4"


def raw_outputs(hits=(), order="opencv5"):
    """Fake model outputs for the three grid scales. `hits` = (stride, gx, gy, class, score, bin)."""
    outs = {}
    for stride in (8, 16, 32):
        side = INPUT // stride
        scores = np.full((1, side * side, CLASSES), 0.01, np.float32)
        spread = np.zeros((1, side * side, 4 * BINS), np.float32)
        for s, gx, gy, cls, score, bin_ in hits:
            if s == stride:
                scores[0, gy * side + gx, cls] = score
                spread[0, gy * side + gx].reshape(4, BINS)[:, bin_] = 30.0   # all four sides at `bin_`
        outs[stride] = (scores, spread)
    if order == "opencv5":   # all scores first, then all spreads (what OpenCV 5 returns)
        return [outs[s][0] for s in (8, 16, 32)] + [outs[s][1] for s in (8, 16, 32)]
    return [x for s in (8, 16, 32) for x in outs[s]]   # interleaved, as OpenCV Zoo's code expects


@pytest.mark.parametrize("order", ["opencv5", "zoo"])
def test_decode_places_the_box(order):
    # One person at grid point (10, 20) of the stride-8 grid, every side 2 bins = 16 px away.
    people = decode(raw_outputs([(8, 10, 20, 0, 0.9, 2)], order), scale=INPUT / 640, width=640, height=480,
                    min_confidence=0.5)
    assert len(people) == 1
    cx, cy = 10 * 8 + 3.5, 20 * 8 + 3.5
    expected = np.array([cx - 16, cy - 16, cx + 16, cy + 16]) / (INPUT / 640)
    assert np.allclose(people[0].box, expected, atol=0.5)
    assert people[0].score == pytest.approx(0.9)


def test_decode_keeps_a_detection_at_exactly_the_threshold():
    """Codex review: NMSBoxes' own cut-off is strict and dropped a score of exactly 0.40."""
    people = decode(raw_outputs([(8, 10, 20, 0, 0.40, 2)]), 1.0, INPUT, INPUT, 0.40)
    assert len(people) == 1 and people[0].score == pytest.approx(0.40)


@pytest.mark.parametrize("broken", [
    [],                                                           # no output at all
    raw_outputs()[:3],                                            # scores but no box parts
    [np.full_like(o, np.nan) if o.shape[-1] == CLASSES else o for o in raw_outputs()],   # NaN scores
])
def test_decode_refuses_malformed_output(broken):
    """Codex review: for the privacy guard, a broken answer must not mean 'nothing seen'."""
    with pytest.raises(ValueError):
        decode(broken, 1.0, INPUT, INPUT, 0.4)


def test_decode_ignores_weak_scores_and_other_classes():
    hits = [(8, 5, 5, 0, 0.3, 2),      # a person, but below min_confidence
            (16, 8, 8, 2, 0.95, 3)]    # class 2 (a car) with a high score
    assert decode(raw_outputs(hits), 1.0, INPUT, INPUT, 0.5) == []


def test_decode_merges_boxes_of_the_same_person():
    hits = [(8, 20, 20, 0, 0.9, 3), (8, 21, 20, 0, 0.8, 3)]   # two grid points, almost the same box
    people = decode(raw_outputs(hits), 1.0, INPUT, INPUT, 0.5)
    assert len(people) == 1 and people[0].score == pytest.approx(0.9)


def test_missing_or_changed_model_is_refused(tmp_path):
    fake = tmp_path / "object_detection_nanodet_2022nov.onnx"
    fake.write_bytes(b"not the model")
    for path in (tmp_path / "missing.onnx", fake):
        with pytest.raises(KozError) as caught:
            NanoDetPersons(path)
        assert caught.value.code == "UNSUPPORTED_CAPABILITY"


def test_committed_model_is_the_pinned_file():
    require_pinned(MODEL_PATH, MODEL_SHA256, "UNSUPPORTED_CAPABILITY")


def test_real_model_finds_nobody_in_a_video_without_people(test_video):
    detector = NanoDetPersons()
    with FileCamera(test_video) as camera:
        while (frame := camera.read()) is not None:
            assert detector.detect(frame.image, 0.5) == []


@pytest.mark.skipif(not PRIVATE_CLIP.exists(), reason="no local clip in tests/fixtures/private/")
def test_real_model_finds_the_person_in_the_private_clip():
    """A measurement on Islombek's own clip (never committed). Prints the rate."""
    detector, frames, found = NanoDetPersons(), 0, 0
    with FileCamera(PRIVATE_CLIP) as camera:
        while (frame := camera.read()) is not None:
            frames += 1
            found += bool(detector.detect(frame.image, 0.5))
    print(f"person found in {found}/{frames} frames")
    assert frames > 0 and found / frames >= 0.5
