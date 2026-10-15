"""The fixed message for each error code, in Uzbek, Russian and English, read from the contract
(contracts/events.md, section 11). Nothing in Ko'z writes its own error text."""
import re
from functools import lru_cache

from . import CONTRACTS

LANGUAGES = ("uz", "ru", "en")


@lru_cache(maxsize=1)
def _table():
    text = (CONTRACTS / "events.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| `([A-Z_]+)` \| [^|]* \| [^|]* \| ([^|]*) \| ([^|]*) \| ([^|]*) \|$", text, re.M)
    return {code: {"en": en.strip(), "ru": ru.strip(), "uz": uz.strip()} for code, en, ru, uz in rows}


def message(code, language="en"):
    """The contract's fixed message for `code` in `language` (uz, ru or en)."""
    return _table()[code][language if language in LANGUAGES else "en"]


def all_messages(language="en"):
    return {code: texts[language] for code, texts in _table().items()}
