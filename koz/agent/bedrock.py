"""BedrockPlanner: Amazon Nova 2 Lite on Amazon Bedrock (AWS) chooses the job; Ko'z builds the recipe.

Same safety as every AI planner (koz/agent/menu.py): the rule refusals run first, so a forbidden
request is never sent; the model only picks from a fixed menu (job, colour, school, refusal); any
refusal wins; the recipe and the text the owner reads come from fixed templates.

Model: eu.amazon.nova-2-lite-v1:0, Nova 2 Lite's EU cross-Region profile. Called from eu-central-1
(Frankfurt) it is served only in EU Regions: Frankfurt, Stockholm, Milan, Spain, Ireland, Paris
(AWS model card, checked Oct 16 2026). Why this one (docs, not guesses):
  - it is Amazon's own model: no AWS Marketplace subscription, which Free-plan accounts may be
    refused (Claude on Bedrock is sold through the Marketplace);
  - it runs from eu-central-1, where Ko'z's AWS part lives;
  - it supports "over 200 languages", optimised for 15 including Russian and Turkish. Uzbek is not
    in that list, so it is measured before it is trusted, with the same bar as the local Gemma
    (18 of 20 right): scripts/score_sentences.py --planner bedrock. Below that, use the rule planner.
Reasoning is off by default on this model (none is asked for here).

Auth: an Amazon Bedrock API key, AWS_BEARER_TOKEN_BEDROCK in .env, sent as "Authorization: Bearer"
(AWS docs: "Use an Amazon Bedrock API key"). Region: AWS_REGION, default eu-central-1. Without the
key Ko'z never calls Bedrock. What leaves this computer: only the sentence (the report says the
text goes to AWS's EU Regions, not to Uzbekistan). Never frames or camera numbers."""
import http.client
import json
import os
import sys
import urllib.parse

from ..errors import KozError
from .menu import SYSTEM, parse_choice, plan_from_choice
from .planner import refusal_for, refused

DEFAULT_MODEL = "eu.amazon.nova-2-lite-v1:0"
DEFAULT_REGION = "eu-central-1"


class BedrockPlanner:
    source = "bedrock"

    def __init__(self, api_key, model=None, region=None, send=None, timeout=30):
        self._key, self.timeout = api_key, timeout
        self.model, self.region = model or DEFAULT_MODEL, region or DEFAULT_REGION
        if not all(c.isalnum() or c == "-" for c in self.region):
            raise KozError("PLANNER_UNAVAILABLE", "bad AWS region")
        self.name = f"Amazon Bedrock ({self.model}, {self.region})"
        self._send = send or self._https   # replaced in tests: no network there

    def available(self):
        return bool(self._key)

    def plan(self, text):
        code = refusal_for(text)
        if code:
            return refused(text, code)   # never sent to AWS
        return plan_from_choice(text, self.ask(text), self.source)

    def ask(self, text):
        """The model's own choice (plan() runs the rule check first). Used alone only to measure the model."""
        reply = self._send(f"/model/{urllib.parse.quote(self.model, safe='')}/converse", {
            "system": [{"text": SYSTEM}],
            "messages": [{"role": "user", "content": [{"text": text}]}],
            "inferenceConfig": {"maxTokens": 300, "temperature": 0}})
        try:
            content = reply["output"]["message"]["content"]
            answer = "".join(part["text"] for part in content if "text" in part)
            return parse_choice(answer)
        except (KeyError, TypeError, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "the planner's answer was not a valid choice") from None

    def _https(self, path, body):
        """One HTTPS request to Bedrock Runtime. Any failure is PLANNER_UNAVAILABLE (the key is never shown)."""
        host = f"bedrock-runtime.{self.region}.amazonaws.com"
        connection = http.client.HTTPSConnection(host, timeout=self.timeout)
        try:
            connection.request("POST", path, body=json.dumps(body),
                               headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"})
            response = connection.getresponse()
            text = response.read(1_000_000)
            if response.status != 200:
                raise ValueError("status")
            return json.loads(text.decode("utf-8"))
        except (OSError, http.client.HTTPException, ValueError):
            raise KozError("PLANNER_UNAVAILABLE", "Bedrock did not answer") from None
        finally:
            connection.close()


def main(argv=None):
    """Plan one sentence with Bedrock (needs AWS_BEARER_TOKEN_BEDROCK in .env)."""
    import time
    from .choose import load_env
    args = sys.argv[1:] if argv is None else argv
    env = {**load_env(), **os.environ}
    if not env.get("AWS_BEARER_TOKEN_BEDROCK"):
        print("AWS_BEARER_TOKEN_BEDROCK is not set in .env.")
        return 1
    planner = BedrockPlanner(env["AWS_BEARER_TOKEN_BEDROCK"], env.get("BEDROCK_MODEL") or None,
                             env.get("AWS_REGION") or None)
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
