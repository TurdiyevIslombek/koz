"""The web app's eye: a small live preview of what Ko'z sees, for THIS computer only
(contracts/events.md section 14; Islombek's decision, Oct 17; CLAUDE.md rule 8: "the preview is
local and blurred").

What it sends, and only on the runner's local socket (ws://127.0.0.1:8765/v1/preview), to the web
app's own server on the same computer:
  - binary messages: a JPEG of the newest frame the privacy guard APPROVED, after the allowed-area
    mask and face blur (Runner.eye_frame), at most PREVIEW_WIDTH px wide, at most PREVIEW_FPS a
    second, at most MAX_PREVIEW_BYTES each (raised Oct 18 for a smooth eye and its large view:
    measured, the old 5 a second was the lag, not the guard or the detectors);
  - a text message {"v":1,"type":"preview","state":"closed","reason":R} as soon as there is no such
    frame, with R one of CLOSED_REASONS: "not_running" (no job, or it stopped), "checking" (the guard
    is checking, or confirming something it saw once), "not_fresh" (the newest frame is too old).
It is not an event: it never goes into the event log, never over the cloud link (koz/cloud.py does
not import this module, and tests/test_eye.py checks every message the cloud link sends), and it is
never written anywhere. This is the only module in koz/ that encodes a frame (tests check that)."""
import asyncio
import ipaddress
import json
import time

import cv2

PATH = "/v1/preview"
PREVIEW_WIDTH = 640
PREVIEW_FPS = 15
MAX_PREVIEW_BYTES = 160 * 1024
JPEG_QUALITIES = (75, 60, 45)    # tried in order until the picture fits MAX_PREVIEW_BYTES
POLL_S = 1 / 60                  # how often the feed looks for a new frame (it sends at most PREVIEW_FPS)
CLOSED_REASONS = ("not_running", "checking", "not_fresh")


def check_local(host):
    """The eye is served only on a socket of this computer (a loopback address)."""
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = host == "localhost"
    if not local:
        raise ValueError(f"the eye preview is only for this computer, not {host}")


def encode(image):
    """A frame (BGR) -> JPEG bytes, at most PREVIEW_WIDTH wide and MAX_PREVIEW_BYTES; None if it
    can't be made that small. In memory only."""
    height, width = image.shape[:2]
    if width > PREVIEW_WIDTH:
        image = cv2.resize(image, (PREVIEW_WIDTH, round(height * PREVIEW_WIDTH / width)), interpolation=cv2.INTER_AREA)
    for quality in JPEG_QUALITIES:
        ok, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok and len(jpeg) <= MAX_PREVIEW_BYTES:
            return jpeg.tobytes()
    return None


def closed(reason):
    assert reason in CLOSED_REASONS
    return json.dumps({"v": 1, "type": "preview", "state": "closed", "reason": reason}, separators=(",", ":"))


async def feed(connection, hub, interval=POLL_S):
    """Send the eye to one local connection until it closes (watched separately, so a quiet eye,
    with nothing to send, still notices a closed connection and lets the server shut down)."""
    sending = asyncio.create_task(_send(connection, hub, interval))
    closing = asyncio.create_task(connection.wait_closed())
    try:
        await asyncio.wait({sending, closing}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        sending.cancel()
        closing.cancel()
        await asyncio.gather(sending, closing, return_exceptions=True)


async def _send(connection, hub, interval):
    """The eye for one connection. `hub.eye_frame()` gives
    (image, seq, None) or (None, None, reason). A frame is sent only if it is still the current
    approved frame after encoding. "closed" is sent once each time the eye closes: at once when the
    job stops; otherwise only if the gap lasts 0.15 s, because a routine privacy check clears the
    frame for about one frame and the eye shouldn't blink (no frame is sent in the gap either way)."""
    from websockets.exceptions import ConnectionClosed

    sent_seq, sent_closed, waiting, sent_at = None, None, None, None
    try:
        while True:
            image, seq, reason = hub.eye_frame()
            if image is not None:
                waiting = None
                due = sent_at is None or time.monotonic() - sent_at >= 1 / PREVIEW_FPS - 0.002
                if seq != sent_seq and due:
                    jpeg = await asyncio.to_thread(encode, image)
                    if jpeg is not None and hub.eye_frame()[1] == seq:   # still current: not stopped or checking since
                        await connection.send(jpeg)
                        sent_seq, sent_closed, sent_at = seq, None, time.monotonic()
            elif reason != sent_closed:
                if reason == "not_running" or (waiting is not None and reason == waiting[0]
                                                and time.monotonic() - waiting[1] >= 0.15):
                    await connection.send(closed(reason))
                    sent_seq, sent_closed, waiting = None, reason, None
                elif waiting is None or waiting[0] != reason:
                    waiting = (reason, time.monotonic())
            await asyncio.sleep(interval)
    except ConnectionClosed:
        return
