# Ko'z — tell a camera what job to do

You are working with Islombek, a self-taught builder in Uzbekistan. Claude Code is the lead engineer; Codex is the second engineer (see "Lanes" and "Cross-Model Collaboration").

## The product
A person describes a camera job in plain words (Uzbek, Russian or English). An AI agent turns it into a **recipe** (a JSON list of tested OpenCV 5 blocks + settings), runs it on live frames, checks the results, adjusts, then connects it to an action (motors, alert, dashboard). Recipes can be exported as a file and imported by anyone with a similar camera.

Brainstorm page: https://claude.ai/artifact/U9zJc3dcBAqr2spWpdXHW5

## Deadlines (Tashkent time)
- **OpenCV AI Competition: Oct 27, 11:45.** Target: submitted Oct 26 evening. https://opencv26.devpost.com
- Nebius × NVIDIA (Physical AI): Oct 30, 22:00. Same code; the planner model is Nemotron on Nebius Token Factory.
- Oct 22: no building.

## MVP scope for Oct 26 (nothing else until this works)
1. Camera input: ESP32-CAM stream; also a phone/RTSP camera if easy.
2. About 8 OpenCV 5 blocks: color finder, motion zone, person detector, line counter, face blur, **privacy guard**, fly-brain steering, (stretch) looming detector.
3. Recipe runner: loads a recipe JSON, runs blocks in order, emits events.
4. Agent loop: words → recipe → run on live/recorded frames → check results → adjust (max 3 rounds) → run.
5. Web app on AWS: setup chat (Uz/Ru/En text), live status, trial dashboard, recipe export/import.
6. Three demos: fly-brain car chases the red ball; classroom counter with faces blurred; privacy guard stops a camera pointed at a bathroom.
7. Evaluation: 10 trials per demo, failures recorded.

**Later (not before Oct 27):** voice in Uzbek; camera setup helper (photo or model name → short setup guide); public recipe library. **Never:** letting the agent control the user's computer.

## Privacy and refusals (v1 — agreed Oct 14)
Claude and Codex each proposed rules in /collab, debated once and merged them; Islombek set the scope. Tags:
**MVP** = enforced in code by Oct 26 · **simple** = a simple version in code by Oct 26 · **stretch** = only if everything else works by Oct 23 · **design** = in the report as design, never claimed as built.
Every refusal returns a fixed error code and a fixed Uz/Ru/En message (list in `contracts/events.md`). A refused plan never runs. Software can't prove who owns a camera or where it points; the report says so.

1. **Safety lives in fixed code, not in the AI.** `MVP`
   - Why: the planner can be talked around (3 languages, 2 Uzbek alphabets, a tampered import), and the adjust loop chases "it works", which could mean "remove the blur".
   - Code: `koz/policy.py` holds the allowlist (blocks, setting ranges, locked safety blocks: privacy guard, face blur). `koz/recipe.py` checks planner output, every adjust round and every import; it rejects unknown fields, code, URLs, file paths and model files. The runner runs only checked recipes. The planner's only tool is "propose a recipe". 3 failed rounds → the job stays off.
2. **The privacy guard stops on what it sees.** `MVP` (updated Oct 15, live tests #1–#4)
   - Why: a room model can't tell a desk in a bedroom from a bedroom, and refused every room in a real home; a bed or a toilet in view is something a person can check. A classifier mistake must still never let a frame through unchecked.
   - Code: `koz/privacy.py` sits between the camera and every block; only APPROVED frames go on, and while it confirms something it saw once, no frame is shown and no block runs. Default for every job: stop on a bed or toilet in view (NanoDet, 2 of 3 checks), a sink with a bathroom-like room, a dark or covered lens, or a confident private room (Places365); otherwise run. `--strict`, and every school-mode job, runs only in listed public places. Objects checked every 0.5 s, the room every 3 s, and on the next frame when the camera moves. A missing model, an error or a slow check stops the job. Measured on 71 real photos: the default lets 3 of 23 bathroom/bedroom photos through, strict none (`docs/TRIALS.md`). It is an alarm, not proof that a room is safe.
3. **Scene-change tripwire on fixed cameras.** `stretch`
   - Why: with a check only every few minutes, a camera turned toward a bathroom keeps working for minutes.
   - Code: at approval, keep a small grey reference frame in memory only. Every frame: histogram distance + mean pixel difference; a dark, flat image means the lens is covered. Big change → hold outputs, re-run the scene check, resume only if APPROVED. Not on the moving car.
4. **No identity, by any route.** `MVP`
   - Why: identity turns counting into surveillance, and shops will ask ("tell me when he comes back", "read number plates").
   - Code: no blocks exist for face recognition, face fingerprints (embeddings), body or walk matching, plate/document/badge reading or OCR. Counting track IDs live in memory, expire seconds after the person leaves, and have no field in the event format.
5. **No profiling or judging people.** `MVP`
   - Why: "lazy worker", "suspicious customer" or "pupil not paying attention" can get someone punished without anyone saying a name.
   - Code: no age, gender, ethnicity, emotion or religion blocks; no per-person timers, scores or rankings; no automatic police or discipline reports. Events hold only zone counts and fixed labels; alert text comes from fixed templates, never from the LLM.
6. **School mode is locked down.** `simple`
   - Why: children can't consent, and software can't check whether a teacher may film.
   - Code (simple): a `school` flag forces face blur before every other block and allows counts only.
   - Design: coarse time bins, no remote video, snapshots or per-pupil output; the UI says consent is the school's job.
7. **Only allowed, visible views, never the neighbours.** `simple`
   - Why: owning a camera gives no right to film a neighbour's courtyard, windows or the mahalla street; hidden use is the biggest misuse risk.
   - Code (simple): an "I own this camera" checkbox and an allowed-area mask; pixels outside it are blacked out before any block. The dashboard shows "camera on".
   - Design: stated purpose and notice, redo setup when the camera moves, setup never comes from an imported recipe.
8. **Frames never leave the device; no audio at all.** `MVP`
   - Why: biometric data must be stored in Uzbekistan (Law ZRU-1125, 26 Mar 2026) and AWS has no region there; frames that never leave avoid the question.
   - Code: `koz/capture.py` opens video only, never the microphone. Frames live in a small memory buffer; no code writes frames to disk (no screenshots, no debug dumps); the preview is local and blurred.
9. **The cloud and the planner get numbers, not pictures.** `MVP` + `simple`
   - Why: limits what can leak, and stops prompt injection from the scene (someone holding up a sign with instructions for the AI).
   - Code (MVP): the fixed event format in `contracts/events.md` (numbers, fixed labels, rounded times; images, free text, embeddings and track IDs are rejected) and a simple login (the account comes from the login, never from the request). The planner gets the user's text, the checked recipe and numbers, never pixels or camera-derived text.
   - Code (simple): a "don't type names" note in the setup chat.
   - Design: per-operation permission checks. Report limitation: chat text goes to Nebius abroad, and no approved cross-border route is set up.
10. **Stale or overloaded means stop and say "unknown".** `MVP`
    - Why: a frozen stream must not look like "0 people, all fine", or starve the privacy check.
    - Code: `recipe.py` caps resolution, number of blocks and settings. `runner.py` keeps only the newest frame and gives each a deadline; late or missing → outputs say `unknown` (not 0), actions pause, motors stop. Jobs where Ko'z would be the only protection (a child alone, fire, medical) are refused.
11. **Motors never aim at people and stop by themselves.** `MVP`
    - Why: a crash or bad command must not leave a robot driving into a child or an animal.
    - Code (MVP): in `firmware/motor_listener/`, the board starts stopped, a timer stops the motors if no fresh command arrives within 250 ms, speed is capped, and the ultrasonic sensor stops the car at a distance above its measured stopping distance. Islombek adds a physical switch.
    - Design: steering takes input only from the colour and looming blocks; no locks, gates, shocks or chasing people/animals; re-arm by hand after a fault.
12. **Data deletes itself.** `MVP`
    - Why: logs outlive their purpose, and exact times can point back to a pupil.
    - Code: the cloud database's built-in auto-delete: events after 7 days, totals after 30. Trial summaries the owner saves stay until the owner deletes them. Local logs never hold frames or prompts.

## Hard rules from the OpenCV competition
- OpenCV 5 must do real image/video analysis at runtime, central to the project. A meaningful part runs on AWS.
- Submit: technical report (problem, users, architecture, OpenCV 5, AWS, evaluation, limitations, responsible use); repo with pinned dependencies and run/test steps; architecture diagram; web endpoint or live screen-share; video ≤ 5 min; evaluation evidence with failure cases.
- Rubric: technical execution 30, innovation 20, real-world impact 20, UX 10, documentation 10, cloud delivery/reproducibility/responsible ops 10.
- Agentic Vision award ($1k): OpenCV 5 output must change the agent's next plan, tool call or action. Our check-and-adjust loop and the privacy guard are that.
- Never claim a result we have not measured.

## Lanes (so the two AIs never edit the same files)
- **Claude Code — core:** `koz/` (blocks, recipe runner, agent loop, fly brain, privacy guard), `firmware/` (Arduino motor listener), `tests/`.
- **Codex — web + review:** `web/` (setup chat, dashboard, recipe export/import, AWS deploy), plus tests and reviews of Claude's code via `/collab-review`.
- **Design brief:** `docs/DESIGN.md` (Islombek's; Codex builds the web UI from it).
- **Shared contract, written first, changed only by agreement:** `contracts/recipe.schema.json` and `contracts/events.md`.
- **Islombek:** hardware, trials, video, every final decision. He must be able to explain every part.

## The robot (stages 1–3 already work)
Arduino Uno, L298N, 4 gear motors, LM2596, ultrasonic sensor on a scanning servo, ESP32-CAM, runs from his MacBook. The original stage 1–3 code is in his maker portfolio: **never modify it.** Ask where it is, copy what is needed into `koz/brains/flybrain/`, and build on the copy.

**The robot is a demo of Ko'z, not the product.** A user types: "ESP32-CAM on a robot car, Arduino Uno + L298N, 4 motors — make it chase the red ball with a fruit-fly brain." Ko'z does not generate new firmware. It builds a recipe from existing blocks: camera → color finder → fly-brain block → motor block, runs it, and checks the car really moves toward the ball. Built once, beforehand:
- `firmware/motor_listener/`: a tiny Arduino sketch that only receives "left speed, right speed" over USB serial.
- the fly-brain block, from the copy of stage 2–3 code.
Second demo, no robot: a teacher types "count students entering my class, blur faces" — same Ko'z, different blocks. This shows it is universal.

## Decisions and ideas log (Oct 13)
Islombek's ideas, decided:
- Ko'z itself: describe a camera job in plain words; AI builds it. **In.**
- Uzbek, Russian, English (text). **In.** Voice in Uzbek: later.
- Shareable, downloadable recipes, so a shop with the same camera reuses another's setup. **In** as export/import of a recipe file. Public recipe library: later.
- Privacy shut-off when the camera sees a toilet or bathroom. **In** (privacy guard block).
- Works with cameras people already own (shops, markets, homes). **In** if easy (RTSP/phone); otherwise first thing after Oct 26.
- Camera setup helper: user sends a photo or model name, gets a short, easy setup guide. **Later** (good fit for Nebius after Oct 26).
- Different insect brains as different "personalities" (fly vs worm). **Later**; mention in the report as future work.
- AI controlling the user's laptop to set things up. **No**: too risky and too big.
Claude's additions:
- The agent picks from tested blocks instead of writing free code (reliability).
- Faces blurred by default; no identity (judges can reject surveillance risk).
- Fly-eye looming detector (LPLC2 neurons) as a stretch block.
- Lanes: Claude = core, Codex = web + review, shared contract first.
- Fallback: if the agent loop isn't working by Oct 21, ship the fly-brain car with OpenCV 5 + AWS dashboard.
- Differs from LandingAI VisionAgent: $10 camera, no GPU, tests itself on live frames, drives real actions.

## How we work
- Python 3 for `koz/`. Pin every dependency. Tests: `python -m pytest`. Hardware code gets a mock mode.
- Explain non-obvious code in plain words. Define jargon.
- Log every substantial AI contribution in `AI_LOG.md` (date · which AI · what it did · what Islombek decided).
- Secrets only in `.env` (git-ignored). Commit before every Codex build. "Done" = tests + Islombek's own demo pass.

## Cross-Model Collaboration (Codex)
Claude Code can delegate to OpenAI Codex via `.claude/bin/codex-bridge.sh` (subscription login, no API key).

| Command | Purpose |
|---------|---------|
| `/collab <task>` | Think, build, or debug with Codex |
| `/collab-review` | Quick second opinion from Codex on current changes |

- `codex-bridge.sh think "prompt"` — read-only (sync). `codex-bridge.sh build "prompt"` — workspace-write (async). Specs in `.collab/specs/`.
- Get Codex's independent view before showing it yours. Never overlap files. Run the tests yourself after Codex builds. Keep Codex prompts under 500 words. Synthesize, don't relay.
