# Ko'z status

Updated Oct 14, after the classroom blocks. 136 tests pass, 1 skipped (it needs your face clip):
`.venv/bin/python -m pytest -q`

## What works

| Part | State |
|---|---|
| Recipe checks (`koz/recipe.py`) | Strict parsing → contract schema → extra checks → "is it built?". Tested. |
| Privacy guard (`koz/privacy.py`, `koz/scene.py`) | Places365 on OpenCV 5; blocks 16 private rooms; fails closed (errors, slow or stuck checks, uncertain scenes all stop the job). Rechecks every 120 s. **Not yet measured on real rooms.** |
| Face blur (`koz/blocks/face_blur.py`) | YuNet on OpenCV 5, heavy pixelation, fails closed. **No real-face test yet** (waiting for your clip in `tests/fixtures/private/face.mp4`). |
| Colour finder (`koz/blocks/color_finder.py`) | Biggest patch of one colour → left / center / right / lost. Tested on the recorded test video. |
| Person detector (`koz/blocks/person_detector.py`) | NanoDet-Plus on OpenCV 5, "person" class only; boxes stay local, only the number of people is sent. Decoding tested with exact fake outputs. **Not yet measured on real people.** |
| Line counter (`koz/blocks/line_counter.py`) | In-memory tracker; counts crossings through the line segment in each direction; person numbers forgotten 2 s after they leave. Tested with scripted walkers. |
| Runner (`koz/runner.py`) | mask → privacy → blur → blocks → events; stale or slow frames → `unknown` with a reason. School mode allows the counter only. |
| Events (`koz/events.py`) | status, observation (target, people, in, out), fault, exactly as `contracts/events.md`. |
| Cameras (`koz/capture.py`) | Recorded video (mock camera); live reader for the MacBook camera. **ESP32-CAM stream: not tried yet.** |
| Live demo (`scripts/live_demo.py`) | Colour job or `--job counter`: blurred view, red-object ring or people boxes + line, status, scene guesses. Runs headless in tests; **not yet run on your real camera.** |

## How to run

Double-click in Finder (uses the MacBook camera; q quits):
- `demo-blur.command`: privacy guard + face blur + colour finder (red object)
- `demo-counter.command`: people counter in school mode

Or in Terminal:

```bash
python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/live_demo.py --i-own-this-camera
.venv/bin/python scripts/live_demo.py --i-own-this-camera --job counter --school
```

## What's next

1. You: run both demos on the MacBook camera; record the face clip.
2. Fly-brain block (from the copied stage 2–3 code) + `firmware/motor_listener/` (car demo).
3. Agent loop: words → recipe → check on live frames → adjust (max 3 tries).
4. Web app (Codex's lane) and AWS in eu-central-1 on Oct 19–20.
5. Trials: `docs/TRIALS.md` (privacy list drafted; car and classroom lists to write).

## Known limits

- Privacy thresholds (15 % private, 20 % top answer), face-blur and tracker settings are proposals until the trials measure them.
- Places365 has no toilet class; a toilet stall is trial #3.
- Which crossing direction counts as "in" (right-to-left of the line A→B) is defined in `koz/blocks/line_counter.py` but not yet in the contract; to agree with Codex in one short question.
- Someone standing on the counting line and swaying can be counted in and out.
- The live demo finds one colour (red by default); the agent loop will tune it later.
