"""The live camera reader, tried on the recorded test video instead of a real camera."""
import time

import pytest

from helpers import LABELS
from koz.capture import LiveCamera
from koz.errors import KozError


def test_live_camera_hands_out_the_newest_frame_and_lets_it_age(test_video):
    with LiveCamera(str(test_video), warmup_s=0) as camera:
        seen = [camera.read()]
        for _ in range(50):   # read until no newer frame comes (the file has ended)
            frame = camera.read()
            if frame.index == seen[-1].index:
                break
            seen.append(frame)
        indices = [f.index for f in seen]
        assert indices == sorted(set(indices))      # only ever newer frames, never a backlog
        assert indices[-1] == len(LABELS) - 1       # the last frame of the file
        assert frame.t == seen[-1].t                # the same frame again: it only gets older
    assert camera.read() is None


def test_warmup_frames_are_dropped(test_video):
    """A file is read in a few milliseconds, all inside the warm-up: nothing usable arrives."""
    with pytest.raises(KozError) as caught:
        LiveCamera(str(test_video), warmup_s=1.0, first_frame_timeout_s=0.1)
    assert caught.value.code == "UNSUPPORTED_CAPABILITY"


def test_a_camera_that_cannot_open_is_refused(tmp_path):
    with pytest.raises(KozError) as caught:
        LiveCamera(str(tmp_path / "no-such-camera.avi"), warmup_s=0)
    assert caught.value.code == "UNSUPPORTED_CAPABILITY"


def test_a_recording_can_play_at_its_own_speed(test_video):
    """The demos and the runner play --video like a camera (10 fps here), so a short clip
    lasts long enough for the agent's rounds."""
    import time

    from koz.capture import FileCamera
    camera = FileCamera(test_video, realtime=True)
    started = time.monotonic()
    for _ in range(6):
        assert camera.read() is not None
    assert time.monotonic() - started >= 0.45   # frames 0..5 at 10 fps: 0.5 s
    camera.close()


# --- MJPEG over HTTP (the ESP32-CAM, a phone IP camera) ---------------------------------------

def mjpeg_server(frames_per_second=30, frame_count=None, password=None):
    """A local HTTP server that streams MJPEG like the ESP32-CAM (multipart JPEGs)."""
    import base64
    import http.server
    import threading

    import cv2
    import numpy as np

    class Stream(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if password and self.headers.get("Authorization") != "Basic " + base64.b64encode(password.encode()).decode():
                self.send_response(401)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            i = 0
            try:
                while frame_count is None or i < frame_count:
                    image = np.full((120, 160, 3), (i * 20) % 255, np.uint8)
                    jpeg = cv2.imencode(".jpg", image)[1].tobytes()
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
                    self.wfile.flush()
                    i += 1
                    time.sleep(1 / frames_per_second)
                time.sleep(5)   # then silence on an open connection, like a Wi-Fi stall
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stream)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_mjpeg_stream_gives_the_newest_frame_and_reconnects_after_a_stop():
    from koz.capture import MjpegCamera
    server = mjpeg_server()
    try:
        camera = MjpegCamera(f"http://127.0.0.1:{server.server_port}/stream")
        first, second = camera.read(), camera.read()
        assert first.image.shape == (120, 160, 3) and second.index > first.index
        camera.close()
        assert camera.read() is None
    finally:
        server.shutdown()


def test_a_stream_that_stops_sending_gets_stale_not_fresh():
    from koz.capture import MjpegCamera
    server = mjpeg_server(frame_count=5)
    try:
        camera = MjpegCamera(f"http://127.0.0.1:{server.server_port}/stream")
        time.sleep(0.5)                                       # the 5 frames are over; the stream stalls
        a, b = camera.read(), camera.read()
        assert a.index == b.index and time.monotonic() - b.t > 0.3   # the same old frame: the runner says FRAME_STALE
        camera.close()
    finally:
        server.shutdown()


def test_a_phone_camera_with_a_password_and_a_wrong_address():
    from koz.capture import MjpegCamera, describe, open_camera
    from koz.errors import KozError
    server = mjpeg_server(password="me:secret")
    try:
        camera = open_camera(f"http://me:secret@127.0.0.1:{server.server_port}/video")
        assert camera.read() is not None
        camera.close()
        with pytest.raises(KozError):   # wrong password: no picture, fails closed
            MjpegCamera(f"http://me:wrong@127.0.0.1:{server.server_port}/video", first_frame_timeout_s=1.0)
    finally:
        server.shutdown()
    for bad in ("/etc/passwd", "file:///etc/passwd", "ftp://x/y", ""):
        with pytest.raises(KozError):
            open_camera(bad)
    assert "secret" not in describe("rtsp://me:secret@192.168.1.5:554/live") == "rtsp://192.168.1.5:554/live"
