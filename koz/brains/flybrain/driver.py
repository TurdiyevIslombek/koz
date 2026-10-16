"""Eye firing rates -> the fly brain -> wheel speeds. A port of common/brain_driver.py from
Islombek's car (koz/brains/flybrain/original/), with the numbers of its config.py. The maths is
the same, so tests/test_flybrain_block.py requires the same wheels as the original for the same
input and seed.

In plain words, each tick:
  1. The two eye rates (Hz) are smoothed: they rise fast (40 ms) and fade slowly (200 ms).
  2. The brain runs for `ms` of brain time with those rates on its looming eye neurons.
  3. Over the last 100 ms, how often did the output neurons fire? DNa01 and DNa02 steer (right
     minus left = turn right); MDN is the "walk backwards" neuron.
  4. forward = 130 - 14 x MDN; left wheel = forward + 3 x turn, right = forward - 3 x turn;
     backwards at most 150 (the car is blind behind); the wheels follow over 120 ms.
Wheel speeds are -255..255 (car.ino's units) and stay on this computer."""
from collections import deque

import numpy as np

from .brain import FlyBrain

OUT = ["DNa01_L", "DNa01_R", "DNa02_L", "DNa02_R", "MDN_L", "MDN_R"]

# From the original config.py (and brain_driver.py's defaults where config.py has none).
TICK_MS = 50
SEED = 0
BASE = 130            # forward drive when nothing is seen
K_TURN = 3.0          # wheel units per Hz of steering difference
K_BACK = 14.0         # wheel units per Hz of moonwalker firing
WINDOW_MS = 100       # how much recent spiking is read
REVERSE_MAX = 150
EYE_RISE_MS = 40.0
EYE_FADE_MS = 200.0
WHEEL_SMOOTH_MS = 120.0
MAX_HZ = 250.0        # strongest eye input


class BrainDriver:
    def __init__(self, brain=None, seed=SEED):
        self.brain = brain if brain is not None else FlyBrain(seed=seed)
        self.member = {k: np.isin(np.arange(self.brain.N), self.brain.groups[k]) for k in OUT}
        self.size = {k: len(self.brain.groups[k]) for k in OUT}
        self.history = deque()
        self.eyes_in = (0.0, 0.0)        # what the eye neurons really received (after smoothing)
        self.wheels_s = (0.0, 0.0)       # smoothed wheel speeds

    def reset(self):
        self.brain.reset()
        self.history.clear()
        self.eyes_in = (0.0, 0.0)
        self.wheels_s = (0.0, 0.0)

    @staticmethod
    def _follow(old, new, dt_ms, tau_ms):
        return old + (new - old) * (1.0 - np.exp(-dt_ms / tau_ms))

    def _smooth_eyes(self, eye_L, eye_R, ms):
        out = []
        for old, new in zip(self.eyes_in, (eye_L, eye_R)):
            out.append(self._follow(old, new, ms, EYE_RISE_MS if new > old else EYE_FADE_MS))
        self.eyes_in = tuple(out)
        return self.eyes_in

    def tick(self, eye_L, eye_R, ms=TICK_MS):
        """Run the brain for `ms` milliseconds. Returns (hz of the output neurons, (left, right) wheels)."""
        eye_L, eye_R = self._smooth_eyes(eye_L, eye_R, ms)
        stim = {"loom_L": eye_L, "loom_R": eye_R}
        counts = {k: 0 for k in OUT}
        for _ in range(int(ms / self.brain.dt)):
            s = self.brain.step(stim)
            if s.size:
                for k in OUT:
                    counts[k] += int(self.member[k][s].sum())
        self.history.append((ms, counts))
        while sum(h[0] for h in self.history) > WINDOW_MS:
            self.history.popleft()
        win = sum(h[0] for h in self.history) / 1000.0
        hz = {k: sum(h[1][k] for h in self.history) / self.size[k] / win for k in OUT}
        turn = (hz["DNa01_R"] + hz["DNa02_R"]) - (hz["DNa01_L"] + hz["DNa02_L"])     # > 0 = turn right
        back = (hz["MDN_L"] + hz["MDN_R"]) / 2
        forward = BASE - K_BACK * back
        target = (float(np.clip(forward + K_TURN * turn, -REVERSE_MAX, 255)),
                  float(np.clip(forward - K_TURN * turn, -REVERSE_MAX, 255)))
        self.wheels_s = tuple(self._follow(o, n, ms, WHEEL_SMOOTH_MS) for o, n in zip(self.wheels_s, target))
        left, right = (int(round(w)) for w in self.wheels_s)
        return hz, (left, right)
