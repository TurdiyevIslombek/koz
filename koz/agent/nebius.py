"""NebiusPlanner: NVIDIA Nemotron on Nebius Token Factory chooses the job; Ko'z builds the recipe.

The model only picks from a fixed menu (find a colour, count people, or refuse). It never
writes a recipe or the text the owner reads: the recipe and the plan text come from the same
templates as FakePlanner, and the recipe goes through koz.recipe like any other (CLAUDE.md
rules 1 and 5), so the model can't promise something Ko'z doesn't do.
The same refusal rules as FakePlanner run first, so a forbidden request is never sent.

What leaves the computer: only the user's sentence (CLAUDE.md rule 9; the chat shows
"Do not type names", and the report lists that the text goes to Nebius abroad). Never
frames or camera numbers: the adjust step is local (koz/agent/tuner.py).

API: OpenAI-style, https://api.tokenfactory.nebius.com/v1 (docs.tokenfactory.nebius.com),
key from .env as NEBIUS_API_KEY. The model is NEBIUS_MODEL from .env if set, else
DEFAULT_MODEL (Nemotron 3 Super; the ID Nebius's own cookbook uses, checked Oct 15 2026,
not yet tried with our key). To see the Nemotron IDs your key can use:
    .venv/bin/python -m koz.agent.nebius --models"""
import http.client
import json
import os
import re
import sys
import urllib.parse

from .. import ROOT
from ..errors import CODES, KozError
from .planner import (COLOURS, HUES, FakePlanner, Plan, colour_recipe, counter_recipe, language_of, plan_message,
                      refusal_for, refused)

BASE_URL = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
REFUSAL_CODES = {"IDENTITY_FORBIDDEN", "PROFILING_FORBIDDEN", "VIEW_FORBIDDEN", "AUDIO_FORBIDDEN",
                 "SOLE_PROTECTION_FORBIDDEN", "MOTOR_TARGET_FORBIDDEN", "ACTUATOR_FORBIDDEN",
                 "UNSUPPORTED_CAPABILITY", "PRIVATE_BATHROOM", "PRIVATE_TOILET", "PRIVATE_BEDROOM",
                 "PRIVATE_CHANGING_ROOM"}
SYSTEM = f"""You set up Ko'z, a privacy-first camera. Read the owner's request (Uzbek, Russian or English)
and reply with ONE JSON object and nothing else:
{{"job": "find_colour" | "count_people" | "refuse",
 "colour": {" | ".join(f'"{c}"' for c in HUES)} | null,
 "school": true | false,
 "refusal": null | one of {sorted(REFUSAL_CODES)}}}
Ko'z can only: find one coloured object and say if it is left, center or right ("find_colour");
or count people crossing a line in the middle of the view ("count_people"; "school": true for
classes and pupils). Faces are always blurred and nothing is saved. Refuse ("job": "refuse") anything
else, and always refuse: identifying or following a person, number plates, guessing age, gender,
emotion or ethnicity, judging people, hidden cameras, sound, bathrooms, toilets, bedrooms, changing
rooms, being the only protection for a child, and robots chasing people or animals."""


def load_env(path=None):
    """KEY=VALUE lines from .env (git-ignored). Values are never printed."""
    path = path or ROOT / ".env"
    values = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    except OSError:
        pass
    return values


def make_planner(choice="auto", env=None, say=print):
    """FakePlanner or NebiusPlanner. Without NEBIUS_API_KEY it says so and uses FakePlanner."""
    env = {**load_env(), **os.environ} if env is None else env
    if choice == "fake":
        return FakePlanner()
    if env.get("NEBIUS_API_KEY"):
        return NebiusPlanner(env["NEBIUS_API_KEY"], model=env.get("NEBIUS_MODEL") or None)
    say("NEBIUS_API_KEY is not set in .env, so the rule-based FakePlanner is used.")
    return FakePlanner()


class NebiusPlanner:
    name = "NebiusPlanner (Nemotron on Nebius Token Factory)"

    def __init__(self, api_key, model=None, base_url=BASE_URL, send=None, timeout=30):
        self._key, self.base_url, self.timeout = api_key, base_url.rstrip("/"), timeout
        self.model = model or DEFAULT_MODEL
        self._send = send or self._http   # replaced in tests: no network there

    def plan(self, text):
        code = refusal_for(text)
        if code:
            return refused(text, code)   # never sent to Nebius
        language = language_of(text)
        reply = self._send("POST", "/chat/completions", {
            "model": self.model, "temperature": 0, "max_tokens": 2000,   # room for a reasoning model's thinking
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]})
        try:
            choice = parse_choice(reply["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "the planner's answer was not a valid choice") from None
        if choice["job"] == "refuse" or choice["refusal"] is not None:   # any refusal wins (Codex review)
            return refused(text, choice["refusal"] if choice["refusal"] in REFUSAL_CODES else "UNSUPPORTED_CAPABILITY")
        if choice["job"] == "find_colour":
            colour = choice["colour"] or "red"
            return Plan(language, "find_colour", colour_recipe(colour, language), None,
                        plan_message("find_colour", language, colour=colour))
        return Plan(language, "count_people", counter_recipe(choice["school"], language), None,
                    plan_message("count_people", language, school=choice["school"]))

    def nemotron_models(self):
        """The Nemotron model IDs this key can use (GET /v1/models)."""
        try:
            ids = [m["id"] for m in self._send("GET", "/models", None)["data"]]
        except (KeyError, TypeError):
            raise KozError("PLANNER_UNAVAILABLE", "unexpected model list") from None
        return sorted(i for i in ids if isinstance(i, str) and "nemotron" in i.lower())

    def _http(self, method, path, body):
        """One HTTPS request to Nebius. Any failure is PLANNER_UNAVAILABLE (the key is never shown)."""
        url = urllib.parse.urlsplit(self.base_url)
        if url.scheme != "https":
            raise KozError("PLANNER_UNAVAILABLE", "the planner address must be https")
        connection = http.client.HTTPSConnection(url.netloc, timeout=self.timeout)
        try:
            connection.request(method, url.path + path, body=None if body is None else json.dumps(body),
                               headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"})
            response = connection.getresponse()
            text = response.read(1_000_000)
            if response.status != 200:
                raise ValueError("status")
            return json.loads(text.decode("utf-8"))
        except (OSError, http.client.HTTPException, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "Nebius did not answer") from None
        finally:
            connection.close()


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
    if (type(choice) is not dict or set(choice) - {"job", "colour", "school", "refusal", "message"}
            or choice.get("job") not in ("find_colour", "count_people", "refuse")
            or choice.get("colour") not in (None, *HUES) or type(choice.get("school", False)) is not bool
            or (choice.get("refusal") is not None and choice.get("refusal") not in CODES)):
        raise ValueError("not a valid choice")
    # Any "message" the model adds anyway is ignored: the owner reads only fixed templates.
    return {"job": choice["job"], "colour": choice.get("colour"), "school": choice.get("school", False),
            "refusal": choice.get("refusal")}


def main(argv=None):
    """--models: print the Nemotron IDs your key can use. Otherwise: plan one sentence."""
    args = sys.argv[1:] if argv is None else argv
    env = {**load_env(), **os.environ}
    if not env.get("NEBIUS_API_KEY"):
        print("NEBIUS_API_KEY is not set in .env.")
        return 1
    planner = NebiusPlanner(env["NEBIUS_API_KEY"], model=env.get("NEBIUS_MODEL") or None)
    try:
        if args == ["--models"]:
            print("\n".join(planner.nemotron_models()) or "no Nemotron models for this key")
            return 0
        plan = planner.plan(" ".join(args) or "find the red ball")
    except KozError as error:
        print(error.code)
        return 1
    print(f"{planner.model}: {plan.job or plan.refusal} ({plan.language}) {plan.message}")
    return 0


__all__ = ["NebiusPlanner", "make_planner", "load_env", "parse_choice", "COLOURS", "DEFAULT_MODEL"]

if __name__ == "__main__":
    sys.exit(main())
