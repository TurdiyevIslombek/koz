"""Checks over the source code itself, so a rule can't be broken quietly."""
import re
from pathlib import Path

from koz import CONTRACTS, policy
from koz.blocks import TASK_BLOCKS
from koz.errors import CODES

KOZ = Path(__file__).resolve().parent.parent / "koz"


def test_error_codes_match_the_contract():
    table = (CONTRACTS / "events.md").read_text(encoding="utf-8")
    assert set(re.findall(r"^\| `([A-Z_]+)` \|", table, re.M)) == CODES


def test_koz_cannot_save_frames_or_open_audio():
    """Rule 8: no code in koz/ writes images or video, encodes frames, or touches audio."""
    forbidden = ["imwrite", "VideoWriter", "imencode", "CAP_PROP_AUDIO", "pyaudio", "sounddevice",
                 "write_bytes", "write_text", "open("]
    for path in KOZ.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for word in forbidden:
            assert word not in source, f"{word} in {path.relative_to(KOZ)}"


def test_policy_matches_the_blocks_that_exist():
    assert policy.LOCKED_BLOCKS == policy.BLOCK_ORDER[:2]
    assert policy.BUILT_BLOCKS == set(policy.LOCKED_BLOCKS) | set(TASK_BLOCKS)
