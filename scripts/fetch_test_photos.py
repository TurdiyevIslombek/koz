"""Download the real photos for the privacy guard's regression test, and check each SHA-256.

    .venv/bin/python scripts/fetch_test_photos.py

The photos (listed in tests/places365_photos.txt) come from the Places365 validation set
by MIT CSAIL. Their copyright belongs to their owners, so they are not in git; this script
reads the official archive until it has every listed photo, then stops (about 80 MB of the
525 MB archive). The Places team asks users of the original Places365 data to sign a form
on http://places2.csail.mit.edu/download.html.

    .venv/bin/python scripts/fetch_test_photos.py --tar val_256.tar   # from a copy you already have"""
import argparse
import hashlib
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "tests" / "places365_photos.txt"
OUT = ROOT / "tests" / "fixtures" / "places365"
ARCHIVE = "https://data.csail.mit.edu/places/places365/val_256.tar"


def wanted():
    rows = [line.split() for line in LIST.read_text().splitlines() if line and not line.startswith("#")]
    return {name: (group, sha256) for group, name, sha256 in rows}


def main():
    parser = argparse.ArgumentParser(description="Fetch the guard's test photos")
    parser.add_argument("--tar", help="read this local copy of val_256.tar instead of downloading")
    args = parser.parse_args()
    todo = {name: info for name, info in wanted().items()
            if not (OUT / info[0] / name).exists()
            or hashlib.sha256((OUT / info[0] / name).read_bytes()).hexdigest() != info[1]}
    if not todo:
        print("all test photos already here, SHA-256 matches")
        return 0
    print(f"{len(todo)} photos to get from {args.tar or ARCHIVE}")
    source = open(args.tar, "rb") if args.tar else urllib.request.urlopen(ARCHIVE, timeout=60)
    bad = 0
    try:
        with source, tarfile.open(fileobj=source, mode="r|") as tar:
            for member in tar:
                name = Path(member.name).name
                if name not in todo or not member.isfile():
                    continue
                group, expected = todo.pop(name)
                data = tar.extractfile(member).read()
                if hashlib.sha256(data).hexdigest() != expected:
                    print(f"{name}: SHA-256 does not match; skipped")
                    bad += 1
                else:
                    (OUT / group).mkdir(parents=True, exist_ok=True)
                    (OUT / group / name).write_bytes(data)
                if not todo:
                    break
    except (tarfile.ReadError, EOFError, OSError) as error:
        print(f"archive ended early: {type(error).__name__}")
    if todo or bad:
        print(f"missing {len(todo)}, wrong {bad}")
        return 1
    print("all test photos downloaded, SHA-256 matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
