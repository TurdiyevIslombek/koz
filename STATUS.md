# Ko'z status

Updated Oct 15, after live test #2 (object check in the privacy guard). 197 tests pass, 1 skipped (it needs your face clip):
`.venv/bin/python -m pytest -q`

## What works

| Part | State |
|---|---|
| Recipe checks (`koz/recipe.py`) | Strict parsing → contract schema → extra checks → "is it built?". Tested. |
| Privacy guard (`koz/privacy.py`, `koz/scene.py`) | Every check: darkness, then an **object check** (NanoDet: a bed or toilet at ≥ 0.40 in 2 of 3 checks stops it; a sink only with a bathroom-like room), then the room check (Places365). **Strict**: allowlist (≥ 0.30; corridors/lobbies ≥ 0.50), private room in the top 5 above 0.10 stops. **Workspace** (`demo-desk*.command`): room check stops only when confident (private top guess ≥ 0.50, or ≥ 0.40 together). Checks every 10 s; one line per check on screen and in the terminal. On 71 real photos: strict stops all 23 bathrooms/bedrooms; workspace runs 10/12 desks and all kitchens but approves 3 of 23 private photos (limit). **Your rooms: live test #3 pending.** |
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
- `demo-blur.command`: privacy guard + face blur + colour finder, **strict** (to check a bathroom or bedroom is refused)
- `demo-counter.command`: people counter in school mode, **strict** (runs only in an allowed place, e.g. a classroom)
- `demo-desk.command`: colour finder + face blur with the **owner-confirmed workspace** (your desk, the robot arena)
- `demo-desk-counter.command`: people counter (school mode) with the **owner-confirmed workspace**

Or in Terminal:

```bash
python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
.venv/bin/python scripts/fetch_test_photos.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/live_demo.py --i-own-this-camera
.venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter --school
.venv/bin/python scripts/live_demo.py --i-own-this-camera --owner-workspace   # your desk / robot arena
```

## What's next

1. You: live test #3 (`demo-desk.command` at your desk, bed out of view; then with the bed in view; `demo-blur.command` in the bathroom); the privacy trials in `docs/TRIALS.md`; the face clip.
2. Contract: `owner_workspace` in `status` and `trial_result`, to agree with Codex after 22:11 (quota), so the dashboard and trial reports show it.
3. Fly-brain block (from the copied stage 2–3 code) + `firmware/motor_listener/` (car demo).
4. Agent loop: words → recipe → check on live frames → adjust (max 3 tries).
5. Web app (Codex's lane) and AWS in eu-central-1 on Oct 19–20.
6. Trials: car and classroom lists to write in `docs/TRIALS.md`.

## Known limits

- Privacy limits were set on 46 Places365 photos, not yet on your rooms; face-blur and tracker settings are still proposals.
- Living room and kitchen aren't on the allowlist; use the owner-confirmed workspace for your own desk or arena.
- The owner-confirmed workspace trusts you: on 3 of 23 private photos it sees no bed or toilet and isn't sure of the room, so it approves them (trial W3 checks your bathroom). A bed mostly out of view can be missed.
- Until the contract change, the workspace shows only in the live window and terminal, not in events.
- The stricter guard stops more often by mistake ("uncertain"); the trials measure how often.
- Places365 has no toilet class; a toilet stall is trial #3.
- Which crossing direction counts as "in" (right-to-left of the line A→B) is defined in `koz/blocks/line_counter.py` but not yet in the contract; to agree with Codex in one short question.
- Someone standing on the counting line and swaying can be counted in and out.
- The live demo finds one colour (red by default); the agent loop will tune it later.
