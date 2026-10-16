"""BedrockPlanner (koz/agent/bedrock.py): same safety as the other AI planners; fake network only."""
import json

import pytest

from koz.agent import BedrockPlanner, FakePlanner, make_planner
from koz.agent.bedrock import DEFAULT_MODEL
from koz.errors import KozError
from koz.events import EventLog
from koz.messages import message
from koz.recipe import check_recipe

KEY = "bedrock-api-key-for-tests"


class FakeBedrock:
    """Answers like Bedrock Runtime's Converse, and keeps what it was sent."""

    def __init__(self, text='{"job": "count_people", "colour": null, "school": true, "refusal": null}', fail=False):
        self.text, self.fail, self.sent = text, fail, []

    def __call__(self, path, body):
        if self.fail:
            raise KozError("PLANNER_UNAVAILABLE")
        self.sent.append((path, body))
        return {"output": {"message": {"role": "assistant", "content": [{"text": self.text}]}},
                "stopReason": "end_turn", "usage": {"inputTokens": 400, "outputTokens": 20}}


def test_bedrock_picks_from_the_menu_and_ko_z_builds_the_recipe():
    fake = FakeBedrock()
    plan = BedrockPlanner(KEY, send=fake).plan("Sinfga kirgan o'quvchilarni sana")
    assert (plan.job, plan.language, plan.source, plan.recipe["privacy"]["school"]) == ("count_people", "uz", "bedrock", True)
    check_recipe(plan.recipe)
    path, body = fake.sent[0]
    assert path == "/model/eu.amazon.nova-2-lite-v1%3A0/converse" and DEFAULT_MODEL == "eu.amazon.nova-2-lite-v1:0"
    assert body["messages"] == [{"role": "user", "content": [{"text": "Sinfga kirgan o'quvchilarni sana"}]}]
    assert body["inferenceConfig"] == {"maxTokens": 300, "temperature": 0}
    assert KEY not in json.dumps(body)            # the key goes only in the Authorization header


def test_forbidden_requests_never_reach_aws():
    fake = FakeBedrock()
    for sentence in ("Recognise who is standing at my door", "Яширин камера қилиб қўйгин", "Chase the dog"):
        assert BedrockPlanner(KEY, send=fake).plan(sentence).source == "rules"
    assert fake.sent == []


@pytest.mark.parametrize("text,code", [
    ('{"job": "chase_colour", "colour": "red", "school": false, "refusal": "MOTOR_TARGET_FORBIDDEN"}', "MOTOR_TARGET_FORBIDDEN"),
    ('{"job": "refuse", "colour": null, "school": false, "refusal": null}', "UNSUPPORTED_CAPABILITY"),
])
def test_any_refusal_from_bedrock_wins(text, code):
    plan = BedrockPlanner(KEY, send=FakeBedrock(text)).plan("go to the ball")
    assert (plan.job, plan.recipe, plan.refusal) == (None, None, code) and plan.message == message(code, "en")


@pytest.mark.parametrize("text", ["", "Sure! I would count people.", '{"job": "write_code"}',
                                  '{"job": "count_people", "school": "yes"}'])
def test_a_bad_answer_is_planner_unavailable(text):
    with pytest.raises(KozError) as error:
        BedrockPlanner(KEY, send=FakeBedrock(text)).plan("count people")
    assert error.value.code == "PLANNER_UNAVAILABLE"


def test_the_car_job_works_through_bedrock_too():
    plan = BedrockPlanner(KEY, send=FakeBedrock('{"job": "chase_colour", "colour": "green", "school": false, '
                                                '"refusal": null}')).plan("drive to the green ball")
    assert plan.job == "chase_colour" and check_recipe(plan.recipe).data["brain"]["type"] == "flybrain"


def test_bedrock_is_used_only_with_a_key_and_falls_back_to_rules():
    assert isinstance(make_planner(env={}), FakePlanner)
    auto = make_planner(env={"AWS_BEARER_TOKEN_BEDROCK": KEY})
    assert [p.source for p in auto.planners] == ["bedrock", "rules"]
    assert auto.planners[0].region == "eu-central-1"
    assert [p.source for p in make_planner(env={"AWS_BEARER_TOKEN_BEDROCK": KEY, "NEBIUS_API_KEY": "k"}).planners] == \
        ["nebius", "bedrock", "rules"]
    auto.planners[0]._send = FakeBedrock(fail=True)
    said = []
    auto.say = said.append
    assert auto.plan("find the red ball").source == "rules" and "PLANNER_UNAVAILABLE" in said[0]
    other = make_planner(env={"AWS_BEARER_TOKEN_BEDROCK": KEY, "AWS_REGION": "eu-west-1", "BEDROCK_MODEL": "eu.x"})
    assert (other.planners[0].region, other.planners[0].model) == ("eu-west-1", "eu.x")
    with pytest.raises(KozError):
        BedrockPlanner(KEY, region="eu-central-1.evil.example/")   # the region can't redirect the request


def test_status_can_say_bedrock_planned_it():
    events = []
    log = EventLog(events.append, report_planner=True)
    log.set_planner("bedrock")
    log.emit("status", {"state": "idle", "camera_on": False, "privacy": "unknown", "school": False,
                        "motor": "not_present", "opencv_major": 5, "capabilities": []})
    assert events[0]["data"]["planner"] == "bedrock"
