"""Run a colour job on the camera for a few minutes and log every stop with its reason.

    .venv/bin/python scripts/guard_watch.py --i-own-this-camera --minutes 5

The job restarts after each stop (like the planner measurement did). Each stop prints one line:
the reason and the privacy guard's last check (room guesses, objects seen). At the end, a count
of stops by reason. Nothing is saved: no frames."""
import argparse
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.agent.planner import colour_recipe  # noqa: E402
from koz.capture import open_camera  # noqa: E402
from koz.errors import KozError  # noqa: E402
from koz.events import EventLog  # noqa: E402
from koz.local_setup import LocalSetup  # noqa: E402
from koz.recipe import check_recipe  # noqa: E402
from koz.runner import Runner, print_stops  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Log every privacy-guard stop for a few minutes")
    parser.add_argument("--i-own-this-camera", action="store_true")
    parser.add_argument("--camera", default="0")
    parser.add_argument("--minutes", type=float, default=5.0)
    args = parser.parse_args()
    print_stops()
    setup = LocalSetup(owner_confirmed=args.i_own_this_camera,
                       allowed_area=(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),))
    recipe, models, reasons, frames = check_recipe(colour_recipe("red", "en")), {}, Counter(), 0
    end = time.monotonic() + args.minutes * 60
    while time.monotonic() < end:
        try:
            camera = open_camera(args.camera)
            runner = Runner(recipe, setup, camera, EventLog(lambda e: None), **models)
        except KozError as error:
            print(f"Could not start: {error.code}")
            return 1
        models = runner.models
        while time.monotonic() < end and runner.step():
            frames += runner.preview is not None
        if time.monotonic() < end:
            reasons[runner.stop_reason] += 1
            time.sleep(0.5)
        else:
            runner.stop()
    print(f"\n{args.minutes:g} minutes, {frames} processed frames. Stops by reason: {dict(reasons) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
