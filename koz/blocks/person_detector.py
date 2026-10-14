"""person_detector: finds people with OpenCV Zoo's NanoDet-Plus on OpenCV 5 DNN.

Only the "person" class (COCO class 0) is used. The block reports how many people are
in the allowed area right now; the boxes stay on this computer and feed line_counter.
It finds people, never who they are (CLAUDE.md rule 4).

How the model's answer is read (the same maths as OpenCV Zoo's nanodet.py):
- the frame is scaled to fit 416 x 416 (black padding below or to the right), then
  normalised with the model's fixed mean and standard deviation;
- the model scores a grid of points at three scales (every 8, 16 and 32 pixels);
- for each point it gives a person score and, for each side of a box, a spread over
  8 possible distances; that side's distance is the average of the spread, times the scale;
- overlapping boxes of the same person are merged (non-maximum suppression).
OpenCV 5 returns the outputs in a different order than the Zoo code expects, so they
are matched by shape, not by position."""
from dataclasses import dataclass

import cv2
import numpy as np

from .. import MODELS
from ..errors import KozError
from ..pinned import require_pinned
from .base import Block

# OpenCV Zoo, models/object_detection_nanodet (Apache 2.0, see koz/models/NANODET_LICENSE).
# The SHA-256 matches the official Git LFS record of the file.
MODEL_PATH = MODELS / "object_detection_nanodet_2022nov.onnx"
MODEL_SHA256 = "4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186"
INPUT = 416
MEAN = np.array([103.53, 116.28, 123.675], np.float32)   # B, G, R
STD = np.array([57.375, 57.12, 58.395], np.float32)
CLASSES, BINS, PERSON = 80, 8, 0
MERGE_IOU = 0.6


@dataclass(frozen=True)
class Person:
    box: tuple      # x0, y0, x1, y1 in pixels of the frame (local only)
    score: float


class NanoDetPersons:
    """detect(image, min_confidence) -> list of Person."""

    def __init__(self, model_path=None):
        model_path = model_path or MODEL_PATH
        require_pinned(model_path, MODEL_SHA256, "UNSUPPORTED_CAPABILITY")
        try:
            self._net = cv2.dnn.readNet(str(model_path))
        except cv2.error:
            raise KozError("UNSUPPORTED_CAPABILITY", "person model failed to load") from None
        self._names = self._net.getUnconnectedOutLayersNames()

    def detect(self, image, min_confidence):
        height, width = image.shape[:2]
        scale = INPUT / max(width, height)
        resized = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((INPUT, INPUT, 3), np.float32)
        canvas[:resized.shape[0], :resized.shape[1]] = resized
        self._net.setInput(cv2.dnn.blobFromImage((canvas - MEAN) / STD))
        return decode(self._net.forward(self._names), scale, width, height, min_confidence)


def decode(outputs, scale, width, height, min_confidence):
    """The model's raw outputs -> people in frame pixels."""
    scores = sorted((o for o in outputs if o.shape[-1] == CLASSES), key=lambda o: -o.size)
    spreads = sorted((o for o in outputs if o.shape[-1] == 4 * BINS), key=lambda o: -o.size)
    boxes, confidences = [], []
    for score, spread in zip(scores, spreads):
        score, spread = score.reshape(-1, CLASSES), spread.reshape(-1, 4, BINS)
        side = round(len(score) ** 0.5)        # the grid is side x side points
        stride = INPUT / side
        keep = np.nonzero(score[:, PERSON] >= min_confidence)[0]
        if keep.size == 0:
            continue
        cx = (keep % side) * stride + (stride - 1) / 2
        cy = (keep // side) * stride + (stride - 1) / 2
        p = np.exp(spread[keep] - spread[keep].max(axis=2, keepdims=True))
        distance = (p / p.sum(axis=2, keepdims=True) * np.arange(BINS)).sum(axis=2) * stride
        x0, y0 = (cx - distance[:, 0]) / scale, (cy - distance[:, 1]) / scale
        x1, y1 = (cx + distance[:, 2]) / scale, (cy + distance[:, 3]) / scale
        for box, confidence in zip(np.column_stack([x0, y0, x1, y1]), score[keep, PERSON]):
            bx0, by0 = max(0.0, box[0]), max(0.0, box[1])
            bx1, by1 = min(float(width), box[2]), min(float(height), box[3])
            if bx1 - bx0 >= 2 and by1 - by0 >= 2:
                boxes.append((bx0, by0, bx1, by1))
                confidences.append(float(confidence))
    if not boxes:
        return []
    kept = cv2.dnn.NMSBoxes([[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in boxes], confidences,
                            min_confidence, MERGE_IOU)
    return [Person(boxes[i], confidences[i]) for i in np.array(kept).reshape(-1)]


class PersonDetector(Block):
    type = "person_detector"

    def __init__(self, settings, detector=None):
        self.min_confidence = settings["min_confidence"]
        # Load the model now, so a missing model stops the job before any frame is used.
        self.detector = detector if detector is not None else NanoDetPersons()

    def process(self, ctx):
        ctx.results[self.type] = tuple(self.detector.detect(ctx.image, self.min_confidence))
