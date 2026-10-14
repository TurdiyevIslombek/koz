"""Events leave exactly as the contract says, or not at all (CLAUDE.md rule 9)."""
import pytest

from helpers import FakeClock
from koz.errors import KozError
from koz.events import EventLog, count_known, count_unknown, new_id


def observation(**changes):
    data = {"round": None, "privacy": "approved", "occupancy": None, "entered": None, "exited": None,
            "coverage": "complete", "target": "left", "motion": None, "looming": None, "alert": None,
            "unknown_reason": None}
    data.update(changes)
    return data


def test_envelope_and_numbering():
    sent = []
    job = new_id()
    log = EventLog(sent.append, job_id=job, wall_clock=FakeClock(1_788_000_059.9))
    log.emit("observation", observation(), revision=2)
    log.emit("fault", {"code": "FRAME_STALE", "effect": "held"})
    first, second = sent
    assert set(first) == {"v", "type", "session_id", "seq", "job_id", "trial_id", "revision", "minute", "data"}
    assert (first["v"], first["seq"], second["seq"]) == (1, 1, 2)
    assert first["job_id"] == job and first["trial_id"] is None and first["revision"] == 2
    assert first["minute"] == 1_788_000_059 // 60   # whole minutes only, never exact times
    assert len(first["session_id"]) == 32


def test_counts_known_and_unknown_are_allowed():
    sent = []
    EventLog(sent.append).emit("observation", observation(
        occupancy=count_known(0), entered=count_unknown("FRAME_STALE"), exited=None,
        unknown_reason="FRAME_STALE"))
    assert sent[0]["data"]["occupancy"] == {"state": "known", "value": 0, "reason": None}


@pytest.mark.parametrize("data", [
    observation(face_box=[10, 20, 30, 40]),          # a field the contract doesn't have
    {k: v for k, v in observation().items() if k != "alert"},   # a missing field
    observation(target="a man in a red coat"),       # free text
    observation(target=[0.4, 0.5]),                  # coordinates
    observation(round=True),                         # True is not 1
    observation(round=4),
    observation(occupancy={"state": "unknown", "value": 3, "reason": "FRAME_STALE"}),
    observation(occupancy={"state": "known", "value": -1, "reason": None}),
    observation(occupancy={"state": "unknown", "value": None, "reason": "made up"}),
])
def test_anything_off_contract_is_refused(data):
    sent = []
    log = EventLog(sent.append)
    with pytest.raises(KozError) as caught:
        log.emit("observation", data)
    assert caught.value.code == "INVALID_EVENT" and sent == []
    log.emit("observation", observation())
    assert sent[0]["seq"] == 1   # a refused event uses no sequence number


def test_unknown_types_revisions_and_ids_are_refused():
    log = EventLog([].append)
    for kind, data, revision in (("frame", {}, None), ("fault", {"code": "OOPS", "effect": "off"}, None),
                                 ("observation", observation(), 4)):
        with pytest.raises(KozError):
            log.emit(kind, data, revision=revision)
    with pytest.raises(KozError):
        EventLog([].append, job_id="not-a-hex-id")


def test_closed_privacy_gate_hides_every_output():
    log = EventLog([].append)
    closed = {"privacy": "blocked", "unknown_reason": "PRIVATE_BATHROOM"}
    for data in (observation(**closed),                                            # target still "left"
                 observation(**closed, target="unknown", occupancy=count_known(5)),
                 observation(**closed, target="unknown", alert="count_changed")):
        with pytest.raises(KozError):
            log.emit("observation", data)
    log.emit("observation", observation(**closed, target="unknown",
                                        occupancy=count_unknown("PRIVATE_BATHROOM")))


def test_ids_must_be_exactly_32_hex_characters():
    with pytest.raises(KozError):
        EventLog([].append, job_id="a" * 32 + "\n")


@pytest.mark.parametrize("data", [
    observation(target="unknown"),                                       # unknown with no reason
    observation(unknown_reason="FRAME_STALE"),                           # a reason with nothing unknown
    observation(privacy="unknown", target=None),                         # gate closed, no reason
    observation(target="unknown", unknown_reason="camera broke"),        # free text
    observation(target="unknown", unknown_reason="FRAME_STALE",
                occupancy=count_unknown("OVERLOADED")),                  # two different causes
])
def test_unknown_reason_rules_refuse(data):
    with pytest.raises(KozError) as caught:
        EventLog([].append).emit("observation", data)
    assert caught.value.code == "INVALID_EVENT"


@pytest.mark.parametrize("data", [
    observation(target="unknown", unknown_reason="OVERLOADED"),
    observation(target="lost"),                                          # lost is a measurement
    observation(privacy="blocked", target=None, unknown_reason="PRIVATE_BEDROOM"),   # nothing configured
    observation(privacy="unknown", target="unknown", unknown_reason="FRAME_STALE"),  # before the first check
])
def test_unknown_reason_rules_allow(data):
    EventLog([].append).emit("observation", data)
