# Ko'z status

Updated Oct 19, after the motor soft start and the three "Try again" fixes (AWS day). Tests below.
`.venv/bin/python -m pytest -q`

## What works

| Part | State |
|---|---|
| Recipe checks (`koz/recipe.py`) | Strict parsing → contract schema → extra checks → "is it built?". Tested. |
| Privacy guard (`koz/privacy.py`, `koz/scene.py`) | **Default (every job): run anywhere, stop on what it sees**: darkness or a covered lens, a bed or toilet (NanoDet ≥ 0.40 in 2 of 3 checks), a sink in what looks like a bathroom, or a confident private room (top guess ≥ 0.50, or ≥ 0.55 together). **`--strict`** (schools, public cameras): only listed public places run. Objects checked every 0.5 s, the room every 3 s, and on the next frame when the camera moves; stops 0.07 s after a toilet or bed comes into view on recorded clips (target 1 s); one line per check, with timings. On 71 real photos: default runs every desk without a bed, kitchen, classroom and shop, and lets 4 of 23 bathroom/bedroom photos through (limit); strict stops all 23. **Room guard tuning stopped (Oct 16): demos are filmed outside the bedroom.** **Live stop time: to measure (live test #5).** |
| Face blur (`koz/blocks/face_blur.py`) | YuNet on OpenCV 5, heavy pixelation, fails closed. **No real-face test yet** (waiting for your clip in `tests/fixtures/private/face.mp4`). |
| Colour finder (`koz/blocks/color_finder.py`) | The biggest **round** patch of one colour (roundness ≥ 0.65, fills ≥ 0.70 of its circle, radius ≥ 8 px; fixed in code) → left / center / right / lost. Measured on drawn shapes: finds balls (small, highlighted, a quarter hidden, a third out of the frame); rejects squares, rectangles, triangles, long ovals and the orange-lit classroom that fooled it. **Not yet tried on a real ball on camera.** |
| Person detector (`koz/blocks/person_detector.py`) | NanoDet-Plus on OpenCV 5, "person" class only; boxes stay local, only the number of people is sent. Decoding tested with exact fake outputs. **Not yet measured on real people.** |
| Line counter (`koz/blocks/line_counter.py`) | In-memory tracker; counts crossings through the line segment in each direction; person numbers forgotten 2 s after they leave. Tested with scripted walkers. |
| Runner (`koz/runner.py`) | mask → privacy → blur → blocks → events; stale or slow frames → `unknown` with a reason. School mode allows the counter only. |
| Events (`koz/events.py`) | All 7 types (status, recipe, observation, decision, command_result, fault, trial_result), checked against `contracts/events.md` before sending. |
| Agent loop (`koz/agent/`) | Words → plan → try 3 s → check the OpenCV numbers → change one setting → try again (3 tries at most) → run. Each step is an event (observation → decision → new revision → result) and one printed line. Refusals stop before the camera opens. On recorded clips: red asked, ball looks orange-red → hue 0 → 13, found; with the real models, green asked for a teal ball → hue 60 → 77, found. **Not yet tried on your camera.** |
| Planners (`koz/agent/`) | **Default: the rule planner** (Nebius first if a key exists, then Amazon Nova 2 Lite on Bedrock if `AWS_BEARER_TOKEN_BEDROCK` is in `.env`; Bedrock tested with a fake network only, real score on Oct 19). Uzbek in both alphabets. Islombek's 20 fresh sentences: **20/20 before any fix, but 4 of 7 refusals only because nothing matched**; after new refusal rules 20/20 with all refusals by a rule (tuned on that set). The AI only picks job / colour / school / refusal; any refusal wins. Gemma 4 on this Mac: 14/20, removed (in the Trash). |
| Runner WebSocket (`koz/server.py`) | `ws://127.0.0.1:8765` for the web app: every event as JSON, the 4 commands, trials → `trial_result` with the agent's changes. Refuses browser connections. `--window` shows each job's blurred camera view. `--cloud wss://IP/v1/runner` connects out to the web app on AWS (contract section 5: status first, offline queue, no replay); tested against the web app's token mode on this Mac. |
| The eye (`koz/eye.py`) | A live preview for the local web app only: JPEG ≤ 640 px, ≤ 15 per second (13–14 measured, was 4.6), only approved and face-blurred frames; tap it for a large view, on `ws://127.0.0.1:8765/v1/preview`; closes with a reason (not_running, checking, not_fresh). Never stored, never on the cloud link (a test checks every cloud message). Web side: Codex (`.collab/specs/web-eye-preview.md`). |
| AWS (`deploy/`) | One CloudFormation stack: t3.micro in Sydney (the AWS project's Region), Nginx + Let's Encrypt IP certificate, DynamoDB with auto-delete, owner password generated in Secrets Manager, no SSH. Click list and record: `docs/AWS_DAY.md`. **Live since Oct 22: https://16.178.45.27/** (Sydney; valid HTTPS; judges' view with no login loads no picture and no socket; eye route 404). Bedrock planner not measurable (zero daily tokens on the new account): rule planner stays. Next: Islombek logs in, makes the runner token, connects the Mac. |
| Firmware (`firmware/`) | `motor_listener`: USB `ARM / DISARM / STOP / M,L,R`; starts disarmed; a fault (250 ms without commands, forward into an obstacle, forward while blind) disarms until armed by hand; speed caps. Since Oct 19, as in Islombek's own `car.ino`: at most 6 V to the motors from the 9.5 V pack, a soft start (2 PWM per ms) and stop-before-reverse (40 ms); near an obstacle the soft start never adds up to forward motion (security review, tests first). Safety rules tested on the Mac (logic and the real sketch on a fake Arduino); both sketches compile for the Uno. `stop_test` + README to measure the speed cap and stopping distance. **Not yet on the car.** |
| Fly brain (`koz/brains/flybrain/`) | Copy of the original simulation (same spikes), the driver (same wheels), and option B steering. Simulation only: reaches the ball in ~3 s from most starts. **Time box: chasing reliably (at least 7 of 10 trials) by Oct 21, else option A.** |
| Motors (`koz/actions/motors.py`) | Serial link + mock; speed = the lower of the recipe's 0.25 and the local cap (0.15 until measured); stops on stale frames and during privacy checks; disarms at job end; armed only by a person (Enter / A key). **Codex's motor safety review (5 findings) and its re-review (3 more) fixed, tests first** (`tests/test_motor_safety.py`, `firmware/tests/test_sketch.cpp`): Stop halts at once and before it is reported; any stop, job end or USB failure locks the link until a person arms again; the sketch stops the motors within 250 ms of the last command even while the sonar pings, and reads only exact lines. Codex's confirmation of the last 3 fixes is pending (quota). |
| Cameras | `--camera slot=source`: this Mac, the ESP32-CAM MJPEG stream, a phone (MJPEG or RTSP). `--upside-down` / `--mirror` for a camera mounted that way (the car's ESP32-CAM is upside down, as in the original `config.py`): turned before the guard sees it. The web can pick a slot once Codex adds it (`.collab/specs/web-camera-choice.md`). |
| One launcher (`start-koz.command`) | Runner + web app, opens Setup. One camera view: the eye in the browser (`KOZ_WINDOW=1` adds the runner window). Enter in its Terminal arms a car's motors (the runner now reads that Terminal). Closing Terminal (HUP) or TERM stops both. |
| Web Live screen (UX pass, Oct 18) | Every state says why, what to do, and one obvious action in Stop's place (Try again / New job after a stop); a privacy stop names what the guard saw; plain words in Uz/Ru/En; the eye's picture fills the eye; a 3-second test bar. Screenshots of all 10 states: `web/review/states/`. Codex's 3 findings fixed (Oct 19, tests first): a fault or an unknown number never shows green "Running" (amber, in the contract's words, e.g. OVERLOADED; a privacy stop shows at once); Try again keeps the job's camera, even after a page reload (this tab keeps only session, job and camera); in a trial whose one job ran, one button "Finish trial and try again" (saved as unknown, interrupted) instead of BUSY. Checked in a real browser with the real Hub (`web/review/states/retry_probe.mjs`). |
| Texts (`docs/TEXTS.md`) | Every Uzbek and Russian plan, refusal and stop text, made from the code and the contract (a test keeps it up to date). **Waiting for your check.** |
| Cameras (`koz/capture.py`) | Recorded video (mock camera); live reader for the MacBook camera that drops the first second (too dark). **ESP32-CAM stream: not tried yet.** |
| Live demo (`scripts/live_demo.py`) | Colour job or `--job counter`: blurred view, red-object ring or people boxes + line, status, scene guesses; a full-width red banner when it stops or can't start (e.g. camera not allowed). Runs headless in tests. Live test #1 on your camera found the guard bug (fixed); **re-run pending.** |

## How to run

Double-click in Finder (uses the MacBook camera; q quits; if Ko'z stops, a red banner says why):
- `start-koz.command`: the runner and the web app together; type the job in the browser's Setup page
- `demo-agent.command`: type the job in Terminal; Ko'z plans, tries, checks, adjusts and runs it
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

1. You, Tue Oct 20: `docs/CAR_DAY.md` (portfolio recordings with the original car first, stop test, motor_listener, 10 chase trials, original back). Option B time box: Wed Oct 21.
2. You: then the classroom and privacy trials; the video (`docs/VIDEO.md`); check the report draft (`docs/REPORT.md`).
3. Codex: `.collab/specs/web-camera-choice.md` and `web-planner-and-live.md`.
4. Mon Oct 19: `docs/AWS_DAY.md` ($1 budget first). Before it: make the GitHub repo public (your decision) and Codex builds `.collab/specs/aws-review.md`.

## Known limits

- Privacy limits were set on 46 Places365 photos, not yet on your rooms; face-blur and tracker settings are still proposals.
- The default guard lets 4 of 23 private photos through: it sees no bed or toilet and isn't sure of the room, so it runs (trial 7 checks your bathroom). A bed mostly out of view can be missed. `--strict` stops all 23.
- Strict mode shows only in the live window and terminal, not in events (no contract field yet).
- The stricter guard stops more often by mistake ("uncertain"); the trials measure how often.
- Places365 has no toilet class; a toilet stall is trial #3.
- In glued-photo test clips NanoDet saw a "bed" at 0.40–0.44 while panning (false stop); raising the bed limit to 0.45 would avoid it (your decision).
- Which crossing direction counts as "in" (right-to-left of the line A→B) is defined in `koz/blocks/line_counter.py` but not yet in the contract; to agree with Codex in one short question.
- Someone standing on the counting line and swaying can be counted in and out.
- The live demo finds one fixed colour (red by default); the agent demo tunes it.
- The agent can only adjust the settings the contract lists (colour and detector numbers). The counting line's position is geometry, which the contract doesn't allow an adjustment to change; moving it needs a new start (or a contract change).
- "Target visible" now needs a round blob, but any round thing of that colour counts (a red plate, a red lamp). A ball more than half out of the frame, or stretched more than about 1.5 : 1 by motion blur, counts as lost.
- The plan texts in Uzbek and Russian need your check (`koz/agent/planner.py`).
- The cloud connection (runner → web on AWS with a runner token) is built and tested on this Mac, not yet on AWS.
- At Islombek's desk (in a bedroom) the default guard still stops when the room looks very like a bedroom (with the 0.55 limit: 43 stops in the first 100 s, then 191 s without a stop). Every stop logs why (`docs/TRIALS.md`).
- The rule planner's 20/20 after the Cyrillic fix is on the sentences that showed the gap: a fresh set of real sentences is needed before claiming a number.
- Recorded clips (`--video`) now play at their own speed, like a camera.

