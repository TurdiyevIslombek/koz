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


def load_demo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("live_demo", DEMO)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stop_banner_says_why_and_what_to_do():
    demo = load_demo()
    messages = demo.english_messages()
    title, lines = demo.stop_banner("PRIVATE_BEDROOM", messages, owner_workspace=False)
    assert title == "STOPPED" and "bedroom?" in lines[0] and "demo-desk.command" in lines[1]
    _, lines = demo.stop_banner("PRIVATE_BATHROOM", messages, owner_workspace=False)
    assert "bathroom?" in lines[0] and "demo-desk" not in " ".join(lines)   # never suggest a way round a bathroom
    _, lines = demo.stop_banner("PRIVATE_BEDROOM", messages, owner_workspace=True)
    assert "never overrides" in lines[1]
    _, lines = demo.stop_banner("PRIVACY_UNCERTAIN", messages, owner_workspace=True)
    assert "too dark" in lines[0]
    _, lines = demo.stop_banner("BLUR_UNAVAILABLE", messages, owner_workspace=False)
    assert lines == ["Face blur is unavailable.", "(BLUR_UNAVAILABLE)"]
    title, lines = demo.startup_banner("UNSUPPORTED_CAPABILITY", messages, camera_problem=True)
    assert title == "CAMERA NOT ALLOWED" and "Privacy & Security > Camera" in lines[1]


def test_banner_is_a_full_width_red_band():
    import numpy as np
    demo = load_demo()
    view = demo.draw_banner(np.zeros((480, 640, 3), np.uint8), "STOPPED",
                            ["this room isn't allowed (bedroom?)",
                             "If this is your desk, use demo-desk.command and keep the bed out of view."])
    middle = view[240]
    assert (middle[:, 2] > 150).mean() > 0.6           # mostly red across the whole width
    assert tuple(view[5, 5]) == (0, 0, 0)              # the top of the window is left alone


def test_launchers_keep_the_strict_and_desk_demos_apart():
    root = DEMO.parent.parent
    args = {name: next(line for line in (root / name).read_text().splitlines() if "live_demo.py" in line)
            for name in ("demo-blur.command", "demo-counter.command", "demo-desk.command",
                         "demo-desk-counter.command")}
    assert "--owner-workspace" not in args["demo-blur.command"] + args["demo-counter.command"]
    assert all("--owner-workspace" in args[n] for n in ("demo-desk.command", "demo-desk-counter.command"))
    assert "--job counter" in args["demo-desk-counter.command"] and "--job counter" not in args["demo-desk.command"]
