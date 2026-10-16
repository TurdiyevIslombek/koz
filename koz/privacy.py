"""The privacy guard (CLAUDE.md rule 2).

PrivacyGate sits between the camera and every block. Only APPROVED frames go on. Anything
else (a private room, an uncertain or dark view, a missing model, an error, a slow or stuck
check) stops the job.

GuardCheck is what the gate runs, for every job: objects every 0.5 s, the room every 3 s,
and on the very next frame when the camera moved (live test #4: stop within 1 s):
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

import cv2
import numpy as np

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


def thumbnail(image):
    """A tiny grey copy of the frame (32 x 24), to notice when the camera moves."""
    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.resize(grey, (32, 24), interpolation=cv2.INTER_AREA).astype(np.int16)


def _moved(a, b):
    return a is not None and b is not None and np.abs(a - b).mean() > policy.SCENE_CHANGE_DIFF


class GuardCheck:
    """check(image) -> PrivacyResult, following the steps in the module docstring.

    The object check runs on every check (every OBJECT_RECHECK_S); the room check only every
    ROOM_RECHECK_S, or sooner when the view changed a lot (at most every ROOM_CHANGE_MIN_GAP_S).
    `scene` is a koz.scene.PlacesSceneChecker (or a stand-in with the same methods);
    `objects` a PrivateObjects. `watch_changes` is off on the moving car, whose view always
    changes. The latest room guesses, objects and result are kept for a local display
    (`line`); they are never sent."""

    def __init__(self, scene, objects, strict=False, clock=time.monotonic, watch_changes=True):
        self.scene, self.objects, self.strict = scene, objects, strict
        self._clock, self.watch_changes = clock, watch_changes
        self._history = deque(maxlen=policy.OBJECT_CHECK_WINDOW)   # objects seen in each recent check
        self._started = clock()
        self._last_thumb = self._room_thumb = self._room_at = None
        self._first_seen = {}       # object -> when this run of sightings began
        self.checks = self.room_checks = 0
        self.last_probabilities, self.last_found, self.last_result = None, {}, None
        self.last_at, self.last_room_fresh, self.stop_delay = None, False, None

    def changed(self, image):
        """True if the view changed a lot since the last check (the camera moved)."""
        return self.watch_changes and _moved(thumbnail(image), self._last_thumb)

    def check(self, image):
        now, thumb = self._clock(), thumbnail(image)
        room_due = (self.last_probabilities is None or now - self._room_at >= policy.ROOM_RECHECK_S
                    or (self.watch_changes and _moved(thumb, self._room_thumb)
                        and now - self._room_at >= policy.ROOM_CHANGE_MIN_GAP_S))
        if room_due:
            self.last_probabilities = self.scene.probabilities(image)
            self._room_at, self._room_thumb = now, thumb
            self.room_checks += 1
        found = self.objects.find(image)
        self._history.append(set(found) & set(policy.PRIVATE_OBJECTS))
        for name in SEEN:            # when did the current run of sightings of each object begin?
            if name in found:
                self._first_seen.setdefault(name, now)
            elif not any(name in seen for seen in self._history):   # (sinks aren't in the history)
                self._first_seen.pop(name, None)
        self.checks += 1
        self._last_thumb, self.last_at, self.last_room_fresh, self.last_found = thumb, now, room_due, found
        self.last_result = self._decide(image, self.last_probabilities, found)
        if self.last_result.state == BLOCKED and self.last_result.seen in self._first_seen:
            self.stop_delay = now - self._first_seen[self.last_result.seen]
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
        """One line for the screen and the terminal, e.g. "check 7 @ 3.1 s (room+objects):
        room bathroom 0.62, shower 0.11, ... | seen toilet 0.81 -> blocked, 0.07 s after first seen"."""
        if self.last_probabilities is None:
            return "check: not yet"
        rooms = ", ".join(f"{name} {p:.2f}" for name, p in self.scene.top(self.last_probabilities, 3))
        total = getattr(self.scene, "private_total", None)   # stand-ins in tests may not have it
        if total is not None:
            rooms += f" (private rooms together {total(self.last_probabilities):.2f})"
        seen = ", ".join(f"{name} {score:.2f}" for name, score in sorted(self.last_found.items())) or "nothing"
        result = self.last_result.state + (" (confirming)" if self.last_result.confirming else "")
        if self.last_result.state == BLOCKED and self.stop_delay is not None:
            result += f", {self.stop_delay:.2f} s after first seen"
        kind = "room+objects" if self.last_room_fresh else "objects"
        return f"check {self.checks} @ {self.last_at - self._started:.1f} s ({kind}): room {rooms} | seen {seen} -> {result}"


class PrivacyGate:
    """Runs the guard's check on the first frame, then every OBJECT_RECHECK_S, on the next frame
    when the view changed a lot (if the checker has changed(); at most every CHANGE_MIN_GAP_S),
    and on every frame while a check is confirming an object it saw once.

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

    def due(self, image=None):
        if self._checked_at is None or (self.last is not None and self.last.confirming):
            return True
        since = self._clock() - self._checked_at
        if since >= policy.OBJECT_RECHECK_S:
            return True
        changed = getattr(self._checker, "changed", None)
        return bool(since >= policy.CHANGE_MIN_GAP_S and image is not None and changed is not None and changed(image))

    def admit(self, image):
        if self.due(image):
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
