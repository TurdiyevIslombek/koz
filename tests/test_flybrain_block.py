"""The fly-brain block (koz/brains/flybrain/driver.py, steering.py): the same wheels as Islombek's
original brain_driver.py, option B's directions, and chasing a ball in a simple simulation.
No hardware: the brain runs on this computer; wheel speeds go nowhere."""
import importlib
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from koz.blocks.base import FrameContext
from koz.blocks.color_finder import LOST, Target
from koz.brains.flybrain.driver import BrainDriver
from koz.brains.flybrain.steering import HIGH_HZ, LOW_HZ, SEARCH_HZ, FlyBrainSteering, eye_rates

ORIGINAL = Path(__file__).resolve().parent.parent / "koz" / "brains" / "flybrain" / "original"


def original_driver_class():
    """Islombek's BrainDriver, imported from the unchanged copy (no cache files written there)."""
    saved_path, saved_flag = list(sys.path), sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ORIGINAL))
    try:
        for name in [m for m in sys.modules if m in ("config", "flybrain") or m.startswith("common")]:
            del sys.modules[name]
        return importlib.import_module("common.brain_driver").BrainDriver
    finally:
        sys.path[:], sys.dont_write_bytecode = saved_path, saved_flag


def test_same_wheels_as_the_original_driver():
    theirs, ours = original_driver_class()(), BrainDriver(seed=0)
    for step in range(60):   # 3 s: left looming, then right, then both, then nothing
        eyes = [(200.0, 0.0), (0.0, 120.0), (250.0, 250.0), (0.0, 0.0)][step // 15]
        _, hz_theirs, wheels_theirs = theirs.tick(*eyes, ms=50)
        hz_ours, wheels_ours = ours.tick(*eyes, ms=50)
        assert wheels_ours == wheels_theirs and hz_ours == hz_theirs, f"step {step}"
    assert not list(ORIGINAL.rglob("__pycache__"))   # nothing was written into the copy


# --- option B: the ball's side -> the OTHER eye --------------------------------------------------

def test_ball_on_the_left_drives_the_right_eye_and_the_other_way_round():
    assert eye_rates(0.1, 1.0, 0.1, None)[0] == 0 and eye_rates(0.1, 1.0, 0.1, None)[1] > 0
    assert eye_rates(0.9, 1.0, 0.1, None)[1] == 0 and eye_rates(0.9, 1.0, 0.1, None)[0] > 0
    assert eye_rates(0.55, 1.0, 0.1, None) == (0.0, 0.0)            # inside the deadband: straight on
    assert eye_rates(0.0, 1.0, 0.1, None) == (0.0, HIGH_HZ)          # at the edge: the strongest turn
    assert eye_rates(0.39, 1.0, 0.1, None)[1] == pytest.approx(LOW_HZ + (HIGH_HZ - LOW_HZ) * 0.01 / 0.4)
    assert eye_rates(0.0, 0.5, 0.1, None) == (0.0, HIGH_HZ / 2)      # turn_gain scales it


def test_a_lost_ball_keeps_the_brain_turning_toward_where_it_went():
    assert eye_rates(None, 1.0, 0.1, "right") == (SEARCH_HZ, 0.0)    # it went right: turn right
    assert eye_rates(None, 1.0, 0.1, "left") == (0.0, SEARCH_HZ)
    assert eye_rates(None, 1.0, 0.1, None) == (0.0, SEARCH_HZ)       # never seen: turn left


def test_the_brain_really_turns_the_way_option_b_needs():
    """Measured on the brain itself, not assumed: right-eye looming turns it left (left wheel slower)."""
    for eyes, slower in (((0.0, 60.0), "left"), ((60.0, 0.0), "right")):
        driver = BrainDriver(seed=0)
        wheels = [driver.tick(*eyes, ms=50)[1] for _ in range(30)][10:]
        left, right = np.mean(wheels, axis=0)
        assert (left < right) if slower == "left" else (right < left)


def frame(t, target):
    ctx = FrameContext(np.zeros((2, 2, 3), np.uint8), t=t)
    ctx.results["color_finder"] = target
    return ctx


def test_the_block_runs_the_brain_for_the_time_between_frames():
    block = FlyBrainSteering({"turn_gain": 1.0, "deadband": 0.1}, driver=BrainDriver(seed=0))
    steps = []
    block.driver.brain.step = (lambda real: lambda rates: steps.append(1) or real(rates))(block.driver.brain.step)
    for t in (10.0, 10.08, 10.5):   # first frame 50 ms; then 80 ms; then a 420 ms gap is capped at 100 ms
        block.process(frame(t, Target("left", 0.2, 0.5, 0.01)))
    dt = block.driver.brain.dt
    assert len(steps) == int(50 / dt) + int((10.08 - 10.0) * 1000 / dt) + int(100 / dt)
    block.reset()
    block.process(frame(99.0, LOST))   # after a reset the first frame is 50 ms again, and the side is forgotten
    assert len(steps) == int(50 / dt) + int((10.08 - 10.0) * 1000 / dt) + int(100 / dt) + int(50 / dt)
    assert block.driver.eyes_in[1] > 0 and block.driver.eyes_in[0] == 0   # never seen since reset: turn left


# --- a simple closed loop: does the brain chase the ball? -------------------------------------------

FOV = math.radians(60)   # the camera sees 60 degrees across


def chase(ball_angle_deg, seconds=5.0, seed=0, v_per_unit=0.5, turn_per_unit=0.01):
    """A car on a floor and a ball 2 m away. The brain's wheels move the car; the ball's position in
    the picture is the colour target. Assumed car: 130 wheel units = 65 cm/s, (L - R) x 0.01 rad/s.
    Returns (distance left in cm, seconds taken)."""
    block = FlyBrainSteering({"turn_gain": 1.0, "deadband": 0.1}, driver=BrainDriver(seed=seed))
    car_x = car_y = heading = 0.0
    ball_x = -200 * math.sin(math.radians(ball_angle_deg))   # + angle = to the left
    ball_y = 200 * math.cos(math.radians(ball_angle_deg))
    t, dt, distance = 0.0, 0.05, 200.0
    while t < seconds and distance > 25:
        dx, dy = ball_x - car_x, ball_y - car_y
        bearing = (math.atan2(dx, dy) - heading + math.pi) % (2 * math.pi) - math.pi   # + = to the right
        distance = math.hypot(dx, dy)
        x = 0.5 + bearing / FOV
        target = Target("center", x, 0.5, 0.01) if abs(bearing) < FOV / 2 else LOST
        ctx = frame(t, target)
        block.process(ctx)
        left, right = ctx.results["flybrain"].wheels
        heading += (left - right) * turn_per_unit * dt
        speed = (left + right) / 2 * v_per_unit
        car_x, car_y, t = car_x + speed * dt * math.sin(heading), car_y + speed * dt * math.cos(heading), t + dt
    return distance, t


@pytest.mark.parametrize("angle", [0, 25, -25, 40])
def test_in_simulation_the_brain_reaches_the_ball(angle):
    """Measured Oct 16 in this simulation: reached in about 3 s from 0, +25, -25 and +40 degrees (+40 =
    out of view on the left: the search turns left first). Not a claim about the real car."""
    distance, seconds = chase(angle)
    assert distance <= 25 and seconds < 5


def test_in_simulation_a_ball_never_seen_on_the_right_is_found_late():
    """The honest limit: never seen, the search turns left first, so a ball out of view on the right
    takes a full turn to find (Oct 16: still 101 cm away after 6 s)."""
    distance, _ = chase(-40, seconds=3.0)
    assert distance > 25
