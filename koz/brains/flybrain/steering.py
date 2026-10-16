"""The fly-brain block: recipe "brain": {"type": "flybrain", "settings": {"turn_gain", "deadband"}}.

Option B (Islombek's decision, Oct 16): the fly brain itself does the chasing. The fly's looming
circuit makes it turn AWAY from the eye that sees something coming (measured on Oct 16 with the
original brain_driver: looming on the left eye turns the car right, on the right eye left; nothing
seen drives straight; both eyes back it up). So Ko'z shows the brain a "threat" on the side
WITHOUT the ball:
    ball on the left   -> looming on the RIGHT eye -> the brain turns left, toward the ball
    ball on the right  -> looming on the LEFT eye  -> the brain turns right
    ball in the middle -> nothing                  -> the brain drives straight at it
    ball lost          -> a steady SEARCH_HZ on the eye opposite where it was last seen, so the brain
                          keeps turning that way (never seen: it turns left)
The farther the ball is from the middle, the stronger the looming: LOW_HZ just outside the
`deadband`, HIGH_HZ at the edge of the picture, times `turn_gain` (both tuned by the agent).
Measured response (Oct 16): below about 20 Hz the brain doesn't turn; 40 Hz curves; 60 Hz+ spins.

Only the colour finder's target feeds the brain (rule 11: never people). The wheel speeds stay on
this computer (the contract never sends them); the motors action sends them over USB."""
from dataclasses import dataclass

import numpy as np

from .driver import MAX_HZ, TICK_MS, BrainDriver

LOW_HZ = 30.0       # just above where the brain starts to turn
HIGH_HZ = 100.0     # a fast turn
SEARCH_HZ = 45.0    # a steady turn while the ball is out of sight


@dataclass(frozen=True)
class Steering:
    eyes: tuple         # (left eye Hz, right eye Hz) given to the brain
    wheels: tuple       # (left, right), -255..255; local only
    side: str           # where the ball was: left / center / right / lost


def eye_rates(x, turn_gain, deadband, last_side):
    """Ball position x (0..1, None if lost) -> (left eye Hz, right eye Hz), option B."""
    if x is None:
        return (SEARCH_HZ, 0.0) if last_side == "right" else (0.0, SEARCH_HZ)
    offset = x - 0.5
    excess = (abs(offset) - deadband) / (0.5 - deadband)
    if excess <= 0:
        return (0.0, 0.0)
    rate = float(np.clip(turn_gain * (LOW_HZ + (HIGH_HZ - LOW_HZ) * min(excess, 1.0)), 0.0, MAX_HZ))
    return (0.0, rate) if offset < 0 else (rate, 0.0)   # ball left -> right eye; ball right -> left eye


class FlyBrainSteering:
    type = "flybrain"

    def __init__(self, settings, driver=None):
        self.turn_gain, self.deadband = settings["turn_gain"], settings["deadband"]
        self.driver = driver if driver is not None else BrainDriver()
        self._last_t, self._last_side = None, None

    def process(self, ctx):
        """Needs ctx.results["color_finder"] (koz.blocks.color_finder.Target). Runs the brain for the
        real time since the last frame (10-100 ms of brain time; the first frame: 50 ms)."""
        target = ctx.results["color_finder"]
        x = target.x if target.label != "lost" else None
        ms = TICK_MS if self._last_t is None else float(np.clip((ctx.t - self._last_t) * 1000.0, 10.0, 100.0))
        self._last_t = ctx.t
        eyes = eye_rates(x, self.turn_gain, self.deadband, self._last_side)
        _, wheels = self.driver.tick(*eyes, ms=ms)
        side = "lost" if x is None else ("center" if abs(x - 0.5) <= self.deadband else ("left" if x < 0.5 else "right"))
        if side in ("left", "right"):
            self._last_side = side
        ctx.results[self.type] = Steering(eyes, wheels, side)

    def reset(self):
        """Forget everything (a new job, or after a pause: no old momentum)."""
        self.driver.reset()
        self._last_t, self._last_side = None, None
