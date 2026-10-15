"""NebiusPlanner: NVIDIA Nemotron on Nebius Token Factory chooses the job; Ko'z builds the recipe.

Same safety as every AI planner (koz/agent/menu.py): the rule refusals run first, the model
only picks from a fixed menu, any refusal wins, and the recipe and plan text come from templates.

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
import sys
import urllib.parse

from ..errors import KozError
from .menu import SYSTEM, parse_choice, plan_from_choice
from .planner import refusal_for, refused

BASE_URL = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"


class NebiusPlanner:
    source = "nebius"

    def __init__(self, api_key, model=None, base_url=BASE_URL, send=None, timeout=30):
        self._key, self.base_url, self.timeout = api_key, base_url.rstrip("/"), timeout
        self.model = model or DEFAULT_MODEL
        self.name = f"Nemotron on Nebius ({self.model})"
        self._send = send or self._http   # replaced in tests: no network there

    def available(self):
        return bool(self._key)

    def plan(self, text):
        code = refusal_for(text)
        if code:
            return refused(text, code)   # never sent to Nebius
        reply = self._send("POST", "/chat/completions", {
            "model": self.model, "temperature": 0, "max_tokens": 2000,   # room for a reasoning model's thinking
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]})
        try:
            choice = parse_choice(reply["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "the planner's answer was not a valid choice") from None
        return plan_from_choice(text, choice, self.source)

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


def main(argv=None):
    """--models: print the Nemotron IDs your key can use. Otherwise: plan one sentence."""
    from .choose import load_env
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


__all__ = ["NebiusPlanner", "parse_choice", "DEFAULT_MODEL"]

if __name__ == "__main__":
    sys.exit(main())
