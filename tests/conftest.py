import pytest

from helpers import record_test_video


@pytest.fixture(scope="session")
def test_video(tmp_path_factory):
    """The recorded test video, written once per test run into a temporary folder."""
    return record_test_video(tmp_path_factory.mktemp("video") / "red_ball.avi")
