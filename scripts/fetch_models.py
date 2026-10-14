"""Download the model files Ko'z doesn't keep in git, and check each one's SHA-256.

    .venv/bin/python scripts/fetch_models.py

Today that is one file: the Places365 scene model for the privacy guard (see README.md,
"Models and credits"). A download whose SHA-256 doesn't match is deleted, never used."""
import hashlib
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koz.scene import MODEL_PATH, MODEL_SHA256  # noqa: E402  (the pinned hash lives in one place)

RELEASE = "https://github.com/TurdiyevIslombek/koz-models/releases/download/models-v1"
FILES = {MODEL_PATH: MODEL_SHA256}


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(target, expected):
    if target.exists() and sha256_of(target) == expected:
        print(f"{target.name}: already here, SHA-256 matches")
        return True
    url = f"{RELEASE}/{target.name}"
    print(f"{target.name}: downloading {url}")
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".part", delete=False) as tmp:
        partial = Path(tmp.name)
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                while chunk := response.read(1 << 20):
                    tmp.write(chunk)
        except OSError as error:
            print(f"{target.name}: download failed ({error})")
            partial.unlink(missing_ok=True)
            return False
    if sha256_of(partial) != expected:
        partial.unlink()
        print(f"{target.name}: SHA-256 does not match the pinned value; deleted")
        return False
    partial.replace(target)
    print(f"{target.name}: downloaded, SHA-256 matches")
    return True


def main():
    results = [fetch(target, expected) for target, expected in FILES.items()]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
