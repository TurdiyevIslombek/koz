"""Score the rule planner on a sentences file ("sentence | expected" per line).

    .venv/bin/python scripts/score_sentences.py tests/fixtures/sentences_islombek.txt

expected: `count` (count people), `find:<colour>` (find that colour), `refuse` (any refusal).
For each refusal it also says HOW it was refused: by a refusal rule (the check every planner
runs first, so an AI planner never sees the sentence) or only because nothing matched
(UNSUPPORTED_CAPABILITY: with an AI planner, that sentence would be sent to the model)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.agent.planner import HUES, FakePlanner, refusal_for  # noqa: E402


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
    return "find:" + next(c for c, h in HUES.items() if h == hue)


def score(path, planner=None):
    """[(sentence, expected, got, plan, by_rule)] for every line."""
    planner = planner or FakePlanner()
    return [(s, e, got(p := planner.plan(s)), p, refusal_for(s) is not None) for s, e in read(path)]


def main(path):
    rows = score(path)
    for sentence, expected, answer, plan, by_rule in rows:
        how = ""
        if plan.refusal:
            how = f" {plan.refusal}" + (" (refusal rule)" if by_rule else " (nothing matched)")
        extra = f", school" if plan.job == "count_people" and plan.recipe["privacy"]["school"] else ""
        print(f"{'ok ' if answer == expected else 'NO '} {plan.language} {answer}{extra}{how}  <- {sentence}")
    right = sum(answer == expected for _, expected, answer, _, _ in rows)
    unmatched = sum(1 for *_, plan, by_rule in rows if plan.refusal and not by_rule)
    print(f"\n{right}/{len(rows)} right; refusals only because nothing matched: {unmatched}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tests" / "fixtures" / "sentences_islombek.txt"))
