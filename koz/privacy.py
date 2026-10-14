"""The privacy gate (CLAUDE.md rule 2).

It sits between the camera and every block. Only APPROVED frames go on. Anything else
(a private room, low confidence, a missing model, an error, a slow or stuck check)
stops the job. The scene check itself is koz.scene.PlacesSceneChecker."""
import threading
import time
from dataclasses import dataclass

from . import policy
from .errors import CODES

APPROVED, BLOCKED, UNKNOWN = "approved", "blocked", "unknown"


@dataclass(frozen=True)
class PrivacyResult:
    state: str               # approved | blocked | unknown
    code: str | None = None  # why it is not approved, e.g. "PRIVATE_BATHROOM"; None when approved


FAILED = PrivacyResult(UNKNOWN, "PRIVACY_UNAVAILABLE")


class PrivacyGate:
    """Runs the scene check on the first frame, then again every PRIVACY_RECHECK_S.

    A scene checker is any object with check(image) -> PrivacyResult. Each check runs in
    a background thread: if it hasn't answered within `timeout_s` (real seconds), or the
    runner's clock says it took longer than that, it counts as failed. A stuck check is
    left behind; Python can't stop a thread, but the job stops anyway."""

    def __init__(self, checker, clock=time.monotonic, timeout_s=policy.PRIVACY_TIMEOUT_S):
        self._checker = checker
        self._clock = clock
        self._timeout_s = timeout_s
        self._checked_at = None
        self.last = None   # the latest PrivacyResult, or None before the first check

    def due(self):
        return self._checked_at is None or self._clock() - self._checked_at >= policy.PRIVACY_RECHECK_S

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
        worker = threading.Thread(target=work, name="koz-scene-check", daemon=True)
        worker.start()
        worker.join(self._timeout_s)
        if worker.is_alive() or self._clock() - start > self._timeout_s:
            return FAILED
        result = answer.get("result", FAILED)
        return result if _well_formed(result) else FAILED


def _well_formed(result):
    if not isinstance(result, PrivacyResult):
        return False
    if result.state == APPROVED:
        return result.code is None
    return result.state in (BLOCKED, UNKNOWN) and isinstance(result.code, str) and result.code in CODES
