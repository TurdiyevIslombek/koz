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
def test_demo_says_when_strict_mode_is_on(test_video):
    result = run("--i-own-this-camera", "--strict", "--video", str(test_video), "--no-window", "--frames", "5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Strict mode: ON" in result.stdout and "[strict mode]" in result.stdout


def load_demo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("live_demo", DEMO)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stop_banner_is_short_by_default():
    demo = load_demo()
    messages = demo.english_messages()
    assert demo.stop_banner("PRIVATE_BATHROOM", messages, strict=False, seen="toilet") == ("STOPPED", ["a toilet is in view."])
    assert demo.stop_banner("PRIVATE_BEDROOM", messages, strict=False, seen="bed") == ("STOPPED", ["a bed is in view."])
    assert demo.stop_banner("PRIVACY_UNCERTAIN", messages, strict=False) == ("STOPPED", ["camera is covered or too dark."])
    assert demo.stop_banner("PRIVATE_BEDROOM", messages, strict=False) == ("STOPPED", ["this looks like a bedroom."])
    for code in ("PRIVATE_BATHROOM", "PRIVATE_BEDROOM", "PRIVACY_UNCERTAIN"):   # allowed places: --strict only
        assert "classroom" not in " ".join(demo.stop_banner(code, messages, strict=False)[1])
    assert demo.stop_banner("BLUR_UNAVAILABLE", messages, strict=False)[1] == ["Face blur is unavailable.", "(BLUR_UNAVAILABLE)"]


def test_stop_banner_in_strict_mode_names_the_allowed_places():
    demo = load_demo()
    messages = demo.english_messages()
    _, lines = demo.stop_banner("PRIVACY_UNCERTAIN", messages, strict=True)
    assert "strict mode" in lines[0] and "classroom, shop or office" in lines[1]
    _, lines = demo.stop_banner("PRIVATE_BEDROOM", messages, strict=True)
    assert "bedroom?" in lines[0]
    title, lines = demo.startup_banner("UNSUPPORTED_CAPABILITY", messages, camera_problem=True)
    assert title == "CAMERA NOT ALLOWED" and "Privacy & Security > Camera" in lines[1]


def test_banner_is_a_full_width_red_band():
    import numpy as np
    demo = load_demo()
    view = demo.draw_banner(np.zeros((480, 640, 3), np.uint8), "STOPPED",
                            ["this room isn't allowed (bedroom?)",
                             "a long second line to check that the text still fits the width of the window"])
    middle = view[240]
    assert (middle[:, 2] > 150).mean() > 0.6           # mostly red across the whole width
    assert tuple(view[5, 5]) == (0, 0, 0)              # the top of the window is left alone


def test_one_launcher_per_job_both_using_the_default_guard():
    root = DEMO.parent.parent
    assert sorted(p.name for p in root.glob("demo-*.command")) == ["demo-agent.command", "demo-blur.command",
                                                                    "demo-counter.command"]
    args = {name: next(line for line in (root / name).read_text().splitlines() if "live_demo.py" in line)
            for name in ("demo-blur.command", "demo-counter.command")}
    assert all("--strict" not in a and "--owner-workspace" not in a for a in args.values())
    assert "--job counter" in args["demo-counter.command"] and "--job counter" not in args["demo-blur.command"]
    assert "--school" not in args["demo-counter.command"]   # school mode is strict: it wouldn't start at home


def test_agent_launcher_asks_for_the_job_and_warns_about_names():
    text = (DEMO.parent.parent / "demo-agent.command").read_text()
    run = next(line for line in text.splitlines() if "agent_demo.py" in line)
    assert "--i-own-this-camera" in run and '"$job"' in run and "--strict" not in run
    assert "read -r" in text and "Do not type names" in text   # CLAUDE.md rule 9 (simple)


def test_start_koz_runs_runner_and_web_together_and_stops_both():
    root = DEMO.parent.parent
    launcher = root / "start-koz.command"
    text = launcher.read_text()
    assert launcher.stat().st_mode & 0o111   # double-clickable
    assert subprocess.run(["bash", "-n", str(launcher)]).returncode == 0
    runner = next(line for line in text.splitlines() if "koz.server" in line and not line.lstrip().startswith("#"))
    assert "--i-own-this-camera" in runner and "$window" in runner and "--strict" not in runner
    assert "node server/index.mjs" in text and "#setup" in text
    assert "trap 'stop; exit 0' INT TERM HUP" in text   # closing the Terminal window stops both
    assert "Do not type names" in text
