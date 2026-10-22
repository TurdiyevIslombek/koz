"""Every event the runner and agent send must pass the web app's own check (web/src/protocol.js).

Found Oct 22 in Islombek's live test: "find a colour" with nothing in view decided `unknown` -> `run`
(contract section 9), the website accepted `run` only after `pass`, answered `protocol_error`
and closed the link. This test runs real jobs with fake models and checks each event they send
with the website's validator in Node, so the two sides can't drift apart again."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from helpers import FULL_FRAME, Approve, EndlessCamera, FakeClock, FakeFaces, Refuse, ScriptedPeople, walker

from koz.agent import Agent, FakePlanner
from koz.blocks import Detection
from koz.blocks.object_finder import OBJECTS
from koz.events import EventLog
from koz.local_setup import LocalSetup

WEB = Path(__file__).resolve().parent.parent / "web"
CHECK = """
import { validateEvent } from './src/protocol.js';
const events = JSON.parse(await new Promise(r => { let s = ''; process.stdin.on('data', d => s += d); process.stdin.on('end', () => r(s)); }));
const bad = [];
for (const e of events) { try { validateEvent(e); } catch { bad.push(`${e.type} ${JSON.stringify(e.data)}`); } }
console.log(JSON.stringify(bad));
"""


class Objects:
    def __init__(self, detections):
        self.detections = detections

    def detect(self, image, classes, min_confidence):
        return [d for d in self.detections if d.class_id in classes and d.score >= min_confidence]


def run_job(text, guard=None, people=None, objects=()):
    clock, events = FakeClock(), []
    models = {"scene_checker": guard or Approve(), "face_detector": FakeFaces(), "object_detector": Objects(objects)}
    if people is not None:
        models["person_detector"] = people
    agent = Agent(FakePlanner(), LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME),
                  lambda: EndlessCamera(np.full((240, 320, 3), 128, np.uint8), clock), EventLog(events.append, job_id="a" * 32),
                  clock=clock, eval_seconds=2.0, models=models)
    result = agent.run(text)
    if result.runner is not None:
        for _ in range(5):          # a few frames of the running job too
            result.runner.step()
        result.runner.stop()
    return events


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is not installed")
def test_every_job_sends_only_events_the_website_accepts():
    jobs = {
        "colour, nothing in view (run and wait)": run_job("find the red ball"),
        "thing in view": run_job("find the phone", objects=[Detection(OBJECTS["cell phone"], (500, 160, 580, 320), 0.8)]),
        "thing not in view (run and wait)": run_job("find my blue backpack"),
        "counting": run_job("count people entering my shop",
                            people=ScriptedPeople([[box] for box in walker(600, 60, 400)])),
        "privacy stop": run_job("find the red ball", guard=Refuse("PRIVATE_BEDROOM")),
        "refused": run_job("who is this man at my door"),
    }
    for name, events in jobs.items():
        assert events, name
        answer = subprocess.run(["node", "--input-type=module", "-e", CHECK], cwd=WEB, input=json.dumps(events),
                                capture_output=True, text=True, timeout=60)
        assert answer.returncode == 0, answer.stderr
        assert json.loads(answer.stdout) == [], name


@pytest.mark.filterwarnings("ignore:.*found in sys.modules:RuntimeWarning")
def test_a_message_that_is_not_a_command_never_stops_the_runner_started_as_a_module():
    """`python -m koz.server` (start-koz-cloud.command) runs server.py as __main__, a second copy of
    the module. Its BadMessage must be the one the cloud link catches (Oct 22: the runner stopped)."""
    import runpy

    from koz.errors import BadMessage
    as_main = runpy.run_module("koz.server", run_name="koz_server_as_main")   # the code again, not main()
    with pytest.raises(BadMessage):
        as_main["parse_command"]('{"v":1,"type":"protocol_error","code":"INVALID_EVENT"}')
