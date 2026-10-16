"""The agent loop (koz/agent/): words -> plan -> try -> check -> adjust -> run.

Every test uses FakePlanner (rules, no network) or NebiusPlanner with a fake network, and
fake guard / face / person models, so they are fast and deterministic. The colour finder
and the tuner are the real OpenCV code, on recorded clips."""
import json

import numpy as np
import pytest
from helpers import (FULL_FRAME, GREEN, ORANGE_RED, RED, Approve, EndlessCamera, FakeClock, FakeFaces, Refuse,
                     ScriptedPeople, TickingCamera, record_ball_clip)

from koz import policy
from koz.agent import Agent, ChainLog, FakePlanner, NebiusPlanner, make_planner
from koz.agent import loop as agent_loop
from koz.agent.choose import load_env
from koz.agent.menu import parse_choice
from koz.agent.planner import HUES, language_of
from koz.capture import FileCamera
from koz.errors import KozError
from koz.events import EventLog
from koz.local_setup import LocalSetup
from koz.messages import message
from koz.recipe import check_recipe

SETUP = LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME)

# 3 jobs x 3 languages: (sentence, language, job, school, colour)
JOBS = [
    ("Find the red ball", "en", "find_colour", False, "red"),
    ("Найди красный мяч", "ru", "find_colour", False, "red"),
    ("Qizil koptokni top", "uz", "find_colour", False, "red"),
    ("Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir", "uz", "count_people", True, None),
    ("Count the students entering my class and blur faces", "en", "count_people", True, None),
    ("Посчитай учеников, которые входят в класс, и размой лица", "ru", "count_people", True, None),
    ("Count customers coming into my shop", "en", "count_people", False, None),
    ("Посчитай покупателей, которые заходят в магазин", "ru", "count_people", False, None),
    ("Do'konimga kirgan mijozlarni sana", "uz", "count_people", False, None),
]

# Refused before any camera opens: (sentence, code)
REFUSALS = [
    ("Who is this man at my door? Recognise his face", "IDENTITY_FORBIDDEN"),
    ("Yashirin kamera qilib qo'shnimning hovlisini kuzat", "VIEW_FORBIDDEN"),
    ("Определи возраст и пол покупателей", "PROFILING_FORBIDDEN"),
]


@pytest.fixture(scope="module")
def clips(tmp_path_factory):
    folder = tmp_path_factory.mktemp("agent")
    return {"red": record_ball_clip(folder / "red.avi", RED),
            "orange_red": record_ball_clip(folder / "orange_red.avi", ORANGE_RED),
            "green": record_ball_clip(folder / "green.avi", GREEN),
            "empty": record_ball_clip(folder / "empty.avi", ball=False)}


class Run:
    """One agent with a fake clock, the events it sent, and how often it opened the camera."""

    def __init__(self, camera_factory=None, planner=None, setup=SETUP, guard=None, people=None,
                 eval_seconds=2.0, **agent_args):
        self.clock, self.events, self.opened = FakeClock(), [], 0
        self.log = EventLog(self.events.append, wall_clock=lambda: 1.76e9)
        models = {"scene_checker": guard or Approve(), "face_detector": FakeFaces()}
        if people is not None:
            models["person_detector"] = people
        self.camera_factory = camera_factory
        self.agent = Agent(planner or FakePlanner(), setup, self._open, self.log, clock=self.clock,
                           eval_seconds=eval_seconds, models=models, **agent_args)

    def _open(self):
        self.opened += 1
        self.camera = self.camera_factory(self.clock)
        return self.camera

    def of(self, kind):
        return [e for e in self.events if e["type"] == kind]


def clip_camera(path):
    return lambda clock: TickingCamera(FileCamera(path, clock), clock, 0.1)


def endless(clock):
    image = np.full((240, 320, 3), 128, np.uint8)
    return EndlessCamera(image, clock)


def walking_people():
    from helpers import walker
    return ScriptedPeople([[box] for box in walker(260, 60, 400)])


# --- 1. the planner: 3 jobs x 3 languages ------------------------------------------------

@pytest.mark.parametrize("sentence,language,job,school,colour", JOBS)
def test_planner_turns_each_job_into_a_checked_recipe_in_its_language(sentence, language, job, school, colour):
    plan = FakePlanner().plan(sentence)
    assert (plan.language, plan.job, plan.refusal) == (language, job, None)
    checked = check_recipe(plan.recipe)          # passes contracts/recipe.schema.json and every rule
    assert checked.data["language"] == language
    assert checked.data["privacy"]["school"] is school
    assert [b["type"] for b in checked.data["blocks"][:2]] == ["privacy_guard", "face_blur"]
    types = [b["type"] for b in checked.data["blocks"][2:]]
    if job == "find_colour":
        assert types == ["color_finder"] and checked.data["blocks"][2]["settings"]["hue_center"] == HUES[colour]
    else:
        assert types == ["person_detector", "line_counter"]
    # The plain-language plan is in the same language as the sentence.
    words = {"en": "I will", "ru": "Я ", "uz": "man"}
    assert words[language] in plan.message
    assert language_of(plan.message) == language


@pytest.mark.parametrize("sentence,language,job,school,colour", JOBS)
def test_each_job_runs_end_to_end_and_passes_its_check(clips, sentence, language, job, school, colour):
    people = walking_people() if job == "count_people" else None
    run = Run(clip_camera(clips["red"]) if job == "find_colour" else endless, people=people)
    result = run.agent.run(sentence)
    assert result.state == "running" and result.code is None
    assert result.decisions[-1]["next"] == "run" and result.decisions[-1]["result"] == "pass"
    assert result.decisions[-1]["check"] == ("target_visible" if job == "find_colour" else "counts_available")
    assert [r["data"]["origin"] for r in run.of("recipe")] == ["planner"]
    assert run.of("status")[-1]["data"]["state"] == "running"
    result.runner.stop()
    assert run.camera.is_open is False


# --- 2. refusals: before any camera opens ----------------------------------------------

@pytest.mark.parametrize("sentence,code", REFUSALS)
def test_forbidden_requests_are_refused_before_the_camera_opens(sentence, code):
    run = Run(lambda clock: pytest.fail("the camera must not open"))
    result = run.agent.run(sentence)
    assert (result.state, result.code, run.opened) == ("refused", code, 0)
    assert result.plan.message == message(code, result.plan.language)   # the contract's fixed text
    assert [e["type"] for e in run.events] == ["status", "fault", "status"]
    assert run.of("fault")[0]["data"] == {"code": code, "effect": "off"}
    assert run.of("status")[-1]["data"]["state"] == "refused"


def test_nebius_never_receives_a_forbidden_request():
    sent = []
    planner = NebiusPlanner("key", send=lambda *a: sent.append(a) or pytest.fail("sent"))
    for sentence, code in REFUSALS:
        assert planner.plan(sentence).refusal == code
    assert sent == []


def test_a_recipe_that_breaks_a_rule_is_refused_before_the_camera_opens():
    recipe = FakePlanner().plan("find the red ball").recipe
    recipe["blocks"] = recipe["blocks"][1:]   # no privacy guard
    run = Run(lambda clock: pytest.fail("the camera must not open"))
    result = run.agent.run_recipe(recipe)
    assert (result.state, result.code, run.opened) == ("refused", "SAFETY_LOCKED", 0)


def test_no_ownership_means_no_camera():
    setup = LocalSetup(owner_confirmed=False, allowed_area=FULL_FRAME)
    run = Run(lambda clock: pytest.fail("the camera must not open"), setup=setup)
    assert run.agent.run("find the red ball").code == "OWNERSHIP_REQUIRED" and run.opened == 0


# --- 3./4. check and adjust: the evidence chain ------------------------------------------

def test_wrong_hue_is_fixed_from_what_opencv_measured(clips):
    """The planner asks for red (hue 0); on this clip the ball looks orange-red (hue 13).
    Round 1 finds nothing, the tuner measures the ball's hue, round 2 finds it, and it runs."""
    run = Run(clip_camera(clips["orange_red"]))
    result = run.agent.run("find the red ball")
    assert result.state == "running"
    first, second = result.decisions
    assert (first["round"], first["result"], first["next"], first["next_revision"]) == (1, "fail", "adjust", 2)
    assert first["change"]["setting"] == "color_finder.hue_center"
    assert first["change"]["before"] == 0 and 10 <= first["change"]["after"] <= 16
    assert (second["round"], second["result"], second["next"]) == (2, "pass", "run")

    # The chain the dashboard checks (contract section 9), in seq order.
    by_seq = {e["seq"]: e for e in run.events}
    decision = next(e for e in run.of("decision") if e["data"]["next"] == "adjust")
    evidence = [by_seq[s] for s in decision["data"]["evidence_seq"]]
    assert all(e["type"] == "observation" and e["revision"] == 1 and e["data"]["round"] == 1
               and e["data"]["target"] == "lost" and e["seq"] < decision["seq"] for e in evidence)
    new_recipe = next(e for e in run.of("recipe") if e["data"]["origin"] == "adjustment")
    assert new_recipe["revision"] == 2 and new_recipe["data"]["caused_by"] == decision["seq"]
    old_recipe = run.of("recipe")[0]["data"]["recipe"]
    expected = json.loads(json.dumps(old_recipe))
    expected["blocks"][2]["settings"]["hue_center"] = first["change"]["after"]
    assert new_recipe["data"]["recipe"] == expected   # exactly one setting changed
    installed = next(e for e in run.of("status") if e["revision"] == 2 and e["data"]["state"] == "evaluating")
    after = next(e for e in run.of("observation") if e["revision"] == 2 and e["seq"] > installed["seq"])
    assert new_recipe["seq"] < installed["seq"] < after["seq"]
    assert after["data"]["target"] in ("left", "center", "right") and after["data"]["round"] == 2

    assert result.agent_changes == [{"from_revision": 1, "to_revision": 2, "check": "target_visible",
                                     "before_label": "lost", "change": first["change"], "executed": True,
                                     "after_label": result.agent_changes[0]["after_label"],
                                     "after_result": "pass"}]
    result.runner.stop()


def test_chain_log_prints_one_line_per_step(clips):
    lines = []
    chain = ChainLog()
    run = Run(clip_camera(clips["orange_red"]))
    run.log.listeners.append(lambda e: lines.append(chain(e)))
    run.agent.run("find the red ball").runner.stop()
    text = "\n".join(line for line in lines if line)
    assert "decide    round 1: target_visible fail" in text and "-> adjust: color_finder.hue_center 0 ->" in text
    assert "revision 2 from the adjustment, because of decision #" in text
    assert "decide    round 2: target_visible pass" in text


def test_no_fix_from_the_numbers_stops_with_check_failed(clips):
    """Nothing coloured at all: lower saturation once, then there is no allowed fix left."""
    run = Run(clip_camera(clips["empty"]))
    result = run.agent.run("find the red ball")
    assert (result.state, result.code) == ("held", "CHECK_FAILED")
    assert [d["next"] for d in result.decisions] == ["adjust", "stop"]
    assert result.decisions[0]["change"] == {"setting": "color_finder.saturation_min", "before": 120, "after": 80}
    assert run.of("fault")[-1]["data"] == {"code": "CHECK_FAILED", "effect": "held"}
    assert run.of("status")[-1]["data"]["state"] == "held" and run.camera.is_open is False


def test_three_failed_rounds_stop_with_adjustment_limit(clips, monkeypatch):
    """A tuner whose changes never help: 3 rounds at most, then the job stays off."""
    def useless(recipe, check, frames):
        hue = recipe["blocks"][2]["settings"]["hue_center"]
        return {"setting": "color_finder.hue_center", "before": hue, "after": hue + 5}

    monkeypatch.setattr(agent_loop.tuner, "propose", useless)
    run = Run(clip_camera(clips["green"]), eval_seconds=1.0)
    result = run.agent.run("find the red ball")
    assert (result.state, result.code) == ("held", "ADJUSTMENT_LIMIT")
    assert [(d["round"], d["next"]) for d in result.decisions] == [(1, "adjust"), (2, "adjust"), (3, "stop")]
    assert [r["revision"] for r in run.of("recipe")] == [1, 2, 3]
    assert len(result.agent_changes) == 2
    assert run.of("status")[-1]["data"]["state"] == "held"


def test_a_privacy_stop_is_never_adjusted(clips):
    run = Run(clip_camera(clips["red"]), guard=Refuse("PRIVATE_BATHROOM"))
    result = run.agent.run("find the red ball")
    assert (result.state, result.code) == ("refused", "PRIVATE_BATHROOM")
    assert [r["data"]["origin"] for r in run.of("recipe")] == ["planner"]   # no new revision
    assert result.decisions == [{"round": 1, "evidence_seq": result.decisions[0]["evidence_seq"],
                                 "check": "privacy_approved", "result": "fail", "next": "stop",
                                 "next_revision": None, "change": None, "code": "PRIVATE_BATHROOM"}]


def test_a_tuner_change_that_breaks_a_rule_is_never_tried(clips, monkeypatch):
    monkeypatch.setattr(agent_loop.tuner, "propose", lambda recipe, check, frames: {
        "setting": "color_finder.hue_center", "before": 0, "after": 500})   # outside the schema's range
    run = Run(clip_camera(clips["green"]))
    result = run.agent.run("find the red ball")
    assert (result.state, result.code) == ("held", "CHECK_FAILED")
    assert len(run.of("recipe")) == 1 and result.decisions[-1]["next"] == "stop"


def test_stop_during_evaluation_closes_the_camera_and_goes_idle():
    seen = []

    def on_frame(runner):
        seen.append(runner)
        if len(seen) == 3:
            run.agent.stop_requested = True

    run = Run(endless, on_frame=on_frame)
    result = run.agent.run("find the red ball")
    assert (result.state, result.code, result.decisions) == ("idle", None, [])
    assert run.camera.is_open is False and run.of("status")[-1]["data"]["state"] == "idle"


def test_a_plan_that_arrives_after_stop_never_starts_the_job():
    class SlowPlanner:
        def plan(self, text):
            run.agent.stop_requested = True   # stop_job arrives while the planner thinks
            return FakePlanner().plan(text)

    run = Run(lambda clock: pytest.fail("the camera must not open"), planner=SlowPlanner())
    assert run.agent.run("find the red ball").state == "idle" and run.opened == 0


def test_evaluation_uses_the_policy_limits():
    assert policy.AGENT_MAX_ROUNDS == 3 and 0 < policy.AGENT_EVAL_S <= 10   # contract section 9


# --- 5. NebiusPlanner (fake network) and the fallback --------------------------------------

def nebius_reply(content):
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def test_nebius_planner_picks_from_the_menu_and_ko_z_builds_the_recipe():
    sent = []

    def send(method, path, body):
        sent.append((method, path, body))
        return nebius_reply('Thinking about it {not json}... {"job": "count_people", "colour": null, '
                            '"school": true, "refusal": null, "message": "I will film everyone"}')

    plan = NebiusPlanner("secret-key", send=send).plan("Sinfga kirgan o'quvchilarni sana")
    assert (plan.job, plan.language, plan.recipe["privacy"]["school"]) == ("count_people", "uz", True)
    check_recipe(plan.recipe)
    assert "film everyone" not in plan.message   # the owner reads only fixed templates
    (method, path, body), = sent
    assert (method, path, body["model"]) == ("POST", "/chat/completions", "nvidia/nemotron-3-super-120b-a12b")
    assert body["messages"][1] == {"role": "user", "content": "Sinfga kirgan o'quvchilarni sana"}
    assert "secret-key" not in json.dumps(body)   # the key goes only in the Authorization header


@pytest.mark.parametrize("content", [
    "no json here", '{"job": "write_code"}', '{"job": "find_colour", "colour": "infrared"}',
    '{"job": "find_colour", "job": "refuse"}', '{"job": "count_people", "recipe": {"blocks": []}}'])
def test_a_bad_planner_answer_is_planner_unavailable_and_nothing_runs(content):
    planner = NebiusPlanner("key", send=lambda *a: nebius_reply(content))
    run = Run(lambda clock: pytest.fail("the camera must not open"), planner=planner)
    result = run.agent.run("find the ball")
    assert (result.state, result.code, run.opened) == ("refused", "PLANNER_UNAVAILABLE", 0)


def test_nebius_refusal_uses_the_contract_message():
    planner = NebiusPlanner("key", send=lambda *a: nebius_reply(
        '{"job": "refuse", "colour": null, "school": false, "refusal": "PROFILING_FORBIDDEN"}'))
    plan = planner.plan("Tell me which workers are tired")
    assert plan.refusal == "PROFILING_FORBIDDEN" and plan.message == message("PROFILING_FORBIDDEN", "en")


def test_without_a_key_the_rule_planner_is_the_default():
    """Gemma on this Mac got 14/20 on Oct 15 (docs/TRIALS.md): only on request (--planner ollama)."""
    assert isinstance(make_planner(env={}), FakePlanner)
    assert isinstance(make_planner("rules", env={}), FakePlanner)
    assert [p.source for p in make_planner(env={"NEBIUS_API_KEY": "k"}).planners] == ["nebius", "rules"]
    assert make_planner(env={"NEBIUS_API_KEY": "k", "NEBIUS_MODEL": "nvidia/x"}).planners[0].model == "nvidia/x"
    ollama = make_planner("ollama", env={})
    assert [p.source for p in ollama.planners] == ["ollama", "rules"]
    ollama.planners[0]._send = lambda *a, **k: (_ for _ in ()).throw(KozError("PLANNER_UNAVAILABLE"))
    assert ollama.plan("find the red ball").source == "rules"   # Ollama not running: the rules answer


# Uzbek in Cyrillic (new sentences, not the 20 measured ones): read as Uzbek Latin too.
CYRILLIC_UZBEK = [
    ("Кўк коптокни топ", ("find_colour", 110)),
    ("Бинафша рангли нарсани изла", ("find_colour", 140)),
    ("Мижозларни сана", ("count_people", False)),
    ("Дарсга кирган ўқувчиларни санаб бер", ("count_people", True)),
    ("Яширин камера қилиб қўйгин", ("refuse", "VIEW_FORBIDDEN")),
    ("Ким кирганини таниб бер", ("refuse", "IDENTITY_FORBIDDEN")),
    ("Ёшини ва жинсини аниқла", ("refuse", "PROFILING_FORBIDDEN")),
    ("Ҳожатхонадаги одамларни сана", ("refuse", "PRIVATE_TOILET")),
]


@pytest.mark.parametrize("sentence,expected", CYRILLIC_UZBEK)
def test_uzbek_in_cyrillic_is_planned_and_refused_like_latin(sentence, expected):
    plan = FakePlanner().plan(sentence)
    assert plan.language == "uz"
    if expected[0] == "refuse":
        assert plan.refusal == expected[1]
    elif expected[0] == "find_colour":
        assert (plan.job, plan.recipe["blocks"][2]["settings"]["hue_center"]) == expected
    else:
        assert (plan.job, plan.recipe["privacy"]["school"]) == expected


def test_reading_russian_as_uzbek_latin_adds_no_wrong_jobs():
    for sentence, language, job, school, colour in JOBS:
        plan = FakePlanner().plan(sentence)
        assert (plan.language, plan.job) == (language, job)


def test_env_file_is_read_without_printing(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("# comment\nNEBIUS_API_KEY='abc'\nNEBIUS_MODEL = nvidia/m\n", encoding="utf-8")
    assert load_env(env) == {"NEBIUS_API_KEY": "abc", "NEBIUS_MODEL": "nvidia/m"}
    assert load_env(tmp_path / "missing") == {}
    assert "abc" not in capsys.readouterr().out


def test_parse_choice_takes_the_last_choice_after_thinking():
    content = '<think>{"job": "refuse"}</think> maybe {"job": "find_colour"} final: ' \
              '{"job": "find_colour", "colour": "blue", "school": false, "refusal": null}'
    assert parse_choice(content)["colour"] == "blue"
    with pytest.raises(ValueError):
        parse_choice('{"job": "find_colour", "colour": "red", "extra": 1}')


def test_nebius_network_failure_is_planner_unavailable():
    planner = NebiusPlanner("key", base_url="http://api.tokenfactory.nebius.com/v1")   # not https
    with pytest.raises(KozError) as error:
        planner.plan("find the red ball")
    assert error.value.code == "PLANNER_UNAVAILABLE"


# --- found in Codex's review (Oct 15) -----------------------------------------------------

def test_a_stopped_import_never_opens_the_camera():
    run = Run(lambda clock: pytest.fail("the camera must not open"))
    run.agent.stop_requested = True
    result = run.agent.run_recipe(FakePlanner().plan("find the red ball").recipe)
    assert (result.state, run.opened) == ("idle", 0)


def test_a_planner_failure_after_stop_stays_idle():
    class FailingAfterStop:
        def plan(self, text):
            run.agent.stop_requested = True
            raise KozError("PLANNER_UNAVAILABLE")

    run = Run(lambda clock: pytest.fail("the camera must not open"), planner=FailingAfterStop())
    assert run.agent.run("find the red ball").state == "idle"
    assert run.of("status")[-1]["data"]["state"] == "idle" and not run.of("fault")


def test_a_planner_refusal_wins_over_a_job_in_the_same_answer():
    planner = NebiusPlanner("key", send=lambda *a: nebius_reply(
        '{"job": "count_people", "colour": null, "school": false, "refusal": "PROFILING_FORBIDDEN"}'))
    plan = planner.plan("count the workers")
    assert (plan.job, plan.recipe, plan.refusal) == (None, None, "PROFILING_FORBIDDEN")


def test_judge_uses_only_what_it_cites_and_mostly_unknown_is_unknown():
    seen = {"privacy": "approved", "target": "center"}
    gone = {"privacy": "approved", "target": "unknown"}
    assert agent_loop.judge("find_colour", [seen] * 4 + [gone] * 6)[1] == "unknown"
    assert agent_loop.judge("find_colour", [seen] * 5 + [gone] * 5)[1] == "pass"


def test_normal_running_starts_its_line_counts_at_zero():
    """Someone crosses during the evaluation round: that crossing must not count in the job."""
    from helpers import walker
    crossing = [[b] for b in walker(560, 80, 15, y=240)] + [[]] * 400   # in during round 1 (640 px wide), then nobody
    run = Run(endless, people=ScriptedPeople(crossing))
    result = run.agent.run("Count customers coming into my shop")
    assert result.state == "running"
    evaluating = [o for o in run.of("observation") if o["data"]["round"] == 1]
    assert evaluating[-1]["data"]["entered"]["value"] == 1
    result.runner.step()
    first = next(o for o in run.of("observation") if o["data"]["round"] is None)
    assert first["data"]["entered"] == {"state": "known", "value": 0, "reason": None}
    assert first["data"]["coverage"] == "complete"
    result.runner.stop()


def test_islombeks_sentences_are_planned_and_every_refusal_is_a_rule():
    """tests/fixtures/sentences_islombek.txt (Oct 16). The rule planner was TUNED on this set after
    scoring it (docs/TRIALS.md), so this only guards against going backwards; it is not a fair score."""
    import importlib.util
    from pathlib import Path
    script = Path(__file__).resolve().parent.parent / "scripts" / "score_sentences.py"
    spec = importlib.util.spec_from_file_location("score_sentences", script)
    score = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(score)
    rows = score.score(Path(__file__).parent / "fixtures" / "sentences_islombek.txt")
    assert len(rows) == 20
    assert [s for s, expected, got, *_ in rows if got != expected] == []
    assert [s for s, _, _, plan, by_rule, _ in rows if plan.refusal and not by_rule] == []
