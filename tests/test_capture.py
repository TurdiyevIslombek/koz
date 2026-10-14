"""The live camera reader, tried on the recorded test video instead of a real camera."""
import pytest

from helpers import LABELS
from koz.capture import LiveCamera
from koz.errors import KozError


def test_live_camera_hands_out_the_newest_frame_and_lets_it_age(test_video):
    with LiveCamera(str(test_video)) as camera:
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


def test_a_camera_that_cannot_open_is_refused(tmp_path):
    with pytest.raises(KozError) as caught:
        LiveCamera(str(tmp_path / "no-such-camera.avi"))
    assert caught.value.code == "UNSUPPORTED_CAPABILITY"
