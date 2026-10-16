"""Agent demo: type a camera job in plain words; Ko'z plans it, tries it, checks it, adjusts it, runs it.

    .venv/bin/python scripts/agent_demo.py --i-own-this-camera "find the red ball"
    .venv/bin/python scripts/agent_demo.py --i-own-this-camera "Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir"
    .venv/bin/python scripts/agent_demo.py --i-own-this-camera "Найди красный мяч" --video clip.mp4 --no-window

The terminal shows the plan (in the job's language) and then every event as one line:
observation -> decision -> new setting -> result. The window shows what Ko'z sees (faces
blurred) while it tries each revision and then runs. Nothing is saved or sent anywhere;
with NEBIUS_API_KEY in .env only the sentence goes to Nemotron on Nebius. Press q to quit."""
import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.agent import Agent, ChainLog, make_planner  # noqa: E402
from koz.agent.choose import CHOICES, planned_by  # noqa: E402
from koz.capture import FileCamera, LiveCamera  # noqa: E402
from koz.errors import KozError  # noqa: E402
from koz.events import EventLog  # noqa: E402
from koz.local_setup import LocalSetup  # noqa: E402
from koz.messages import all_messages, message  # noqa: E402
from koz.preview import WINDOW, draw, draw_banner, quit_pressed, startup_banner  # noqa: E402
from koz.runner import print_stops  # noqa: E402


def counting_line(recipe):
    block = next((b for b in recipe["blocks"] if b["type"] == "line_counter"), None) if recipe else None
    return None if block is None else tuple(block["settings"]["line"][0] + block["settings"]["line"][1])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ko'z agent demo")
    parser.add_argument("job", help='the camera job in plain words, e.g. "find the red ball"')
    parser.add_argument("--i-own-this-camera", action="store_true",
                        help="confirm the camera is yours and you may film this view (rule 7)")
    parser.add_argument("--camera", default="0", help="0 = this computer's camera, or a stream URL")
    parser.add_argument("--video", help="play a recorded video file instead of a camera")
    parser.add_argument("--planner", choices=CHOICES, default="auto",
                        help="auto: Nemotron on Nebius if NEBIUS_API_KEY is in .env, else the rule planner; "
                             "ollama: Gemma 4 on this Mac (14/20 on Oct 15, see docs/TRIALS.md)")
    parser.add_argument("--strict", action="store_true", help="strict mode for schools and public cameras")
    parser.add_argument("--seconds", type=float, help="stop this many seconds after the job starts running")
    parser.add_argument("--no-window", action="store_true", help="terminal only")
    args = parser.parse_args(argv)
    print_stops()   # every stop says why, with the last privacy check

    planner = make_planner(args.planner)
    setup = LocalSetup(owner_confirmed=args.i_own_this_camera,
                       allowed_area=(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),), strict=args.strict)
    messages = all_messages("en")
    latest, shown = {}, {"line": None}
    chain = ChainLog()

    def on_event(event):
        latest[event["type"]] = event["data"]
        if event["type"] == "recipe":
            shown["line"] = counting_line(event["data"]["recipe"])
        text = chain(event)
        if text:
            print(text, flush=True)

    events = EventLog(lambda event: None)
    events.listeners.append(on_event)
    clock = {"start": time.monotonic(), "frames": 0}

    def on_frame(runner):
        clock["frames"] += 1
        if args.no_window:
            return
        fps = clock["frames"] / max(time.monotonic() - clock["start"], 1e-6)
        cv2.imshow(WINDOW, draw(runner, latest, messages, fps, shown["line"]))
        if quit_pressed(1):
            agent.stop_requested = True

    def open_camera():
        if args.video:
            return FileCamera(args.video, realtime=True)
        return LiveCamera(int(args.camera) if args.camera.isdigit() else args.camera)

    def on_plan(plan):
        chain.language = plan.language
        print(f"Plan by {planned_by(plan, planner)}.")
        print(f"\nPlan ({plan.language}): {plan.message}\n", flush=True)

    print(f"Planners, in order: {planner.name}")
    agent = Agent(planner, setup, open_camera, events, on_frame=on_frame, on_plan=on_plan)
    try:
        result = agent.run(args.job)
    except KozError as error:
        print(f"Ko'z did not start: {error.code}: {messages.get(error.code, '')}")
        return 1
    plan = result.plan

    if result.state == "running":
        print("The check passed: running. Press q in the window (or Ctrl+C) to stop.")
        runner, since = result.runner, time.monotonic()
        try:
            while not agent.stop_requested and runner.step():
                on_frame(runner)
                if args.seconds is not None and time.monotonic() - since >= args.seconds:
                    break
        except KeyboardInterrupt:
            pass
        runner.stop()
        fault = latest.get("fault") if runner.state == "held" else None
        print(f"\nResult: the job ran, then {runner.state}"
              + (f" ({fault['code']}): {message(fault['code'], plan.language)}" if fault else "."))
    else:
        code = result.code
        passed = bool(result.decisions) and result.decisions[-1]["next"] == "run"
        why = message(code, plan.language if plan else "en") if code else \
            "the check passed; the recording ended" if passed else "stopped"
        print(f"\nResult: {result.state}" + (f" ({code})" if code else "") + f": {why}")
        if not args.no_window and code and result.state != "refused":
            view = np.zeros((480, 640, 3), np.uint8)
            cv2.imshow(WINDOW, draw_banner(view, *startup_banner(code, messages, False)))
            while not quit_pressed(100):
                pass
    for change in result.agent_changes:
        c = change["change"]
        print(f"Adjusted: {c['setting']} {c['before']} -> {c['after']} "
              f"({change['check']}: {change['before_label']} -> {change['after_label']}, {change['after_result']})")
    if not args.no_window:
        cv2.destroyAllWindows()
    return 0 if result.state in ("running", "idle") else 2


if __name__ == "__main__":
    sys.exit(main())
