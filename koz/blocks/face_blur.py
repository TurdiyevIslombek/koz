"""face_blur: finds faces with OpenCV's YuNet model and blurs each one (CLAUDE.md rules 4, 6, 8).

It is a locked block: second in every recipe, right after the privacy guard, with
nothing to tune. Every later block, and the local preview, sees only blurred faces.
It finds faces only; it never recognises who someone is.

The blur is heavy pixelation: each face box (grown by FACE_MARGIN) becomes at most
FACE_PIXEL_CELLS x FACE_PIXEL_CELLS flat squares. A light Gaussian blur can sometimes be
sharpened back; averaged squares can't.

It fails closed: if the model file is missing, has the wrong SHA-256, or detection
fails, the frame goes no further (BLUR_UNAVAILABLE)."""
import hashlib
from pathlib import Path

import cv2

from .. import MODELS, policy
from ..errors import KozError
from .base import Block

# OpenCV Zoo, models/face_detection_yunet (MIT license, see koz/models/YUNET_LICENSE).
# The SHA-256 matches the official Git LFS record of the file.
MODEL_PATH = MODELS / "face_detection_yunet_2023mar.onnx"
MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"


class YuNetDetector:
    """OpenCV 5 DNN face detector. detect(image) -> list of (x, y, w, h) boxes in pixels."""

    def __init__(self, model_path=MODEL_PATH, score_threshold=policy.FACE_SCORE_THRESHOLD):
        model_path = Path(model_path)
        try:
            digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
        except OSError:
            raise KozError("BLUR_UNAVAILABLE", "face model missing") from None
        if digest != MODEL_SHA256:
            raise KozError("BLUR_UNAVAILABLE", "face model is not the pinned file")
        self._size = (320, 240)
        try:
            self._net = cv2.FaceDetectorYN.create(str(model_path), "", self._size, score_threshold)
        except cv2.error:
            raise KozError("BLUR_UNAVAILABLE", "face model failed to load") from None

    def detect(self, image):
        height, width = image.shape[:2]
        if (width, height) != self._size:
            self._size = (width, height)
            self._net.setInputSize(self._size)
        _, faces = self._net.detect(image)
        if faces is None:
            return []
        return [tuple(int(round(v)) for v in face[:4]) for face in faces]


class FaceBlur(Block):
    type = "face_blur"

    def __init__(self, settings, detector=None):
        if settings != {}:
            raise KozError("SAFETY_LOCKED")
        # Load the model now, so a missing model stops the job before any frame is used.
        self.detector = detector if detector is not None else YuNetDetector()

    def process(self, ctx):
        try:
            boxes = self.detector.detect(ctx.image)
        except Exception:   # any detector failure means "can't blur", never "no faces"
            raise KozError("BLUR_UNAVAILABLE", "face detection failed") from None
        height, width = ctx.image.shape[:2]
        for x, y, w, h in boxes:
            dx, dy = round(w * policy.FACE_MARGIN), round(h * policy.FACE_MARGIN)
            x0, y0 = max(0, x - dx), max(0, y - dy)
            x1, y1 = min(width, x + w + dx), min(height, y + h + dy)
            if x1 > x0 and y1 > y0:
                _pixelate(ctx.image, x0, y0, x1, y1)
        ctx.results[self.type] = len(boxes)   # a count for local tests; never sent


def _pixelate(image, x0, y0, x1, y1):
    width, height = x1 - x0, y1 - y0
    # Fewer squares for small faces: each square averages at least FACE_MIN_CELL_PX pixels,
    # so even a 4 x 4 face can't come through unchanged.
    cells_x = max(1, min(policy.FACE_PIXEL_CELLS, width // policy.FACE_MIN_CELL_PX))
    cells_y = max(1, min(policy.FACE_PIXEL_CELLS, height // policy.FACE_MIN_CELL_PX))
    small = cv2.resize(image[y0:y1, x0:x1], (cells_x, cells_y), interpolation=cv2.INTER_AREA)
    image[y0:y1, x0:x1] = cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
