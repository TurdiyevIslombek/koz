"""The README's public clip runs through real models and the CLI, with no camera or keys."""
import subprocess
import sys
from pathlib import Path

import cv2
import pytest

from koz.scene import MODEL_PATH

ROOT = Path(__file__).resolve().parent.parent
CLIP = ROOT / "samples" / "orange-red-ball.mp4"


def run(video):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "agent_demo.py"),
         "--i-own-this-camera", "--planner", "rules", "--video", str(video),
         "--no-window", "--seconds", "1", "find the red ball"],
        cwd=ROOT, capture_output=True, text=True, timeout=90)


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="run scripts/fetch_models.py first")
def test_public_clip_really_plans_tests_adjusts_and_runs():
    assert CLIP.stat().st_size < 2_000_000
    result = run(CLIP)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    stages = ["Plan (en):", "target_visible fail", "-> adjust: color_finder.hue_center 0 ->",
              "target_visible pass", "-> run", "status    running (revision 2)", "Adjusted:"]
    positions = [output.index(stage) for stage in stages]
    assert positions == sorted(positions), output
    assert "privacy approved" in output and ", pass)" in output


@pytest.mark.parametrize("corrupt", [False, True])
def test_cli_explains_a_missing_or_corrupt_video(tmp_path, corrupt):
    path = tmp_path / "clip.mp4"
    if corrupt:
        path.write_bytes(b"not a video")
    result = run(path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "VIDEO_UNREADABLE: video file not found or unreadable" in result.stdout
    assert "UNSUPPORTED_CAPABILITY" not in result.stdout


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="run scripts/fetch_models.py first")
def test_cli_does_not_report_success_if_video_ends_before_the_check_passes(tmp_path):
    clip = tmp_path / "too-short.mp4"
    source = cv2.VideoCapture(str(CLIP))
    writer = cv2.VideoWriter(str(clip), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    assert writer.isOpened()
    try:
        for _ in range(10):
            ok, frame = source.read()
            assert ok
            writer.write(frame)
    finally:
        source.release()
        writer.release()
    result = run(clip)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "CHECK_FAILED" in result.stdout
