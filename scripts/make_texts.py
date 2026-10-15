"""Write docs/TEXTS.md: every Uzbek and Russian text Ko'z itself shows, for Islombek to check.

    .venv/bin/python scripts/make_texts.py

Made from the code (koz/agent/planner.py) and the contract (contracts/events.md), so it is
always what Ko'z really says; tests/test_texts.py fails if the file is out of date. To fix a text,
tell Claude: the fix goes into the code or the contract, then this file is made again."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.agent.menu import REFUSAL_CODES  # noqa: E402
from koz.agent.planner import COLOUR_WORDS, HUES, PLAN_TEXT, plan_message  # noqa: E402
from koz.messages import _table  # noqa: E402

OUT = ROOT / "docs" / "TEXTS.md"
NAMES = {"en": "English", "ru": "Russian", "uz": "Uzbek"}
# The other codes a job can stop with before it runs: a request the planner can't handle.
PLANNING_CODES = ("INVALID_COMMAND", "PLANNER_UNAVAILABLE")


def check(lines, texts):
    for lang in ("en", "ru", "uz"):
        lines.append(f"- {lang.upper()}: {texts[lang]}")
    lines.append("- [ ] Russian OK   - [ ] Uzbek OK")
    lines.append("")


def render():
    table = _table()
    lines = ["# Texts to check (Uzbek and Russian)", "",
             "Every text Ko'z itself shows in Uzbek and Russian: the plan after you type a job, the",
             "refusals, and the fixed stop and error messages. Made by `scripts/make_texts.py` from",
             "`koz/agent/planner.py` and `contracts/events.md`, so this is exactly what Ko'z says.",
             "Tick the box when it reads naturally, or write the better wording under it; Claude then",
             "puts your fixes into the code or the contract (the codes stay) and makes this file again.",
             "", "The web app's own screens are in `web/src/i18n.js` (Codex's lane), not here.", ""]

    lines += ["## 1. Plans", "",
              "What Ko'z says it will do, in the language of the job. A colour plan with each colour:", ""]
    for job, title in (("find_colour", "Find a colour"), ("count_people", "Count people"),
                       ("count_school", "Count pupils (school mode)")):
        lines.append(f"### {title}")
        lines.append("")
        if job == "find_colour":
            for colour in HUES:
                lines.append(f"**{COLOUR_WORDS[colour]['en']}**")
                check(lines, {lang: plan_message(job, lang, colour=colour) for lang in ("en", "ru", "uz")})
        else:
            check(lines, PLAN_TEXT[job])

    lines += ["## 2. Refusals", "",
              "When Ko'z refuses a job, before any camera opens. The same text for every planner.", ""]
    for code in sorted(REFUSAL_CODES) + list(PLANNING_CODES):
        lines.append(f"### `{code}`")
        check(lines, table[code])

    lines += ["## 3. Other stop and error messages", "",
              "Shown when a running job stops, or a command or recipe is refused.", ""]
    for code in table:
        if code not in REFUSAL_CODES and code not in PLANNING_CODES:
            lines.append(f"### `{code}`")
            check(lines, table[code])
    return "\n".join(lines).rstrip("\n") + "\n"


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
