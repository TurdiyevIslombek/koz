"""Video sources (CLAUDE.md rule 8).

Video only: nothing here asks OpenCV for an audio stream, and nothing writes frames
to disk. A frame lives in memory until the runner is done with it."""
import threading
import time
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
