"""Video sources (CLAUDE.md rule 8).

Video only: nothing here asks OpenCV for an audio stream, and nothing writes frames
to disk. A frame lives in memory until the runner is done with it."""
import time
from dataclasses import dataclass

import cv2
import numpy as np

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
    (Ko'z never records), and a recipe can never choose the path."""
    capabilities = ("recorded_fixture",)

    def __init__(self, path, clock=time.monotonic):
        self._clock = clock
        self._cap = cv2.VideoCapture(str(path))
        if not self._cap.isOpened():
            raise KozError("UNSUPPORTED_CAPABILITY", "video file cannot be opened")
        self._index = 0
        self.is_open = True

    def read(self):
        """The next frame, or None when the recording has ended."""
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
