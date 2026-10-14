"""The recipe runner (contracts/events.md section 3).

For every frame, always in this order:
  capture -> allowed-area mask -> privacy guard -> face blur -> the recipe's other blocks -> actions
Only frames the privacy guard APPROVED reach face blur and the other blocks.
When something can't be trusted (frame too old, processing too slow), outputs say
"unknown", never 0 or an old value. When privacy or blur fails, or anything
unexpected goes wrong, the job stops.

Built so far: the gate, face blur, color_finder, and the dashboard action (= the
observation events). The fly brain, motors and the other blocks come later; recipes
that need them are refused in koz.recipe with UNSUPPORTED_CAPABILITY."""
import time

import cv2

from . import policy
from .blocks import TASK_BLOCKS, FaceBlur, FrameContext
from .errors import KozError
from .privacy import APPROVED, UNKNOWN, NoSceneModel, PrivacyGate
from .recipe import CheckedRecipe, check_recipe

OPENCV_MAJOR = int(cv2.__version__.split(".")[0])


class Runner:
    """Runs one checked recipe on one camera and sends events to `events` (a koz.events.EventLog).

    `scene_checker` and `face_detector` are only replaced in tests. By default the
    privacy guard never approves (the scene classifier isn't built yet) and face blur
    uses the pinned YuNet model."""

    def __init__(self, recipe, setup, camera, events, scene_checker=None, face_detector=None,
                 revision=1, clock=time.monotonic):
        if not isinstance(recipe, CheckedRecipe):
            raise TypeError("Runner needs a CheckedRecipe from koz.recipe")
        if OPENCV_MAJOR != 5:
            raise KozError("UNSUPPORTED_CAPABILITY", "Ko'z needs OpenCV 5")
        setup.check()
        # Check again here: a CheckedRecipe's dict could have been changed since it was
        # checked, and the local school setting must apply too.
        recipe = check_recipe(recipe.data, local_school=setup.school)
        self.recipe, self.camera, self.events = recipe, camera, events
        self.revision, self._clock = revision, clock
        width, height = (int(n) for n in recipe.data["camera"]["size"].split("x"))
        self.size = (width, height)
        self._mask = setup.mask(width, height)
        self._gate = PrivacyGate(scene_checker if scene_checker is not None else NoSceneModel(), clock)
        self._blur = FaceBlur({}, detector=face_detector)
        self._blocks = [TASK_BLOCKS[b["type"]](b["settings"]) for b in recipe.data["blocks"][2:]]
        self._has_target = any(b["type"] == "color_finder" for b in recipe.data["blocks"])

        self.state = None           # set to "checking" on the first step
        self.coverage = "complete"  # becomes "gapped" after any stale or slow frame, and stays so
        self.preview = None         # the latest fresh, masked, blurred frame, for a local window only
        self._was_running = False
        self._last_target = None
        self._last_observation_t = None
        self._last_status_t = None

    def run(self, max_frames=None):
        """Process frames until the job stops (or max_frames). Returns the final state."""
        done = 0
        while (max_frames is None or done < max_frames) and self.step():
            done += 1
        return self.state

    def step(self):
        """Process one frame. Returns False once the job has stopped."""
        if self.state is None:
            self._set_state("checking")
        if self.state not in ("checking", "running"):
            return False
        try:
            return self._process_next_frame()
        except Exception as error:   # fail closed: anything unexpected stops the job
            code = error.code if isinstance(error, KozError) else "INTERNAL_ERROR"
            try:
                self._fault(code)
            except Exception:        # even reporting failed: still stop
                self.preview = None
                self.camera.close()
                self.state = "held" if self._was_running else "refused"
            return False

    def _process_next_frame(self):
        frame = self.camera.read()
        if frame is None:   # the recording ended
            self._stop("idle")
            return False
        if self._clock() - frame.t > policy.MAX_FRAME_AGE_S:   # FRAME_STALE
            self._unknown()
            return True

        image = cv2.resize(frame.image, self.size, interpolation=cv2.INTER_AREA)
        image = cv2.bitwise_and(image, image, mask=self._mask)   # black outside the allowed area
        if self._gate.due():
            self.preview = None
            self._set_state("checking")
        privacy = self._gate.admit(image)
        if privacy.state != APPROVED:
            self._fault(privacy.code, privacy.state)
            return False
        if self.state == "checking":
            self._was_running = True
            self._set_state("running")

        ctx = FrameContext(image)
        self._blur.process(ctx)   # raises BLUR_UNAVAILABLE if it can't blur
        for block in self._blocks:
            block.process(ctx)
        if self._clock() - frame.t > policy.MAX_FRAME_AGE_S:   # OVERLOADED: processing took too long
            self._unknown()
            return True
        self.preview = ctx.image
        target = ctx.results["color_finder"].label if self._has_target else None
        self._observe(APPROVED, target)
        self._heartbeat()
        return True

    # --- events -------------------------------------------------------------

    def _unknown(self):
        """A frame we can't trust: outputs become unknown and coverage has a gap.
        The target label has no field for the reason; Count outputs (later) will carry it."""
        self.coverage = "gapped"
        self.preview = None
        self._observe(self._privacy_state(), "unknown" if self._has_target else None)
        self._heartbeat()

    def _observe(self, privacy, target):
        """At most one observation per second, except at once when an output turns unknown."""
        now = self._clock()
        turned_unknown = target == "unknown" and self._last_target != "unknown"
        due = self._last_observation_t is None or now - self._last_observation_t >= policy.OBSERVATION_INTERVAL_S
        self._last_target = target
        if not (due or turned_unknown):
            return
        self._last_observation_t = now
        self.events.emit("observation", {
            "round": None,   # set by the agent loop during evaluation rounds (next task)
            "privacy": privacy, "occupancy": None, "entered": None, "exited": None,
            "coverage": self.coverage, "target": target, "motion": None, "looming": None, "alert": None,
        }, revision=self.revision)

    def _fault(self, code, privacy=None):
        """Stop the job. Outputs become unknown first. "off" if it never ran, "held" if it was running."""
        self.preview = None
        self._observe(privacy or self._privacy_state(), "unknown" if self._has_target else None)
        self.events.emit("fault", {"code": code, "effect": "held" if self._was_running else "off"},
                         revision=self.revision)
        self._stop("held" if self._was_running else "refused")

    def _stop(self, state):
        self.camera.close()
        self.preview = None
        self._set_state(state)

    def _privacy_state(self):
        return self._gate.last.state if self._gate.last else UNKNOWN

    def _set_state(self, state):
        if state != self.state:
            self.state = state
            self._emit_status()

    def _heartbeat(self):
        if self._clock() - self._last_status_t >= policy.STATUS_INTERVAL_S:
            self._emit_status()

    def _emit_status(self):
        self._last_status_t = self._clock()
        self.events.emit("status", {
            "state": self.state,
            "camera_on": bool(getattr(self.camera, "is_open", False)),
            "privacy": self._privacy_state(),
            "school": self.recipe.school,
            "motor": "not_present",
            "opencv_major": OPENCV_MAJOR,
            "capabilities": sorted(getattr(self.camera, "capabilities", ())),
        }, revision=self.revision)
