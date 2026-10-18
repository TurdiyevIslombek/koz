"""The web app's eye: a small live preview, for this computer only (koz/eye.py; contracts/events.md
section 14; Islombek's decision, Oct 17). Only approved, face-blurred frames; closed with a reason
otherwise; only over the runner's local socket; never on the cloud link; never saved."""
import asyncio
import json
import socket
import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from helpers import FULL_FRAME, HEIGHT, WIDTH, Approve, EndlessCamera, FakeClock, FakeFaces, Sequence, color_recipe

from koz.agent import FakePlanner
from koz.events import EventLog, new_id
from koz.local_setup import LocalSetup
from koz.privacy import PrivacyResult
from koz.recipe import check_recipe
from koz.runner import Runner
from koz.server import Hub, serve

SETUP = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME)
FACE = (100, 60, 80, 80)   # where FakeFaces "finds" a face (x, y, w, h)
NOW = 1.76e9
KOZ = Path(__file__).resolve().parent.parent / "koz"


def noisy_scene():
    """Every pixel different, so pixelation is easy to see."""
    return np.random.default_rng(0).integers(0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8)


def runner_with(guard=None, camera=None, clock=None):
    clock = clock or FakeClock()
    runner = Runner(check_recipe(color_recipe()), SETUP, camera or EndlessCamera(noisy_scene(), clock),
                    EventLog(lambda e: None), scene_checker=guard or Approve(), face_detector=FakeFaces([FACE]),
                    clock=clock)
    return runner, clock


def colours(image, box):
    x, y, w, h = box
    return len(np.unique(image[y:y + h, x:x + w].reshape(-1, 3), axis=0))


def test_the_eye_shows_only_approved_frames_after_face_blur():
    from koz import eye

    runner, _ = runner_with()
    assert runner.eye_frame()[2] == "not_running"           # before the first frame
    assert runner.step() and runner.state == "running"
    image, seq, why = runner.eye_frame()
    assert why is None and image is not None and seq >= 1
    assert colours(noisy_scene(), FACE) > 5000 and colours(image, FACE) <= 64   # the face is pixelated
    jpeg = eye.encode(image)
    assert jpeg[:2] == b"\xff\xd8" and len(jpeg) <= eye.MAX_PREVIEW_BYTES
    shown = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    assert shown.shape[1] <= eye.PREVIEW_WIDTH
    runner.stop()
    assert runner.eye_frame() == (None, None, "not_running")


def test_the_eye_closes_while_the_guard_checks_or_confirms():
    once = PrivacyResult("unknown", "PRIVACY_UNCERTAIN", "bed", confirming=True)   # as the real guard says it
    guard = Sequence(PrivacyResult("approved"), *[once] * 5)    # confirming re-checks at once
    runner, _ = runner_with(guard=guard)
    assert runner.step() and runner.eye_frame()[0] is not None
    runner._gate._checked_at -= 1                             # the next frame is due a check: a bed, once
    assert runner.step() and runner.state == "checking"
    assert runner.eye_frame() == (None, None, "checking")


def test_the_eye_closes_on_a_stale_frame_and_on_a_privacy_stop():
    from helpers import Refuse

    clock = FakeClock()

    class Stale(EndlessCamera):
        def read(self):
            frame = super().read()
            return frame if self.index != 3 else type(frame)(frame.image, frame.t - 1.0, frame.index)

    runner, _ = runner_with(camera=Stale(noisy_scene(), clock), clock=clock)
    assert runner.step() and runner.step() and runner.eye_frame()[0] is not None
    assert runner.step() and runner.eye_frame() == (None, None, "not_fresh")
    assert runner.step() and runner.eye_frame()[0] is not None   # fresh again
    clock.advance(1.0)                                           # nothing new for a second
    assert runner.eye_frame() == (None, None, "not_fresh")
    runner._gate._checker = Refuse("PRIVATE_BATHROOM")
    runner._gate._checked_at -= 10
    assert runner.step() is False and runner.state == "held"
    assert runner.eye_frame() == (None, None, "not_running")


# --- the local socket ---------------------------------------------------------------------------------

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class PacedCamera:
    """A live-like camera: a frame every 1/30 s of real time (a fake clock would flood the sockets)."""
    capabilities = ()

    def __init__(self, image):
        self.image, self.index, self.is_open = image, 0, True

    def read(self):
        from koz.capture import Frame
        if not self.is_open:
            return None
        time.sleep(1 / 30)
        self.index += 1
        return Frame(self.image, time.monotonic(), self.index)

    def close(self):
        self.is_open = False


def running_hub():
    hub = Hub(SETUP, lambda: PacedCamera(noisy_scene()), FakePlanner(), wall_clock=lambda: NOW, eval_seconds=0.5,
              models={"scene_checker": Approve(), "face_detector": FakeFaces([FACE])})
    job = new_id()

    def command(name, data):
        hub.handle(json.dumps({"v": 1, "type": "command", "command_id": new_id(), "session_id": hub.events.session_id,
                               "job_id": job, "trial_id": None, "expires_at": NOW + 10, "command": name, "data": data}))

    command("start_job", {"input": "recipe", "recipe": color_recipe()})
    deadline = time.monotonic() + 5
    while hub.eye_frame()[0] is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert hub.eye_frame()[0] is not None
    return hub, command


def test_the_local_socket_sends_the_eye_at_most_5_times_a_second_then_closes_it():
    from websockets.asyncio.client import connect
    from websockets.exceptions import InvalidStatus

    from koz import eye

    port = free_port()
    hub, command = running_hub()

    async def scenario():
        started = asyncio.Event()
        server = asyncio.create_task(serve(hub, port=port, started=started))
        await started.wait()
        try:
            async with connect(f"ws://127.0.0.1:{port}{eye.PATH}", max_size=None) as ws, \
                    connect(f"ws://127.0.0.1:{port}") as events:
                frames, began = [], time.monotonic()
                while time.monotonic() - began < 1.2:
                    frames.append(await asyncio.wait_for(ws.recv(), 2))
                assert frames and all(isinstance(f, bytes) and f[:2] == b"\xff\xd8" for f in frames)
                assert len(frames) <= 1.2 * eye.PREVIEW_FPS + 2 and max(map(len, frames)) <= eye.MAX_PREVIEW_BYTES
                assert len(frames) >= 1.2 * 10   # smooth: at least 10 a second when the camera gives 30 (Oct 18)
                await asyncio.to_thread(command, "stop_job", {})
                message = await asyncio.wait_for(ws.recv(), 2)
                while isinstance(message, bytes):          # at most a frame already on its way
                    message = await asyncio.wait_for(ws.recv(), 2)
                assert json.loads(message) == {"v": 1, "type": "preview", "state": "closed", "reason": "not_running"}
                seen = []                                     # the event socket: text only, no picture
                try:
                    while True:
                        seen.append(await asyncio.wait_for(events.recv(), 0.3))
                except TimeoutError:
                    pass
                assert seen and all(isinstance(m, str) and "/9j/" not in m for m in seen)
            with pytest.raises(InvalidStatus) as refused:    # a browser can't open it directly
                async with connect(f"ws://127.0.0.1:{port}{eye.PATH}", origin="http://127.0.0.1:4173"):
                    pass
            assert refused.value.response.status_code == 403
        finally:
            server.cancel()
            await asyncio.gather(server, return_exceptions=True)

    try:
        asyncio.run(scenario())
    finally:
        hub.stop_local()
        hub._thread.join(5)


def test_the_eye_is_refused_on_a_socket_that_is_not_this_computer():
    from koz import eye

    with pytest.raises(ValueError):
        eye.check_local("0.0.0.0")
    with pytest.raises(ValueError):
        eye.check_local("192.168.1.20")
    eye.check_local("127.0.0.1")


# --- the cloud link: never ------------------------------------------------------------------------------

def test_the_cloud_link_never_carries_the_eye():
    from websockets.asyncio.server import serve as ws_serve

    from koz.cloud import link_cloud
    from koz.events import FIELDS

    port, received, shown = free_port(), [], []
    hub, command = running_hub()

    async def web(connection):   # a stand-in cloud web app: keeps everything the runner sends
        async for message in connection:
            received.append(message)

    async def scenario():
        up = asyncio.Event()
        async with ws_serve(web, "127.0.0.1", port, max_size=None):
            link = asyncio.create_task(link_cloud(hub, f"ws://127.0.0.1:{port}/v1/runner", "a" * 64, connected=up,
                                                  retry_s=(0.05,)))
            await asyncio.wait_for(up.wait(), 5)
            for _ in range(15):                     # 1.5 s with a running job and fresh eye frames
                shown.append(hub.eye_frame()[0] is not None)
                await asyncio.sleep(0.1)
            link.cancel()
            await asyncio.gather(link, return_exceptions=True)

    try:
        asyncio.run(scenario())
    finally:
        hub.stop_local()
        hub._thread.join(5)
    assert sum(shown) >= 10                                              # the eye had frames all along
    assert received and all(isinstance(m, str) for m in received)        # no binary message at all
    for message in received:
        assert json.loads(message)["type"] in FIELDS                        # the 7 contract events only
        assert "/9j/" not in message and "preview" not in message.lower() and "jpeg" not in message.lower()


def test_only_the_eye_module_encodes_a_frame_and_the_cloud_link_never_imports_it():
    users = sorted(p.relative_to(KOZ).as_posix() for p in KOZ.rglob("*.py") if "imencode" in p.read_text())
    assert users == ["eye.py"]
    importers = sorted(p.relative_to(KOZ).as_posix() for p in KOZ.rglob("*.py")
                       if "import eye" in p.read_text() or "from .eye" in p.read_text() or "koz.eye" in p.read_text())
    assert importers == ["server.py"]
    assert "eye" not in (KOZ / "cloud.py").read_text().lower()
