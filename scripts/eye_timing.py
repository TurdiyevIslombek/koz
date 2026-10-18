"""Where the time goes on this Mac while the web app's eye is open (Islombek, Oct 18).

Runs the real runner (koz.server's Hub, real models, the real camera, the local eye socket) and times
each stage: camera wait, privacy guard (object check, room check), face blur, the job's detectors,
the whole frame, and the eye (JPEG encoding, frames sent, capture-to-send age). It starts the job
itself, restarts it after a privacy stop (so the eye can be measured), and prints a table.
Open the web app (npm start) at http://127.0.0.1:4173/#live while it runs: the eye only streams
while a page watches it. Must run from Terminal (camera permission). Nothing is saved or sent.

    .venv/bin/python scripts/eye_timing.py --seconds 45 --job "count people entering"
"""
import argparse
import asyncio
import json
import statistics
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz import capture, eye, privacy, runner, scene  # noqa: E402
from koz.agent.choose import make_planner  # noqa: E402
from koz.blocks import color_finder, face_blur, line_counter, person_detector  # noqa: E402
from koz.events import new_id  # noqa: E402
from koz.local_setup import LocalSetup  # noqa: E402
from koz.server import Hub, serve  # noqa: E402

TIMES = defaultdict(list)          # stage -> [seconds]
EYE_AGES = []                      # seconds from capture to the eye sending it
EYE_SENT = []                      # monotonic times the eye sent a frame
LOCK = threading.Lock()


def timed(cls, method, stage):
    original = getattr(cls, method)

    def wrapper(self, *args, **kwargs):
        start = time.perf_counter()
        try:
            return original(self, *args, **kwargs)
        finally:
            with LOCK:
                TIMES[stage].append(time.perf_counter() - start)
    setattr(cls, method, wrapper)


def instrument(hub):
    timed(capture.LiveCamera, "read", "camera: wait for a new frame")
    timed(privacy.PrivateObjects, "find", "guard: objects (NanoDet: bed, toilet, sink)")
    timed(scene.PlacesSceneChecker, "probabilities", "guard: room (Places365)")
    timed(privacy.PrivacyGate, "admit", "guard: whole step in the frame loop")
    timed(face_blur.YuNetDetector, "detect", "face blur: find faces (YuNet)")
    timed(face_blur.FaceBlur, "process", "face blur: find + pixelate")
    timed(person_detector.NanoDetPersons, "detect", "people (NanoDet)")
    timed(line_counter.LineCounter, "process", "line counter")
    timed(color_finder.ColorFinder, "process", "colour finder")
    timed(runner.Runner, "_process_next_frame", "whole frame (camera to blocks)")
    original = eye.encode

    def encode(image):
        start = time.perf_counter()
        jpeg = original(image)
        with LOCK:
            TIMES["eye: shrink + JPEG"].append(time.perf_counter() - start)
            agent = hub.agent
            if agent is not None and agent.runner is not None and agent.runner.preview_t is not None:
                EYE_AGES.append(time.monotonic() - agent.runner.preview_t)
            EYE_SENT.append(time.monotonic())
        return jpeg
    eye.encode = encode


def stats(values):
    ms = sorted(v * 1000 for v in values)
    return len(ms), statistics.mean(ms), ms[len(ms) // 2], ms[min(len(ms) - 1, int(len(ms) * 0.95))]


def main():
    parser = argparse.ArgumentParser(description="Times every stage while the web's eye is open")
    parser.add_argument("--seconds", type=float, default=45)
    parser.add_argument("--job", default="count people entering")
    parser.add_argument("--camera", default="0")
    args = parser.parse_args()
    setup = LocalSetup(owner_confirmed=True, allowed_area=(((0, 0), (1, 0), (1, 1), (0, 1)),))
    hub = Hub(setup, lambda: capture.open_camera(args.camera), make_planner("rules"), report_planner=True,
              cameras={"mac_camera": lambda: capture.open_camera(args.camera)}, report_cameras=True,
              say=lambda text: print(text, flush=True))
    instrument(hub)
    stops, running, faults = [], {"s": 0.0}, []
    hub.events.listeners.append(lambda e: faults.append(e["data"]["code"]) if e["type"] == "fault" else None)

    def start():
        hub.handle(json.dumps({"v": 1, "type": "command", "command_id": new_id(), "session_id": hub.events.session_id,
                               "job_id": new_id(), "trial_id": None, "expires_at": int(time.time()) + 10,
                               "command": "start_job", "data": {"input": "prompt", "language": "en", "text": args.job}}))

    def driver():
        time.sleep(4)          # the web app connects first
        start()
        end, last = time.monotonic() + args.seconds, time.monotonic()
        while time.monotonic() < end:
            time.sleep(0.25)
            now = time.monotonic()
            state = hub._status[0]["state"] if hub._status else None
            if state in ("evaluating", "running"):
                running["s"] += now - last
            last = now
            if not hub.busy and state in ("held", "refused", "idle"):
                stops.append(faults[-1] if faults else state)
                time.sleep(1.0)
                start()        # the guard stopped it: try again, so the eye can be measured
        report(args, stops, running["s"])
        hub.stop_local()
        loop.call_soon_threadsafe(task.cancel)

    loop = asyncio.new_event_loop()
    task = loop.create_task(serve(hub))
    threading.Thread(target=driver, daemon=True).start()
    print("eye_timing: open http://127.0.0.1:4173/#live now", flush=True)
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    return 0


def report(args, stops, running_s):
    with LOCK:
        rows = [(stage, *stats(values)) for stage, values in TIMES.items() if values]
        ages, sent = list(EYE_AGES), list(EYE_SENT)
    print(f"\nJob: {args.job!r}, {args.seconds:.0f} s, running or testing {running_s:.0f} s, restarts after a stop: {len(stops)}"
          + (f" ({', '.join(sorted(set(stops)))})" if stops else ""))
    print(f"{'stage':52} {'calls':>6} {'mean ms':>8} {'p50':>7} {'p95':>7}")
    for stage, n, mean, p50, p95 in sorted(rows, key=lambda r: -r[2] * r[1]):
        print(f"{stage:52} {n:6d} {mean:8.1f} {p50:7.1f} {p95:7.1f}")
    frames = len(TIMES.get("whole frame (camera to blocks)", []))
    print(f"\nframes processed: {frames / max(running_s, 1e-6):.1f} per second while running")
    if sent:
        span = max(sent[-1] - sent[0], 1e-6)
        gaps = sorted((b - a) * 1000 for a, b in zip(sent, sent[1:]))
        print(f"eye frames sent: {len(sent)} = {len(sent) / span:.1f} per second over the time it was open")
        if gaps:
            print(f"eye gap between frames: p50 {gaps[len(gaps) // 2]:.0f} ms, p95 {gaps[int(len(gaps) * 0.95)]:.0f} ms, max {gaps[-1]:.0f} ms")
    if ages:
        n, mean, p50, p95 = stats(ages)
        print(f"eye frame age when sent (capture -> send): p50 {p50:.0f} ms, p95 {p95:.0f} ms")
    print("", flush=True)


if __name__ == "__main__":
    sys.exit(main())
