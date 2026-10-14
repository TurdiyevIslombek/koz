"""scripts/live_demo.py runs headless on the recorded test video (no camera, no window)."""
import subprocess
import sys
from pathlib import Path

import pytest

from koz.scene import MODEL_PATH

DEMO = Path(__file__).resolve().parent.parent / "scripts" / "live_demo.py"


def run(*args):
    return subprocess.run([sys.executable, str(DEMO), *args], capture_output=True, text=True, timeout=120)


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="run scripts/fetch_models.py first")
def test_demo_runs_on_a_recorded_video(test_video):
    result = run("--i-own-this-camera", "--video", str(test_video), "--no-window", "--frames", "5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "final state:" in result.stdout


def test_demo_needs_the_ownership_confirmation(test_video):
    result = run("--video", str(test_video), "--no-window")
    assert result.returncode == 1
    assert "OWNERSHIP_REQUIRED" in result.stdout


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="run scripts/fetch_models.py first")
def test_counter_demo_runs_on_a_recorded_video(test_video):
    result = run("--i-own-this-camera", "--job", "counter", "--school", "--video", str(test_video),
                 "--no-window", "--frames", "5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "final state:" in result.stdout


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="run scripts/fetch_models.py first")
def test_demo_says_when_the_owner_workspace_is_on(test_video):
    result = run("--i-own-this-camera", "--owner-workspace", "--video", str(test_video), "--no-window", "--frames", "5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Owner-confirmed workspace: ON" in result.stdout and "[owner-confirmed workspace]" in result.stdout
