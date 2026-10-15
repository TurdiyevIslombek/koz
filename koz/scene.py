"""The privacy guard's scene check: which kind of room is this? (CLAUDE.md rule 2)

Model: ResNet18 trained on Places365 (365 kinds of places) by the MIT CSAIL Places team,
CC BY, converted to ONNX by scripts/convert_places365.py and run here with OpenCV 5 DNN.
The file isn't in git: scripts/fetch_models.py downloads it and checks its SHA-256.

check() first refuses frames it can't judge, then decide() reads the 365 probabilities.
  0. the allowed area is too dark or too flat (e.g. a camera's first frames, a covered lens)
                                                          -> UNKNOWN (PRIVACY_UNCERTAIN)
Default mode (live test #3: run everywhere, stop on what you see; the object check in
koz/privacy.py does most of the work):
  1. a private room is the top guess at DEFAULT_PRIVATE_TOP_BLOCKS or more -> BLOCKED
  2. private rooms together reach DEFAULT_PRIVATE_SUM_BLOCKS              -> BLOCKED
  3. anything else, even "unknown room"                                   -> APPROVED
Strict mode (--strict, for schools and public cameras): an allowlist.
  1. the top guess is a private room                     -> BLOCKED (that room's code)
  2. a private room in the top 5 is above SCENE_PRIVATE_TOP5_BLOCKS -> BLOCKED
  3. private rooms together reach SCENE_PRIVATE_SUM_BLOCKS          -> BLOCKED
  4. the top guess is an allowed place, at least SCENE_MIN_TOP_PROB
     (SCENE_MIN_TOP_PROB_CAUTIOUS for corridors and lobbies)        -> APPROVED
  5. anything else                                        -> UNKNOWN (PRIVACY_UNCERTAIN)
The allowlist came from live test #1 (a dark first frame looked like a "catacomb" and a
bathroom was approved); the default moved to "stop on what you see" after live test #3,
because in real homes the room model guessed "airplane_cabin" (docs/TRIALS.md).
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

NAMES = [line.split()[0].split("/", 2)[2] for line in
         (MODELS / "categories_places365.txt").read_text(encoding="utf-8").splitlines()]
_GROUP_OF = {index: code for code, scenes in policy.PRIVATE_SCENES.items() for index, _ in scenes}
_ALLOWED = frozenset(NAMES.index(name) for name in policy.ALLOWED_SCENES)   # a typo fails at import
_CAUTIOUS = frozenset(NAMES.index(name) for name in policy.CAUTIOUS_SCENES)


class PlacesSceneChecker:
    """check(image) -> PrivacyResult, for koz.privacy.PrivacyGate."""

    def __init__(self, model_path=None, strict=False):
        self.strict = strict   # from local setup only, see koz/local_setup.py
        model_path = model_path or MODEL_PATH
        require_pinned(model_path, MODEL_SHA256, "PRIVACY_UNAVAILABLE")
        try:
            self._net = cv2.dnn.readNetFromONNX(str(model_path))
        except cv2.error:
            raise KozError("PRIVACY_UNAVAILABLE", "scene model failed to load") from None
        self.last_probabilities = None   # from the latest check, for a local display only; never sent

    def probabilities(self, image):
        """365 probabilities for a BGR frame. The model itself normalises colours and
        applies softmax (see scripts/convert_places365.py), so the input is the plain picture."""
        self._net.setInput(cv2.dnn.blobFromImage(image, 1.0, INPUT_SIZE, (0, 0, 0), swapRB=True))
        return self._net.forward().reshape(-1).astype(np.float64)

    def check(self, image):
        """The room check alone. The privacy guard uses koz.privacy.GuardCheck, which adds the
        object check and calls the methods below."""
        self.last_probabilities = self.probabilities(image)
        if too_dark_or_flat(image):
            return PrivacyResult(UNKNOWN, "PRIVACY_UNCERTAIN")
        return decide(self.last_probabilities, self.strict)

    # Used by koz.privacy.GuardCheck:
    @staticmethod
    def too_dark_or_flat(image):
        return too_dark_or_flat(image)

    @staticmethod
    def judge(probabilities, strict):
        return decide(probabilities, strict)

    @staticmethod
    def top(probabilities, n=3):
        """[(name, probability)] of the n likeliest places."""
        return [(NAMES[i], float(probabilities[i])) for i in np.argsort(probabilities)[::-1][:n]]


def too_dark_or_flat(image):
    """True if the allowed area is too dark or has too little contrast to judge. Pixels the
    allowed-area mask blacked out (exactly 0) don't count; if almost nothing is left, it can't be judged."""
    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    visible = grey[image.any(axis=2)]
    if visible.size < 0.1 * grey.size:
        return True
    return visible.mean() < policy.SCENE_MIN_BRIGHTNESS or visible.std() < policy.SCENE_MIN_CONTRAST


def decide(probabilities, strict=False):
    """365 probabilities -> PrivacyResult. Anything malformed counts as a failed check.
    Default: stop only on a confident private room. Strict: the allowlist (module docstring)."""
    p = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if p.size != CLASSES or not np.all(np.isfinite(p)) or p.min() < 0 or not math.isclose(p.sum(), 1, abs_tol=1e-3):
        return FAILED
    top5 = [int(i) for i in np.argsort(p)[::-1][:5]]
    if not strict:
        group_sums = {code: sum(p[i] for i, _ in scenes) for code, scenes in policy.PRIVATE_SCENES.items()}
        if top5[0] in _GROUP_OF and p[top5[0]] >= policy.DEFAULT_PRIVATE_TOP_BLOCKS:
            return PrivacyResult(BLOCKED, _GROUP_OF[top5[0]])
        if sum(group_sums.values()) >= policy.DEFAULT_PRIVATE_SUM_BLOCKS:
            return PrivacyResult(BLOCKED, max(group_sums, key=group_sums.get))
        return PrivacyResult(APPROVED)
    if top5[0] in _GROUP_OF:
        return PrivacyResult(BLOCKED, _GROUP_OF[top5[0]])
    private_in_top5 = [i for i in top5 if i in _GROUP_OF and p[i] > policy.SCENE_PRIVATE_TOP5_BLOCKS]
    if private_in_top5:
        return PrivacyResult(BLOCKED, _GROUP_OF[private_in_top5[0]])
    group_sums = {code: sum(p[i] for i, _ in scenes) for code, scenes in policy.PRIVATE_SCENES.items()}
    if sum(group_sums.values()) >= policy.SCENE_PRIVATE_SUM_BLOCKS:
        return PrivacyResult(BLOCKED, max(group_sums, key=group_sums.get))
    needed = policy.SCENE_MIN_TOP_PROB_CAUTIOUS if top5[0] in _CAUTIOUS else policy.SCENE_MIN_TOP_PROB
    if top5[0] in _ALLOWED and p[top5[0]] >= needed:
        return PrivacyResult(APPROVED)
    return PrivacyResult(UNKNOWN, "PRIVACY_UNCERTAIN")
