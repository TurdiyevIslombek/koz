"""The colour finder finds only round, single-coloured things (a ball): roundness >= 0.65 is fixed in
code. Islombek asked Oct 22: "what if I write blue backpack or phone?" They were planned as a
colour job and failed three times (ADJUSTMENT_LIMIT). Now everyday things the detector knows go to
the object finder (tests/test_object_finder.py), and things no block can find (keys, a wallet,
shoes...) are refused at once by every planner (UNSUPPORTED_CAPABILITY, before any camera opens),
in Uzbek, Russian and English; balls, toys, "something red" and counting jobs still plan as before."""
import pytest

from koz.agent.planner import FakePlanner, refusal_for

NOT_FINDABLE = ["find my wallet", "where are my keys", "find my black shoes", "kalitimni top", "hamyonimni top",
                "найди мои ключи", "найди кошелёк", "find my sunglasses", "Калитимни топ"]
STILL_PLANNED = [("find the blue ball", "find_colour"), ("Tell me where the blue toy is", "find_colour"),
                 ("Qizil koptokni kuzat", "find_colour"), ("find something red", "find_colour"),
                 ("Найди красный мяч", "find_colour"), ("chase the red ball with the car", "chase_colour"),
                 ("find my blue backpack", "find_object"), ("telefonimni top", "find_object"),
                 ("watch my bag", "find_object"), ("найди красную сумку", "find_object"),
                 ("count customers carrying bags into my shop", "count_people"),
                 ("sumka bilan kirgan mijozlarni sana", "count_people"),
                 ("count people with umbrellas", "count_people")]


@pytest.mark.parametrize("text", NOT_FINDABLE)
def test_things_no_block_can_find_are_refused_before_the_camera(text):
    assert refusal_for(text) == "UNSUPPORTED_CAPABILITY"
    plan = FakePlanner().plan(text)
    assert plan.job is None and plan.refusal == "UNSUPPORTED_CAPABILITY"


@pytest.mark.parametrize("text,job", STILL_PLANNED)
def test_balls_toys_things_and_counting_still_plan(text, job):
    assert refusal_for(text) is None
    assert FakePlanner().plan(text).job == job
