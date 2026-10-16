"""Score a planner on the test sentences ("sentence | expected" per line), with the time per plan.

    .venv/bin/python scripts/score_sentences.py                                   # the rule planner
    .venv/bin/python scripts/score_sentences.py --planner bedrock                  # Amazon Bedrock (Oct 19)
    .venv/bin/python scripts/score_sentences.py --planner bedrock FILE             # one file only

Default files: tests/fixtures/sentences_islombek.txt (Islombek's 20) and
tests/fixtures/sentences_measured.txt (the 20 from the Gemma measurement, Oct 15).
expected: `count`, `find:<colour>`, `chase:<colour>`, `refuse` (any refusal).
For each refusal it says HOW it was refused: by a refusal rule (the check every planner runs
first, so an AI planner never sees the sentence) or only because nothing matched
(UNSUPPORTED_CAPABILITY: with an AI planner, that sentence would be sent to the model).
For an AI planner it also scores the model alone (no rule check first), as for Gemma."""
import argparse
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.agent.choose import make_planner  # noqa: E402
from koz.agent.menu import plan_from_choice  # noqa: E402
from koz.agent.planner import HUES, FakePlanner, refusal_for  # noqa: E402
from koz.errors import KozError  # noqa: E402

FILES = [ROOT / "tests" / "fixtures" / "sentences_islombek.txt", ROOT / "tests" / "fixtures" / "sentences_measured.txt"]


def read(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            sentence, expected = (part.strip() for part in line.rsplit("|", 1))
            rows.append((sentence, expected))
    return rows


def got(plan):
    if plan.refusal:
        return "refuse"
    if plan.job == "count_people":
        return "count"
    hue = plan.recipe["blocks"][2]["settings"]["hue_center"]
    colour = next(c for c, h in HUES.items() if h == hue)
    return ("chase:" if plan.job == "chase_colour" else "find:") + colour


def score(path, planner=None):
    """[(sentence, expected, got, plan, by_rule, seconds)] for every line."""
    planner, rows = planner or FakePlanner(), []
    for sentence, expected in read(path):
        start = time.monotonic()
        try:
            plan = planner.plan(sentence)
            answer = got(plan)
        except KozError as error:
            plan, answer = None, f"error {error.code}"
        rows.append((sentence, expected, answer, plan, refusal_for(sentence) is not None, time.monotonic() - start))
    return rows


def report(title, rows):
    print(f"\n{title}")
    for sentence, expected, answer, plan, by_rule, seconds in rows:
        how = ""
        if plan is not None and plan.refusal:
            how = f" {plan.refusal}" + (" (refusal rule)" if by_rule else " (nothing matched)" if plan.source == "rules"
                                        else f" ({plan.source})")
        print(f"{'ok ' if answer == expected else 'NO '} {seconds:5.1f} s {answer}{how}  <- {sentence}")
    right = sum(answer == expected for _, expected, answer, _, _, _ in rows)
    times = [seconds for *_, seconds in rows]
    print(f"{right}/{len(rows)} right; time per plan median {statistics.median(times):.1f} s, max {max(times):.1f} s")
    return right


def main():
    parser = argparse.ArgumentParser(description="Score a planner on the test sentences")
    parser.add_argument("--planner", default="rules", choices=("rules", "bedrock", "nebius", "ollama"))
    parser.add_argument("files", nargs="*", default=[str(f) for f in FILES])
    args = parser.parse_args()
    planner = make_planner(args.planner)
    ai = getattr(planner, "planners", [planner])[0]
    print(f"Planner: {ai.name}")
    for path in args.files:
        report(f"{Path(path).name}: Ko'z with this planner (rule refusal check first)", score(path, planner))
        if hasattr(ai, "ask"):   # the model alone, as measured for Gemma
            class Alone:
                def plan(self, text):
                    return plan_from_choice(text, ai.ask(text), ai.source)
            report(f"{Path(path).name}: the model alone (no rule check)", score(path, Alone()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
