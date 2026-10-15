"""OllamaPlanner: a local Gemma 4 model, through Ollama on this Mac, chooses the job.

Same safety as every AI planner (koz/agent/menu.py): the rule refusals run first, the model
only picks from a fixed menu (here also enforced by Ollama's JSON-schema "format"), any refusal
wins, and the recipe and plan text come from templates.

Nothing leaves the computer: Ollama runs here, and this planner only talks to 127.0.0.1.
That is better for privacy than a cloud planner (CLAUDE.md rule 9).

Which model: OLLAMA_MODEL from .env, else DEFAULT_MODEL. gemma4:e2b-it-qat is the smallest
Gemma 4 (4.3 GB download, ollama.com/library/gemma4, checked Oct 15 2026). This Mac has 8 GB
of memory shared by macOS, the browser, the camera models and the planner; E4B (6.1 GB and up)
would not fit next to them. KEEP_ALIVE = "0" unloads the model right after it answers: the
planner is needed once per job, before the camera opens, and the memory then goes back to the
camera models. Each job pays a few seconds to load it again (to measure).

    ollama pull gemma4:e2b-it-qat
    .venv/bin/python -m koz.agent.ollama "find the red ball"     # try one sentence"""
import http.client
import json
import os
import sys
import urllib.parse

from ..errors import KozError
from .menu import CHOICE_SCHEMA, SYSTEM, parse_choice, plan_from_choice
from .planner import refusal_for, refused

BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma4:e2b-it-qat"
KEEP_ALIVE = "0"
LOOPBACK = ("127.0.0.1", "localhost", "::1")


class OllamaPlanner:
    source = "ollama"

    def __init__(self, model=None, base_url=BASE_URL, send=None, timeout=120):
        self.model, self.base_url, self.timeout = model or DEFAULT_MODEL, base_url.rstrip("/"), timeout
        self.name = f"Gemma 4 on this Mac (Ollama, {self.model})"
        self._send = send or self._http   # replaced in tests: no Ollama there

    def available(self):
        """True if Ollama is running here and has the model (asked fresh for every job)."""
        try:
            tags = self._send("GET", "/api/tags", None, timeout=1.0)
            names = {m["name"] for m in tags["models"]}
        except (KozError, KeyError, TypeError):
            return False
        return self.model in names or f"{self.model}:latest" in names

    def plan(self, text):
        code = refusal_for(text)
        if code:
            return refused(text, code)   # never sent to the model
        reply = self._send("POST", "/api/chat", {
            "model": self.model, "stream": False, "format": CHOICE_SCHEMA, "keep_alive": KEEP_ALIVE,
            "options": {"temperature": 0, "num_ctx": 2048},   # a small context: less memory
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]})
        try:
            choice = parse_choice(reply["message"]["content"])
        except (KeyError, TypeError, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "the planner's answer was not a valid choice") from None
        return plan_from_choice(text, choice, self.source)

    def _http(self, method, path, body, timeout=None):
        """One request to Ollama on this computer. Any failure is PLANNER_UNAVAILABLE."""
        url = urllib.parse.urlsplit(self.base_url)
        if url.scheme != "http" or url.hostname not in LOOPBACK:
            raise KozError("PLANNER_UNAVAILABLE", "Ollama must run on this computer")
        connection = http.client.HTTPConnection(url.hostname, url.port or 11434, timeout=timeout or self.timeout)
        try:
            connection.request(method, path, body=None if body is None else json.dumps(body),
                               headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            text = response.read(1_000_000)
            if response.status != 200:
                raise ValueError("status")
            return json.loads(text.decode("utf-8"))
        except (OSError, http.client.HTTPException, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "Ollama did not answer") from None
        finally:
            connection.close()


def main(argv=None):
    """Plan one sentence with the local model and say how long it took."""
    import time
    from .choose import load_env
    args = sys.argv[1:] if argv is None else argv
    env = {**load_env(), **os.environ}
    planner = OllamaPlanner(env.get("OLLAMA_MODEL") or None)
    if not planner.available():
        print(f"Ollama isn't running here, or doesn't have {planner.model} (ollama pull {planner.model}).")
        return 1
    started = time.monotonic()
    try:
        plan = planner.plan(" ".join(args) or "find the red ball")
    except KozError as error:
        print(error.code)
        return 1
    print(f"{planner.model} ({time.monotonic() - started:.1f} s, planned by {plan.source}): "
          f"{plan.job or plan.refusal} ({plan.language}) {plan.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
