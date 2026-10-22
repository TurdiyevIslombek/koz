#!/bin/bash
# Double-click to connect this Mac's camera to the Ko'z web app on AWS (Oct 22).
# The first time, Ko'z asks for two things from the web app (Connect device): the server address and
# the device token (hidden while you paste). It saves both in .env, so next time it just connects.
# Pictures stay on this Mac (the runner window shows them, faces blurred); only numbers go to AWS.
# For the car, arming the motors stays here: press Enter in this window. Ctrl+C or closing stops it.
cd "$(dirname "$0")" || exit 1
finish() { echo; read -r -p "Press Enter to close this window. "; exit "$1"; }

if [ ! -x .venv/bin/python ]; then
  echo "Ko'z isn't set up yet. In this folder, run:"
  echo "  python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  finish 1
fi
.venv/bin/python scripts/fetch_models.py || finish 1
.venv/bin/python -m koz.server --i-own-this-camera --window --planner rules --cloud
finish $?
