"""The fixed menu an AI planner chooses from (NebiusPlanner, OllamaPlanner). Same safety for both:

1. The rule planner's refusal check runs first, so a forbidden request is never sent to a model.
2. The model only picks: the job (find a colour / count people / refuse), the colour, school or not,
   and a refusal code. Anything else in its answer is ignored or makes the answer invalid.
3. Any refusal in the answer wins, even next to a job.
4. The recipe and the text the owner reads come from fixed templates (koz/agent/planner.py), and
   the recipe goes through koz.recipe like any other (CLAUDE.md rules 1 and 5). So the model can't
   write code, settings or promises.
An answer that isn't a valid choice is PLANNER_UNAVAILABLE: nothing runs."""
import json
import re

from ..errors import CODES
from .planner import HUES, Plan, chase_recipe, colour_recipe, counter_recipe, language_of, plan_message, refused

REFUSAL_CODES = {"IDENTITY_FORBIDDEN", "PROFILING_FORBIDDEN", "VIEW_FORBIDDEN", "AUDIO_FORBIDDEN",
                 "SOLE_PROTECTION_FORBIDDEN", "MOTOR_TARGET_FORBIDDEN", "ACTUATOR_FORBIDDEN",
                 "UNSUPPORTED_CAPABILITY", "PRIVATE_BATHROOM", "PRIVATE_TOILET", "PRIVATE_BEDROOM",
                 "PRIVATE_CHANGING_ROOM"}
JOBS = ("find_colour", "chase_colour", "count_people", "refuse")
SYSTEM = f"""You set up Ko'z, a privacy-first camera. Read the owner's request (Uzbek, Russian or English)
and reply with ONE JSON object and nothing else:
{{"job": "find_colour" | "chase_colour" | "count_people" | "refuse",
 "colour": {" | ".join(f'"{c}"' for c in HUES)} | null,
 "school": true | false,
 "refusal": null | one of {sorted(REFUSAL_CODES)}}}
Ko'z can only: find one coloured object and say if it is left, center or right ("find_colour");
drive the owner's robot car toward one coloured ball with its fruit-fly brain ("chase_colour");
or count people crossing a line in the middle of the view ("count_people"; "school": true for
classes and pupils). Faces are always blurred and nothing is saved. Refuse ("job": "refuse") anything
else, and always refuse: identifying or following a person, number plates, guessing age, gender,
emotion or ethnicity, judging people, hidden cameras, sound, bathrooms, toilets, bedrooms, changing
rooms, being the only protection for a child, and robots chasing or hitting people or animals."""

# The same menu as a JSON schema, for models that can be held to one (Ollama "format").
CHOICE_SCHEMA = {
    "type": "object",
    "properties": {"job": {"enum": list(JOBS)}, "colour": {"enum": [*HUES, None]},
                   "school": {"type": "boolean"}, "refusal": {"enum": [*sorted(REFUSAL_CODES), None]}},
    "required": ["job", "colour", "school", "refusal"],
    "additionalProperties": False,
}


def _no_duplicates(pairs):
    if len({k for k, _ in pairs}) != len(pairs):
        raise ValueError("duplicate key")
    return dict(pairs)


def parse_choice(content):
    """The model's JSON choice, strictly checked; anything else raises ValueError.
    A reasoning model may think first (sometimes inside <think>...</think>): the last JSON
    object in the answer is the choice."""
    if type(content) is not str:
        raise ValueError("no text")
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    decoder, objects = json.JSONDecoder(object_pairs_hook=_no_duplicates), []
    for start in (m.start() for m in re.finditer(r"\{", content)):
        try:
            objects.append(decoder.raw_decode(content, start)[0])
        except ValueError:
            continue
    choices = [o for o in objects if type(o) is dict and "job" in o]
    if not choices:
        raise ValueError("no JSON choice")
    choice = choices[-1]
    if (set(choice) - {"job", "colour", "school", "refusal", "message"}
            or choice.get("job") not in JOBS
            or choice.get("colour") not in (None, *HUES) or type(choice.get("school", False)) is not bool
            or (choice.get("refusal") is not None and choice.get("refusal") not in CODES)):
        raise ValueError("not a valid choice")
    # Any "message" the model adds anyway is ignored: the owner reads only fixed templates.
    return {"job": choice["job"], "colour": choice.get("colour"), "school": choice.get("school", False),
            "refusal": choice.get("refusal")}


def plan_from_choice(text, choice, source):
    """A checked choice -> Plan, built from the templates. `source` names the planner ("nebius", "ollama")."""
    language = language_of(text)
    if choice["job"] == "refuse" or choice["refusal"] is not None:   # any refusal wins (Codex review)
        code = choice["refusal"] if choice["refusal"] in REFUSAL_CODES else "UNSUPPORTED_CAPABILITY"
        return refused(text, code, source)
    if choice["job"] in ("find_colour", "chase_colour"):
        colour = choice["colour"] or "red"
        make = chase_recipe if choice["job"] == "chase_colour" else colour_recipe
        return Plan(language, choice["job"], make(colour, language), None,
                    plan_message(choice["job"], language, colour=colour), source)
    return Plan(language, "count_people", counter_recipe(choice["school"], language), None,
                plan_message("count_people", language, school=choice["school"]), source)
