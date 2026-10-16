"""Which planner makes the plan: Nemotron on Nebius if there is a key, else Amazon Bedrock if there is
a Bedrock API key (AWS_BEARER_TOKEN_BEDROCK), else the rule planner.
Gemma 4 on this Mac (Ollama) only when asked for (--planner ollama): measured Oct 15 with the
camera running, it got 14 of 20 test sentences right (the rule planner 18) and refused every
people-counting job (docs/TRIALS.md, "Planner on this Mac"). Asked again for every job. If an AI planner fails (PLANNER_UNAVAILABLE), the
next one in the list is asked, down to the rule planner, which always answers. The plan says
which planner made it (Plan.source); the terminal prints it and status.planner carries it."""
import os

from .. import ROOT
from ..errors import KozError
from .bedrock import BedrockPlanner
from .nebius import NebiusPlanner
from .ollama import OllamaPlanner
from .planner import FakePlanner

CHOICES = ("auto", "rules", "fake", "ollama", "nebius", "bedrock")   # "fake" = "rules" (older name)


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


class AutoPlanner:
    """Tries `planners` in order, skipping those that aren't available; the last is the rule planner."""

    def __init__(self, planners, say=print):
        self.planners, self.say = list(planners), say
        self.name = " -> ".join(p.name for p in self.planners)
        self.last = None   # the planner that made the latest plan

    def available(self):
        return True

    def plan(self, text):
        for planner in self.planners:
            if not planner.available():
                continue
            try:
                plan = planner.plan(text)
            except KozError as error:
                if planner is self.planners[-1]:
                    raise
                self.say(f"{planner.name} did not answer ({error.code}); asking the next planner.")
                continue
            self.last = planner
            return plan
        raise KozError("PLANNER_UNAVAILABLE", "no planner available")


def make_planner(choice="auto", env=None, say=print):
    """`auto`: Nebius (if NEBIUS_API_KEY) -> Bedrock (if AWS_BEARER_TOKEN_BEDROCK) -> rules.
    `rules` / `ollama` / `nebius` / `bedrock`: only that one (the AI ones still fall back to rules)."""
    env = {**load_env(), **os.environ} if env is None else env
    rules = FakePlanner()
    nebius = NebiusPlanner(env["NEBIUS_API_KEY"], model=env.get("NEBIUS_MODEL") or None) \
        if env.get("NEBIUS_API_KEY") else None
    ollama = OllamaPlanner(env.get("OLLAMA_MODEL") or None)
    bedrock = BedrockPlanner(env["AWS_BEARER_TOKEN_BEDROCK"], env.get("BEDROCK_MODEL") or None,
                             env.get("AWS_REGION") or None) if env.get("AWS_BEARER_TOKEN_BEDROCK") else None
    if choice in ("rules", "fake"):
        return rules
    if choice == "nebius":
        if nebius is None:
            say("NEBIUS_API_KEY is not set in .env, so the rule planner is used.")
        return AutoPlanner([p for p in (nebius, rules) if p is not None], say)
    if choice == "ollama":
        return AutoPlanner([ollama, rules], say)
    if choice == "bedrock":
        if bedrock is None:
            say("AWS_BEARER_TOKEN_BEDROCK is not set in .env, so the rule planner is used.")
        return AutoPlanner([p for p in (bedrock, rules) if p is not None], say)
    if nebius is None and bedrock is None:
        return rules   # Gemma on this Mac fell short of 18/20 (Oct 15): use --planner ollama to try it
    return AutoPlanner([p for p in (nebius, bedrock, rules) if p is not None], say)


def planned_by(plan, planner):
    """Who made `plan`, in words for the terminal and the local window (never sent: model names
    are free text; status.planner carries only "rules" / "ollama" / "nebius")."""
    if plan.source == "rules":
        return "the rule planner (no AI model)"
    chosen = getattr(planner, "last", None) or planner
    return getattr(chosen, "name", plan.source)

