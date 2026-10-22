"""docs/TEXTS.md is exactly what Ko'z says (scripts/make_texts.py), so Islombek checks the real texts."""
import importlib.util
from pathlib import Path

from koz.errors import CODES

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "make_texts.py"


def load():
    spec = importlib.util.spec_from_file_location("make_texts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_texts_file_is_up_to_date():
    make = load()
    assert make.OUT.read_text(encoding="utf-8") == make.render(), \
        "docs/TEXTS.md is out of date: run .venv/bin/python scripts/make_texts.py"


def test_texts_file_has_every_code_and_every_plan():
    text = load().render()
    assert all(f"### `{code}`" in text for code in CODES)
    # every message, 6 find + 6 chase colours, 2 counters, 11 things
    assert text.count("- [ ] Russian OK") == len(CODES) + 6 + 6 + 2 + len(load().OBJECT_EXAMPLES)
