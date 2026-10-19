"""koz/brains/flybrain/original/ is an unchanged copy of Islombek's fly-brain car files (Oct 16; refreshed
Oct 19 to his Oct 18 hardware fixes, at his request).
Work happens next to it, never in it: this fails if any copied file changes."""
import hashlib
from pathlib import Path

ORIGINAL = Path(__file__).resolve().parent.parent / "koz" / "brains" / "flybrain" / "original"


def test_copied_originals_are_unchanged():
    rows = [line.split("  ", 1) for line in (ORIGINAL / "ORIGINALS.sha256").read_text().splitlines() if line]
    assert len(rows) == 13
    for digest, name in rows:
        assert hashlib.sha256((ORIGINAL / name).read_bytes()).hexdigest() == digest, name


def test_nothing_else_was_added_to_the_copy():
    listed = {line.split("  ", 1)[1] for line in (ORIGINAL / "ORIGINALS.sha256").read_text().splitlines() if line}
    present = {str(p.relative_to(ORIGINAL)) for p in ORIGINAL.rglob("*")
               if p.is_file() and p.name != "ORIGINALS.sha256" and "__pycache__" not in p.parts}
    assert present == listed
