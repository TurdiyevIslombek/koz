"""Delivering the runner's events over WebSocket, to the local web app (koz/server.py: it connects in)
or to the cloud web app on AWS (link_cloud: the runner connects out). contracts/events.md section 5.

Cloud mode: one outbound WebSocket from this computer,
    wss://<web origin>/v1/runner      Authorization: Bearer <KOZ_RUNNER_TOKEN>
Nothing connects into this computer; it needs no AWS keys for this, and no camera is ever reachable
from outside. The same events and commands as locally, checked the same way:
  - every connection starts with a fresh status, then the events that waited (below), then
    everything new, in seq order;
  - while disconnected, recipe/decision/fault/command_result/trial_result wait in memory (at most
    200; an overflow marks the open trial's evidence incomplete); status and observations are
    dropped, and the running job's coverage becomes "gapped";
  - a reconnect never replays a command, starts a job or arms motors (contract section 5);
  - the web origin and token are local config (.env), never printed and never from a command."""
import asyncio
import getpass
import json
import os
import re
import urllib.parse
from collections import deque

OFFLINE_QUEUE = 200
KEEP_OFFLINE = frozenset({"recipe", "decision", "fault", "command_result", "trial_result"})
LOOPBACK = ("127.0.0.1", "localhost", "::1")
RETRY_S = (1, 2, 5, 10, 30)   # waits between reconnect attempts


class Outbox:
    """The hub's events -> WebSocket connections, in seq order. Create it on the event loop's thread;
    deliver() may be called from any thread. `send(connections, text)` is websockets' broadcast."""

    def __init__(self, hub, loop, send):
        self.hub, self.loop, self.send = hub, loop, send
        self.clients, self.joining, self.queue = set(), {}, deque()
        hub.deliver = self.deliver

    def deliver(self, event):   # from any thread
        try:
            self.loop.call_soon_threadsafe(self._dispatch, event)
        except RuntimeError:   # the loop already stopped
            pass

    def _dispatch(self, event):   # always on the event loop, in seq order
        text = json.dumps(event, allow_nan=False)
        joiner = self.joining.pop(event["seq"], None)
        if self.clients:
            self.send(set(self.clients), text)
        elif joiner is None and event["type"] in KEEP_OFFLINE:
            if len(self.queue) == OFFLINE_QUEUE:
                self.queue.popleft()
                self.hub.mark_lost()
            self.queue.append(text)
        if joiner is not None:   # its first message is this fresh status, then what waited
            self.send([joiner], text)
            while self.queue:
                self.send([joiner], self.queue.popleft())
            self.clients.add(joiner)

    def join(self, connection):
        """A new connection (on the loop's thread): a fresh status goes to it first."""
        self.joining[self.hub.emit_status()["seq"]] = connection   # no await before _dispatch runs

    def leave(self, connection):
        self.clients.discard(connection)
        for seq in [s for s, c in self.joining.items() if c is connection]:
            del self.joining[seq]
        if not self.clients:
            self.hub.went_offline()


async def heartbeat(hub):
    while True:
        await asyncio.sleep(0.25)
        hub.heartbeat()


TOKEN_PATTERN = re.compile(r"^[0-9a-f]{64}$")   # the web app makes 32 random bytes, in hex


def ask_value(kind, prompt=None, say=print, tries=3):
    """Ask in Terminal for the server `address` or the device `token` (hidden while typing or pasting).
    Returns the checked value, or None (Enter alone, end of input, or `tries` wrong answers).
    What was typed is never repeated."""
    if prompt is None:
        prompt = getpass.getpass if kind == "token" else input
    question = {"token": "Device token (hidden; paste it, then press Enter): ",
                "address": "Server address (web app -> Connect device -> Server address): "}[kind]
    for _ in range(tries):
        try:
            answer = prompt(question).strip()
        except EOFError:
            return None
        if not answer:
            return None
        if kind == "token" and TOKEN_PATTERN.match(answer):
            return answer
        if kind == "address":
            try:
                return check_cloud_url(answer)
            except ValueError:
                pass
        say("That doesn't look like a device token (64 letters and digits from the web app). Try again."
            if kind == "token" else "That doesn't look like the server address (it starts with wss://). Try again.")
    return None


def cloud_settings(url, env_path=None, interactive=True, prompt=None, say=print, environ=None):
    """The cloud address and device token for this start: from the command line or .env, else asked
    once in Terminal and saved in .env (Oct 22). None (with a message said) if Ko'z can't start."""
    from .agent.choose import load_env, save_env
    environ = os.environ if environ is None else environ
    saved = load_env(env_path)
    if url is None:
        url = saved.get("KOZ_CLOUD_URL")
        if not url and interactive:
            say("Ko'z needs the server address once. In the web app: Connect device -> Server address. Copy it here.")
            url = ask_value("address", prompt, say)
            if url:
                save_env("KOZ_CLOUD_URL", url, env_path)
    elif url != saved.get("KOZ_CLOUD_URL"):
        try:
            save_env("KOZ_CLOUD_URL", check_cloud_url(url), env_path)
        except ValueError:
            pass
    if not url:
        say("Ko'z did not start: it needs the server address. Double-click start-koz-cloud.command, "
            "or start it with --cloud wss://SERVER/v1/runner.")
        return None
    try:
        check_cloud_url(url)
    except ValueError:
        say("Ko'z did not start: the server address must start with wss://.")
        return None
    token = environ.get("KOZ_RUNNER_TOKEN") or saved.get("KOZ_RUNNER_TOKEN")
    if not token and interactive:
        say("Ko'z needs the device token once. In the web app: Connect device -> Create device token -> Copy.")
        token = ask_value("token", prompt, say)
        if token:
            save_env("KOZ_RUNNER_TOKEN", token, env_path)
            say("Saved on this Mac: Ko'z won't ask again.")
    if not token:
        say("Ko'z did not start: it needs the device token. Double-click start-koz-cloud.command "
            "(it asks once and remembers it).")
        return None
    return url, token


def check_cloud_url(url):
    """wss:// for the cloud; ws:// only to this computer (tests, a local web app)."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme == "wss" or (parts.scheme == "ws" and parts.hostname in LOOPBACK):
        return url
    raise ValueError("the cloud address must be wss://")


async def link_cloud(hub, url, token, connected=None, retry_s=RETRY_S, ask_new_token=None):
    """Keep one outbound connection to the cloud web app until cancelled. `connected` (an
    asyncio.Event) is set each time a connection is up (for tests). `ask_new_token` (optional,
    called in a thread) asks for a new token when the web app refuses this one (Oct 22)."""
    from websockets.asyncio.client import connect
    from websockets.asyncio.server import broadcast
    from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidStatus

    from .events import MAX_MESSAGE_BYTES
    from .errors import BadMessage

    check_cloud_url(url)
    outbox = Outbox(hub, asyncio.get_running_loop(), broadcast)
    beating = asyncio.create_task(heartbeat(hub))
    failures = 0
    try:
        while True:
            try:
                async with connect(url, additional_headers={"Authorization": f"Bearer {token}"},
                                   max_size=MAX_MESSAGE_BYTES, compression=None, open_timeout=10) as ws:
                    failures = 0
                    hub.say("Connected to the web app.")
                    outbox.join(ws)
                    if connected is not None:
                        connected.set()
                    try:
                        async for message in ws:
                            if not isinstance(message, str):
                                break   # the web never sends binary: something is wrong; reconnect
                            try:
                                await asyncio.to_thread(hub.handle, message)
                            except BadMessage:   # e.g. {"type":"protocol_error"}: it refused an event
                                hub.say("The web app answered with something that isn't a command.")
                    finally:
                        outbox.leave(ws)
                        if connected is not None:
                            connected.clear()
                hub.say("Disconnected from the web app; reconnecting.")
            except InvalidStatus as error:
                code = error.response.status_code
                if code == 401 and ask_new_token is not None:
                    hub.say("The web app refused this token (HTTP 401): a newer token replaced it. Click this "
                            "Terminal window and paste the new one (web app -> Connect device).")
                    new = await asyncio.to_thread(ask_new_token)
                    if new:
                        token, failures = new, 0
                        continue
                else:
                    hub.say(f"The web app refused the connection (HTTP {code})"
                            + (": check KOZ_RUNNER_TOKEN in .env." if code == 401 else "."))
            except (OSError, ConnectionClosed, InvalidHandshake, TimeoutError):
                hub.say("The web app can't be reached; trying again.")
            await asyncio.sleep(retry_s[min(failures, len(retry_s) - 1)])
            failures += 1
    finally:
        beating.cancel()
