"""The privacy guard (CLAUDE.md rule 2).

PrivacyGate sits between the camera and every block. Only APPROVED frames go on. Anything
else (a private room, an uncertain or dark view, a missing model, an error, a slow or stuck
check) stops the job.

GuardCheck is what the gate runs on a frame, for every job:
  0. too dark or too flat to judge                                  -> UNKNOWN
  1. object check: a bed or a toilet (NanoDet, confidence >= 0.40)
     seen in 2 of the last 3 checks                                 -> BLOCKED (bedroom / bathroom)
     seen once in the last 2 checks                                 -> CONFIRMING: hold every frame
                                                                       and check the next ones first
  2. a sink, while the room check has bathroom or shower in its top 3 -> BLOCKED (bathroom)
  3. the room check (koz/scene.py): by default only a confident private room stops it;
     with --strict, the allowlist of public places                  -> BLOCKED / UNKNOWN / APPROVED
The object check came from live test #2: a desk in a bedroom is not a bedroom, but a bed in
view is. Its limit: a bed mostly out of view can be missed, so the room check stays as a
backup (docs/TRIALS.md). Since live test #3 this is the default for every job: run
everywhere, stop on what you see."""
import threading
import time
from collections import deque
from dataclasses import dataclass

from . import policy
from .blocks.person_detector import NanoDet
from .errors import CODES

APPROVED, BLOCKED, UNKNOWN = "approved", "blocked", "unknown"
SEEN = ("bed", "toilet", "sink")


@dataclass(frozen=True)
class PrivacyResult:
    state: str               # approved | blocked | unknown
    code: str | None = None  # why it is not approved, e.g. "PRIVATE_BATHROOM"; None when approved
    seen: str | None = None  # the object that decided it ("bed", "toilet", "sink"), if any
    confirming: bool = False  # an object was seen once: hold, and check the next frames first


FAILED = PrivacyResult(UNKNOWN, "PRIVACY_UNAVAILABLE")
UNCERTAIN = PrivacyResult(UNKNOWN, "PRIVACY_UNCERTAIN")


class PrivateObjects:
    """find(image) -> {"bed": 0.83, ...}: beds, toilets and sinks NanoDet sees at
    OBJECT_MIN_CONFIDENCE or more, each with its best confidence."""
    _NAMES = {**{cls: name for name, (cls, _) in policy.PRIVATE_OBJECTS.items()}, policy.SINK_CLASS: "sink"}

    def __init__(self, detector=None):
        self.detector = detector if detector is not None else NanoDet(error_code="PRIVACY_UNAVAILABLE")

    def find(self, image):
        found = {}
        for d in self.detector.detect(image, tuple(self._NAMES), policy.OBJECT_MIN_CONFIDENCE):
            name = self._NAMES[d.class_id]
            found[name] = max(found.get(name, 0.0), d.score)
        return found


class GuardCheck:
    """check(image) -> PrivacyResult, following the steps in the module docstring.

    `scene` is a koz.scene.PlacesSceneChecker (or a stand-in with the same methods);
    `objects` a PrivateObjects. The latest room guesses, objects and result are kept for a
    local display (`line`); they are never sent."""

    def __init__(self, scene, objects, strict=False):
        self.scene, self.objects, self.strict = scene, objects, strict
        self._history = deque(maxlen=policy.OBJECT_CHECK_WINDOW)   # objects seen in each recent check
        self.checks = 0
        self.last_probabilities, self.last_found, self.last_result = None, {}, None

    def check(self, image):
        probabilities = self.scene.probabilities(image)
        found = self.objects.find(image)
        self._history.append(set(found) & set(policy.PRIVATE_OBJECTS))
        self.checks += 1
        self.last_probabilities, self.last_found = probabilities, found
        self.last_result = self._decide(image, probabilities, found)
        return self.last_result

    def _decide(self, image, probabilities, found):
        if self.scene.too_dark_or_flat(image):
            return UNCERTAIN
        for name in ("toilet", "bed"):
            if sum(name in seen for seen in self._history) >= policy.OBJECT_CHECKS_TO_STOP:
                return PrivacyResult(BLOCKED, policy.PRIVATE_OBJECTS[name][1], seen=name)
        recent = list(self._history)[-(policy.OBJECT_CHECK_WINDOW - 1):]
        for name in ("toilet", "bed"):
            if any(name in seen for seen in recent):
                # Seen once in the last checks: a second sighting would still stop it, so look
                # again before letting anything through (Codex review: don't resume early).
                return PrivacyResult(UNKNOWN, "PRIVACY_UNCERTAIN", seen=name, confirming=True)
        if "sink" in found and any(room in policy.SINK_ROOMS for room, _ in self.scene.top(probabilities, 3)):
            return PrivacyResult(BLOCKED, "PRIVATE_BATHROOM", seen="sink")
        return self.scene.judge(probabilities, self.strict)

    @property
    def line(self):
        """One line for the screen and the terminal, e.g.
        "check 3: room bedroom 0.41, home_office 0.20, dorm_room 0.08 | seen bed 0.83 -> blocked"."""
        if self.last_probabilities is None:
            return "check: not yet"
        rooms = ", ".join(f"{name} {p:.2f}" for name, p in self.scene.top(self.last_probabilities, 3))
        seen = ", ".join(f"{name} {score:.2f}" for name, score in sorted(self.last_found.items())) or "nothing"
        result = self.last_result.state + (" (confirming)" if self.last_result.confirming else "")
        return f"check {self.checks}: room {rooms} | seen {seen} -> {result}"


class PrivacyGate:
    """Runs the guard's check on the first frame, then again every PRIVACY_RECHECK_S, and on
    every frame while a check is confirming an object it saw once.

    A checker is any object with check(image) -> PrivacyResult. Each check runs in a
    background thread: if it hasn't answered within `timeout_s` (real seconds), or the
    runner's clock says it took longer than that, it counts as failed. A stuck check is
    left behind; Python can't stop a thread, but the job stops anyway."""

    def __init__(self, checker, clock=time.monotonic, timeout_s=policy.PRIVACY_TIMEOUT_S):
        self._checker = checker
        self._clock = clock
        self._timeout_s = timeout_s
        self._checked_at = None
        self.last = None   # the latest PrivacyResult, or None before the first check

    def due(self):
        return (self._checked_at is None or (self.last is not None and self.last.confirming)
                or self._clock() - self._checked_at >= policy.PRIVACY_RECHECK_S)

    def admit(self, image):
        if self.due():
            self._checked_at = self._clock()
            self.last = self._run_check(image)
        return self.last

    def _run_check(self, image):
        answer = {}

        def work():
            try:
                answer["result"] = self._checker.check(image)
            except Exception:   # any failure inside the checker is a failed check, never a pass
                answer["result"] = FAILED

        start = self._clock()
        worker = threading.Thread(target=work, name="koz-privacy-check", daemon=True)
        worker.start()
        worker.join(self._timeout_s)
        if worker.is_alive() or self._clock() - start > self._timeout_s:
            return FAILED
        result = answer.get("result", FAILED)
        return result if _well_formed(result) else FAILED


def _well_formed(result):
    if not isinstance(result, PrivacyResult) or result.seen not in (None, *SEEN) or type(result.confirming) is not bool:
        return False
    if result.confirming:
        return result.state == UNKNOWN and result.code == "PRIVACY_UNCERTAIN" and result.seen in SEEN
    if result.state == APPROVED:
        return result.code is None
    return result.state in (BLOCKED, UNKNOWN) and isinstance(result.code, str) and result.code in CODES
