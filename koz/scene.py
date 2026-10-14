"""The privacy guard's scene check: which kind of room is this? (CLAUDE.md rule 2)

Model: ResNet18 trained on Places365 (365 kinds of places) by the MIT CSAIL Places team,
CC BY, converted to ONNX by scripts/convert_places365.py and run here with OpenCV 5 DNN.
The file isn't in git: scripts/fetch_models.py downloads it and checks its SHA-256.

decide() turns the 365 probabilities into an answer, always erring towards "stop":
  1. the most likely place is a private room             -> BLOCKED (that room's code)
  2. private rooms together reach SCENE_PRIVATE_SUM_BLOCKS -> BLOCKED (the likeliest group)
  3. the most likely place is below SCENE_MIN_TOP_PROB     -> UNKNOWN (PRIVACY_UNCERTAIN)
  4. otherwise                                             -> APPROVED
The two thresholds are proposals until the privacy trials measure them (docs/TRIALS.md).
This is an alarm, not proof that a room is safe."""
import math

import cv2
import numpy as np

from . import MODELS, policy
from .errors import KozError
from .pinned import require_pinned
from .privacy import APPROVED, BLOCKED, FAILED, UNKNOWN, PrivacyResult

MODEL_PATH = MODELS / "places365_resnet18.onnx"
MODEL_SHA256 = "f3ff46af262967b00a3f8cd69f415b722ea8e4c7cbfbdf8bdec67defcd40f124"
INPUT_SIZE = (224, 224)
CLASSES = 365

_GROUP_OF = {index: code for code, scenes in policy.PRIVATE_SCENES.items() for index, _ in scenes}


class PlacesSceneChecker:
    """check(image) -> PrivacyResult, for koz.privacy.PrivacyGate."""

    def __init__(self, model_path=None):
        model_path = model_path or MODEL_PATH
        require_pinned(model_path, MODEL_SHA256, "PRIVACY_UNAVAILABLE")
        try:
            self._net = cv2.dnn.readNetFromONNX(str(model_path))
        except cv2.error:
            raise KozError("PRIVACY_UNAVAILABLE", "scene model failed to load") from None

    def probabilities(self, image):
        """365 probabilities for a BGR frame. The model itself normalises colours and
        applies softmax (see scripts/convert_places365.py), so the input is the plain picture."""
        self._net.setInput(cv2.dnn.blobFromImage(image, 1.0, INPUT_SIZE, (0, 0, 0), swapRB=True))
        return self._net.forward().reshape(-1).astype(np.float64)

    def check(self, image):
        return decide(self.probabilities(image))


def decide(probabilities):
    """365 probabilities -> PrivacyResult. Anything malformed counts as a failed check."""
    p = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if p.size != CLASSES or not np.all(np.isfinite(p)) or p.min() < 0 or not math.isclose(p.sum(), 1, abs_tol=1e-3):
        return FAILED
    top = int(p.argmax())
    if top in _GROUP_OF:
        return PrivacyResult(BLOCKED, _GROUP_OF[top])
    group_sums = {code: sum(p[i] for i, _ in scenes) for code, scenes in policy.PRIVATE_SCENES.items()}
    likeliest = max(group_sums, key=group_sums.get)
    if sum(group_sums.values()) >= policy.SCENE_PRIVATE_SUM_BLOCKS:
        return PrivacyResult(BLOCKED, likeliest)
    if p[top] < policy.SCENE_MIN_TOP_PROB:
        return PrivacyResult(UNKNOWN, "PRIVACY_UNCERTAIN")
    return PrivacyResult(APPROVED)
