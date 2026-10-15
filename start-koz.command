#!/bin/bash
# Double-click to start Ko'z: the runner (this Mac's camera) and the web app, together.
# The browser opens the Setup page: type the job there and watch it run. The numbers show in
# the browser; the camera view (faces blurred) shows in the "Ko'z runner" window. q in that
# window stops the job. Nothing is saved or sent.
# Close this Terminal window, or press Ctrl+C here, to stop both.
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
finish() { echo; read -r -p "Press Enter to close this window. "; exit "$1"; }

if [ ! -x .venv/bin/python ]; then
  echo "Ko'z isn't set up yet. In this folder, run:"
  echo "  python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  finish 1
fi
if ! command -v node >/dev/null 2>&1 || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 22 ]; then
  echo "The web app needs Node.js 22 or newer: https://nodejs.org"
  finish 1
fi
if nc -z 127.0.0.1 4173 2>/dev/null; then
  echo "Port 4173 is already in use (maybe the web app from open-web.command). Quit it, then try again."
  finish 1
fi
if nc -z 127.0.0.1 8765 2>/dev/null; then
  echo "Port 8765 is already in use (maybe another Ko'z runner). Close it, then try again."
  finish 1
fi
.venv/bin/python scripts/fetch_models.py || finish 1
echo "Preparing the web app..."
if ! (cd web && { { [ -d node_modules/ws ] && [ -d node_modules/ajv ] && [ -d node_modules/esbuild ]; } \
                  || npm ci --no-audit --no-fund; } && node scripts/build.mjs); then
  echo "The web app could not be built."
  finish 1
fi

runner_pid=""
web_pid=""
stop() {   # stop both, the web app first, and wait until they have closed (camera included)
  trap - INT TERM HUP EXIT
  [ -n "$web_pid" ] && kill -TERM "$web_pid" 2>/dev/null
  [ -n "$runner_pid" ] && kill -TERM "$runner_pid" 2>/dev/null
  wait 2>/dev/null
  echo "Ko'z stopped."
}
trap 'stop; exit 0' INT TERM HUP
trap stop EXIT

# For testing: KOZ_RUNNER_ARGS adds runner options (e.g. "--video clip.mp4" instead of the camera),
# KOZ_NO_WINDOW=1 hides the camera window, KOZ_NO_BROWSER=1 doesn't open the browser.
window="--window"
[ "$KOZ_NO_WINDOW" = "1" ] && window=""
.venv/bin/python -m koz.server --i-own-this-camera $window $KOZ_RUNNER_ARGS &
runner_pid=$!
(cd web && exec node server/index.mjs) &
web_pid=$!

for _ in $(seq 1 50); do
  curl -s -m 1 -o /dev/null http://127.0.0.1:4173/api/health && break
  sleep 0.2
done
[ "$KOZ_NO_BROWSER" = "1" ] || open "http://127.0.0.1:4173/#setup"
echo
echo "Ko'z is running: http://127.0.0.1:4173 (Setup: type the job; Live: watch it)."
echo "Do not type names of people. Close this window or press Ctrl+C to stop."

while kill -0 "$runner_pid" 2>/dev/null && kill -0 "$web_pid" 2>/dev/null; do
  sleep 1
done
echo "One part of Ko'z stopped; stopping the other."
stop
finish 1
