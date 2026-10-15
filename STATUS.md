# Ko'z status

Updated Oct 15, after live test #3 (new default guard). 203 tests pass, 1 skipped (it needs your face clip):
`.venv/bin/python -m pytest -q`

## What works

| Part | State |
|---|---|
| Recipe checks (`koz/recipe.py`) | Strict parsing → contract schema → extra checks → "is it built?". Tested. |
| Privacy guard (`koz/privacy.py`, `koz/scene.py`) | **Default (every job): run anywhere, stop on what it sees**: darkness or a covered lens, a bed or toilet (NanoDet ≥ 0.40 in 2 of 3 checks), a sink in what looks like a bathroom, or a confident private room (top guess ≥ 0.50, or ≥ 0.40 together). **`--strict`** (schools, public cameras): only listed public places run. Checks every 10 s; one line per check on screen and in the terminal. On 71 real photos: default runs every desk without a bed, kitchen, classroom and shop, and lets 3 of 23 bathroom/bedroom photos through (limit); strict stops all 23. **Your rooms: live test #4 pending.** |
| Face blur (`koz/blocks/face_blur.py`) | YuNet on OpenCV 5, heavy pixelation, fails closed. **No real-face test yet** (waiting for your clip in `tests/fixtures/private/face.mp4`). |
| Colour finder (`koz/blocks/color_finder.py`) | Biggest patch of one colour → left / center / right / lost. Tested on the recorded test video. |
| Person detector (`koz/blocks/person_detector.py`) | NanoDet-Plus on OpenCV 5, "person" class only; boxes stay local, only the number of people is sent. Decoding tested with exact fake outputs. **Not yet measured on real people.** |
| Line counter (`koz/blocks/line_counter.py`) | In-memory tracker; counts crossings through the line segment in each direction; person numbers forgotten 2 s after they leave. Tested with scripted walkers. |
| Runner (`koz/runner.py`) | mask → privacy → blur → blocks → events; stale or slow frames → `unknown` with a reason. School mode allows the counter only. |
| Events (`koz/events.py`) | status, observation (target, people, in, out), fault, exactly as `contracts/events.md`. |
| Cameras (`koz/capture.py`) | Recorded video (mock camera); live reader for the MacBook camera that drops the first second (too dark). **ESP32-CAM stream: not tried yet.** |
| Live demo (`scripts/live_demo.py`) | Colour job or `--job counter`: blurred view, red-object ring or people boxes + line, status, scene guesses; a full-width red banner when it stops or can't start (e.g. camera not allowed). Runs headless in tests. Live test #1 on your camera found the guard bug (fixed); **re-run pending.** |

## How to run

Double-click in Finder (uses the MacBook camera; q quits; if Ko'z stops, a red banner says why):
- `demo-blur.command`: privacy guard + face blur + colour finder (red object)
- `demo-counter.command`: people counter in school mode

Or in Terminal:

```bash
python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
.venv/bin/python scripts/fetch_test_photos.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/live_demo.py --i-own-this-camera
.venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter --school
.venv/bin/python scripts/live_demo.py --i-own-this-camera --strict   # schools, public cameras
```

## What's next

1. You: live test #4 with `demo-blur.command` (desk, bed, bathroom, covered lens); then the privacy trials in `docs/TRIALS.md`; the face clip.
2. Contract (maybe): a `strict` flag in `status` and `trial_result`, so the dashboard and trial reports can show the mode; to agree with Codex.
3. Fly-brain block (from the copied stage 2–3 code) + `firmware/motor_listener/` (car demo).
4. Agent loop: words → recipe → check on live frames → adjust (max 3 tries).
5. Web app (Codex's lane) and AWS in eu-central-1 on Oct 19–20.
6. Trials: car and classroom lists to write in `docs/TRIALS.md`.

## Known limits

- Privacy limits were set on 46 Places365 photos, not yet on your rooms; face-blur and tracker settings are still proposals.
- The default guard lets 3 of 23 private photos through: it sees no bed or toilet and isn't sure of the room, so it runs (trial 7 checks your bathroom). A bed mostly out of view can be missed. `--strict` stops all 23.
- Strict mode shows only in the live window and terminal, not in events (no contract field yet).
- The stricter guard stops more often by mistake ("uncertain"); the trials measure how often.
- Places365 has no toilet class; a toilet stall is trial #3.
- Which crossing direction counts as "in" (right-to-left of the line A→B) is defined in `koz/blocks/line_counter.py` but not yet in the contract; to agree with Codex in one short question.
- Someone standing on the counting line and swaying can be counted in and out.
- The live demo finds one colour (red by default); the agent loop will tune it later.
