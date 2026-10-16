"""Live demo: your camera -> privacy guard -> face blur -> a job, in a window.

    .venv/bin/python scripts/live_demo.py --i-own-this-camera                 # find the red object
    .venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter   # count people crossing a line
    .venv/bin/python scripts/live_demo.py --i-own-this-camera --camera http://flycar-cam.local:81/stream
    .venv/bin/python scripts/live_demo.py --i-own-this-camera --strict   # schools, public cameras: listed places only

The window shows only what Ko'z itself sees: the allowed area, with faces blurred, a ring
around the red object (or people's boxes and the counting line), plus the status line. Nothing is saved or sent anywhere.
Press q to quit. The first time, macOS asks whether this terminal may use the camera.
By default Ko'z runs anywhere and stops on what the privacy guard sees (a bed, a toilet, a
covered lens...); the window says why. --strict is for schools and public cameras."""
import argparse
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz import CONTRACTS  # noqa: E402
from koz.capture import FileCamera, LiveCamera  # noqa: E402
from koz.errors import KozError  # noqa: E402
from koz.events import EventLog  # noqa: E402
from koz.local_setup import LocalSetup  # noqa: E402
from koz.recipe import check_recipe  # noqa: E402
from koz.runner import Runner, print_stops  # noqa: E402
from koz.preview import (WINDOW, check_line, count_text, draw, draw_banner, put_centred,  # noqa: E402,F401
                         quit_pressed, startup_banner, stop_banner)


def english_messages():
    """The fixed English message for each error code, read from the contract table."""
    table = (CONTRACTS / "events.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| `([A-Z_]+)` \| [^|]* \| [^|]* \| ([^|]*) \|", table, re.M)
    return {code: text.strip() for code, text in rows}


def demo_recipe(job, hue, line, school):
    if job == "counter":
        blocks = [{"type": "person_detector", "settings": {"min_confidence": 0.5}},
                  {"type": "line_counter", "settings": {"line": [list(line[:2]), list(line[2:])]}}]
    else:
        blocks = [{"type": "color_finder", "settings": {"hue_center": hue, "hue_half_width": 10,
                                                        "saturation_min": 120, "value_min": 70,
                                                        "min_area_ratio": 0.002}}]
    return check_recipe({
        "version": 1, "language": "en",
        "camera": {"source": "device_camera", "size": "640x480", "fps": 15},
        "blocks": [{"type": "privacy_guard", "settings": {}}, {"type": "face_blur", "settings": {}}] + blocks,
        "brain": {"type": "none"}, "actions": [{"type": "dashboard"}], "privacy": {"school": school}})


def main():
    parser = argparse.ArgumentParser(description="Ko'z live demo")
    parser.add_argument("--i-own-this-camera", action="store_true",
                        help="confirm the camera is yours and you may film this view (rule 7)")
    parser.add_argument("--camera", default="0", help="0 = this computer's camera, or a stream URL")
    parser.add_argument("--video", help="play a recorded video file instead of a camera")
    parser.add_argument("--allowed-area", default="0,0,1,1",
                        help="left,top,right,bottom of the allowed area, 0..1 (default: whole frame)")
    parser.add_argument("--job", choices=("color", "counter"), default="color",
                        help="color: find the red object; counter: count people crossing --line")
    parser.add_argument("--hue", type=int, default=0, help="colour to find, OpenCV hue 0..179 (0 = red)")
    parser.add_argument("--line", default="0.5,0,0.5,1",
                        help="counting line ax,ay,bx,by, 0..1; crossing right-to-left of A->B counts as 'in'")
    parser.add_argument("--school", action="store_true", help="school mode: counts only, and always --strict")
    parser.add_argument("--strict", action="store_true",
                        help="strict mode for schools and public cameras: run only in listed public places "
                             "(classroom, shop, office...). Default: run anywhere, stop on what the guard sees")
    parser.add_argument("--no-window", action="store_true", help="print the status instead of showing a window")
    parser.add_argument("--frames", type=int, help="stop after this many frames")
    args = parser.parse_args()
    print_stops()   # every stop says why, with the last privacy check

    messages = english_messages()
    left, top, right, bottom = (float(v) for v in args.allowed_area.split(","))
    setup = LocalSetup(owner_confirmed=args.i_own_this_camera,
                       allowed_area=(((left, top), (right, top), (right, bottom), (left, bottom)),),
                       school=args.school, strict=args.strict)
    line = tuple(float(v) for v in args.line.split(",")) if args.job == "counter" else None
    latest = {}

    def keep_latest(event):
        latest[event["type"]] = event["data"]

    camera = None
    try:
        setup.check()
        if args.video:
            camera = FileCamera(args.video)
        else:
            camera = LiveCamera(int(args.camera) if args.camera.isdigit() else args.camera)
        runner = Runner(demo_recipe(args.job, args.hue, line, args.school), setup, camera, EventLog(keep_latest))
    except KozError as error:
        print(f"Ko'z did not start: {error.code}: {messages.get(error.code, '')}")
        camera_problem = camera is None and not args.video and args.camera.isdigit() \
            and error.code == "UNSUPPORTED_CAPABILITY"
        if camera_problem:
            print("The camera could not be opened. On a Mac this usually means the app that started\n"
                  "this command may not use the camera. Double-click demo-blur.command (it runs in\n"
                  "Terminal, which asks for permission), or allow the app in System Settings >\n"
                  "Privacy & Security > Camera, then try again.")
        if camera is not None:
            camera.close()
        if not args.no_window:   # show it big too, until q
            cv2.imshow(WINDOW, draw_banner(np.zeros((480, 640, 3), np.uint8),
                                           *startup_banner(error.code, messages, camera_problem)))
            while not quit_pressed(100):
                pass
            cv2.destroyAllWindows()
        return 1

    if runner.strict:
        print("Strict mode: ON (runs only in listed public places: classroom, shop, office...)")
    frames, started, alive, printed = 0, time.monotonic(), True, 0
    try:
        while alive and (args.frames is None or frames < args.frames):
            alive = runner.step()
            frames += 1
            if getattr(runner.guard, "checks", 0) != printed:   # one terminal line per privacy check
                printed = runner.guard.checks
                print(check_line(runner))
            fps = frames / max(time.monotonic() - started, 1e-6)
            if args.no_window:
                continue
            cv2.imshow(WINDOW, draw(runner, latest, messages, fps, line))
            if quit_pressed(1):
                break
        if not alive and not args.no_window:   # keep the reason on screen until q
            cv2.imshow(WINDOW, draw(runner, latest, messages, 0.0, line))
            while not quit_pressed(100):
                pass
    finally:
        runner.camera.close()
        cv2.destroyAllWindows()
    fault = latest.get("fault")
    print(f"final state: {runner.state}" + (f" ({fault['code']}: {messages.get(fault['code'], '')})" if fault else "")
          + ("   [strict mode]" if runner.strict else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
