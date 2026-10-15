"""The recipe runner (contracts/events.md section 3).

For every frame, always in this order:
  capture -> allowed-area mask -> privacy guard -> face blur -> the recipe's other blocks -> actions
Only frames the privacy guard APPROVED reach face blur and the other blocks.
When something can't be trusted (frame too old, processing too slow), outputs say
"unknown", never 0 or an old value. When privacy or blur fails, or anything
unexpected goes wrong, the job stops.

Built so far: the privacy guard, face blur, color_finder, person_detector,
line_counter, and the dashboard action (= the observation events). The fly brain, motors and the other blocks come later; recipes
that need them are refused in koz.recipe with UNSUPPORTED_CAPABILITY."""
import time

import cv2

from . import policy
from .blocks import TASK_BLOCKS, FaceBlur, FrameContext, PersonDetector
from .errors import KozError
from .events import count_known, count_unknown
from .privacy import APPROVED, UNKNOWN, GuardCheck, PrivacyGate, PrivateObjects
from .recipe import CheckedRecipe, check_recipe
from .scene import PlacesSceneChecker

OPENCV_MAJOR = int(cv2.__version__.split(".")[0])


class Runner:
    """Runs one checked recipe on one camera and sends events to `events` (a koz.events.EventLog).

    `scene_checker` (the privacy guard's check), `face_detector` and `person_detector` are
    only replaced in tests. By default the guard is koz.privacy.GuardCheck (Places365 room
    check + NanoDet object check), face blur uses YuNet and person_detector NanoDet; if a
    needed model file is missing or changed, the runner refuses to start."""

    def __init__(self, recipe, setup, camera, events, scene_checker=None, face_detector=None,
                 person_detector=None, revision=1, evaluation_round=None, clock=time.monotonic):
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
        # Set by the agent loop while it tries this revision (rounds 1-3): status says
        # "evaluating" instead of "running", and observations carry the round number.
        self.evaluation_round = evaluation_round
        width, height = (int(n) for n in recipe.data["camera"]["size"].split("x"))
        self.size = (width, height)
        self._mask = setup.mask(width, height)
        self.strict = setup.strict or recipe.school   # school mode is always strict (rule 6)
        self.guard = (scene_checker if scene_checker is not None
                      else GuardCheck(PlacesSceneChecker(), PrivateObjects(), self.strict, clock=clock,
                                      watch_changes=setup.mount == "fixed"))
        self._gate = PrivacyGate(self.guard, clock)
        self._blur = FaceBlur({}, detector=face_detector)
        self._blocks = [PersonDetector(b["settings"], detector=person_detector) if b["type"] == "person_detector"
                        else TASK_BLOCKS[b["type"]](b["settings"]) for b in recipe.data["blocks"][2:]]
        self._configured = {b["type"] for b in recipe.data["blocks"][2:]}
        self._settings = {b["type"]: b["settings"] for b in recipe.data["blocks"][2:]}

        self.state = None           # set to "checking" on the first step
        self.coverage = "complete"  # becomes "gapped" after any stale or slow frame, and stays so
        self.preview = None         # the latest fresh, masked, blurred frame, for a local window only
        self.local_results = {}     # that frame's block results (e.g. where the target is); local only
        self._was_running = False
        self._last_reason_sent = None
        self._last_observation_t = None
        self._last_status_t = None

    def finish_evaluation(self):
        """The agent accepted this revision: keep running it as the job itself. A new phase
        (contract 8.3): the line counts start again at 0 and coverage at "complete"."""
        self.evaluation_round = None
        self._blocks = [TASK_BLOCKS[b.type](self._settings[b.type]) if b.type == "line_counter" else b
                        for b in self._blocks]
        self.coverage = "complete"
        self._last_observation_t = None   # the first normal-running observation goes out at once
        if self.state == "evaluating":
            self._set_state("running")

    def stop(self):
        """Stop on the owner's command (stop_job): close the camera, status idle."""
        if self.state in ("checking", "evaluating", "running"):
            self._stop("idle")

    def hold(self, code):
        """The agent loop decided to stop (its decision event carries the same code): outputs
        stop, a fault says why, the camera closes, status held; a new start is needed."""
        if self.state in ("checking", "evaluating", "running"):
            self._drop_preview()
            self.events.emit("fault", {"code": code, "effect": "held"}, revision=self.revision)
            self._stop("held")

    @property
    def models(self):
        """The loaded checks and models, so the agent's next round reuses them (same camera,
        same setup) instead of loading the files again."""
        people = next((b.detector for b in self._blocks if isinstance(b, PersonDetector)), None)
        return {"scene_checker": self.guard, "face_detector": self._blur.detector, "person_detector": people}

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
        if self.state not in ("checking", "evaluating", "running"):
            return False
        try:
            return self._process_next_frame()
        except Exception as error:   # fail closed: anything unexpected stops the job
            code = error.code if isinstance(error, KozError) else "INTERNAL_ERROR"
            try:
                self._fault(code)
            except Exception:        # even reporting failed: still stop
                self._drop_preview()
                self.camera.close()
                self.state = "held" if self._was_running else "refused"
            return False

    def _process_next_frame(self):
        frame = self.camera.read()
        if frame is None:   # the recording ended
            self._stop("idle")
            return False
        if self._clock() - frame.t > policy.MAX_FRAME_AGE_S:
            self._unknown("FRAME_STALE")
            return True

        image = cv2.resize(frame.image, self.size, interpolation=cv2.INTER_AREA)
        image = cv2.bitwise_and(image, image, mask=self._mask)   # black outside the allowed area
        if self._gate.due(image):
            self._drop_preview()   # nothing from before this check stays on screen
        privacy = self._gate.admit(image)
        if privacy.confirming:   # an object seen once: hold this frame and run no block
            self._set_state("checking")   # contract 8.1: "checking" = before approval or confirming
            self._observe(UNKNOWN, None, privacy.code)
            return True
        if privacy.state != APPROVED:
            self._fault(privacy.code, privacy.state)
            return False
        if self.state == "checking":
            self._was_running = True
            self._set_state("evaluating" if self.evaluation_round else "running")

        ctx = FrameContext(image, t=frame.t)
        self._blur.process(ctx)   # raises BLUR_UNAVAILABLE if it can't blur
        for block in self._blocks:
            block.process(ctx)
        if self._clock() - frame.t > policy.MAX_FRAME_AGE_S:   # processing took too long
            self._unknown("OVERLOADED")
            return True
        self.preview, self.local_results = ctx.image, ctx.results
        self._observe(APPROVED, ctx.results)
        self._heartbeat()
        return True

    # --- events -------------------------------------------------------------

    def _unknown(self, code):
        """A frame we can't trust (FRAME_STALE or OVERLOADED): outputs become unknown with
        that reason, and coverage has a gap."""
        self.coverage = "gapped"
        self._drop_preview()
        self._observe(self._privacy_state(), None, code)
        self._heartbeat()

    def _observe(self, privacy, results, cause=None):
        """Send this frame's outputs: at most one observation per second, and at once when
        unknown_reason changes (an output turning unknown always changes it, and so does
        recovering).

        `results` are the frame's block results, or None when its outputs can't be trusted;
        then every configured output is unknown and `cause` says why. The cause becomes
        unknown_reason only when the contract asks for one: an output is unknown, or
        privacy isn't approved."""
        trusted = results is not None and privacy == APPROVED
        reason = None if trusted or not (self._configured or privacy != APPROVED) else cause
        outputs = {"occupancy": None, "entered": None, "exited": None, "target": None}
        if "color_finder" in self._configured:
            outputs["target"] = results["color_finder"].label if trusted else "unknown"
        if "person_detector" in self._configured:
            outputs["occupancy"] = count_known(len(results["person_detector"])) if trusted else count_unknown(reason)
        if "line_counter" in self._configured:
            crossings = results["line_counter"] if trusted else None
            outputs["entered"] = count_known(crossings.entered) if trusted else count_unknown(reason)
            outputs["exited"] = count_known(crossings.exited) if trusted else count_unknown(reason)
        now = self._clock()
        due = self._last_observation_t is None or now - self._last_observation_t >= policy.OBSERVATION_INTERVAL_S
        if not (due or reason != self._last_reason_sent):
            return
        self._last_observation_t, self._last_reason_sent = now, reason
        self.events.emit("observation", {
            "round": self.evaluation_round,
            "privacy": privacy, **outputs, "coverage": self.coverage,
            "motion": None, "looming": None, "alert": None, "unknown_reason": reason,
        }, revision=self.revision)

    def _fault(self, code, privacy=None):
        """Stop the job. Outputs become unknown first. "off" if it never ran, "held" if it was running."""
        self._drop_preview()
        self._observe(privacy or self._privacy_state(), None, code)
        self.events.emit("fault", {"code": code, "effect": "held" if self._was_running else "off"},
                         revision=self.revision)
        self._stop("held" if self._was_running else "refused")

    def _stop(self, state):
        self.camera.close()
        self._drop_preview()
        self._set_state(state)

    def _drop_preview(self):
        self.preview, self.local_results = None, {}

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
