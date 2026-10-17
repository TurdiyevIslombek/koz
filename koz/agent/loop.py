"""The agent loop (CLAUDE.md MVP item 4; contracts/events.md section 9).

    words -> plan (refused before any camera opens, or a checked recipe)
          -> try revision N on live frames for AGENT_EVAL_S, with the privacy guard on
          -> check the OpenCV numbers (is the target visible? are the counts known?)
          -> pass: run it.   fail: change ONE setting from what OpenCV measured (koz/agent/tuner.py)
          -> try revision N+1 ...   at most AGENT_MAX_ROUNDS tries, then stop (ADJUSTMENT_LIMIT)

Every step is a contract event, so the dashboard can show the chain that makes this
agentic (the Agentic Vision award: OpenCV output changes the next action):
    observation (revision N) -> decision citing those observations -> recipe revision N+1
    -> status: revision N+1 installed -> observation under revision N+1.
A failed check never weakens safety: the tuner can only touch the settings the contract
lists, every new revision goes through koz.recipe again, and a privacy stop ends the job
instead of being "adjusted"."""
import time
from collections import Counter
from dataclasses import dataclass, field

from .. import policy
from ..errors import KozError
from ..recipe import check_recipe
from ..runner import OPENCV_MAJOR, Runner
from . import tuner
from .planner import Plan, check_text

POSITIONS = ("left", "center", "right")


@dataclass
class JobResult:
    plan: Plan | None
    state: str                  # running | refused | held | idle
    code: str | None            # why it isn't running, if it isn't
    runner: Runner | None       # the accepted revision, still running (state "running")
    decisions: list = field(default_factory=list)       # each decision event's data
    agent_changes: list = field(default_factory=list)   # executed adjustments (for trial_result)


def job_kind(recipe):
    types = {b["type"] for b in recipe["blocks"]}
    if recipe["brain"]["type"] == "flybrain":
        return "chase_colour"
    return "find_colour" if "color_finder" in types else "count_people" if "person_detector" in types else "other"


def judge(job, observations):
    """(check, result, label) for one round, from its observation events only (contract section 7).

    find_colour: unknown if fewer than half of the observations have a known answer; otherwise
    pass if the target was left/center/right in at least half of the known ones, else fail.
    count_people: pass if the latest counts are known (the detector and line counter work).
    chase_colour (the car): first target_visible as above; once the ball is seen, target_centered:
    pass if the brain had it in the middle in at least a third of the known observations (the car
    swings around the ball while it drives; observations come about once a second)."""
    if job == "chase_colour":
        check, result, label = judge("find_colour", observations)
        if result != "pass":
            return check, result, label
        known = [o["target"] for o in observations if o["privacy"] == "approved" and o["target"] in POSITIONS]
        return "target_centered", "pass" if 3 * known.count("center") >= len(known) else "fail", label
    if job == "find_colour":
        known = [o["target"] for o in observations if o["privacy"] == "approved" and o["target"] not in (None, "unknown")]
        if not known or 2 * len(known) < len(observations):
            return "target_visible", "unknown", "unknown"
        label = Counter(known).most_common(1)[0][0]
        visible = sum(t in POSITIONS for t in known)
        return "target_visible", "pass" if 2 * visible >= len(known) else "fail", label
    last = observations[-1] if observations else None
    if job == "count_people":
        if last and last["occupancy"] is not None and last["occupancy"]["state"] == "known":
            return "counts_available", "pass", "known"
        return "counts_available", "unknown", "unknown"
    if last and last["privacy"] == "approved":
        return "privacy_approved", "pass", "approved"
    return "privacy_approved", "unknown", "unknown"


class Agent:
    """Runs one job for one setup. `open_camera()` is called only after the plan, the local
    setup and the recipe passed every check. `models` replaces the guard / face / person
    models in tests. Make a new Agent for each job; `stop_requested` (set from another thread
    by stop_job) ends it, and a planner answer that arrives after it never starts the job."""

    def __init__(self, planner, setup, open_camera, events, clock=time.monotonic,
                 eval_seconds=policy.AGENT_EVAL_S, models=None, on_frame=None, on_plan=None, motor_link=None):
        self.planner, self.setup, self.open_camera, self.events = planner, setup, open_camera, events
        self.clock, self.eval_seconds, self.models = clock, eval_seconds, models or {}
        self.on_frame = on_frame   # called with the runner after each frame (the demo's window)
        self.on_plan = on_plan     # called with the plan as soon as there is one (the demo prints it)
        self.motor_link = motor_link   # the car's motor board (local hardware), for recipes with motors
        self.stop_requested = False
        self.phase = None    # planning | trying | done (the server reads it)
        self.plan = None     # the plan, once there is one
        self.runner = None   # the runner of the revision being tried or run (the server's window shows it)

    def run(self, text):
        """One sentence -> JobResult."""
        check_text(text)
        if self.stop_requested:
            return self._stopped(None)
        self.phase = "planning"
        self._status("planning")
        try:
            plan = self.planner.plan(text)
        except KozError as error:
            if self.stop_requested:   # a late planner failure doesn't undo stop_job
                return self._stopped(None)
            return self._refuse(None, error.code)
        self.plan = plan
        self.events.set_planner(plan.source)   # status.planner from now on, for this job
        if self.on_plan is not None:
            self.on_plan(plan)
        if self.stop_requested:
            return self._stopped(plan)
        if plan.refusal:
            return self._refuse(plan, plan.refusal)
        return self.run_recipe(plan.recipe, origin="planner", plan=plan)

    def run_recipe(self, recipe, origin="import", plan=None):
        """A recipe (from the planner or an import) -> tried, adjusted, run. If anything fails on the
        way (a report, a callback), the motors stop and disarm before the error goes on (re-review of MS-2)."""
        try:
            return self._run_recipe(recipe, origin, plan)
        except BaseException:
            if self.runner is not None:
                self.runner.end_motors()
            raise

    def _run_recipe(self, recipe, origin, plan):
        self.phase = "trying"
        if self.stop_requested:
            return self._stopped(plan)
        try:
            self.setup.check()
            checked = check_recipe(recipe, local_school=self.setup.school)
            if any(a["type"] == "motors" for a in checked.data["actions"]):   # the car: before the camera
                if self.motor_link is None:
                    raise KozError("UNSUPPORTED_CAPABILITY", "no motor board set up on this computer")
                if self.motor_link.fault is not None:
                    raise KozError("MOTOR_SAFETY_STOP")
                if not self.motor_link.armed:
                    raise KozError("MOTOR_NOT_ARMED")   # a person arms them here, by hand
            camera = self.open_camera()   # only now: refused jobs never open the camera
        except KozError as error:
            return self._refuse(plan, error.code)
        if self.stop_requested:   # stopped while the camera was starting
            camera.close()
            return self._stopped(plan)
        job, revision, models = job_kind(checked.data), 1, dict(self.models)
        decisions, changes, pending = [], [], None
        self.events.emit("recipe", {"origin": origin, "caused_by": None, "recipe": checked.data}, revision=revision)
        for number in range(1, policy.AGENT_MAX_ROUNDS + 1):
            try:
                runner = Runner(checked, self.setup, camera, self.events, revision=revision,
                                evaluation_round=number, clock=self.clock, motor_link=self.motor_link,
                                cancelled=lambda: self.stop_requested, **models)
            except KozError as error:   # a model file missing or changed, or no motor board: nothing runs
                camera.close()
                return self._refuse(plan, error.code)
            self.runner, models = runner, {**runner.models, **self.models}
            observations, frames, fault = self._try(runner, number)
            if self.stop_requested:
                camera.close()   # also when the stop came before the first frame
                return self._stopped(plan, decisions, changes)
            cited = observations[-10:]   # a decision cites at most 10 observations; it judges exactly those
            evidence, data = [seq for seq, _ in cited], [d for _, d in cited]
            check, result, label = judge(job, data)
            if pending and data:   # the previous change has now run: keep it for the trial report
                changes.append({**pending, "executed": True, "after_label": label, "after_result": result})
            pending = None
            ended = runner.state not in ("checking", "evaluating")

            if ended and (fault or runner.state != "idle"):   # the guard stopped it, or a block failed
                code = fault or "INTERNAL_ERROR"   # a policy stop: never "adjusted"
                if evidence:
                    private = code.startswith(("PRIVATE_", "PRIVACY_", "LENS_", "SCENE_"))
                    self._decide(decisions, number, evidence, "privacy_approved" if private else check,
                                 "fail" if code.startswith("PRIVATE_") else "unknown", "stop", revision, None, code)
                return self._end(plan, runner.state, code, decisions, changes)
            if not evidence:   # no observation at all: nothing to decide on
                if ended:
                    return self._end(plan, "idle", "CHECK_FAILED", decisions, changes)
                return self._hold(plan, runner, "CHECK_FAILED", decisions, changes)
            if result == "pass":
                self._decide(decisions, number, evidence, check, "pass", "run", revision, None, None)
                if ended:   # a recording that ended: the check passed, and there is nothing left to run
                    return self._end(plan, "idle", None, decisions, changes)
                runner.finish_evaluation()
                self.phase = "done"
                return JobResult(plan, "running", None, runner, decisions, changes)
            if ended:   # the recording ended before the check passed: no frames left to adjust on
                self._decide(decisions, number, evidence, check, result, "stop", revision, None, "CHECK_FAILED")
                return self._end(plan, "idle", "CHECK_FAILED", decisions, changes)
            if result == "unknown":
                code = next((d["unknown_reason"] for d in reversed(data) if d["unknown_reason"]), "CHECK_FAILED")
                self._decide(decisions, number, evidence, check, result, "stop", revision, None, code)
                return self._hold(plan, runner, code, decisions, changes)
            if number == policy.AGENT_MAX_ROUNDS:
                self._decide(decisions, number, evidence, check, "fail", "stop", revision, None, "ADJUSTMENT_LIMIT")
                return self._hold(plan, runner, "ADJUSTMENT_LIMIT", decisions, changes)

            change = tuner.propose(checked.data, check, frames)
            try:
                new = check_recipe(tuner.apply(checked.data, change), local_school=self.setup.school) if change else None
            except KozError:
                new = None   # a change that breaks a rule is never tried
            if new is None:
                self._decide(decisions, number, evidence, check, "fail", "stop", revision, None, "CHECK_FAILED")
                return self._hold(plan, runner, "CHECK_FAILED", decisions, changes)
            # Contract 8.4: the adjust decision is sent only after the new revision passed every check.
            seq = self._decide(decisions, number, evidence, check, "fail", "adjust", revision, change, None)
            pending = {"from_revision": revision, "to_revision": revision + 1, "check": check,
                       "before_label": label, "change": change}
            revision += 1
            self.events.emit("recipe", {"origin": "adjustment", "caused_by": seq, "recipe": new.data}, revision=revision)
            checked = new
        raise AssertionError("unreachable: the last round always returns")

    # --- helpers ----------------------------------------------------------------------

    def _try(self, runner, number):
        """Run one round for eval_seconds. Returns its observations [(seq, data)], a few local
        frames for the tuner (masked and blurred; they never leave this computer), and the
        last fault code, if any."""
        observations, faults, frames = [], [], []

        def listen(event):
            if (event["type"] == "observation" and event["data"]["round"] == number
                    and event["revision"] == runner.revision):
                observations.append((event["seq"], event["data"]))
            elif event["type"] == "fault":
                faults.append(event["data"]["code"])

        self.events.listeners.append(listen)
        try:
            start, steps = self.clock(), 0
            while self.clock() - start < self.eval_seconds and not self.stop_requested:
                alive = runner.step()
                if self.on_frame is not None:
                    self.on_frame(runner)
                if not alive:
                    break
                steps += 1
                if runner.preview is not None and steps % 3 == 1 and len(frames) < 30:
                    frames.append(runner.preview.copy())
            if self.stop_requested:
                runner.stop()
        except BaseException:   # a callback or anything else failed: the motors stop first (review MS-2)
            runner.end_motors()
            raise
        finally:
            self.events.listeners.remove(listen)
        return observations, frames, (faults[-1] if faults else None)

    def _decide(self, decisions, number, evidence, check, result, next_step, revision, change, code):
        next_revision = {"run": revision, "adjust": revision + 1, "stop": None}[next_step]
        data = {"round": number, "evidence_seq": evidence, "check": check, "result": result, "next": next_step,
                "next_revision": next_revision, "change": change, "code": code}
        decisions.append(data)
        return self.events.emit("decision", data, revision=revision)

    def _hold(self, plan, runner, code, decisions, changes):
        runner.hold(code)
        return self._end(plan, "held", code, decisions, changes)

    def _end(self, plan, state, code, decisions, changes):
        self.phase = "done"
        return JobResult(plan, state, code, None, decisions, changes)

    def _stopped(self, plan, decisions=(), changes=()):
        self._status("idle")
        return self._end(plan, "idle", None, list(decisions), list(changes))

    def _refuse(self, plan, code):
        self.events.emit("fault", {"code": code, "effect": "off"})
        self._status("refused")
        return self._end(plan, "refused", code, [], [])

    def _status(self, state):
        self.events.emit("status", {"state": state, "camera_on": False, "privacy": "unknown",
                                    "school": self.setup.school, "motor": "not_present",
                                    "opencv_major": OPENCV_MAJOR, "capabilities": []})
