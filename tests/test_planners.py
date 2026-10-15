"""The AI planners and the order they are asked in (koz/agent/ollama.py, choose.py, menu.py),
and status.planner (contracts/events.md 8.1). No model and no network: fake replies only."""
import json
import socket

import pytest
from helpers import FULL_FRAME, Approve, FakeFaces

from koz.agent import Agent, AutoPlanner, FakePlanner, NebiusPlanner, OllamaPlanner
from koz.agent.menu import CHOICE_SCHEMA
from koz.errors import KozError
from koz.events import EventLog, new_id
from koz.local_setup import LocalSetup
from koz.messages import message
from koz.recipe import check_recipe

CHOICE = '{"job": "count_people", "colour": null, "school": true, "refusal": null}'


class FakeOllama:
    """Answers like Ollama's /api/tags and /api/chat, and keeps what it was sent."""

    def __init__(self, content=CHOICE, models=("gemma4:e2b-it-qat",), down=False):
        self.content, self.models, self.down, self.sent = content, models, down, []

    def __call__(self, method, path, body, timeout=None):
        if self.down:
            raise KozError("PLANNER_UNAVAILABLE")
        self.sent.append((method, path, body))
        if path == "/api/tags":
            return {"models": [{"name": m} for m in self.models]}
        return {"model": body["model"], "message": {"role": "assistant", "content": self.content}, "done": True}


def failing(*args, **kwargs):
    raise KozError("PLANNER_UNAVAILABLE")


# --- OllamaPlanner ----------------------------------------------------------------------

def test_ollama_picks_from_the_menu_and_ko_z_builds_the_recipe():
    ollama = FakeOllama()
    planner = OllamaPlanner(send=ollama)
    assert planner.available()
    plan = planner.plan("Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir")
    assert (plan.job, plan.language, plan.source, plan.recipe["privacy"]["school"]) == ("count_people", "uz", "ollama", True)
    check_recipe(plan.recipe)
    method, path, body = ollama.sent[-1]
    assert (method, path, body["model"], body["stream"]) == ("POST", "/api/chat", "gemma4:e2b-it-qat", False)
    assert body["format"] == CHOICE_SCHEMA            # Ollama holds the model to the menu
    assert body["keep_alive"] == "0"                  # memory goes back to the camera models
    assert body["messages"][1] == {"role": "user", "content": "Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir"}
    assert len(body["messages"]) == 2                 # only the sentence: no recipe, frames or numbers


def test_ollama_never_receives_a_forbidden_request():
    ollama = FakeOllama()
    plan = OllamaPlanner(send=ollama).plan("Who is this man? Recognise his face")
    assert (plan.refusal, plan.source, ollama.sent) == ("IDENTITY_FORBIDDEN", "rules", [])


@pytest.mark.parametrize("content,code", [
    ('{"job": "find_colour", "colour": "red", "school": false, "refusal": "VIEW_FORBIDDEN"}', "VIEW_FORBIDDEN"),
    ('{"job": "refuse", "colour": null, "school": false, "refusal": null}', "UNSUPPORTED_CAPABILITY"),
])
def test_any_refusal_from_ollama_wins(content, code):
    plan = OllamaPlanner(send=FakeOllama(content)).plan("watch the yard")
    assert (plan.job, plan.recipe, plan.refusal, plan.source) == (None, None, code, "ollama")
    assert plan.message == message(code, "en")


@pytest.mark.parametrize("content", ["", "I think you want a counter.", '{"job": "count_people", "school": "yes"}',
                                     '{"job": "write_code"}'])
def test_a_bad_ollama_answer_is_planner_unavailable(content):
    with pytest.raises(KozError) as error:
        OllamaPlanner(send=FakeOllama(content)).plan("count people")
    assert error.value.code == "PLANNER_UNAVAILABLE"


def test_ollama_without_the_model_or_not_running_is_not_available():
    assert not OllamaPlanner(send=FakeOllama(models=("llama3:8b",))).available()
    assert not OllamaPlanner(send=FakeOllama(down=True)).available()
    assert OllamaPlanner("gemma4:e2b", send=FakeOllama(models=("gemma4:e2b:latest",))).available()


def test_ollama_talks_only_to_this_computer():
    with pytest.raises(KozError):
        OllamaPlanner(base_url="http://192.168.1.20:11434").plan("count people")
    with socket.socket() as s:   # a port nobody listens on: the real HTTP code says "not available"
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    assert not OllamaPlanner(base_url=f"http://127.0.0.1:{port}").available()


# --- the order: Nebius -> Ollama -> rules ------------------------------------------------

def nebius_choice(content):
    return lambda *a: {"choices": [{"message": {"content": content}}]}


def test_the_first_available_planner_answers():
    said = []
    nebius = NebiusPlanner("key", send=nebius_choice('{"job": "find_colour", "colour": "blue", "school": false, '
                                                     '"refusal": null}'))
    auto = AutoPlanner([nebius, OllamaPlanner(send=FakeOllama()), FakePlanner()], said.append)
    plan = auto.plan("find the ball")
    assert (plan.source, auto.last, said) == ("nebius", nebius, [])
    assert plan.recipe["blocks"][2]["settings"]["hue_center"] == 110


def test_a_failing_planner_falls_back_and_says_so():
    said = []
    ollama = OllamaPlanner(send=FakeOllama())
    auto = AutoPlanner([NebiusPlanner("key", send=failing), ollama, FakePlanner()], said.append)
    assert auto.plan("count customers in my shop").source == "ollama" and auto.last is ollama
    assert len(said) == 1 and "PLANNER_UNAVAILABLE" in said[0]


def test_without_ollama_the_rule_planner_answers():
    auto = AutoPlanner([OllamaPlanner(send=FakeOllama(down=True)), FakePlanner()], print)
    assert auto.plan("find the red ball").source == "rules"


def test_a_valid_refusal_ends_planning_without_falling_back():
    ollama = FakeOllama()
    nebius = NebiusPlanner("key", send=nebius_choice('{"job": "refuse", "colour": null, "school": false, '
                                                     '"refusal": "PROFILING_FORBIDDEN"}'))
    plan = AutoPlanner([nebius, OllamaPlanner(send=ollama), FakePlanner()], print).plan("rate my workers")
    assert (plan.refusal, plan.source) == ("PROFILING_FORBIDDEN", "nebius")
    assert not [s for s in ollama.sent if s[1] == "/api/chat"]


# --- status.planner (contract 8.1, optional) ----------------------------------------------

def test_status_carries_the_planner_only_when_reporting_is_on():
    quiet, loud = [], []
    EventLog(quiet.append).emit("status", {"state": "idle", "camera_on": False, "privacy": "unknown", "school": False,
                                           "motor": "not_present", "opencv_major": 5, "capabilities": []})
    assert "planner" not in quiet[0]["data"]   # the web doesn't accept it yet
    log = EventLog(loud.append, report_planner=True)
    status = {"state": "idle", "camera_on": False, "privacy": "unknown", "school": False,
              "motor": "not_present", "opencv_major": 5, "capabilities": []}
    log.emit("status", status)
    log.bind(new_id())
    log.set_planner("ollama")
    log.emit("status", status)
    log.bind(new_id())   # a new job: nobody has planned it yet
    log.emit("status", status)
    assert [e["data"]["planner"] for e in loud] == [None, "ollama", None]
    with pytest.raises(KozError):
        log.set_planner("gemma4:e2b")   # model names are free text: never sent


def test_the_agent_reports_who_planned_each_job():
    events = []
    log = EventLog(events.append, report_planner=True)
    setup = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME)
    agent = Agent(OllamaPlanner(send=FakeOllama('{"job": "refuse", "colour": null, "school": false, '
                                                '"refusal": "VIEW_FORBIDDEN"}')),
                  setup, lambda: pytest.fail("the camera must not open"), log,
                  models={"scene_checker": Approve(), "face_detector": FakeFaces()})
    log.bind(new_id())
    agent.run("watch the street")
    statuses = [e["data"] for e in events if e["type"] == "status"]
    assert [(s["state"], s["planner"]) for s in statuses] == [("planning", None), ("refused", "ollama")]
    assert json.loads(json.dumps(events))   # all valid JSON events
