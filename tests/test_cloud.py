"""The runner's outbound link to the cloud web app (koz/cloud.py; contracts/events.md section 5),
against a stand-in web server on this computer (ws://127.0.0.1)."""
import asyncio
import json
import socket
import time
from http import HTTPStatus

import pytest
from helpers import FULL_FRAME

from koz.agent import FakePlanner
from koz.cloud import check_cloud_url, link_cloud
from koz.events import new_id
from koz.local_setup import LocalSetup
from koz.server import Hub

SETUP = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME)
TOKEN = "a" * 64


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_the_cloud_address_must_be_encrypted_unless_it_is_this_computer():
    assert check_cloud_url("wss://203.0.113.7/v1/runner")
    assert check_cloud_url("ws://127.0.0.1:9000/v1/runner")
    for bad in ("ws://203.0.113.7/v1/runner", "http://x/v1/runner", "https://x"):
        with pytest.raises(ValueError):
            check_cloud_url(bad)


def test_status_first_commands_answered_and_waiting_events_after_a_reconnect():
    from websockets.asyncio.server import serve

    port, said = free_port(), []
    hub = Hub(SETUP, lambda: pytest.fail("no camera"), FakePlanner(), say=said.append)
    received, headers, connections = [], [], []

    async def web(connection):   # the stand-in cloud web app's /v1/runner
        headers.append(connection.request.headers.get("Authorization"))
        connections.append(connection)
        async for message in connection:
            received.append((len(connections), json.loads(message)))

    async def scenario():
        up = asyncio.Event()
        async with serve(web, "127.0.0.1", port):
            link = asyncio.create_task(link_cloud(hub, f"ws://127.0.0.1:{port}/v1/runner", TOKEN, connected=up,
                                                  retry_s=(0.05,)))
            await asyncio.wait_for(up.wait(), 5)
            await asyncio.sleep(0.1)
            first = received[0][1]
            assert first["type"] == "status" and first["session_id"] == hub.events.session_id
            command = {"v": 1, "type": "command", "command_id": new_id(), "session_id": hub.events.session_id,
                       "job_id": None, "trial_id": new_id(), "expires_at": int(time.time()) + 10,
                       "command": "begin_trial", "data": {"demo": "red_ball", "index": 1}}
            await connections[0].send(json.dumps(command))
            await asyncio.sleep(0.3)
            assert any(m["type"] == "command_result" and m["data"]["result"] == "accepted" for _, m in received)

            await connections[0].close()                     # the internet drops
            for _ in range(100):
                if not up.is_set():
                    break
                await asyncio.sleep(0.01)
            hub.events.emit("fault", {"code": "FRAME_STALE", "effect": "held"})        # waits for the reconnect
            hub.events.emit("observation", {"round": None, "privacy": "unknown", "occupancy": None, "entered": None,
                                            "exited": None, "coverage": "gapped", "target": None, "motion": None,
                                            "looming": None, "alert": None, "unknown_reason": "FRAME_STALE"})  # dropped
            await asyncio.wait_for(up.wait(), 5)
            await asyncio.sleep(0.3)
            link.cancel()
            await asyncio.gather(link, return_exceptions=True)

    asyncio.run(scenario())
    assert headers[0] == f"Bearer {TOKEN}" and len(connections) >= 2
    second = [m for n, m in received if n == 2]
    assert second[0]["type"] == "status"                   # a fresh status first, again
    assert second[1]["type"] == "fault" and second[1]["seq"] < second[0]["seq"]   # then what waited
    assert not any(m["type"] == "observation" for m in second)                     # status/observations dropped
    assert hub.busy is False                               # a reconnect never starts anything
    assert "Connected to the web app." in said and TOKEN not in " ".join(said)


def test_a_wrong_token_is_reported_and_retried_without_printing_it():
    from websockets.asyncio.server import serve

    port, said, attempts = free_port(), [], []
    hub = Hub(SETUP, lambda: pytest.fail("no camera"), FakePlanner(), say=said.append)

    def refuse(connection, request):
        attempts.append(request.headers.get("Authorization"))
        return connection.respond(HTTPStatus.UNAUTHORIZED, '{"code":"AUTH_REQUIRED"}')

    async def scenario():
        async with serve(lambda c: None, "127.0.0.1", port, process_request=refuse):
            link = asyncio.create_task(link_cloud(hub, f"ws://127.0.0.1:{port}/v1/runner", TOKEN, retry_s=(0.05,)))
            await asyncio.sleep(0.4)
            link.cancel()
            await asyncio.gather(link, return_exceptions=True)

    asyncio.run(scenario())
    assert len(attempts) >= 2                               # it keeps trying, slowly
    assert any("HTTP 401" in s and "KOZ_RUNNER_TOKEN" in s for s in said)
    assert TOKEN not in " ".join(said)


def test_offline_while_running_marks_the_coverage_gapped():
    hub = Hub(SETUP, lambda: pytest.fail("no camera"), FakePlanner())

    class Runner:
        state, coverage = "running", "complete"

    class Agent:
        runner = Runner()

    hub._agent = Agent()
    hub.went_offline()
    assert Agent.runner.coverage == "gapped"
