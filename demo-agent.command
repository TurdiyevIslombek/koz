#!/bin/bash
# Double-click: type a camera job in plain words (Uzbek, Russian or English) and watch Ko'z
# plan it, try it on this MacBook's camera, check the numbers, adjust and run.
# Nothing is saved. Only your sentence goes to Nemotron on Nebius, and only if NEBIUS_API_KEY is in .env.
cd "$(dirname "$0")" || exit 1
finish() { echo; read -r -p "Press Enter to close this window. "; exit "$1"; }
if [ ! -x .venv/bin/python ]; then
  echo "Ko'z isn't set up yet. In this folder, run:"
  echo "  python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  finish 1
fi
.venv/bin/python scripts/fetch_models.py || finish 1
echo
echo "Describe the camera job in one sentence (Uzbek, Russian or English)."
echo "Examples:  find the red ball  |  Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir"
echo "Do not type names of people."
read -r -p "> " job
if [ -z "$job" ]; then
  echo "No job typed."
  finish 1
fi
.venv/bin/python scripts/agent_demo.py --i-own-this-camera "$job"
finish $?
