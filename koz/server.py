"""The local WebSocket the web app connects to: ws://127.0.0.1:8765
(contracts/events.md sections 5, 6 and 10).

Out: every event exactly as contracts/events.md defines it, one JSON text message each.
     A fresh `status` is the first message on every connection, then one at least every second.
In:  the 4 commands (start_job, stop_job, begin_trial, finish_trial), checked strictly.

Safety:
- It listens on 127.0.0.1 only, so other computers can't reach it.
- It refuses any connection with a browser Origin header. Otherwise any web page open in
  your browser could talk to localhost and start a camera job ("cross-site WebSocket
  hijacking"). The web app's Node server connects without one.
- The local setup (ownership, allowed area, strict mode, which camera) comes from this
  command line only, never from a command (contract section 10, "No command exists for").
- Events never carry pictures or free text: EventLog refuses anything not in the contract.
- While nobody is connected, recipe/decision/fault/command_result/trial_result events wait in
  memory (at most 200); status and observations are dropped (contract section 5).

Run:  python -m koz.server --i-own-this-camera [--camera 0 | --video clip.mp4] [--strict] [--planner fake]"""
import argparse
import asyncio
import json
import os
import sys
import threading
import time
from collections import OrderedDict
from http import HTTPStatus

from . import policy
from .agent import Agent, make_planner
from .agent.choose import CHOICES, planned_by
from .agent.planner import MAX_TEXT
from .errors import CODES, KozError
from .events import CAMERA_SLOTS, ID_PATTERN, MAX_MESSAGE_BYTES, EventLog, count_unknown
from .runner import OPENCV_MAJOR, print_stops

HOST, PORT = "127.0.0.1", 8765
ENVELOPE = frozenset({"v", "type", "command_id", "session_id", "job_id", "trial_id", "expires_at", "command", "data"})
COMMANDS = ("start_job", "stop_job", "begin_trial", "finish_trial")
DEMOS = ("red_ball", "classroom", "privacy_guard")
REASONS = ("none", "missed_target", "wrong_direction", "count_mismatch", "privacy_miss", "safety_stop",
           "interrupted", "unknown")
IDLE_STATES = ("idle", "held", "refused")
STOP_WAIT_S = 3.0   # on Ctrl+C, wait this long for the job to stop


class BadMessage(Exception):
    """A message that isn't even a command we can answer (no valid command_id): close."""


def _id(v, nullable=True):
    return (v is None and nullable) or (type(v) is str and ID_PATTERN.fullmatch(v) is not None)


def parse_command(text):
    """Text -> command dict, or BadMessage. Strict JSON: no duplicate keys, no NaN/Infinity."""
    if type(text) is not str or len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise BadMessage("not a text message, or too large")

    def no_duplicates(pairs):
        if len({k for k, _ in pairs}) != len(pairs):
            raise ValueError("duplicate key")
        return dict(pairs)

    def no_constant(_):
        raise ValueError("NaN or Infinity")

    try:
        command = json.loads(text, object_pairs_hook=no_duplicates, parse_constant=no_constant)
    except (ValueError, RecursionError):
        raise BadMessage("not strict JSON") from None
    if type(command) is not dict or not _id(command.get("command_id"), nullable=False):
        raise BadMessage("no command_id")
    return command


def command_problem(command, session_id, now):
    """The error code for a malformed or expired command, else None (state is checked later)."""
    expires = command.get("expires_at")
    if (set(command) != ENVELOPE or command["v"] != 1 or type(command["v"]) is not int
            or command["type"] != "command" or command["command"] not in COMMANDS
            or not _id(command["job_id"]) or not _id(command["trial_id"])
            or type(expires) not in (int, float) or expires != expires or type(command["data"]) is not dict
            or not _data_ok(command["command"], command["data"])):
        return "INVALID_COMMAND"
    if now > expires:
        return "COMMAND_EXPIRED"
    if command["session_id"] != session_id:
        return "INVALID_COMMAND"
    return None


def _data_ok(name, data):
    if name == "start_job":
        # optional camera_id: one of the fixed slots (contract 10, Oct 16); never an address
        if "camera_id" in data and (type(data["camera_id"]) is not str or data["camera_id"] not in CAMERA_SLOTS):
            return False
        keys = set(data) - {"camera_id"}
        if data.get("input") == "prompt":
            return (keys == {"input", "language", "text"} and data["language"] in ("uz", "ru", "en")
                    and type(data["text"]) is str and 0 < len(data["text"].strip()) and len(data["text"]) <= MAX_TEXT)
        return data.get("input") == "recipe" and keys == {"input", "recipe"} and type(data["recipe"]) is dict
    if name == "stop_job":
        return data == {}
    if name == "begin_trial":
        return (set(data) == {"demo", "index"} and data["demo"] in DEMOS
                and type(data["index"]) is int and 1 <= data["index"] <= 10)
    expected = data.get("expected_count")
    return (set(data) == {"result", "reason", "expected_count"} and data["result"] in ("pass", "fail", "unknown")
            and data["reason"] in REASONS and (data["result"] != "pass" or data["reason"] == "none")
            and (expected is None or (type(expected) is int and 0 <= expected <= 2147483647)))


class Hub:
    """The runner's side of the protocol without the network: commands in (handle), events
    out (deliver). Tests drive it directly; serve() connects it to the WebSocket.

    `open_camera` opens the camera chosen on the command line; `planner` makes the plans."""

    def __init__(self, setup, open_camera, planner, capabilities=(), deliver=None, clock=time.monotonic,
                 wall_clock=time.time, eval_seconds=policy.AGENT_EVAL_S, models=None, report_planner=False,
                 say=lambda text: None, cameras=None, report_cameras=False, motor_link=None):
        """`open_camera` opens the default camera. `cameras` ({slot: open function}, optional) are
        the cameras a start_job may pick by camera_id; `report_cameras` lists their slots in status."""
        self.setup, self._open_camera, self.planner = setup, open_camera, planner
        self.cameras = dict(cameras or {})
        self.motor_link = motor_link   # the car's board (--motors PORT); armed only by a person here
        self._job_camera = open_camera
        self.capabilities = sorted(capabilities)
        self.deliver = deliver or (lambda event: None)
        self.clock, self.wall_clock, self.eval_seconds, self.models = clock, wall_clock, eval_seconds, models
        self.say = say   # one line per job for the terminal: who planned it and how it ended (no job text)
        self.events = EventLog(lambda event: self.deliver(event), wall_clock=wall_clock, report_planner=report_planner,
                               cameras=sorted(self.cameras, key=CAMERA_SLOTS.index) if report_cameras else None)
        self.events.listeners.append(self._track)
        self.lock = self.events.lock   # one lock for events and hub state (see EventLog)
        self._results = OrderedDict()  # command_id -> its command_result data
        self._agent = self._thread = self._camera = None
        self._running_job = None   # the job_id while its thread works (set and cleared under the lock)
        self._job_result = None    # (job_id, JobResult) of the last job
        self._trial = None
        self._status, self._status_t = None, None
        self.emit_status("idle")

    # --- status ---------------------------------------------------------------------

    def emit_status(self, state=None):
        """A status event: the latest one again (heartbeat, new connection) or a new state."""
        with self.lock:
            if state is None and self._status is not None:
                data, revision = self._status
            else:
                data = {"state": state or "idle", "camera_on": False, "privacy": "unknown",
                        "school": self.setup.school, "motor": "not_present", "opencv_major": OPENCV_MAJOR,
                        "capabilities": self.capabilities}
                revision = None
            seq = self.events.emit("status", data, revision=revision)
            return {"seq": seq}

    def heartbeat(self):
        with self.lock:
            if self._status_t is None or self.clock() - self._status_t >= policy.STATUS_INTERVAL_S:
                self.emit_status()

    def _track(self, event):
        """Runs inside EventLog's lock for every event: keeps the latest status and the trial's evidence."""
        kind, data = event["type"], event["data"]
        if kind == "status":
            self._status, self._status_t = (data, event["revision"]), self.clock()
        trial = self._trial
        if trial is None or event["trial_id"] != trial["id"]:
            return
        if kind == "fault":
            trial["fault"] = data["code"]
        elif kind == "recipe":
            trial["revision"] = event["revision"]
        elif kind == "observation" and data["round"] is None and event["job_id"] is not None:
            trial["ran"] = trial["ran"] or data["privacy"] == "approved"
            if data["entered"] is not None:
                if data["entered"]["state"] != "known" or data["coverage"] != "complete":
                    trial["gap"] = trial["gap"] or data["unknown_reason"] or "FRAME_STALE"
                trial["entered"] = data["entered"]

    def went_offline(self):
        """Nobody is connected: the events the web misses now leave a gap in the running job's
        coverage (contract 5: status and observations aren't queued)."""
        agent = self._agent
        runner = agent.runner if agent is not None else None
        if runner is not None and runner.state in ("evaluating", "running"):
            runner.coverage = "gapped"

    def mark_lost(self):
        """An event was dropped from the offline queue: the open trial's evidence is incomplete."""
        with self.lock:
            if self._trial is not None:
                self._trial["lost"] = True

    @property
    def busy(self):
        return self._running_job is not None

    @property
    def agent(self):
        """The current or last job's Agent (its plan and runner), or None."""
        return self._agent

    def arm_motors_by_hand(self):
        """A person armed the motors on this computer (A in the runner window, or Enter in its
        terminal). Contract 3: arming is local and by hand; no command from the web can do this."""
        if self.motor_link is not None:
            self.motor_link.arm_by_hand()
            self.say("Motors armed by hand.")

    def stop_local(self):
        """Stop the current job from this computer (q in the window): the same as stop_job."""
        with self.lock:
            self._stop()

    # --- commands -------------------------------------------------------------------

    def handle(self, text):
        """One message from the web app. Raises BadMessage if it can't even be answered."""
        command = parse_command(text)
        with self.lock:
            cached = self._results.get(command["command_id"])
            if cached is not None:   # a repeat: the same answer, nothing runs twice
                self.events.emit("command_result", cached)
                return
            code = command_problem(command, self.events.session_id, self.wall_clock())
            if code is None:
                code = getattr(self, "_" + command["command"])(command)
            if code is not None:
                self._answer(command, code)

    def _answer(self, command, code=None):
        data = {"command_id": command["command_id"], "result": "rejected" if code else "accepted", "code": code}
        self._results[command["command_id"]] = data
        while len(self._results) > 500:
            self._results.popitem(last=False)
        self.events.emit("command_result", data)

    def _start_job(self, command):
        trial = self._trial
        if self.busy or self._status[0]["state"] not in IDLE_STATES:
            return "BUSY"
        if command["job_id"] is None or command["trial_id"] != (trial["id"] if trial else None):
            return "INVALID_COMMAND"
        if trial is not None and trial["job_id"] is not None:
            return "BUSY"   # one job per trial
        camera_id = command["data"].get("camera_id")
        if camera_id is not None and camera_id not in self.cameras:
            return "UNSUPPORTED_CAPABILITY"   # a known slot, but not set up on this runner
        self._job_camera = self.cameras[camera_id] if camera_id is not None else self._open_camera
        if trial is not None:
            trial["job_id"] = command["job_id"]
        self.events.bind(command["job_id"], command["trial_id"])
        self._answer(command)
        self._job_result, self._camera, self._running_job = None, None, command["job_id"]
        self._agent = Agent(self.planner, self.setup, self._opened_camera, self.events, clock=self.clock,
                            eval_seconds=self.eval_seconds, models=self.models, on_plan=self._planned,
                            motor_link=self.motor_link)
        self._thread = threading.Thread(target=self._work, args=(self._agent, command["job_id"], command["data"]),
                                        name="koz-job", daemon=True)
        self._thread.start()
        return None

    def _stop_job(self, command):
        if command["job_id"] != self.events.job_id or command["trial_id"] != self.events.trial_id:
            return "INVALID_COMMAND"
        self._answer(command)
        self._stop()
        return None

    def _begin_trial(self, command):
        if self.busy or self._status[0]["state"] not in IDLE_STATES or self._trial is not None:
            return "BUSY"
        if command["job_id"] is not None or command["trial_id"] is None:
            return "INVALID_COMMAND"
        self._trial = {"id": command["trial_id"], "demo": command["data"]["demo"], "index": command["data"]["index"],
                       "job_id": None, "revision": None, "fault": None, "ran": False, "entered": None,
                       "gap": None, "lost": False, "finish": None}
        self._job_result = None   # an earlier job's changes never count for this trial
        self.events.bind(None, command["trial_id"])
        self._answer(command)
        return None

    def _finish_trial(self, command):
        if self._trial is None or command["trial_id"] != self._trial["id"]:
            return "INVALID_COMMAND"
        if command["job_id"] != self.events.job_id:
            return "INVALID_COMMAND"
        if command["data"]["expected_count"] is not None and self._trial["demo"] != "classroom":
            return "INVALID_COMMAND"
        if self._trial["finish"] is not None:
            return "BUSY"   # already finishing: waiting for the job to stop
        self._answer(command)
        self._trial["finish"] = command["data"]
        self._stop()
        if not self.busy:
            self._close_trial()
        # Otherwise the job thread sends trial_result once the job has really stopped (_work),
        # so no event of this trial's job can arrive after the trial is closed.
        return None

    def _stop(self):
        """stop_job: at once, before any planner work. A planner answer that comes later can't
        start the job (Agent checks stop_requested)."""
        if self.busy:
            self._agent.stop_requested = True
            if self._agent.phase in (None, "planning") or self._camera is None:
                self.emit_status("idle")   # the planner or the camera may take seconds: say idle now
        elif self._status[0]["state"] != "idle":
            self.emit_status("idle")

    def _close_trial(self):
        """Send trial_result (contract 8.7) and close the trial."""
        trial = self._trial
        if trial is None or trial["finish"] is None:
            return
        job = self._job_result[1] if self._job_result and self._job_result[0] == trial["job_id"] else None
        finish = trial["finish"]
        result, reason = finish["result"], finish["reason"]
        observed = None
        if trial["demo"] == "classroom" and trial["entered"] is not None:
            observed = count_unknown(trial["gap"]) if trial["gap"] else trial["entered"]
        # The runner may lower a pass it can't support to unknown; it never raises a fail.
        supported = {"red_ball": trial["ran"],
                     "classroom": observed is not None and observed["state"] == "known",
                     "privacy_guard": (trial["fault"] or "").startswith("PRIVATE_")}[trial["demo"]]
        if result == "pass" and (not supported or trial["lost"]):
            result, reason = "unknown", "unknown"
        self.events.emit("trial_result", {
            "demo": trial["demo"], "index": trial["index"], "result": result, "basis": "owner_report",
            "reason": reason, "expected_count": finish["expected_count"], "observed_count": observed,
            "fault_code": trial["fault"], "evidence": "incomplete" if trial["lost"] else "complete",
            "agent_changes": (job.agent_changes if job else [])[:2]}, revision=trial["revision"])
        self._trial = None
        self.events.bind(None, None)

    # --- the job thread ---------------------------------------------------------------

    def _planned(self, plan):
        self.say(f"Plan by {planned_by(plan, self.planner)}: "
                 + (f"refused ({plan.refusal})" if plan.refusal else f"{plan.job} ({plan.language})"))

    def _opened_camera(self):
        self._camera = self._job_camera()
        return self._camera

    def _work(self, agent, job_id, start):
        try:
            if start["input"] == "prompt":
                result = agent.run(start["text"])
            else:
                result = agent.run_recipe(start["recipe"], origin="import")
            with self.lock:
                self._job_result = (job_id, result)
            self.say(f"Job {result.state}" + (f" ({result.code})" if result.code else "")
                     + (", after adjusting " + ", ".join(c["change"]["setting"] for c in result.agent_changes)
                        if result.agent_changes else ""))
            if result.state == "running":
                runner = result.runner
                while not agent.stop_requested and runner.step():
                    pass
                runner.stop()
        except Exception as error:   # fail closed: close the camera, say why, hold the job
            if self._camera is not None:
                self._camera.close()
            code = error.code if isinstance(error, KozError) else "INTERNAL_ERROR"
            try:
                self.events.emit("fault", {"code": code if code in CODES else "INTERNAL_ERROR", "effect": "held"})
                self.emit_status("held")
            except Exception:
                pass
        finally:
            with self.lock:
                self._running_job = None
                if self._trial is not None and self._trial["job_id"] == job_id:
                    self._close_trial()   # only if finish_trial is waiting for this job


async def serve(hub, host=HOST, port=PORT, started=None):
    """Serve `hub` on this computer until cancelled (the local web app connects in). `started`
    (an asyncio.Event) is set once it listens. Delivery: koz/cloud.py's Outbox."""
    from websockets.asyncio.server import broadcast
    from websockets.asyncio.server import serve as ws_serve

    from .cloud import Outbox, heartbeat

    outbox = Outbox(hub, asyncio.get_running_loop(), broadcast)

    def refuse_browsers(connection, request):
        if request.headers.get("Origin") is not None:
            return connection.respond(HTTPStatus.FORBIDDEN, "Browsers may not connect to the Ko'z runner.\n")
        return None

    async def connected(connection):
        outbox.join(connection)
        try:
            async for message in connection:
                if not isinstance(message, str):
                    await connection.close(1003, "INVALID_COMMAND")
                    return
                try:
                    await asyncio.to_thread(hub.handle, message)
                except BadMessage:
                    await connection.close(1008, "INVALID_COMMAND")
                    return
        finally:
            outbox.leave(connection)

    async with ws_serve(connected, host, port, process_request=refuse_browsers, max_size=MAX_MESSAGE_BYTES,
                        compression=None):
        beating = asyncio.create_task(heartbeat(hub))
        if started is not None:
            started.set()
        try:
            await asyncio.Future()   # run until cancelled
        finally:
            beating.cancel()


def show_window(hub, alive):
    """The local preview of the current job (--window): what the camera sees, faces blurred,
    with the status and the privacy check. On screen only, never saved or sent (rule 8).
    Runs in the main thread (macOS draws windows only there). q or Esc stops the job."""
    import cv2
    import numpy as np

    from .messages import all_messages
    from .preview import WHITE, draw, put_centred

    title = "Ko'z runner (q stops the job)"
    messages, latest = all_messages("en"), {}

    def keep(event):   # runs in the job thread, inside EventLog's lock: just store
        kind, data = event["type"], event["data"]
        if kind == "status" and data["state"] == "planning":
            latest.clear()   # a new job: forget the last one's fault and numbers
        latest[kind] = data
        if kind == "recipe":
            block = next((b for b in data["recipe"]["blocks"] if b["type"] == "line_counter"), None)
            latest["line"] = tuple(block["settings"]["line"][0] + block["settings"]["line"][1]) if block else None

    def screen(lines):
        view = np.zeros((480, 640, 3), np.uint8)
        for i, text in enumerate(lines):
            put_centred(view, text, 200 + 40 * i, 0.8 if i == 0 else 0.6, 2 if i == 0 else 1, WHITE)
        return view

    hub.events.listeners.append(keep)
    frames, since, last = 0, time.monotonic(), None
    while alive():
        agent = hub.agent
        runner = agent.runner if agent is not None else None
        try:
            if runner is not None and (runner.state in ("checking", "evaluating", "running") or "fault" in latest):
                if runner.preview is not None and runner.preview is not last:
                    frames, last = frames + 1, runner.preview
                note = f"plan by {planned_by(agent.plan, hub.planner)}" if agent.plan is not None else ""
                if hub.motor_link is not None:
                    note += f"   motors: {motor_state(hub.motor_link)} (a = arm)"
                view = draw(runner, latest, messages, frames / max(time.monotonic() - since, 1e-6),
                            latest.get("line"), note)
            elif hub.busy:
                view = screen(["Planning the job...", "then trying it on the camera"])
            elif "fault" in latest:   # refused before any camera opened
                code = latest["fault"]["code"]
                view = screen(["Refused", messages.get(code, code), f"({code})"])
            else:
                frames, since = 0, time.monotonic()
                lines = ["Ko'z is ready", "Type the job in the web app (Setup).",
                         "This window shows what the camera sees, faces blurred."]
                if hub.motor_link is not None:
                    lines.append(f"Motors: {motor_state(hub.motor_link)}. Press A to arm them by hand.")
                view = screen(lines)
        except Exception:   # the job thread changed the frame while drawing: skip this one
            time.sleep(0.01)
            continue
        cv2.imshow(title, view)
        key = cv2.waitKey(30) & 0xFF
        if key in (ord("q"), 27):
            hub.stop_local()
        elif key in (ord("a"), ord("A")):
            hub.arm_motors_by_hand()
    cv2.destroyAllWindows()


def motor_state(link):
    fault = link.fault
    return f"fault {fault}" if fault else ("armed" if link.armed else "disarmed")


def main(argv=None):
    import signal

    from .capture import FileCamera, describe, open_camera as open_source
    from .local_setup import LocalSetup

    parser = argparse.ArgumentParser(description="Ko'z runner: the WebSocket the web app connects to")
    parser.add_argument("--i-own-this-camera", action="store_true",
                        help="confirm the camera is yours and you may film this view (rule 7)")
    parser.add_argument("--camera", action="append", metavar="SLOT=SOURCE",
                        help="a camera the web app can pick: mac_camera=0, esp32_cam=http://192.168.4.1:81/stream, "
                             "phone_ip_camera=http://PHONE:8080/video or rtsp://...; repeat for several (the first is "
                             "the default). Plain 0 = mac_camera, a plain URL = esp32_cam. Default: mac_camera=0")
    parser.add_argument("--report-cameras", action="store_true",
                        help="send status.cameras (contract 8.1); only once the web app accepts it")
    parser.add_argument("--video", help="play a recorded video file instead of a camera (a new start replays it)")
    parser.add_argument("--allowed-area", default="0,0,1,1",
                        help="left,top,right,bottom of the allowed area, 0..1 (default: whole frame)")
    parser.add_argument("--school", action="store_true", help="school mode: counts only, and always strict")
    parser.add_argument("--strict", action="store_true", help="strict mode for schools and public cameras")
    parser.add_argument("--motors", metavar="PORT",
                        help="the car's motor_listener board on USB, e.g. /dev/cu.usbmodem1101, or auto")
    parser.add_argument("--motor-cap", type=float, default=0.15,
                        help="the car's tested speed cap, 0..0.25 of full speed (measure: firmware/stop_test)")
    parser.add_argument("--mount", choices=("fixed", "moving"),
                        help="fixed camera, or moving (the car); default: moving with --motors")
    parser.add_argument("--planner", choices=CHOICES, default="auto",
                        help="auto: Nemotron on Nebius if NEBIUS_API_KEY is in .env, else the rule planner; "
                             "ollama: Gemma 4 on this Mac (14/20 on Oct 15, see docs/TRIALS.md)")
    parser.add_argument("--window", action="store_true", help="show the camera view (faces blurred) of each job")
    parser.add_argument("--no-report-planner", dest="report_planner", action="store_false",
                        help="don't send status.planner (contract 8.1; the web app accepts it since Oct 16)")
    parser.add_argument("--cloud", metavar="WSS_URL",
                        help="connect out to the cloud web app instead of listening here, e.g. "
                             "wss://WEB-IP/v1/runner (token: KOZ_RUNNER_TOKEN in .env)")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args(argv)
    print_stops()   # every stop says why, with the last privacy check

    left, top, right, bottom = (float(v) for v in args.allowed_area.split(","))
    setup = LocalSetup(owner_confirmed=args.i_own_this_camera,
                       allowed_area=(((left, top), (right, top), (right, bottom), (left, bottom)),),
                       school=args.school, strict=args.strict, mount=args.mount or ("moving" if args.motors else "fixed"),
                       motor_cap=args.motor_cap)
    try:
        setup.check()
    except KozError as error:
        print(f"Ko'z did not start: {error.code}. Add --i-own-this-camera if this camera is yours.")
        return 1
    planner = make_planner(args.planner)
    cameras = {}
    for entry in args.camera or ["0"]:
        slot, _, source = entry.partition("=") if "=" in entry.split("://")[0] else ("", "", entry)
        slot = slot or ("mac_camera" if source.strip().isdigit() else "esp32_cam")
        if slot not in CAMERA_SLOTS or slot in cameras:
            print(f"Ko'z did not start: camera slot must be one of {', '.join(CAMERA_SLOTS)}, each once.")
            return 1
        cameras[slot] = (lambda source=source: open_source(source))
        print(f"Camera {slot}: {describe(source)}", flush=True)
    if args.video:
        open_camera, capabilities = (lambda: FileCamera(args.video, realtime=True)), ("recorded_fixture",)
        cameras = {}
    else:
        open_camera, capabilities = next(iter(cameras.values())), ()
    link = None
    if args.motors:
        from .actions.motors import open_motor_board
        try:
            link = open_motor_board(args.motors)
        except (KozError, OSError) as error:
            print(f"Ko'z did not start: the motor board can't be reached ({getattr(error, 'code', type(error).__name__)}).")
            return 1
        print("Motors: disarmed. Arm them by hand: press A in the runner window, or Enter here.", flush=True)
    hub = Hub(setup, open_camera, planner, capabilities=capabilities, report_planner=args.report_planner,
              cameras=cameras, report_cameras=args.report_cameras,
              say=lambda text: print(text, flush=True), motor_link=link)
    if link is not None and sys.stdin.isatty():
        def enter_arms():   # Enter in this terminal = a person arming the motors here
            for _ in sys.stdin:
                hub.arm_motors_by_hand()
        threading.Thread(target=enter_arms, name="koz-arm-by-hand", daemon=True).start()

    def interrupted(signum, frame):   # closing the Terminal window (HUP) or the launcher (TERM): stop cleanly
        raise KeyboardInterrupt
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)

    token = None
    if args.cloud:
        from .agent.choose import load_env
        from .cloud import check_cloud_url
        token = {**load_env(), **os.environ}.get("KOZ_RUNNER_TOKEN")
        try:
            check_cloud_url(args.cloud)
        except ValueError:
            print("Ko'z did not start: --cloud must be a wss:// address.")
            return 1
        if not token:
            print("Ko'z did not start: put KOZ_RUNNER_TOKEN=... in .env (from the web app's Runner token page).")
            return 1
        print("Ko'z runner: connecting out to the cloud web app. Ctrl+C stops.", flush=True)
    else:
        print(f"Ko'z runner on ws://{HOST}:{args.port}. The web app connects here. Ctrl+C stops.", flush=True)
    print(f"Planners, in order: {planner.name}", flush=True)
    failed = []

    def run_server():
        try:
            if args.cloud:
                from .cloud import link_cloud
                asyncio.run(link_cloud(hub, args.cloud, token))
            else:
                asyncio.run(serve(hub, port=args.port))
        except OSError as error:   # most often: another runner already uses the port
            failed.append(error)

    try:
        if args.window:
            server = threading.Thread(target=run_server, name="koz-websocket", daemon=True)
            server.start()
            show_window(hub, server.is_alive)
        else:
            run_server()
    except KeyboardInterrupt:
        pass
    finally:
        hub.stop_local()
        if hub._thread is not None:
            hub._thread.join(STOP_WAIT_S)
        if link is not None:
            try:
                link.disarm()
            except KozError:
                pass
            link.close()
    if failed:
        print(f"Ko'z runner could not listen on port {args.port}: is another runner already running?")
        return 1
    print("Ko'z runner stopped.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
