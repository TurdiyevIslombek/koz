"""A stand-in runner that puts the real Hub into one Live state, for reviewing the web app's screens
(web/review/states/shoot.mjs). Real koz code end to end (Hub, agent loop, runner, events, the local
eye), with scripted fakes for the models, planner and camera. The camera picture is DRAWN (a
doorway with two simple people, faces blurred by the real face-blur step); nothing is filmed.

    .venv/bin/python scripts/ui_states.py running        # then open the local web app (npm start)

States: idle, planning, testing, running, confirming, privacy, stopped, camera_lost, refused, car.
The web starts the job itself (Setup), so its Try again and Stop work as for a real job."""
import argparse
import asyncio
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.actions.motors import MockMotorLink  # noqa: E402
from koz.agent import FakePlanner  # noqa: E402
from koz.blocks import Person  # noqa: E402
from koz.capture import Frame  # noqa: E402
from koz.local_setup import LocalSetup  # noqa: E402
from koz.privacy import PrivacyResult  # noqa: E402
from koz.server import Hub, serve  # noqa: E402

STATES = ("idle", "planning", "testing", "running", "confirming", "privacy", "stopped", "camera_lost", "refused", "car")
SWITCH_S = 4.0   # confirming / privacy / camera_lost begin this long after the first frame


class Scene:
    """Where the two drawn people are now (both fakes read it, so blur and counting match the picture)."""

    def __init__(self, ball=False):
        self.t0, self.ball = time.monotonic(), ball

    def people(self, width, height):
        phase = ((time.monotonic() - self.t0) % 4.0) / 4.0           # one walker every 4 s, right to left
        walker_x = width * (0.85 - 0.7 * phase)
        return [(width * 0.2, height * 0.62), (walker_x, height * 0.6)]

    def draw(self, width=640, height=480):
        image = np.zeros((height, width, 3), np.uint8)
        image[:] = (176, 192, 200)                                   # warm wall
        cv2.rectangle(image, (0, int(height * 0.74)), (width, height), (120, 136, 150), -1)   # floor
        cv2.rectangle(image, (int(width * 0.36), int(height * 0.12)), (int(width * 0.64), int(height * 0.74)),
                      (92, 110, 128), -1)                            # the doorway
        for i in range(8):                                           # some texture, so it reads as a room
            x = int(width * (0.05 + i * 0.12))
            cv2.line(image, (x, int(height * 0.74)), (int(width / 2 + (x - width / 2) * 1.6), height), (110, 126, 140), 2)
        if self.ball:
            cv2.circle(image, (int(width * 0.42), int(height * 0.8)), int(height * 0.07), (40, 40, 210), -1)
        else:
            for x, y in self.people(width, height):
                cv2.ellipse(image, (int(x), int(y)), (int(width * 0.05), int(height * 0.17)), 0, 0, 360, (70, 82, 96), -1)
                cv2.circle(image, (int(x), int(y - height * 0.22)), int(height * 0.055), (150, 175, 205), -1)   # a face
                cv2.circle(image, (int(x - 6), int(y - height * 0.23)), 4, (40, 40, 40), -1)
                cv2.circle(image, (int(x + 6), int(y - height * 0.23)), 4, (40, 40, 40), -1)
        return image


class DrawnCamera:
    """15 frames a second of the drawn scene; with `stall_after`, frames stop being fresh (camera lost)."""
    capabilities = ()

    def __init__(self, scene, stall_after=None):
        self.scene, self.stall_after, self.index, self.is_open, self.first = scene, stall_after, 0, True, None

    def read(self):
        if not self.is_open:
            return None
        time.sleep(1 / 15)
        now = time.monotonic()
        self.first = self.first or now
        self.index += 1
        stalled = self.stall_after is not None and now - self.first > self.stall_after
        return Frame(self.scene.draw(), self.first + self.stall_after - 1 if stalled else now, self.index)

    def close(self):
        self.is_open = False


class Faces:
    def __init__(self, scene):
        self.scene = scene

    def detect(self, image):
        h, w = image.shape[:2]
        return [] if self.scene.ball else [(int(x - w * 0.06), int(y - h * 0.3), int(w * 0.12), int(h * 0.16))
                                           for x, y in self.scene.people(w, h)]


class People:
    def __init__(self, scene):
        self.scene = scene

    def detect(self, image, min_confidence):
        h, w = image.shape[:2]
        return [Person((x - w * 0.06, y - h * 0.3, x + w * 0.06, y + h * 0.2), 0.9) for x, y in self.scene.people(w, h)]


class Guard:
    """Approves; for `confirming` / `privacy`, SWITCH_S after the first check it sees a bed."""

    def __init__(self, mode):
        self.mode, self.t0 = mode, None

    def check(self, image):
        self.t0 = self.t0 or time.monotonic()
        late = time.monotonic() - self.t0 > SWITCH_S
        if late and self.mode == "privacy":
            return PrivacyResult("blocked", "PRIVATE_BEDROOM", "bed")
        if late and self.mode == "confirming":
            return PrivacyResult("unknown", "PRIVACY_UNCERTAIN", "bed", confirming=True)
        return PrivacyResult("approved")


class SlowPlanner(FakePlanner):
    name = "rules"

    def plan(self, text):
        time.sleep(3600)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("state", choices=STATES)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--cameras", default="mac_camera", help="camera slots to offer, comma-separated (all show the drawing)")
    args = parser.parse_args()
    scene = Scene(ball=args.state == "car")
    setup = LocalSetup(owner_confirmed=True, allowed_area=(((0, 0), (1, 0), (1, 1), (0, 1)),),
                       mount="moving" if args.state == "car" else "fixed", motor_cap=0.15)
    camera = lambda: DrawnCamera(scene, stall_after=SWITCH_S if args.state == "camera_lost" else None)   # noqa: E731
    hub = Hub(setup, camera, SlowPlanner() if args.state == "planning" else FakePlanner(),
              eval_seconds=3600 if args.state == "testing" else 3, report_planner=True,
              models={"scene_checker": Guard(args.state), "face_detector": Faces(scene), "person_detector": People(scene)},
              motor_link=MockMotorLink(armed=True) if args.state == "car" else None,
              cameras={slot: camera for slot in args.cameras.split(",")}, report_cameras=True)
    print(f"ui_states: {args.state} on ws://127.0.0.1:{args.port}", flush=True)
    try:
        asyncio.run(serve(hub, port=args.port))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
