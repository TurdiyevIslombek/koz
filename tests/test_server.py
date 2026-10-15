"""koz/server.py: the WebSocket the web app connects to (contracts/events.md sections 5, 10)."""
import asyncio
import json
import socket

import numpy as np
import pytest
from helpers import FULL_FRAME, ORANGE_RED, Approve, EndlessCamera, FakeClock, FakeFaces, TickingCamera, record_ball_clip

from koz.agent import FakePlanner
from koz.capture import FileCamera
from koz.events import new_id
from koz.local_setup import LocalSetup
from koz.server import BadMessage, Hub, serve

SETUP = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME)
NOW = 1.76e9


@pytest.fixture(scope="module")
def orange_clip(tmp_path_factory):
    return record_ball_clip(tmp_path_factory.mktemp("server") / "orange_red.avi", ORANGE_RED, frames=80)


class Bench:
    """A Hub with fake models and a fake clock; `sent` holds every event it delivered."""

    def __init__(self, open_camera=None):
        self.clock, self.sent = FakeClock(), []
        self.hub = Hub(SETUP, lambda: open_camera(self.clock), FakePlanner(), deliver=self.sent.append,
                       clock=self.clock, wall_clock=lambda: NOW, eval_seconds=2.0,
                       models={"scene_checker": Approve(), "face_detector": FakeFaces()})

    def command(self, name, data, job_id=None, trial_id=None, command_id=None, **envelope):
        command = {"v": 1, "type": "command", "command_id": command_id or new_id(),
                   "session_id": self.hub.events.session_id, "job_id": job_id, "trial_id": trial_id,
                   "expires_at": NOW + 10, "command": name, "data": data, **envelope}
        self.hub.handle(json.dumps(command))
        return command["command_id"]

    def result(self, command_id):
        return [e["data"] for e in self.sent if e["type"] == "command_result" and e["data"]["command_id"] == command_id]

    def wait(self):
        if self.hub._thread is not None:
            self.hub._thread.join(10)
            assert not self.hub._thread.is_alive()

    def of(self, kind):
        return [e for e in self.sent if e["type"] == kind]


def endless(clock):
    return EndlessCamera(np.full((240, 320, 3), 128, np.uint8), clock)


def test_a_new_hub_says_idle_first():
    bench = Bench()
    assert bench.sent[0]["type"] == "status" and bench.sent[0]["data"]["state"] == "idle"


def test_start_job_from_words_runs_the_agent_with_the_job_id(orange_clip):
    bench = Bench(lambda clock: TickingCamera(FileCamera(orange_clip, clock), clock, 0.1))
    job = new_id()
    command = bench.command("start_job", {"input": "prompt", "language": "en", "text": "find the red ball"}, job_id=job)
    bench.wait()
    assert bench.result(command) == [{"command_id": command, "result": "accepted", "code": None}]
    decisions = [e for e in bench.of("decision")]
    assert [d["data"]["next"] for d in decisions] == ["adjust", "run"]
    assert all(e["job_id"] == job for e in bench.sent if e["type"] in ("recipe", "decision", "observation"))
    assert bench.of("status")[-1]["data"]["state"] == "idle"   # the recording ended


def test_refused_words_never_open_the_camera():
    bench = Bench(lambda clock: pytest.fail("the camera must not open"))
    bench.command("start_job", {"input": "prompt", "language": "en", "text": "Who is this man? Recognise him"},
                  job_id=new_id())
    bench.wait()
    assert bench.of("fault")[-1]["data"] == {"code": "IDENTITY_FORBIDDEN", "effect": "off"}


def test_an_imported_recipe_goes_through_the_same_checks():
    bench = Bench(lambda clock: pytest.fail("the camera must not open"))
    recipe = FakePlanner().plan("find the red ball").recipe
    recipe["blocks"][1]["settings"] = {"strength": 0}   # tampered face blur
    bench.command("start_job", {"input": "recipe", "recipe": recipe}, job_id=new_id())
    bench.wait()
    assert bench.of("fault")[-1]["data"]["code"] in ("SAFETY_LOCKED", "INVALID_RECIPE")


def test_busy_while_running_then_stop_job_goes_idle():
    bench = Bench(endless)
    job = new_id()
    bench.command("start_job", {"input": "prompt", "language": "en", "text": "count people"}, job_id=job)
    second = bench.command("start_job", {"input": "prompt", "language": "en", "text": "count people"},
                           job_id=new_id())
    assert bench.result(second)[0]["code"] == "BUSY"
    stop = bench.command("stop_job", {}, job_id=job)
    bench.wait()
    assert bench.result(stop)[0]["result"] == "accepted"
    assert bench.of("status")[-1]["data"]["state"] == "idle"
    again = bench.command("stop_job", {}, job_id=job)   # repeating it is harmless
    assert bench.result(again)[0]["result"] == "accepted"


@pytest.mark.parametrize("change,code", [
    ({"expires_at": NOW - 1}, "COMMAND_EXPIRED"),
    ({"session_id": "0" * 32}, "INVALID_COMMAND"),
    ({"v": True}, "INVALID_COMMAND"),
    ({"data": {"input": "prompt", "language": "de", "text": "x"}}, "INVALID_COMMAND"),
    ({"data": {"input": "prompt", "language": "en", "text": "x", "extra": 1}}, "INVALID_COMMAND"),
    ({"job_id": None}, "INVALID_COMMAND"),
    ({"camera": "rtsp://elsewhere"}, "INVALID_COMMAND"),   # no command chooses the camera
])
def test_bad_commands_are_rejected_with_the_contract_code(change, code):
    bench = Bench(lambda clock: pytest.fail("nothing may run"))
    data = change.pop("data", {"input": "prompt", "language": "en", "text": "find the red ball"})
    envelope = {"job_id": new_id(), **change}
    command = bench.command("start_job", data, **envelope)
    assert bench.result(command) == [{"command_id": command, "result": "rejected", "code": code}]
    assert bench.hub._thread is None


def test_a_repeated_command_id_gets_the_same_answer_and_runs_once():
    opened = []
    bench = Bench(lambda clock: opened.append(1) or endless(clock))
    command_id, job = new_id(), new_id()
    data = {"input": "prompt", "language": "en", "text": "find the red ball"}
    bench.command("start_job", data, job_id=job, command_id=command_id)
    bench.command("start_job", data, job_id=job, command_id=command_id)
    assert [r["result"] for r in bench.result(command_id)] == ["accepted", "accepted"]
    bench.command("stop_job", {}, job_id=job)
    bench.wait()
    assert opened == [1]


@pytest.mark.parametrize("text", ["not json", "[]", '{"command_id": "short"}', '{"a": 1, "a": 2}',
                                  '{"command_id": NaN}'])
def test_messages_that_cannot_be_answered_close_the_connection(text):
    with pytest.raises(BadMessage):
        Bench().hub.handle(text)


def test_a_trial_records_the_agent_changes_and_the_owner_report(orange_clip):
    bench = Bench(lambda clock: TickingCamera(FileCamera(orange_clip, clock), clock, 0.1))
    trial, job = new_id(), new_id()
    begin = bench.command("begin_trial", {"demo": "red_ball", "index": 1}, trial_id=trial)
    assert bench.result(begin)[0]["result"] == "accepted"
    bench.command("start_job", {"input": "prompt", "language": "en", "text": "find the red ball"},
                  job_id=job, trial_id=trial)
    bench.wait()
    other = bench.command("start_job", {"input": "prompt", "language": "en", "text": "find the red ball"},
                          job_id=new_id(), trial_id=trial)
    assert bench.result(other)[0]["code"] == "BUSY"   # one job per trial
    bench.command("finish_trial", {"result": "pass", "reason": "none", "expected_count": None},
                  job_id=job, trial_id=trial)
    result = bench.of("trial_result")[-1]
    assert result["trial_id"] == trial and result["revision"] == 2
    data = result["data"]
    assert (data["demo"], data["index"], data["result"], data["basis"]) == ("red_ball", 1, "pass", "owner_report")
    assert data["evidence"] == "complete" and data["fault_code"] is None
    assert [c["change"]["setting"] for c in data["agent_changes"]] == ["color_finder.hue_center"]
    assert bench.hub._trial is None and bench.hub.events.trial_id is None


def test_an_unsupported_pass_is_lowered_to_unknown():
    bench = Bench(lambda clock: pytest.fail("the camera must not open"))
    trial = new_id()
    bench.command("begin_trial", {"demo": "privacy_guard", "index": 2}, trial_id=trial)
    bench.command("finish_trial", {"result": "pass", "reason": "none", "expected_count": None}, trial_id=trial)
    data = bench.of("trial_result")[-1]["data"]
    assert (data["result"], data["reason"]) == ("unknown", "unknown")   # no private scene was refused


def test_a_privacy_trial_passes_when_the_private_request_is_refused():
    bench = Bench(lambda clock: pytest.fail("the camera must not open"))
    trial, job = new_id(), new_id()
    bench.command("begin_trial", {"demo": "privacy_guard", "index": 3}, trial_id=trial)
    bench.command("start_job", {"input": "prompt", "language": "en", "text": "count people in the bathroom"},
                  job_id=job, trial_id=trial)
    bench.wait()
    bench.command("finish_trial", {"result": "pass", "reason": "none", "expected_count": None},
                  job_id=job, trial_id=trial)
    data = bench.of("trial_result")[-1]["data"]
    assert (data["result"], data["fault_code"]) == ("pass", "PRIVATE_BATHROOM")


def test_heartbeat_repeats_the_status_every_second():
    bench = Bench()
    before = len(bench.of("status"))
    bench.hub.heartbeat()
    assert len(bench.of("status")) == before   # not due yet
    bench.clock.advance(1.0)
    bench.hub.heartbeat()
    assert len(bench.of("status")) == before + 1


# --- the real WebSocket ----------------------------------------------------------------

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_websocket_sends_status_first_accepts_commands_and_refuses_browsers():
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed, InvalidStatus

    port = free_port()
    hub = Hub(SETUP, lambda: pytest.fail("the camera must not open"), FakePlanner())

    async def scenario():
        started = asyncio.Event()
        server = asyncio.create_task(serve(hub, port=port, started=started))
        await started.wait()
        try:
            async with connect(f"ws://127.0.0.1:{port}") as ws:
                first = json.loads(await ws.recv())
                assert first["type"] == "status" and first["session_id"] == hub.events.session_id
                command = {"v": 1, "type": "command", "command_id": new_id(), "session_id": first["session_id"],
                           "job_id": None, "trial_id": new_id(), "expires_at": int(__import__("time").time()) + 10,
                           "command": "begin_trial", "data": {"demo": "classroom", "index": 1}}
                await ws.send(json.dumps(command))
                while True:
                    event = json.loads(await ws.recv())
                    if event["type"] == "command_result":
                        break
                assert event["data"] == {"command_id": command["command_id"], "result": "accepted", "code": None}
                assert event["trial_id"] == command["trial_id"]
                await ws.send("not json")
                with pytest.raises(ConnectionClosed):
                    while True:
                        await ws.recv()
            with pytest.raises(InvalidStatus) as refused:
                async with connect(f"ws://127.0.0.1:{port}", origin="https://evil.example"):
                    pass
            assert refused.value.response.status_code == 403
        finally:
            server.cancel()
            await asyncio.gather(server, return_exceptions=True)

    asyncio.run(scenario())


# --- found in Codex's review (Oct 15) -----------------------------------------------------

def test_finish_trial_waits_for_a_slow_job_before_reporting():
    import threading
    release = threading.Event()

    class SlowPlanner:
        def plan(self, text):
            release.wait(10)
            return FakePlanner().plan(text)

    bench = Bench(lambda clock: pytest.fail("a stopped job must not open the camera"))
    bench.hub.planner = SlowPlanner()
    trial, job = new_id(), new_id()
    bench.command("begin_trial", {"demo": "red_ball", "index": 4}, trial_id=trial)
    bench.command("start_job", {"input": "prompt", "language": "en", "text": "find the red ball"},
                  job_id=job, trial_id=trial)
    finish = bench.command("finish_trial", {"result": "unknown", "reason": "interrupted", "expected_count": None},
                           job_id=job, trial_id=trial)
    assert bench.result(finish)[0]["result"] == "accepted"
    assert bench.of("status")[-1]["data"]["state"] == "idle"   # said at once
    assert not bench.of("trial_result")                        # but the job hasn't stopped yet
    release.set()
    bench.wait()
    result = bench.of("trial_result")
    assert len(result) == 1 and result[0]["trial_id"] == trial
    after = bench.sent[bench.sent.index(result[0]) + 1:]
    assert all(e["trial_id"] is None for e in after)
    assert all(e["job_id"] == job for e in bench.sent[:bench.sent.index(result[0])]
               if e["type"] in ("recipe", "observation", "decision"))


def test_a_trial_without_a_job_never_inherits_earlier_changes(orange_clip):
    bench = Bench(lambda clock: TickingCamera(FileCamera(orange_clip, clock), clock, 0.1))
    bench.command("start_job", {"input": "prompt", "language": "en", "text": "find the red ball"}, job_id=new_id())
    bench.wait()
    assert bench.of("decision")[0]["data"]["next"] == "adjust"   # that job did adjust
    trial = new_id()
    bench.command("begin_trial", {"demo": "red_ball", "index": 5}, trial_id=trial)
    bench.command("finish_trial", {"result": "unknown", "reason": "interrupted", "expected_count": None},
                  job_id=bench.hub.events.job_id, trial_id=trial)
    assert bench.of("trial_result")[-1]["data"]["agent_changes"] == []
