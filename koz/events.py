"""Runner events, built exactly as contracts/events.md sections 6-8 define them (CLAUDE.md rule 9).

emit() refuses any field the contract doesn't list, and any string that isn't one of
the contract's fixed words. So free text, pictures, coordinates and IDs of people
have nowhere to go. All seven event types: status, recipe, observation, decision,
command_result, fault, trial_result."""
import json
import math
import re
import secrets
import threading
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
PLANNERS = ("rules", "ollama", "nebius", "bedrock")
_STATUS_PLANNER = _words(*PLANNERS, nullable=True)   # optional status field (contract 8.1, Oct 15)
# Fixed camera slots (contract 8.1 and 10, Oct 16). The runner's command line binds each to a
# source; addresses and names never appear in events or commands.
CAMERA_SLOTS = ("mac_camera", "esp32_cam", "phone_ip_camera")
SEEN_OBJECTS = ("bed", "toilet", "sink")   # fault.seen: the object that made the privacy guard stop


def _camera_slots(v):
    return type(v) is list and len(set(v)) == len(v) and all(type(c) is str and c in CAMERA_SLOTS for c in v)
CHECKS = ("target_visible", "target_centered", "counts_available", "motion_available", "privacy_approved")
LABELS = ("left", "center", "right", "lost", "detected", "clear", "risk", "approved", "blocked", "known", "unknown")
SETTINGS = ("color_finder.hue_center", "color_finder.hue_half_width", "color_finder.saturation_min",
            "color_finder.value_min", "color_finder.min_area_ratio", "motion_zone.pixel_delta",
            "motion_zone.min_changed_ratio", "person_detector.min_confidence", "brain.turn_gain", "brain.deadband")


def _number(v):
    return type(v) in (int, float) and math.isfinite(v)


def _setting_change(v):
    """{"setting": one of SETTINGS, "before": n, "after": n}, before != after (contract section 7)."""
    return (type(v) is dict and set(v) == {"setting", "before", "after"} and type(v["setting"]) is str
            and v["setting"] in SETTINGS and _number(v["before"]) and _number(v["after"]) and v["before"] != v["after"])


def _setting_change_or_null(v):
    return v is None or _setting_change(v)


def _checked_recipe(v):
    from .recipe import check_recipe   # here, not at the top: koz.recipe doesn't need events
    try:
        check_recipe(v)
    except Exception:
        return False
    return True


def _evidence(v):
    return (type(v) is list and 1 <= len(v) <= 10 and len(set(v)) == len(v)
            and all(type(n) is int and n >= 1 for n in v))


def _code_or_null(v):
    return v is None or (type(v) is str and v in CODES)


def _agent_changes(v):
    if type(v) is not list or len(v) > 2:
        return False
    keys = {"from_revision", "to_revision", "check", "before_label", "change", "executed", "after_label", "after_result"}
    return all(type(r) is dict and set(r) == keys and r["from_revision"] in (1, 2) and type(r["from_revision"]) is int
               and r["to_revision"] == r["from_revision"] + 1 and type(r["to_revision"]) is int
               and r["check"] in CHECKS and r["before_label"] in LABELS and _setting_change(r["change"])
               and r["executed"] is True and r["after_label"] in LABELS and r["after_result"] in ("pass", "fail", "unknown")
               for r in v)

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
    "recipe": {
        "origin": _words("planner", "import", "adjustment"),
        "caused_by": _whole(1, 9007199254740991, nullable=True),
        "recipe": _checked_recipe,
    },
    "decision": {
        "round": _whole(1, 3),
        "evidence_seq": _evidence,
        "check": _words(*CHECKS),
        "result": _words("pass", "fail", "unknown"),
        "next": _words("run", "adjust", "stop"),
        "next_revision": _whole(1, 3, nullable=True),
        "change": _setting_change_or_null,
        "code": _code_or_null,
    },
    "command_result": {
        "command_id": lambda v: type(v) is str and ID_PATTERN.fullmatch(v) is not None,
        "result": _words("accepted", "rejected"),
        "code": _code_or_null,
    },
    "trial_result": {
        "demo": _words("red_ball", "classroom", "privacy_guard"),
        "index": _whole(1, 10),
        "result": _words("pass", "fail", "unknown"),
        "basis": _words("owner_report"),
        "reason": _words("none", "missed_target", "wrong_direction", "count_mismatch", "privacy_miss",
                         "safety_stop", "interrupted", "unknown"),
        "expected_count": _whole(0, 2147483647, nullable=True),
        "observed_count": _count_or_null,
        "fault_code": _code_or_null,
        "evidence": _words("complete", "incomplete"),
        "agent_changes": _agent_changes,
    },
}


def _consistent(event_type, data, revision):
    """Rules across fields that the per-field checks can't see (contract sections 8.2-8.7)."""
    if event_type == "observation":
        return _observation_is_consistent(data)
    if event_type == "recipe":
        return (data["origin"] == "adjustment") == (data["caused_by"] is not None) and revision is not None
    if event_type == "decision":
        if revision is None:
            return False
        if data["next"] == "run":   # after pass, or unknown when a find job starts and waits (section 9)
            return (data["next_revision"] == revision and data["change"] is None and data["code"] is None
                    and data["result"] != "fail")
        if data["next"] == "adjust":
            return (data["next_revision"] == revision + 1 and data["change"] is not None
                    and data["code"] is None and data["result"] == "fail")
        return data["next_revision"] is None and data["change"] is None and data["code"] is not None
    if event_type == "command_result":
        return (data["result"] == "accepted") == (data["code"] is None)
    if event_type == "trial_result":
        return data["result"] != "pass" or data["reason"] == "none"
    if event_type == "fault" and "seen" in data:   # only an object stop of a bedroom or bathroom
        return data["code"] in ("PRIVATE_BEDROOM", "PRIVATE_BATHROOM")
    return True


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

    def __init__(self, sink, job_id=None, trial_id=None, wall_clock=time.time, report_planner=False,
                 cameras=None):
        for given in (job_id, trial_id):
            if given is not None and not (type(given) is str and ID_PATTERN.fullmatch(given)):
                raise KozError("INVALID_EVENT", "bad job or trial ID")
        self.session_id = new_id()
        self.job_id, self.trial_id = job_id, trial_id
        self._sink, self._wall_clock = sink, wall_clock
        self._seq = 0
        self.listeners = []   # extra callables that also get every event (e.g. the agent loop)
        # The job thread and the WebSocket thread both emit: one lock keeps seq in order.
        # Re-entrant, so the server can hold it around a check and an emit.
        self.lock = threading.RLock()
        # status.planner (contract 8.1): sent only once the web accepts it (report_planner).
        self.report_planner, self.planner = report_planner, None
        # status.cameras (contract 8.1): the configured camera slots, sent when given (not None).
        if cameras is not None and not _camera_slots(list(cameras)):
            raise KozError("INVALID_EVENT", "unknown camera slot")
        self.cameras = None if cameras is None else list(cameras)

    def emit(self, event_type, data, revision=None):
        with self.lock:
            return self._emit(event_type, data, revision)

    def _emit(self, event_type, data, revision):
        spec = FIELDS.get(event_type)
        if event_type == "status" and self.report_planner and type(data) is dict:
            data, spec = {**data, "planner": self.planner}, {**spec, "planner": _STATUS_PLANNER}
        if event_type == "status" and self.cameras is not None and type(data) is dict:
            data, spec = {**data, "cameras": list(self.cameras)}, {**spec, "cameras": _camera_slots}
        if event_type == "fault" and type(data) is dict and "seen" in data:   # optional (contract 8.6, Oct 18)
            spec = {**spec, "seen": _words(*SEEN_OBJECTS)}
        if (spec is None or type(data) is not dict or set(data) != set(spec)
                or not all(spec[name](data[name]) for name in spec)
                or not _whole(1, 3, nullable=True)(revision)
                or not _consistent(event_type, data, revision)):
            raise KozError("INVALID_EVENT", f"{event_type} does not match the contract")
        event = {"v": 1, "type": event_type, "session_id": self.session_id, "seq": self._seq + 1,
                 "job_id": self.job_id, "trial_id": self.trial_id, "revision": revision,
                 "minute": int(self._wall_clock() // 60), "data": data}
        text = json.dumps(event, allow_nan=False)
        if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise KozError("INVALID_EVENT", "event too large")
        self._seq += 1
        self._sink(json.loads(text))   # a fresh copy, so the sink can't change ours
        for listener in list(self.listeners):
            listener(json.loads(text))
        return self._seq

    def bind(self, job_id=None, trial_id=None):
        """The job and trial the next events belong to (IDs from the web app's commands)."""
        for given in (job_id, trial_id):
            if given is not None and not (type(given) is str and ID_PATTERN.fullmatch(given)):
                raise KozError("INVALID_EVENT", "bad job or trial ID")
        with self.lock:
            if job_id != self.job_id:
                self.planner = None   # a new job: nobody has planned it yet
            self.job_id, self.trial_id = job_id, trial_id

    def set_planner(self, source):
        """Who made the current job's plan: "rules", "ollama", "nebius" or None."""
        if source not in (*PLANNERS, None):
            raise KozError("INVALID_EVENT", "unknown planner")
        with self.lock:
            self.planner = source
