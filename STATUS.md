# Ko'z status

Updated Oct 15, after the agent loop. 291 tests pass, 1 skipped (it needs your face clip):
`.venv/bin/python -m pytest -q`

## What works

| Part | State |
|---|---|
| Recipe checks (`koz/recipe.py`) | Strict parsing → contract schema → extra checks → "is it built?". Tested. |
| Privacy guard (`koz/privacy.py`, `koz/scene.py`) | **Default (every job): run anywhere, stop on what it sees**: darkness or a covered lens, a bed or toilet (NanoDet ≥ 0.40 in 2 of 3 checks), a sink in what looks like a bathroom, or a confident private room (top guess ≥ 0.50, or ≥ 0.40 together). **`--strict`** (schools, public cameras): only listed public places run. Objects checked every 0.5 s, the room every 3 s, and on the next frame when the camera moves; stops 0.07 s after a toilet or bed comes into view on recorded clips (target 1 s); one line per check, with timings. On 71 real photos: default runs every desk without a bed, kitchen, classroom and shop, and lets 3 of 23 bathroom/bedroom photos through (limit); strict stops all 23. **Live stop time: to measure (live test #5).** |
| Face blur (`koz/blocks/face_blur.py`) | YuNet on OpenCV 5, heavy pixelation, fails closed. **No real-face test yet** (waiting for your clip in `tests/fixtures/private/face.mp4`). |
| Colour finder (`koz/blocks/color_finder.py`) | Biggest patch of one colour → left / center / right / lost. Tested on the recorded test video. |
| Person detector (`koz/blocks/person_detector.py`) | NanoDet-Plus on OpenCV 5, "person" class only; boxes stay local, only the number of people is sent. Decoding tested with exact fake outputs. **Not yet measured on real people.** |
| Line counter (`koz/blocks/line_counter.py`) | In-memory tracker; counts crossings through the line segment in each direction; person numbers forgotten 2 s after they leave. Tested with scripted walkers. |
| Runner (`koz/runner.py`) | mask → privacy → blur → blocks → events; stale or slow frames → `unknown` with a reason. School mode allows the counter only. |
| Events (`koz/events.py`) | All 7 types (status, recipe, observation, decision, command_result, fault, trial_result), checked against `contracts/events.md` before sending. |
| Agent loop (`koz/agent/`) | Words → plan → try 3 s → check the OpenCV numbers → change one setting → try again (3 tries at most) → run. Each step is an event (observation → decision → new revision → result) and one printed line. Refusals stop before the camera opens. On recorded clips: red asked, ball looks orange-red → hue 0 → 13, found; with the real models, green asked for a teal ball → hue 60 → 77, found. **Not yet tried on your camera.** |
| Planners (`koz/agent/planner.py`, `nebius.py`) | FakePlanner (word lists, Uz/Ru/En, used by every test). NebiusPlanner: Nemotron picks only the job / colour / school / refusal; the recipe and the plan text come from fixed templates. **No `.env` key yet, so Nemotron is untested**; default model `nvidia/nemotron-3-super-120b-a12b` (from Nebius's cookbook). |
| Runner WebSocket (`koz/server.py`) | `ws://127.0.0.1:8765` for the web app: every event as JSON, the 4 commands, trials → `trial_result` with the agent's changes. Refuses browser connections. Tested with a real WebSocket client; **not yet with Codex's web app.** |
| Cameras (`koz/capture.py`) | Recorded video (mock camera); live reader for the MacBook camera that drops the first second (too dark). **ESP32-CAM stream: not tried yet.** |
| Live demo (`scripts/live_demo.py`) | Colour job or `--job counter`: blurred view, red-object ring or people boxes + line, status, scene guesses; a full-width red banner when it stops or can't start (e.g. camera not allowed). Runs headless in tests. Live test #1 on your camera found the guard bug (fixed); **re-run pending.** |

## How to run

Double-click in Finder (uses the MacBook camera; q quits; if Ko'z stops, a red banner says why):
- `demo-agent.command`: type the job in words; Ko'z plans, tries, checks, adjusts and runs it
- `demo-blur.command`: privacy guard + face blur + colour finder (red object)
- `demo-counter.command`: people counter

Or in Terminal:

```bash
python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
.venv/bin/python scripts/fetch_test_photos.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/live_demo.py --i-own-this-camera
.venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter
.venv/bin/python scripts/live_demo.py --i-own-this-camera --strict   # schools, public cameras
.venv/bin/python scripts/agent_demo.py --i-own-this-camera "find the red ball"
.venv/bin/python -m koz.server --i-own-this-camera   # the runner the web app connects to
```

## What's next

1. You: try `demo-agent.command` with the red ball (and a ball that isn't quite red); live test #5 with `demo-blur.command`; the privacy trials in `docs/TRIALS.md`; the face clip.
2. You: put `NEBIUS_API_KEY=...` in `.env`, then `.venv/bin/python -m koz.agent.nebius --models` to see the Nemotron IDs.
3. Codex: connect the web app to `ws://127.0.0.1:8765`.
4. Fly-brain block (from the copied stage 2–3 code) + `firmware/motor_listener/` (car demo).
5. AWS in eu-central-1 on Oct 19–20.
6. Trials: car and classroom lists to write in `docs/TRIALS.md`.

## Known limits

- Privacy limits were set on 46 Places365 photos, not yet on your rooms; face-blur and tracker settings are still proposals.
- The default guard lets 3 of 23 private photos through: it sees no bed or toilet and isn't sure of the room, so it runs (trial 7 checks your bathroom). A bed mostly out of view can be missed. `--strict` stops all 23.
- Strict mode shows only in the live window and terminal, not in events (no contract field yet).
- The stricter guard stops more often by mistake ("uncertain"); the trials measure how often.
- Places365 has no toilet class; a toilet stall is trial #3.
- In glued-photo test clips NanoDet saw a "bed" at 0.40–0.44 while panning (false stop); raising the bed limit to 0.45 would avoid it (your decision).
- Which crossing direction counts as "in" (right-to-left of the line A→B) is defined in `koz/blocks/line_counter.py` but not yet in the contract; to agree with Codex in one short question.
- Someone standing on the counting line and swaying can be counted in and out.
- The live demo finds one fixed colour (red by default); the agent demo tunes it.
- The agent can only adjust the settings the contract lists (colour and detector numbers). The counting line's position is geometry, which the contract doesn't allow an adjustment to change; moving it needs a new start (or a contract change).
- "Target visible" passes if any patch of the asked colour is in view, not necessarily the ball (seen on a classroom photo with other red things).
- The plan texts in Uzbek and Russian need your check (`koz/agent/planner.py`).
- The web app talks to the runner on this computer (`ws://127.0.0.1:8765`, no login). The contract's cloud connection (runner → web with a runner token, section 5) comes with AWS.

