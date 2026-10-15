"""Live demo: your camera -> privacy guard -> face blur -> a job, in a window.

    .venv/bin/python scripts/live_demo.py --i-own-this-camera                 # find the red object
    .venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter   # count people crossing a line
    .venv/bin/python scripts/live_demo.py --i-own-this-camera --camera http://flycar-cam.local:81/stream
    .venv/bin/python scripts/live_demo.py --i-own-this-camera --owner-workspace   # your desk / robot arena

The window shows only what Ko'z itself sees: the allowed area, with faces blurred, a ring
around the red object (or people's boxes and the counting line), plus the status line. Nothing is saved or sent anywhere.
Press q to quit. The first time, macOS asks whether this terminal may use the camera.
If the privacy guard refuses the room, the window says why and Ko'z stops."""
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
from koz.runner import Runner  # noqa: E402

WINDOW = "Ko'z live demo (q to quit)"
GREEN, AMBER, RED, WHITE = (60, 180, 75), (0, 170, 255), (60, 60, 230), (255, 255, 255)
BANNER_RED = (30, 30, 190)
FONT = cv2.FONT_HERSHEY_SIMPLEX   # OpenCV's built-in fonts are ASCII only, so no long dashes
ROOM_GUESS = {"PRIVATE_BATHROOM": "bathroom", "PRIVATE_TOILET": "toilet",
              "PRIVATE_BEDROOM": "bedroom", "PRIVATE_CHANGING_ROOM": "changing room"}


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


def count_text(count):
    return "-" if count is None else "?" if count["state"] == "unknown" else str(count["value"])


def top_places(checker, names, n=3):
    """The scene classifier's top guesses from its latest check, e.g. "office 0.41"."""
    p = checker.last_probabilities
    if p is None:
        return "scene: not checked yet"
    return "scene: " + ", ".join(f"{names[i]} {p[i]:.2f}" for i in np.argsort(p)[::-1][:n])


def draw(runner, latest, messages, fps, scene_line, line):
    width, height = runner.size
    view = runner.preview.copy() if runner.preview is not None else np.zeros((height, width, 3), np.uint8)
    for person in runner.local_results.get("person_detector", ()):
        x0, y0, x1, y1 = (int(v) for v in person.box)
        cv2.rectangle(view, (x0, y0), (x1, y1), AMBER, 2)
    if line is not None:
        a, b = (int(line[0] * width), int(line[1] * height)), (int(line[2] * width), int(line[3] * height))
        cv2.line(view, a, b, WHITE, 2)
        cv2.putText(view, "B", b, cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
    target = runner.local_results.get("color_finder")
    if target is not None and target.x is not None:
        centre = (int(target.x * width), int(target.y * height))
        radius = max(8, int((target.area_ratio * width * height / np.pi) ** 0.5))
        cv2.circle(view, centre, radius, GREEN, 3)
        cv2.putText(view, target.label, (centre[0] + radius + 6, centre[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)

    status = latest.get("status", {})
    observation = latest.get("observation", {})
    fault = latest.get("fault")
    state = status.get("state", "starting")
    colour = GREEN if state == "running" else AMBER if state == "checking" else RED
    privacy = status.get("privacy", "-")
    if runner.owner_workspace and privacy == "approved":
        privacy = "approved (owner-confirmed)"
    if line is not None:
        job = (f"people: {count_text(observation.get('occupancy'))}   in: {count_text(observation.get('entered'))}"
               f"   out: {count_text(observation.get('exited'))}")
    else:
        job = f"target: {observation.get('target', '-')}"
    lines = [f"state: {state}   privacy: {privacy}   {job}   {fps:4.1f} fps", scene_line]
    reason = fault["code"] if fault else observation.get("unknown_reason")
    if reason:
        lines.append(f"{reason}: {messages.get(reason, '')}")
    if runner.owner_workspace:
        lines.append("OWNER-CONFIRMED WORKSPACE: approved on your word unless a private room or darkness is seen")
    cv2.rectangle(view, (0, 0), (width, 28 * len(lines) + 8), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        tint = colour if i == 0 else AMBER if line.startswith("OWNER-CONFIRMED") else WHITE
        cv2.putText(view, line, (10, 24 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6 if i < 2 else 0.45, tint, 1)
    if fault:
        draw_banner(view, *stop_banner(fault["code"], messages, runner.owner_workspace))
    return view


def stop_banner(code, messages, owner_workspace):
    """What the big banner says when Ko'z stops: (title, lines)."""
    if code in ROOM_GUESS:
        room = ROOM_GUESS[code]
        if owner_workspace:
            return "STOPPED", [f"this looks like a private room ({room}?)",
                               "The workspace option never overrides a private room.",
                               "Point the camera away from it and start again."]
        hint = ("If this is your desk, use demo-desk.command and keep the bed out of view."
                if room == "bedroom" else "Private rooms always stop Ko'z.")
        return "STOPPED", [f"this room isn't allowed ({room}?)", hint]
    if code == "PRIVACY_UNCERTAIN":
        if owner_workspace:   # in a workspace only darkness makes the guard unsure
            return "STOPPED", ["too dark to check the room", "Turn on a light or uncover the lens, then start again."]
        return "STOPPED", ["Ko'z can't tell this is an allowed place",
                           "Too dark, or not a classroom, shop or office.",
                           "For your desk use demo-desk.command."]
    return "STOPPED", [messages.get(code, code), f"({code})"]


def startup_banner(code, messages, camera_problem):
    """What the banner says when Ko'z can't start at all: (title, lines)."""
    if camera_problem:
        return "CAMERA NOT ALLOWED", ["macOS didn't let this app use the camera.",
                                      "Allow Terminal in System Settings > Privacy & Security > Camera,",
                                      "then double-click the demo again."]
    return "KO'Z DID NOT START", [messages.get(code, code), f"({code})"]


def put_centred(view, text, y, scale, thickness, colour):
    """Write text centred at height y, shrinking it until it fits the width."""
    while scale > 0.3 and cv2.getTextSize(text, FONT, scale, thickness)[0][0] > view.shape[1] - 30:
        scale -= 0.05
    width = cv2.getTextSize(text, FONT, scale, thickness)[0][0]
    cv2.putText(view, text, ((view.shape[1] - width) // 2, y), FONT, scale, colour, thickness, cv2.LINE_AA)


def draw_banner(view, title, lines):
    """A full-width red band across the middle of the window."""
    height = view.shape[0]
    top = height // 2 - 70
    bottom = top + 90 + 34 * len(lines)
    cv2.rectangle(view, (0, top), (view.shape[1], bottom), BANNER_RED, -1)
    put_centred(view, title, top + 60, 1.8, 4, WHITE)
    for i, text in enumerate(lines):
        put_centred(view, text, top + 100 + 34 * i, 0.75, 2, WHITE)
    return view


def quit_pressed(wait_ms):
    """q, Esc, or the window's close button."""
    key = cv2.waitKey(wait_ms) & 0xFF
    return key in (ord("q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1


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
    parser.add_argument("--school", action="store_true", help="school mode: counts only")
    parser.add_argument("--owner-workspace", action="store_true",
                        help="confirm this room is your own workspace (desk, robot arena): the guard approves "
                             "it unless a private room or darkness is seen; shown as 'owner-confirmed'")
    parser.add_argument("--no-window", action="store_true", help="print the status instead of showing a window")
    parser.add_argument("--frames", type=int, help="stop after this many frames")
    args = parser.parse_args()

    messages = english_messages()
    left, top, right, bottom = (float(v) for v in args.allowed_area.split(","))
    setup = LocalSetup(owner_confirmed=args.i_own_this_camera,
                       allowed_area=(((left, top), (right, top), (right, bottom), (left, bottom)),),
                       school=args.school, owner_workspace=args.owner_workspace)
    line = tuple(float(v) for v in args.line.split(",")) if args.job == "counter" else None
    latest = {}

    def keep_latest(event):
        latest[event["type"]] = event["data"]

    names = [line.split()[0].split("/", 2)[2] for line in
             (ROOT / "koz" / "models" / "categories_places365.txt").read_text().splitlines()]
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

    checker = runner.scene_checker
    if runner.owner_workspace:
        print("Owner-confirmed workspace: ON (the guard approves this room unless a private room or darkness is seen)")
    frames, started, alive = 0, time.monotonic(), True
    try:
        while alive and (args.frames is None or frames < args.frames):
            alive = runner.step()
            frames += 1
            fps = frames / max(time.monotonic() - started, 1e-6)
            if args.no_window:
                continue
            cv2.imshow(WINDOW, draw(runner, latest, messages, fps, top_places(checker, names), line))
            if quit_pressed(1):
                break
        if not alive and not args.no_window:   # keep the reason on screen until q
            cv2.imshow(WINDOW, draw(runner, latest, messages, 0.0, top_places(checker, names), line))
            while not quit_pressed(100):
                pass
    finally:
        runner.camera.close()
        cv2.destroyAllWindows()
    print(top_places(checker, names))
    fault = latest.get("fault")
    print(f"final state: {runner.state}" + (f" ({fault['code']}: {messages.get(fault['code'], '')})" if fault else "")
          + ("   [owner-confirmed workspace]" if runner.owner_workspace else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
