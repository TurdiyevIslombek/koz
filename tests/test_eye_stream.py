"""The eye in the AWS website, on the camera computer only (Islombek, Oct 22: "the results should be
visible without getting out of the website"; he couldn't tell he hadn't left the camera's view).

With --cloud, the runner serves the same eye picture as the local web app (approved, face-blurred
frames, at most 640 px and 15 a second) as an MJPEG stream on 127.0.0.1 only, for an <img> in the
website's page opened on THIS computer. The picture goes camera -> this computer's browser; it is
never sent over the cloud link (tests/test_eye.py checks every cloud message). A cross-origin image
can be shown but not read by the page's code. The stream answers only our website's page (its
Referer), only on 127.0.0.1 / localhost (its Host: no DNS rebinding), only GET of the stream path.
When nothing may be shown it sends a blank lens and, when the job stops, ends.
The picture carries the counting line with its entry side, people boxes and the target ring, drawn
on a copy by the runner (koz/preview.py; the frame the blocks used is never changed)."""
import asyncio
import socket

import cv2
import numpy as np
import pytest

from koz import eye
from koz.preview import annotate

ORIGIN = "https://16.178.45.27"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeHub:
    """eye_frame() as the Hub gives it: (image, seq, None) or (None, None, reason)."""

    def __init__(self):
        self.image, self.seq, self.reason = np.full((240, 320, 3), 128, np.uint8), 1, None

    def eye_frame(self):
        if self.reason:
            return None, None, self.reason
        return self.image, self.seq, None


async def request(port, path=eye.STREAM_PATH, host=None, referer=ORIGIN + "/", method="GET", extra="", read_s=0.6):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    head = f"{method} {path} HTTP/1.1\r\nHost: {host or f'127.0.0.1:{port}'}\r\n"
    if referer:
        head += f"Referer: {referer}\r\n"
    writer.write((head + extra + "\r\n").encode())
    await writer.drain()
    data = b""
    try:
        while True:
            chunk = await asyncio.wait_for(reader.read(65536), read_s)
            if not chunk:
                break
            data += chunk
    except asyncio.TimeoutError:
        pass
    writer.close()
    return data


def run(scenario, hub, port):
    async def main():
        started = asyncio.Event()
        server = asyncio.create_task(eye.serve_stream(hub, ORIGIN, port=port, started=started))
        await started.wait()
        try:
            return await scenario()
        finally:
            server.cancel()
            await asyncio.gather(server, return_exceptions=True)
    return asyncio.run(main())


def jpeg_parts(data):
    return [p for p in data.split(b"--" + eye.BOUNDARY.encode()) if b"Content-Type: image/jpeg" in p]


def test_our_page_on_this_computer_gets_the_live_picture():
    hub, port = FakeHub(), free_port()
    data = run(lambda: request(port), hub, port)
    head = data.split(b"\r\n\r\n", 1)[0].decode()
    assert head.startswith("HTTP/1.1 200")
    assert f"multipart/x-mixed-replace; boundary={eye.BOUNDARY}" in head and "Cache-Control: no-store" in head
    assert "Access-Control-Allow-Origin" not in head   # no page can read the pixels
    parts = jpeg_parts(data)
    assert parts and cv2.imdecode(np.frombuffer(parts[0].split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n"), np.uint8),
                                  cv2.IMREAD_COLOR) is not None


@pytest.mark.parametrize("case", ["other site", "no referer", "rebinding host", "other path", "post"])
def test_everyone_else_is_refused(case):
    hub, port = FakeHub(), free_port()
    kwargs = {"other site": dict(referer="https://evil.example/"), "no referer": dict(referer=None),
              "rebinding host": dict(host=f"evil.example:{port}"), "other path": dict(path="/"),
              "post": dict(method="POST")}[case]
    data = run(lambda: request(port, **kwargs), hub, port)
    assert data.split(b"\r\n", 1)[0] in (b"HTTP/1.1 403 Forbidden", b"HTTP/1.1 404 Not Found", b"HTTP/1.1 405 Method Not Allowed")
    assert b"image/jpeg" not in data


def test_a_gap_shows_a_blank_lens_and_a_stop_ends_the_stream():
    hub, port = FakeHub(), free_port()

    async def scenario():
        reading = asyncio.create_task(request(port, read_s=2.5))
        await asyncio.sleep(0.4)
        hub.reason = "checking"            # a privacy check: nothing from the camera may show
        await asyncio.sleep(0.6)
        hub.reason = "not_running"         # the job stopped: the stream ends
        return await reading

    data = run(scenario, hub, port)
    parts = jpeg_parts(data)
    images = [cv2.imdecode(np.frombuffer(p.split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n"), np.uint8), cv2.IMREAD_COLOR) for p in parts]
    assert any(i.mean() > 100 for i in images)        # the camera frame (grey 128)
    assert images[-1].mean() < 30                      # then the blank lens, last
    assert data.rstrip().endswith(b"--" + eye.BOUNDARY.encode() + b"--")   # and the stream closed


def test_the_stream_is_only_ever_on_this_computer():
    with pytest.raises(ValueError):
        asyncio.run(eye.serve_stream(FakeHub(), ORIGIN, host="0.0.0.0", port=free_port()))


def test_the_overlay_draws_on_a_copy():
    image = np.zeros((240, 320, 3), np.uint8)

    class Person:
        box = (40, 40, 100, 200)

    class Target:
        x, y, area_ratio, label = 0.75, 0.5, 0.02, "right"

    view = annotate(image, {"person_detector": [Person()], "color_finder": Target()}, [[0.5, 0.0], [0.5, 1.0]])
    assert image.max() == 0                            # the frame the blocks used is unchanged
    assert view[120, 160].max() > 0                    # the counting line (x = 0.5)
    assert view[40, 70].max() > 0                      # a person's box
    assert view[:, 230:250].max() > 0                  # the target ring around x = 0.75
    assert annotate(image, {}, None).max() == 0    # nothing to draw: the picture as it is


def test_the_entry_arrow_points_the_way_the_counter_counts_in():
    """koz/blocks/line_counter.py: A top middle, B bottom middle -> walking right to left is "entered".
    The arrow must point the same way, or the owner would walk the wrong way (Oct 22)."""
    from koz.preview import ENTRY
    view = annotate(np.zeros((240, 320, 3), np.uint8), {}, [[0.5, 0.0], [0.5, 1.0]])
    ys, xs = np.where(np.all(view == ENTRY, axis=2))
    assert xs.size and xs.min() < 160 - 20 and xs.max() > 160 + 20     # the arrow crosses the line
    tip_side = xs[ys == ys[np.argmin(xs)]].mean()
    assert tip_side < 160                                               # its tip (and "IN") on the left
