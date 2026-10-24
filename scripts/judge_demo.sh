#!/usr/bin/env bash
# Fresh-clone setup and a real, bounded OpenCV agent run on the public drawn clip.
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${PYTHON:-python3.13}"
if ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "Install Python 3.13 (including venv), then rerun this command." >&2
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  "$python_bin" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
echo "Judge demo: plan -> test -> adjust -> run (drawn clip; real OpenCV; rules planner)."
exec .venv/bin/python scripts/agent_demo.py --i-own-this-camera \
  --planner rules --video samples/orange-red-ball.mp4 --no-window --seconds 4 \
  "find the red ball"
