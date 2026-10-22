"""Connecting this Mac to the cloud web app without editing .env by hand (Oct 22). Islombek had to
create a token, paste it into .env, restart, and each new token silently disconnected the Mac. Now
Ko'z asks once for the server address and the token (hidden), saves both in .env itself, and when
the server refuses the token it asks for the new one instead of failing. Values are never printed."""
import asyncio
import os
import stat
from http import HTTPStatus

import pytest
from helpers import FULL_FRAME
from test_cloud import free_port

from koz.agent import FakePlanner
from koz.agent.choose import load_env, save_env
from koz.cloud import ask_value, cloud_settings, link_cloud
from koz.local_setup import LocalSetup
from koz.server import Hub

OLD, NEW = "a" * 64, "b" * 64
URL = "wss://16.178.45.27/v1/runner"


def test_save_env_replaces_only_that_key_and_keeps_the_file_private(tmp_path):
    env = tmp_path / ".env"
    env.write_text(f"# settings\nNEBIUS_API_KEY=keep-me\nKOZ_RUNNER_TOKEN={OLD}\nX=1\nKOZ_RUNNER_TOKEN=older\n")
    save_env("KOZ_RUNNER_TOKEN", NEW, env)
    text = env.read_text()
    assert text.count("KOZ_RUNNER_TOKEN=") == 1 and f"KOZ_RUNNER_TOKEN={NEW}" in text
    assert "NEBIUS_API_KEY=keep-me" in text and "# settings" in text and "X=1" in text
    assert load_env(env)["KOZ_RUNNER_TOKEN"] == NEW
    assert stat.S_IMODE(os.stat(env).st_mode) == 0o600
    save_env("KOZ_CLOUD_URL", URL, tmp_path / "new.env")          # a missing file is created, private
    assert load_env(tmp_path / "new.env") == {"KOZ_CLOUD_URL": URL}
    assert stat.S_IMODE(os.stat(tmp_path / "new.env").st_mode) == 0o600


def test_ask_value_checks_the_answer_and_never_repeats_it():
    answers, said = iter(["not a token", "  " + NEW + "  "]), []
    got = ask_value("token", prompt=lambda text: next(answers), say=said.append)
    assert got == NEW
    assert any("doesn't look like" in s for s in said) and NEW not in " ".join(said)
    assert ask_value("token", prompt=lambda text: "", say=said.append) is None      # Enter alone: give up
    def eof(text):
        raise EOFError
    assert ask_value("token", prompt=eof, say=said.append) is None
    assert ask_value("address", prompt=lambda text: "http://16.178.45.27", say=said.append, tries=1) is None   # not wss://


def test_cloud_settings_asks_once_then_remembers(tmp_path):
    env, said = tmp_path / ".env", []
    asked = []
    def prompt(text):
        asked.append(text)
        return URL if "address" in text else NEW
    url, token = cloud_settings(None, env, interactive=True, prompt=prompt, say=said.append)
    assert (url, token) == (URL, NEW) and len(asked) == 2
    assert load_env(env) == {"KOZ_CLOUD_URL": URL, "KOZ_RUNNER_TOKEN": NEW}
    asked.clear()
    assert cloud_settings(None, env, interactive=True, prompt=prompt, say=said.append) == (URL, NEW)
    assert asked == []                                          # the second start asks nothing
    other = "wss://16.178.45.28/v1/runner"                      # a new address on the command line is saved
    assert cloud_settings(other, env, interactive=True, prompt=prompt, say=said.append)[0] == other
    assert load_env(env)["KOZ_CLOUD_URL"] == other
    assert NEW not in " ".join(said)


def test_cloud_settings_without_a_terminal_explains_instead_of_asking(tmp_path):
    said = []
    assert cloud_settings(None, tmp_path / ".env", interactive=False, prompt=pytest.fail, say=said.append) is None
    assert any("start-koz-cloud.command" in s for s in said)


def test_a_refused_token_is_asked_for_again_then_the_link_connects():
    from websockets.asyncio.server import serve

    port, said, attempts, asked = free_port(), [], [], []
    hub = Hub(LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME), lambda: pytest.fail("no camera"),
              FakePlanner(), say=said.append)
    connected = asyncio.Event()

    def check(connection, request):
        attempts.append(request.headers.get("Authorization"))
        if request.headers.get("Authorization") != f"Bearer {NEW}":
            return connection.respond(HTTPStatus.UNAUTHORIZED, '{"code":"AUTH_REQUIRED"}')
        return None

    def ask_new_token():
        asked.append(1)
        return NEW

    async def scenario():
        async with serve(lambda c: c.wait_closed(), "127.0.0.1", port, process_request=check):
            link = asyncio.create_task(link_cloud(hub, f"ws://127.0.0.1:{port}/v1/runner", OLD, connected=connected,
                                                  retry_s=(0.05,), ask_new_token=ask_new_token))
            await asyncio.wait_for(connected.wait(), 5)
            link.cancel()
            await asyncio.gather(link, return_exceptions=True)

    asyncio.run(scenario())
    assert asked == [1] and attempts[0] == f"Bearer {OLD}" and attempts[-1] == f"Bearer {NEW}"
    assert any("refused this token" in s for s in said)
    assert OLD not in " ".join(said) and NEW not in " ".join(said)


def test_the_cloud_launcher_asks_instead_of_carrying_an_address_or_token():
    from pathlib import Path
    text = (Path(__file__).resolve().parent.parent / "start-koz-cloud.command").read_text()
    run = [line for line in text.splitlines() if "koz.server" in line]
    assert run == [".venv/bin/python -m koz.server --i-own-this-camera --window --planner rules --cloud"]
    assert "wss://" not in text and "KOZ_RUNNER_TOKEN=" not in text


def test_save_env_takes_only_one_short_plain_setting(tmp_path):
    """The only file writer in koz/ can't carry a picture (rule 8): capitals for the name, at most 512
    printable characters for the value, no spaces or line breaks."""
    env = tmp_path / ".env"
    for key, value in [("KOZ_RUNNER_TOKEN", "x" * 513), ("KOZ_RUNNER_TOKEN", "a\nB=c"), ("KOZ_RUNNER_TOKEN", "two words"),
                       ("koz_lower", "v"), ("KOZ_RUNNER_TOKEN", ""), ("A" * 65, "v"), ("KOZ_RUNNER_TOKEN", "\x00" * 4)]:
        with pytest.raises(ValueError):
            save_env(key, value, env)
    assert not env.exists()
