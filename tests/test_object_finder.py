"""object_finder (Islombek, Oct 22: "track a silver phone", "a blue backpack"): one kind of everyday
thing, found with the same NanoDet-Plus model on OpenCV 5 that counts people (COCO classes),
optionally of one colour, reported like color_finder: left / center / right / lost. On this
computer only. People and animals are never objects (rules 4 and 11); beds, toilets and sinks are
the privacy guard's; only a ball (color_finder) can steer the car."""
import numpy as np
import pytest
from helpers import FULL_FRAME, Approve, EndlessCamera, FakeClock, FakeFaces

from koz.agent import Agent, FakePlanner
from koz.agent.planner import refusal_for
from koz.blocks import Detection
from koz.blocks.object_finder import OBJECTS, ObjectFinder, colour_matches
from koz.errors import KozError
from koz.events import EventLog
from koz.local_setup import LocalSetup
from koz.recipe import check_recipe

PHONE, BACKPACK = OBJECTS["cell phone"], OBJECTS["backpack"]


class FakeObjects:
    """detect(image, classes, min_confidence) like NanoDet: the scripted detections of those classes."""

    def __init__(self, detections):
        self.detections, self.asked = detections, []

    def detect(self, image, classes, min_confidence):
        self.asked.append((tuple(classes), min_confidence))
        return [d for d in self.detections if d.class_id in classes and d.score >= min_confidence]


def scene(colour=None, box=None):
    image = np.full((240, 320, 3), 128, np.uint8)
    if box is not None:
        x0, y0, x1, y1 = box
        image[y0:y1, x0:x1] = colour
    return image


def settings(obj="cell phone", colour="any", min_confidence=0.45):
    return {"object": obj, "colour": colour, "min_confidence": min_confidence}


@pytest.mark.parametrize("x0,label", [(10, "left"), (140, "center"), (250, "right")])
def test_it_says_where_the_thing_is(x0, label):
    finder = ObjectFinder(settings(), detector=FakeObjects([Detection(PHONE, (x0, 80, x0 + 40, 160), 0.8)]))
    target = finder.find(scene())
    assert target.label == label and 0 < target.area_ratio < 1


def test_only_that_kind_of_thing_and_only_confident_answers():
    detector = FakeObjects([Detection(BACKPACK, (140, 80, 180, 160), 0.9), Detection(PHONE, (10, 80, 50, 160), 0.3)])
    finder = ObjectFinder(settings(min_confidence=0.45), detector=detector)
    assert finder.find(scene()).label == "lost"          # a backpack is not a phone; the phone is unsure
    assert detector.asked[-1] == ((PHONE,), 0.45)


def test_the_colour_must_match_when_asked():
    blue, red = (200, 60, 30), (30, 30, 200)              # BGR
    box = (140, 80, 200, 170)
    detector = FakeObjects([Detection(BACKPACK, box, 0.9)])
    assert ObjectFinder(settings("backpack", "blue"), detector=detector).find(scene(blue, box)).label == "center"
    assert ObjectFinder(settings("backpack", "blue"), detector=detector).find(scene(red, box)).label == "lost"
    assert ObjectFinder(settings("backpack", "any"), detector=detector).find(scene(red, box)).label == "center"
    silver = (175, 175, 175)
    assert colour_matches(scene(silver, box), box, "grey") and not colour_matches(scene(silver, box), box, "red")


def test_people_animals_and_the_guards_things_are_never_objects():
    assert 0 not in OBJECTS.values()                              # person
    assert not set(range(14, 24)) & set(OBJECTS.values())         # bird, cat, dog, horse, ... giraffe
    assert not {59, 61, 71} & set(OBJECTS.values())               # bed, toilet, sink: the privacy guard's


@pytest.mark.parametrize("text,obj,colour", [
    ("find my blue backpack", "backpack", "blue"), ("track a silver phone", "cell phone", "grey"),
    ("find the phone", "cell phone", "any"), ("telefonimni top", "cell phone", "any"),
    ("ko'k ryukzakni kuzat", "backpack", "blue"), ("найди синий рюкзак", "backpack", "blue"),
    ("где мой телефон", "cell phone", "any"), ("find the green bottle", "bottle", "green"),
    ("qizil sumkani top", "handbag", "red")])
def test_the_planner_turns_things_into_an_object_job(text, obj, colour):
    plan = FakePlanner().plan(text)
    assert plan.job == "find_object" and plan.refusal is None
    finder = next(b for b in plan.recipe["blocks"] if b["type"] == "object_finder")
    assert finder["settings"]["object"] == obj and finder["settings"]["colour"] == colour
    check_recipe(plan.recipe)                                      # every rule still holds


@pytest.mark.parametrize("text", ["find my wallet", "where are my keys", "find my shoes", "chase the bottle with the car",
                                  "drive the car to my backpack"])
def test_things_koz_cannot_find_and_the_car_following_things_are_refused(text):
    assert refusal_for(text) is not None or FakePlanner().plan(text).refusal is not None
    assert FakePlanner().plan(text).job is None


def test_balls_stay_with_the_colour_finder():
    assert FakePlanner().plan("find the red ball").job == "find_colour"
    assert FakePlanner().plan("chase the red ball with the car").job == "chase_colour"


def test_an_object_cannot_steer_the_car_and_a_wrong_name_is_refused():
    plan = FakePlanner().plan("find the phone")
    car = dict(plan.recipe, brain={"type": "flybrain", "settings": {"turn_gain": 1.0, "deadband": 0.1}},
               actions=[{"type": "dashboard"}, {"type": "motors", "max_speed_ratio": 0.25}])   # valid but for rule 11
    with pytest.raises(KozError):
        check_recipe(car)
    wrong = dict(plan.recipe, blocks=[*plan.recipe["blocks"][:2], {"type": "object_finder", "settings": settings("person")}])
    with pytest.raises(KozError):
        check_recipe(wrong)


def run_agent(detections):
    clock, events = FakeClock(), []
    agent = Agent(FakePlanner(), LocalSetup(owner_confirmed=True, allowed_area=FULL_FRAME),
                  lambda: EndlessCamera(scene(), clock), EventLog(events.append), clock=clock, eval_seconds=2.0,
                  models={"scene_checker": Approve(), "face_detector": FakeFaces(),
                          "object_detector": FakeObjects(detections)})
    return agent.run("find the phone"), events


def test_a_phone_in_view_passes_and_runs():
    result, events = run_agent([Detection(PHONE, (500, 160, 580, 320), 0.8)])   # the runner works at 640x480
    assert result.state == "running" and result.decisions[-1]["result"] == "pass"
    assert [e["data"]["target"] for e in events if e["type"] == "observation"][-1] == "right"
    result.runner.stop()


def test_no_phone_in_view_runs_and_waits():
    result, events = run_agent([])
    assert (result.state, result.code) == ("running", None)
    assert [(d["result"], d["next"]) for d in result.decisions] == [("unknown", "run")]
    result.runner.stop()


def test_an_ai_planner_can_choose_a_thing_but_only_from_the_menu():
    from koz.agent.menu import parse_choice, plan_from_choice
    choice = parse_choice('{"job": "find_object", "colour": "grey", "object": "cell phone", "school": false, "refusal": null}')
    plan = plan_from_choice("track my silver phone", choice, "nebius")
    assert plan.job == "find_object" and plan.source == "nebius"
    check_recipe(plan.recipe)
    for bad in ['{"job": "find_object", "colour": "red", "object": null, "school": false, "refusal": null}',
                '{"job": "find_object", "colour": "red", "object": "person", "school": false, "refusal": null}',
                '{"job": "find_object", "colour": "red", "object": "dog", "school": false, "refusal": null}',
                '{"job": "find_colour", "colour": "grey", "object": null, "school": false, "refusal": null}']:
        with pytest.raises(ValueError):
            parse_choice(bad)


def test_the_schema_the_block_and_the_planner_name_the_same_things():
    import json
    from pathlib import Path

    from koz.agent.planner import OBJECT_WORDS, OBJECTS as PLANNER_OBJECTS
    schema = json.loads((Path(__file__).resolve().parent.parent / "contracts" / "recipe.schema.json").read_text())
    assert schema["$defs"]["object_finder"]["properties"]["settings"]["properties"]["object"]["enum"] == list(OBJECTS)
    assert set(OBJECT_WORDS) == {name for name, _ in PLANNER_OBJECTS} <= set(OBJECTS)


def test_a_thing_never_stands_in_for_the_cars_ball():
    """Codex review, Oct 22: with both finders, a phone in the middle passed the car's check while the
    ball was lost. A recipe now holds one finder at most."""
    from koz.agent.planner import chase_recipe, colour_recipe, object_recipe
    thing = object_recipe("cell phone", "any", "en")["blocks"][2]
    for recipe in (chase_recipe("red", "en"), colour_recipe("red", "en")):
        recipe["blocks"].append(thing)
        with pytest.raises(KozError):
            check_recipe(recipe)


def test_an_ai_planners_school_answer_is_kept_and_refused():
    """Codex review, Oct 22: a model's "school": true was dropped for a thing job."""
    from koz.agent.menu import parse_choice, plan_from_choice
    for job, extra in (("find_object", '"object": "backpack", "colour": null'), ("find_colour", '"object": null, "colour": "red"')):
        choice = parse_choice(f'{{"job": "{job}", {extra}, "school": true, "refusal": null}}')
        with pytest.raises(KozError) as error:
            check_recipe(plan_from_choice("find it in my class", choice, "nebius").recipe)
        assert error.value.code == "SCHOOL_COUNTS_ONLY"
