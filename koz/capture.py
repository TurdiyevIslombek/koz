"""Video sources (CLAUDE.md rule 8).

Video only: nothing here asks OpenCV for an audio stream, and nothing writes frames
to disk. A frame lives in memory until the runner is done with it.

Sources (open_camera): this computer's camera (0), an MJPEG stream over HTTP (the ESP32-CAM
"http://192.168.4.1:81/stream", or a phone IP-camera app), or RTSP (some phone apps and IP
cameras). The address comes only from the runner's own command line, never from a recipe or
the web app, and is never printed or sent (it may hold a password)."""
import base64
import http.client
import threading
import time
import urllib.parse
from dataclasses import dataclass

import cv2
import numpy as np

from . import policy
from .errors import KozError


@dataclass(frozen=True)
class Frame:
    """One picture from a camera. `t` is time.monotonic() when it arrived; the runner
    uses it to spot stale frames."""
    image: np.ndarray   # BGR, as OpenCV gives it
    t: float
    index: int


class FileCamera:
    """The mock camera: plays a recorded video file, one frame per read().

    For tests and trials only. The file must not be a recording made by Ko'z
    (Ko'z never records), and a recipe can never choose the path.

    `realtime=True` plays it at its own frame rate, like a camera (the demos and the runner):
    otherwise a short clip is over before the agent's 3-second rounds are. Tests leave it off
    and move a fake clock instead."""
    capabilities = ("recorded_fixture",)

    def __init__(self, path, clock=time.monotonic, realtime=False):
        self._clock = clock
        self._cap = cv2.VideoCapture(str(path))
        if not self._cap.isOpened():
            raise KozError("UNSUPPORTED_CAPABILITY", "video file cannot be opened")
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._period = (1.0 / fps if fps and 1 <= fps <= 120 else 1 / 15) if realtime else 0.0
        self._started = None
        self._index = 0
        self.is_open = True

    def read(self):
        """The next frame, or None when the recording has ended."""
        if self._period:   # wait until this frame's moment in the recording
            if self._started is None:
                self._started = time.monotonic()
            wait = self._started + self._index * self._period - time.monotonic()
            if wait > 0:
                time.sleep(wait)
        ok, image = self._cap.read() if self.is_open else (False, None)
        if not ok:
            self.close()
            return None
        frame = Frame(image, self._clock(), self._index)
        self._index += 1
        return frame

    def close(self):
        if self.is_open:
            self._cap.release()
            self.is_open = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class LiveCamera:
    """A live camera: the computer's own camera (source 0) or a stream address such as
    the ESP32-CAM's "http://flycar-cam.local:81/stream".

    A background thread keeps reading and holds only the newest frame, so the runner
    never works through a backlog. read() waits briefly for a frame it hasn't returned
    yet; if none comes, it returns the old one again, which is then too old and the
    runner reports FRAME_STALE. That is what happens when Wi-Fi drops."""
    capabilities = ()

    def __init__(self, source=0, clock=time.monotonic, first_frame_timeout_s=5.0,
                 warmup_s=policy.CAMERA_WARMUP_S):
        self._clock = clock
        self._warmup_s = warmup_s   # frames from the first second are dropped: still too dark
        self._cap = cv2.VideoCapture(source)
        if not self._cap.isOpened():
            raise KozError("UNSUPPORTED_CAPABILITY", "camera cannot be opened")
        if isinstance(source, int):   # ask for 4:3, so frames aren't squashed to 640 x 480 later
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._new_frame = threading.Condition()
        self._latest = None
        self._returned_index = None
        self.is_open = True
        self._thread = threading.Thread(target=self._keep_reading, name="koz-camera", daemon=True)
        self._thread.start()
        with self._new_frame:
            self._new_frame.wait_for(lambda: self._latest is not None, timeout=warmup_s + first_frame_timeout_s)
        if self._latest is None:
            self.close()
            raise KozError("UNSUPPORTED_CAPABILITY", "camera sent no picture")

    def _keep_reading(self):
        index, opened = 0, time.monotonic()
        while self.is_open:
            ok, image = self._cap.read()
            if not ok:
                time.sleep(0.01)   # no picture right now; the waiting frame just gets older
                continue
            if time.monotonic() - opened < self._warmup_s:
                continue           # exposure is still settling (see policy.CAMERA_WARMUP_S)
            with self._new_frame:
                self._latest = Frame(image, self._clock(), index)
                self._new_frame.notify_all()
            index += 1

    def read(self):
        """The newest frame, or None once the camera is closed."""
        with self._new_frame:
            self._new_frame.wait_for(
                lambda: not self.is_open or self._latest.index != self._returned_index,
                timeout=policy.MAX_FRAME_AGE_S)
            if not self.is_open:
                return None
            self._returned_index = self._latest.index
            return self._latest

    def close(self):
        if not self.is_open:
            return
        with self._new_frame:
            self.is_open = False
            self._new_frame.notify_all()
        self._thread.join(timeout=2.0)
        if not self._thread.is_alive():   # never release while the thread may still be reading
            self._cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class MjpegCamera:
    """An MJPEG stream over HTTP: the ESP32-CAM, or a phone IP-camera app. Like LiveCamera, a
    background thread keeps only the newest picture, and read() gives the same one again (then
    too old: FRAME_STALE) when Wi-Fi drops. It reconnects by itself. Each picture is cut out of
    the stream at the JPEG start and end markers (as in Islombek's stage 3 reader)."""
    capabilities = ()
    CHUNK = 16384
    MAX_BUFFER = 2_000_000

    def __init__(self, url, clock=time.monotonic, first_frame_timeout_s=5.0, connect_timeout_s=2.0):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise KozError("UNSUPPORTED_CAPABILITY", "not an http stream address")
        self._parts, self._clock, self._timeout = parts, clock, connect_timeout_s
        self._new_frame = threading.Condition()
        self._latest = None
        self._returned_index = None
        self._connection = None
        self.is_open = True
        self._thread = threading.Thread(target=self._keep_reading, name="koz-mjpeg", daemon=True)
        self._thread.start()
        with self._new_frame:
            self._new_frame.wait_for(lambda: self._latest is not None, timeout=first_frame_timeout_s)
        if self._latest is None:
            self.close()
            raise KozError("UNSUPPORTED_CAPABILITY", "camera sent no picture")

    def _connect(self):
        p = self._parts
        kind = http.client.HTTPSConnection if p.scheme == "https" else http.client.HTTPConnection
        connection = kind(p.hostname, p.port, timeout=self._timeout)
        headers = {}
        if p.username:   # some phone apps ask for a user name and password
            login = f"{urllib.parse.unquote(p.username)}:{urllib.parse.unquote(p.password or '')}"
            headers["Authorization"] = "Basic " + base64.b64encode(login.encode()).decode()
        connection.request("GET", (p.path or "/") + (f"?{p.query}" if p.query else ""), headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            connection.close()
            raise ConnectionError("no stream")
        self._connection = connection
        return response

    def _keep_reading(self):
        index = 0
        while self.is_open:
            try:
                response, buffer = self._connect(), b""
                while self.is_open:
                    chunk = response.read1(self.CHUNK)
                    if not chunk:
                        raise ConnectionError("stream ended")
                    buffer += chunk
                    newest = None
                    while True:   # every complete JPEG in the buffer; only the newest is decoded
                        start = buffer.find(b"\xff\xd8")
                        end = buffer.find(b"\xff\xd9", start + 2) if start != -1 else -1
                        if start == -1 or end == -1:
                            break
                        newest, buffer = buffer[start:end + 2], buffer[end + 2:]
                    if len(buffer) > self.MAX_BUFFER:
                        buffer = b""
                    image = cv2.imdecode(np.frombuffer(newest, np.uint8), cv2.IMREAD_COLOR) if newest else None
                    if image is not None:
                        with self._new_frame:
                            self._latest = Frame(image, self._clock(), index)
                            self._new_frame.notify_all()
                        index += 1
            except (OSError, http.client.HTTPException, ValueError):
                pass   # Wi-Fi dropped or the camera restarted: the last frame gets old; try again
            finally:
                if self._connection is not None:
                    self._connection.close()
                    self._connection = None
            if self.is_open:
                time.sleep(0.5)

    def read(self):
        """The newest frame, or None once the camera is closed."""
        with self._new_frame:
            self._new_frame.wait_for(
                lambda: not self.is_open or self._latest.index != self._returned_index,
                timeout=policy.MAX_FRAME_AGE_S)
            if not self.is_open:
                return None
            self._returned_index = self._latest.index
            return self._latest

    def close(self):
        if not self.is_open:
            return
        with self._new_frame:
            self.is_open = False
            self._new_frame.notify_all()
        connection = self._connection
        if connection is not None and connection.sock is not None:
            try:
                connection.sock.shutdown(2)   # wakes the reading thread
            except OSError:
                pass
        self._thread.join(timeout=2.0)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def open_camera(source, clock=time.monotonic):
    """A camera from the runner's command line: "0" (this computer), "http(s)://..." (MJPEG:
    the ESP32-CAM, a phone app) or "rtsp://..." (OpenCV reads it; video only)."""
    text = str(source).strip()
    if text.isdigit():
        return LiveCamera(int(text), clock=clock)
    scheme = urllib.parse.urlsplit(text).scheme
    if scheme in ("http", "https"):
        return MjpegCamera(text, clock=clock)
    if scheme == "rtsp":
        camera = LiveCamera(text, clock=clock, warmup_s=0.0)
        camera.capabilities = ("rtsp",)
        return camera
    raise KozError("UNSUPPORTED_CAPABILITY", "camera must be a number, http(s):// or rtsp://")


def describe(source):
    """The camera for the terminal, without any user name or password in the address."""
    text = str(source).strip()
    if text.isdigit():
        return f"this computer's camera {text}"
    parts = urllib.parse.urlsplit(text)
    return f"{parts.scheme}://{parts.hostname}{':' + str(parts.port) if parts.port else ''}{parts.path}"

