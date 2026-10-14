"""Runner events, built exactly as contracts/events.md sections 6-8 define them (CLAUDE.md rule 9).

emit() refuses any field the contract doesn't list, and any string that isn't one of
the contract's fixed words. So free text, pictures, coordinates and IDs of people
have nowhere to go. Built so far: status, observation, fault. The other four event
types come with the agent loop and the web connection."""
import json
import re
import secrets
import time

from .errors import CODES, KozError

ID_PATTERN = re.compile(r"[0-9a-f]{32}")   # used with fullmatch()
MAX_MESSAGE_BYTES = 32 * 1024


def new_id():
    """A random protocol ID (128 bits). It names a session, job, command or trial, never a person."""
    return secrets.token_hex(16)


def count_known(value):
    return {"state": "known", "value": value, "reason": None}


def count_unknown(code):
    return {"state": "unknown", "value": None, "reason": code}


# Value checks. They compare types exactly, because in Python True == 1 and 1.0 == 1.
def _words(*allowed, nullable=False):
    allowed = frozenset(allowed)
    return lambda v: (v is None and nullable) or (type(v) is str and v in allowed)


def _boolean(v):
    return type(v) is bool


def _whole(low, high, nullable=False):
    return lambda v: (v is None and nullable) or (type(v) is int and low <= v <= high)


def _count_or_null(v):
    if v is None:
        return True
    if type(v) is not dict or set(v) != {"state", "value", "reason"}:
        return False
    if v["state"] == "known":
        return type(v["value"]) is int and 0 <= v["value"] <= 2147483647 and v["reason"] is None
    return v["state"] == "unknown" and v["value"] is None and type(v["reason"]) is str and v["reason"] in CODES


_CAPABILITIES = frozenset({"rtsp", "recorded_fixture", "looming", "scene_tripwire"})


def _capabilities(v):
    return (type(v) is list and len(set(v)) == len(v)
            and all(type(c) is str and c in _CAPABILITIES for c in v))


_PRIVACY = ("approved", "blocked", "unknown")

FIELDS = {
    "status": {
        "state": _words("idle", "planning", "checking", "evaluating", "running", "held", "refused"),
        "camera_on": _boolean,
        "privacy": _words(*_PRIVACY),
        "school": _boolean,
        "motor": _words("not_present", "disarmed", "enabled", "stop_commanded"),
        "opencv_major": _whole(5, 5, nullable=True),
        "capabilities": _capabilities,
    },
    "observation": {
        "round": _whole(1, 3, nullable=True),
        "privacy": _words(*_PRIVACY),
        "occupancy": _count_or_null,
        "entered": _count_or_null,
        "exited": _count_or_null,
        "coverage": _words("complete", "gapped"),
        "target": _words("left", "center", "right", "lost", "unknown", nullable=True),
        "motion": _words("detected", "clear", "unknown", nullable=True),
        "looming": _words("risk", "clear", "unknown", nullable=True),
        "alert": _words("motion_detected", "count_changed", nullable=True),
        "unknown_reason": _words(*CODES, nullable=True),
    },
    "fault": {
        "code": _words(*CODES),
        "effect": _words("off", "held"),
    },
}


def _observation_is_consistent(data):
    """The rules across fields in contracts/events.md 8.3:
    - when privacy isn't approved, every configured output is unknown and no alert fires;
    - unknown_reason is set exactly when an output is unknown or privacy isn't approved;
    - every unknown Count gives the same reason as unknown_reason."""
    labels = [data[k] for k in ("target", "motion", "looming")]
    counts = [data[k] for k in ("occupancy", "entered", "exited") if data[k] is not None]
    unknown_counts = [c for c in counts if c["state"] == "unknown"]
    closed = data["privacy"] != "approved"
    if closed and (any(v not in (None, "unknown") for v in labels) or len(unknown_counts) != len(counts)
                   or data["alert"] is not None):
        return False
    needs_reason = closed or "unknown" in labels or bool(unknown_counts)
    if (data["unknown_reason"] is not None) != needs_reason:
        return False
    return all(c["reason"] == data["unknown_reason"] for c in unknown_counts)


class EventLog:
    """Numbers the events of one runner session and hands each to `sink`
    (a list's append in tests; the WebSocket later)."""

    def __init__(self, sink, job_id=None, trial_id=None, wall_clock=time.time):
        for given in (job_id, trial_id):
            if given is not None and not (type(given) is str and ID_PATTERN.fullmatch(given)):
                raise KozError("INVALID_EVENT", "bad job or trial ID")
        self.session_id = new_id()
        self.job_id, self.trial_id = job_id, trial_id
        self._sink, self._wall_clock = sink, wall_clock
        self._seq = 0

    def emit(self, event_type, data, revision=None):
        spec = FIELDS.get(event_type)
        if (spec is None or type(data) is not dict or set(data) != set(spec)
                or not all(spec[name](data[name]) for name in spec)
                or not _whole(1, 3, nullable=True)(revision)
                or (event_type == "observation" and not _observation_is_consistent(data))):
            raise KozError("INVALID_EVENT", f"{event_type} does not match the contract")
        event = {"v": 1, "type": event_type, "session_id": self.session_id, "seq": self._seq + 1,
                 "job_id": self.job_id, "trial_id": self.trial_id, "revision": revision,
                 "minute": int(self._wall_clock() // 60), "data": data}
        text = json.dumps(event, allow_nan=False)
        if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise KozError("INVALID_EVENT", "event too large")
        self._seq += 1
        self._sink(json.loads(text))   # a fresh copy, so the sink can't change ours
