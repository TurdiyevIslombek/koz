"""The colour finder finds only round, single-coloured things (a ball): roundness >= 0.65 is fixed in
code. Islombek asked Oct 22: "what if I write blue backpack or phone?" They were planned as a
colour job and failed three times (ADJUSTMENT_LIMIT). Now every planner refuses them at once
(UNSUPPORTED_CAPABILITY, before any camera opens), in Uzbek, Russian and English; balls, toys,
"something red" and counting jobs that mention bags still plan as before."""
import pytest

from koz.agent.planner import FakePlanner, refusal_for

NOT_ROUND = ["find my blue backpack", "find the phone", "track the blue backpack", "where is my red bag",
             "find the green bottle", "ko'k sumkani top", "telefonimni top", "qizil ryukzakni kuzat",
             "найди синий рюкзак", "где мой телефон", "найди красную сумку"]
STILL_PLANNED = [("find the blue ball", "find_colour"), ("Tell me where the blue toy is", "find_colour"),
                 ("Qizil koptokni kuzat", "find_colour"), ("find something red", "find_colour"),
                 ("Найди красный мяч", "find_colour"), ("chase the red ball with the car", "chase_colour"),
                 ("count customers carrying bags into my shop", "count_people"),
                 ("sumka bilan kirgan mijozlarni sana", "count_people")]


@pytest.mark.parametrize("text", NOT_ROUND)
def test_things_that_are_not_round_are_refused_before_the_camera(text):
    assert refusal_for(text) == "UNSUPPORTED_CAPABILITY"
    plan = FakePlanner().plan(text)
    assert plan.job is None and plan.refusal == "UNSUPPORTED_CAPABILITY"


@pytest.mark.parametrize("text,job", STILL_PLANNED)
def test_balls_toys_and_counting_still_plan(text, job):
    assert refusal_for(text) is None
    assert FakePlanner().plan(text).job == job
