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
never written anywhere. This is the only module in koz/ that encodes a frame (tests check that).

With --cloud (Oct 22, Islombek: the owner must see what Ko'z sees inside the website), the same
picture is also served as an MJPEG stream on 127.0.0.1 only (serve_stream), for an <img> in the
website's page opened on THIS computer: camera -> this computer's browser, never the cloud link. A
cross-origin image can be shown but not read by the page's code. It answers only our website's page
(Referer), only for 127.0.0.1 / localhost (Host), only GET of STREAM_PATH. The picture carries the
counting line, people boxes and the target ring (annotate), drawn on a copy."""
import asyncio
import ipaddress
import json
import time
import urllib.parse

import cv2
import numpy as np

PATH = "/v1/preview"
PREVIEW_WIDTH = 640
PREVIEW_FPS = 15
MAX_PREVIEW_BYTES = 160 * 1024
JPEG_QUALITIES = (75, 60, 45)    # tried in order until the picture fits MAX_PREVIEW_BYTES
POLL_S = 1 / 60                  # how often the feed looks for a new frame (it sends at most PREVIEW_FPS)
CLOSED_REASONS = ("not_running", "checking", "not_fresh")
STREAM_PATH, STREAM_PORT, BOUNDARY, MAX_VIEWERS = "/eye.mjpg", 8766, "kozframe", 2


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


_BLANK = None


def blank():
    """The closed lens: a dark picture (not from the camera) for a gap, so no last frame stays."""
    global _BLANK
    if _BLANK is None:
        _BLANK = encode(np.zeros((180, 320, 3), np.uint8))
    return _BLANK


def _origin(url):
    parts = urllib.parse.urlsplit(url or "")
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else None


def page_origin(cloud_url):
    """The website's own origin, from the runner's cloud address (wss://IP/v1/runner -> https://IP)."""
    parts = urllib.parse.urlsplit(cloud_url)
    return f"{'https' if parts.scheme == 'wss' else 'http'}://{parts.netloc}"


async def serve_stream(hub, allowed_origin, host="127.0.0.1", port=STREAM_PORT, started=None, interval=POLL_S):
    """The eye as an MJPEG stream for the website's page on this computer, until cancelled."""
    check_local(host)
    viewers = asyncio.Semaphore(MAX_VIEWERS)
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    async def client(reader, writer):
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 5)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ConnectionError):
            writer.close()
            return
        lines = head.decode("latin-1").split("\r\n")
        method, path = (lines[0].split(" ") + ["", ""])[:2]
        headers = {k.strip().lower(): v.strip() for k, v in (h.split(":", 1) for h in lines[1:] if ":" in h)}

        async def answer(status):
            writer.write(f"HTTP/1.1 {status}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode())
            await writer.drain()
            writer.close()

        if method != "GET":
            return await answer("405 Method Not Allowed")
        if path.split("?", 1)[0] != STREAM_PATH:
            return await answer("404 Not Found")
        if headers.get("host") not in hosts or _origin(headers.get("referer")) != allowed_origin \
                or headers.get("sec-fetch-dest", "image") != "image":
            return await answer("403 Forbidden")
        if viewers.locked():
            return await answer("503 Service Unavailable")
        async with viewers:
            await _stream(reader, writer, hub, interval)

    server = await asyncio.start_server(client, host, port)
    if started is not None:
        started.set()
    async with server:
        await server.serve_forever()


async def _stream(reader, writer, hub, interval):
    """Send until the job stops or the page goes away, watched separately: with a still picture
    there is nothing new to write, so a write alone would never notice a closed page."""
    sending = asyncio.create_task(_send_parts(writer, hub, interval))
    leaving = asyncio.create_task(reader.read())   # b"" when the browser drops the picture
    try:
        await asyncio.wait({sending, leaving}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        sending.cancel()
        leaving.cancel()
        await asyncio.gather(sending, leaving, return_exceptions=True)
        writer.close()


async def _send_parts(writer, hub, interval):
    def part(jpeg):
        return f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpeg)}\r\n\r\n".encode() + jpeg + b"\r\n"

    writer.write(("HTTP/1.1 200 OK\r\n" f"Content-Type: multipart/x-mixed-replace; boundary={BOUNDARY}\r\n"
                  "Cache-Control: no-store\r\nPragma: no-cache\r\nX-Content-Type-Options: nosniff\r\n"
                  "Referrer-Policy: no-referrer\r\nConnection: close\r\n\r\n").encode())
    sent_seq, sent_at, gap_since, blank_sent = None, None, None, False
    try:
        while True:
            image, seq, reason = hub.eye_frame()
            if image is not None:
                gap_since = None
                due = sent_at is None or time.monotonic() - sent_at >= 1 / PREVIEW_FPS - 0.002
                if seq != sent_seq and due:
                    jpeg = await asyncio.to_thread(encode, image)
                    if jpeg is not None and hub.eye_frame()[1] == seq:   # still current after encoding
                        writer.write(part(jpeg))
                        await writer.drain()
                        sent_seq, sent_at, blank_sent = seq, time.monotonic(), False
            elif reason == "not_running":
                if not blank_sent:
                    writer.write(part(blank()))
                writer.write(f"--{BOUNDARY}--\r\n".encode())
                await writer.drain()
                return
            else:   # a privacy check or a late frame: a blank lens once it lasts 0.15 s (no blink at routine checks)
                gap_since = gap_since or time.monotonic()
                if not blank_sent and time.monotonic() - gap_since >= 0.15:
                    writer.write(part(blank()))
                    await writer.drain()
                    sent_seq, blank_sent = None, True
            await asyncio.sleep(interval)
    except (ConnectionError, OSError):
        return
