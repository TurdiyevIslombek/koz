"""Model files are pinned by SHA-256 (a fingerprint of the file's bytes): Ko'z refuses
any file that isn't exactly the one we checked (CLAUDE.md rule 1: no model files from recipes)."""
import hashlib
from pathlib import Path

from .errors import KozError


def require_pinned(path, sha256, code):
    """Raise KozError(code) unless the file at `path` exists and has this SHA-256."""
    try:
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        raise KozError(code, "model file missing") from None
    if digest != sha256:
        raise KozError(code, "model file is not the pinned one")
