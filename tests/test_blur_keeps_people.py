"""A person stays countable after the face blur (Islombek's live test, Oct 22: "0 people in view"
while he was in the picture, upper body, face blurred).

Measured on this public-domain portrait placed in a 640 x 480 webcam frame: the person detector
scored 0.88 without blur, 0.29 after the old hard 6 x 6 squares (below the 0.5 Koʻz counts from),
and 0.69 after the same 6 x 6 averages enlarged smoothly (koz/blocks/face_blur.py). Real models
(YuNet and NanoDet-Plus on OpenCV 5). When the head and shoulders fill the picture, NanoDet finds
no person even without blur: the Live page says what it counts instead (web/src/i18n.js)."""
from pathlib import Path

import cv2
import numpy as np
import pytest

from koz.blocks import FaceBlur, FrameContext
from koz.blocks.face_blur import MODEL_PATH as YUNET
from koz.blocks.person_detector import MODEL_PATH as NANODET
from koz.blocks.person_detector import NanoDetPersons

PORTRAIT = Path(__file__).resolve().parent / "fixtures" / "people" / "grace_hopper.jpg"


def webcam_frame(scale):
    """The portrait at `scale` x the frame's height, at the bottom middle of a grey 640 x 480 frame."""
    source = cv2.imread(str(PORTRAIT))
    height = int(480 * scale)
    width = int(source.shape[1] * height / source.shape[0])
    person = cv2.resize(source, (width, height), interpolation=cv2.INTER_AREA)[:480, :640]
    frame = np.full((480, 640, 3), 90, np.uint8)
    h, w = person.shape[:2]
    frame[480 - h:, (640 - w) // 2:(640 - w) // 2 + w] = person
    return frame


@pytest.mark.skipif(not (YUNET.exists() and NANODET.exists()), reason="needs scripts/fetch_models.py")
@pytest.mark.parametrize("scale", [0.6, 0.8, 1.0, 1.4])
def test_a_blurred_person_is_still_counted(scale):
    ctx = FrameContext(webcam_frame(scale))
    FaceBlur({}).process(ctx)
    assert ctx.results["face_blur"] == 1                       # the face was found and blurred
    people = NanoDetPersons().detect(ctx.image, 0.5)           # the counter's own threshold
    assert len(people) >= 1
