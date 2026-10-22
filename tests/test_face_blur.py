"""face_blur: blurs found faces, changes nothing else, and fails closed."""
import hashlib

import numpy as np
import pytest

from helpers import BrokenFaces, FakeFaces
from koz import policy
from koz.blocks import FaceBlur, FrameContext, YuNetDetector
from koz.blocks.face_blur import MODEL_PATH, MODEL_SHA256
from koz.capture import FileCamera
from koz.errors import KozError


def first_frame(path):
    with FileCamera(path) as camera:
        return camera.read().image


def checkerboard(height, width, amount):
    """+amount / -amount on alternate pixels: detail that averages to exactly zero over even squares."""
    signs = np.indices((height, width)).sum(axis=0) % 2 * 2 - 1
    return (signs * amount)[..., None].repeat(3, axis=2)


def test_details_of_a_face_never_come_through(test_video):
    """Two faces with the same 6 x 6 averages give exactly the same picture: nothing finer than
    the averages survives (the box with its margin is 96 x 96 px, so each average covers 16 x 16)."""
    original = first_frame(test_video).astype(np.int16)
    m = round(64 * policy.FACE_MARGIN)
    y0, y1, x0, x1 = 80 - m, 144 + m, 100 - m, 164 + m
    plain = original.copy()
    plain[y0:y1, x0:x1] = np.clip(plain[y0:y1, x0:x1], 40, 215)
    detailed = plain.copy()
    detailed[y0:y1, x0:x1] += checkerboard(y1 - y0, x1 - x0, 40)   # e.g. eyes, a mouth, a scar
    results = []
    for face in (plain, detailed):
        ctx = FrameContext(face.astype(np.uint8))
        FaceBlur({}, detector=FakeFaces([(100, 80, 64, 64)])).process(ctx)
        results.append(ctx.image)
    assert np.array_equal(results[0], results[1])
    assert not np.array_equal(results[1][y0:y1, x0:x1], detailed.astype(np.uint8)[y0:y1, x0:x1])
    assert results[0].shape == plain.shape


def test_blurs_inside_the_face_box_only(test_video):
    original = first_frame(test_video)
    ctx = FrameContext(original.copy())
    FaceBlur({}, detector=FakeFaces([(100, 80, 60, 60)])).process(ctx)
    m = round(60 * policy.FACE_MARGIN)   # the box grows by the margin on every side
    outside = np.ones(original.shape[:2], bool)
    outside[80 - m:140 + m, 100 - m:160 + m] = False
    assert np.array_equal(ctx.image[outside], original[outside])
    assert ctx.results["face_blur"] == 1


def test_box_past_the_edge_is_clipped_and_still_blurred():
    image = np.clip(128 + checkerboard(240, 320, 40), 0, 255).astype(np.uint8)
    ctx = FrameContext(image.copy())
    FaceBlur({}, detector=FakeFaces([(-20, -20, 50, 50)])).process(ctx)
    assert image[0:30, 0:30].std() > 30 and ctx.image[0:30, 0:30].std() < 3   # the detail is gone
    assert np.array_equal(ctx.image[60:, 60:], image[60:, 60:])


def test_detector_failure_fails_closed(test_video):
    with pytest.raises(KozError) as caught:
        FaceBlur({}, detector=BrokenFaces()).process(FrameContext(first_frame(test_video)))
    assert caught.value.code == "BLUR_UNAVAILABLE"


def test_nothing_to_tune():
    with pytest.raises(KozError) as caught:
        FaceBlur({"strength": 0}, detector=FakeFaces())
    assert caught.value.code == "SAFETY_LOCKED"


def test_missing_or_swapped_model_is_refused(tmp_path):
    fake = tmp_path / "face_detection_yunet_2023mar.onnx"
    fake.write_bytes(b"not the real model")
    for path in (tmp_path / "missing.onnx", fake):
        with pytest.raises(KozError) as caught:
            YuNetDetector(path)
        assert caught.value.code == "BLUR_UNAVAILABLE"


def test_committed_model_is_the_pinned_file():
    assert hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() == MODEL_SHA256


def test_real_yunet_runs_on_recorded_video(test_video):
    """OpenCV 5 loads the pinned model and finds no faces in a video with no faces.
    It does not prove real faces are found: that needs a real video of a face, which
    this repo deliberately doesn't hold."""
    detector = YuNetDetector()
    with FileCamera(test_video) as camera:
        while (frame := camera.read()) is not None:
            assert detector.detect(frame.image) == []


def test_tiny_face_is_flattened_not_skipped(test_video):
    original = first_frame(test_video)
    ctx = FrameContext(original.copy())
    FaceBlur({}, detector=FakeFaces([(100, 80, 4, 4)])).process(ctx)   # grows to 6 x 6
    region = ctx.image[79:85, 99:105]
    assert len(np.unique(region.reshape(-1, 3), axis=0)) == 1
    assert not np.array_equal(region, original[79:85, 99:105])
