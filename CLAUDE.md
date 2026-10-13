# FlyBrainCar × OpenCV AI Competition 2026

You are working with Islombek, a self-taught builder in Uzbekistan, on his entry to the OpenCV AI Competition 2026, powered by AWS. You are the PM; Codex is the second engineer (see "Cross-Model Collaboration" below).

## Deadline
- Hard deadline: **Oct 27, 2026, 11:45 Tashkent time** (Oct 26, 23:45 PT), on Devpost: https://opencv26.devpost.com
- Our target: **submitted on the evening of Oct 26**.
- Oct 22 is a no-build day.

## The robot (already built; stages 1–3 work)
- Arduino Uno, L298N motor driver, 4 gear motors, LM2596 regulator, one ultrasonic sensor on a front scanning servo, ESP32-CAM. Runs from his MacBook.
- Stage 1: if-else obstacle avoidance (Islombek wrote it himself, no AI).
- Stage 2: the ultrasonic sensor feeds a simulated fruit-fly connectome on the laptop, which steers.
- Stage 3: the ESP32-CAM replaces the ultrasonic sensor.
- The original stage 1–3 code is part of his maker portfolio. **Never modify the original.** Ask him where it is, copy what is needed into `robot/` in this repo, and build on the copy.

## What we are building (MVP)
1. **Perception, OpenCV 5 on the laptop:** read the ESP32-CAM stream, detect the target and obstacles, turn their positions into the connectome's sensory input.
2. **Decision and action:** the connectome steers the motors. That is the perception → decision → action loop.
3. **AWS:** a small service that stores every trial (detections, neuron activity, outcome) and serves a judge-facing dashboard with replays and metrics. This is the "working web endpoint". The robot itself is shown by live screen-share.
4. **Evaluation:** 10 trials per task. Success rate, collisions, time to target. Stage 2 (ultrasonic) vs the OpenCV 5 version. Record the failures too.

## Hard rules from the competition
- OpenCV 5 must do real image or video analysis at runtime, central to the project (not just installed).
- A meaningful part of the system must run on AWS.
- Submission package: technical report (problem, users, architecture, OpenCV 5 implementation, AWS deployment, evaluation, limitations, responsible use); judge-accessible repo with pinned dependencies and build/run/test steps; architecture diagram; working web endpoint or scheduled live screen-share; public or unlisted video of 5 minutes or less; evaluation evidence including failure cases.
- Rubric: technical execution 30, innovation 20, real-world impact 20, user experience 10, documentation 10, cloud delivery/reproducibility/responsible operation 10.
- Weakest score will be real-world impact. Pick one honest angle early (for example: a low-cost open kit that lets students without GPUs study how real brain wiring produces behaviour) and claim only what we test.
- Optional $1,000 Agentic Vision award: only if an agent uses OpenCV 5 output to change its next plan, tool call or action. An AI coding assistant writing our code does NOT count.
- Never claim a result we have not measured.

## Branches
- `main`: the OpenCV entry.
- Later, `nebius`: adds a Nemotron planner on Nebius Token Factory for the Nebius × NVIDIA hackathon (deadline Oct 30, 22:00 Tashkent). Only after the OpenCV entry is submitted.

## How we work
- Python 3. Pin every dependency in `requirements.txt`. Tests: `python -m pytest`. Every module that doesn't need hardware gets tests; hardware code gets a mock or simulation mode so it can be tested without the robot.
- Islombek must be able to explain every part to judges. When you write something non-obvious, explain it in plain words; define any jargon.
- Log every substantial AI contribution in `AI_LOG.md` (date · which AI · what it did · what Islombek changed or decided). Competitions ask for this.
- Never touch: the original stage 1–3 code, anything outside this folder, credentials. AWS keys go in `.env`, which is git-ignored. Never print or commit secrets.
- Commit before every Codex build. One file, one agent at a time.
- "Done" means tests and Islombek's own demo pass, not "both AIs agree".

## Cross-Model Collaboration (Codex)

Claude Code can delegate work to OpenAI Codex via `.claude/bin/codex-bridge.sh`.
Both run on subscriptions — no API keys. The bridge script unsets `OPENAI_API_KEY`
so Codex never accidentally uses an API key for billing.

| Command | Purpose |
|---------|---------|
| `/collab <task>` | Full collaboration: think, build, or debug with Codex |
| `/collab-review` | Quick second opinion from Codex on current changes |

**Bridge modes:**
- `codex-bridge.sh think "prompt"` — read-only, for debate and review (sync)
- `codex-bridge.sh build "prompt"` — workspace-write, for implementation (async)
- `codex-bridge.sh build "prompt" path/to/spec.md` — build from spec file (async)

**Build specs** go in `.collab/specs/`. **Reports** go in `.collab/reports/`.

**Rules:**
- Ideas: get Codex's independent view before showing it yours.
- Never assign overlapping files to both Claude subagents and Codex.
- Always run `python -m pytest` after Codex builds — never trust the self-report.
- Keep Codex prompts concise (500 words max) — it has no session memory.
- Synthesize Codex output for Islombek; don't relay it raw.
- Break large builds into 2–3 small focused Codex calls (max 3 files each).
