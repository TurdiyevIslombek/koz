"""koz/brains/flybrain/brain.py fires exactly the same neurons as Islombek's original flybrain.py
(koz/brains/flybrain/original/brain/flybrain.py) for the same inputs and seed."""
import importlib.util
from pathlib import Path

import numpy as np

from koz.brains.flybrain.brain import LOCOMOTION, FlyBrain

ORIGINAL = Path(__file__).resolve().parent.parent / "koz" / "brains" / "flybrain" / "original" / "brain" / "flybrain.py"


def original_module():
    spec = importlib.util.spec_from_file_location("islombek_flybrain", ORIGINAL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eye_inputs(step):
    """Looming that comes and goes on each side, like an obstacle passing (Hz)."""
    return {"loom_L": 250.0 * max(0.0, np.sin(step / 700.0)), "loom_R": 250.0 * max(0.0, np.cos(step / 500.0))}


def test_same_spikes_as_the_original_for_the_same_input_and_seed():
    theirs = original_module().FlyBrain(LOCOMOTION, seed=0)
    ours = FlyBrain(seed=0)
    assert ours.N == theirs.N == 2282
    fired = 0
    for step in range(6000):   # 600 ms of brain time
        a, b = theirs.step(eye_inputs(step)), ours.step(eye_inputs(step))
        assert np.array_equal(a, b), f"different spikes at step {step}"
        fired += a.size
    assert fired > 1000   # the inputs really drove the circuit


def test_reset_and_run_match_too():
    theirs, ours = original_module().FlyBrain(LOCOMOTION, seed=3), FlyBrain(seed=3)
    watch = ["DNa01_L", "DNa01_R", "DNa02_L", "DNa02_R", "MDN_L", "MDN_R"]
    for brain in (theirs, ours):
        brain.run({"loom_L": 200.0}, 50, watch)
        brain.reset()
    assert theirs.run({"loom_L": 200.0, "loom_R": 50.0}, 200, watch) == ours.run({"loom_L": 200.0, "loom_R": 50.0}, 200, watch)
