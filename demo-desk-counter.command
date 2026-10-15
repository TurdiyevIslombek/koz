#!/bin/bash
# Double-click to run Ko'z on this MacBook's camera: people counter (school mode) at YOUR DESK.
# Owner-confirmed workspace: approved on your word unless a private room or darkness is seen.
# Nothing is saved or sent. Press q in the window to quit.
cd "$(dirname "$0")" || exit 1
finish() { echo; read -r -p "Press Enter to close this window. "; exit "$1"; }
if [ ! -x .venv/bin/python ]; then
  echo "Ko'z isn't set up yet. In this folder, run:"
  echo "  python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  finish 1
fi
.venv/bin/python scripts/fetch_models.py || finish 1
.venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter --school --owner-workspace
finish $?
