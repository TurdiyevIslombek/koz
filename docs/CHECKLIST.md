# Checklist to the OpenCV submission

**Deadline: Oct 26, 23:59 Pacific Time = Oct 27, 11:59 Tashkent.** Our target: submitted **Oct 26
evening**. Judging Oct 27 – Nov 9; winners Nov 10. Oct 22: no building.
Written Oct 17 from the Devpost page (opencv26.devpost.com and /rules).

Owners: **I** = Islombek · **C** = Claude · **X** = Codex. Status: ✅ done · ⏳ waiting · ☐ to do.

## What Devpost requires (all 7)

| # | Requirement (Devpost) | Where it is | Status |
|---|---|---|---|
| 1 | Technical report: problem, users, architecture, OpenCV 5, AWS deployment, evaluation, limitations, responsible use | `docs/REPORT.md` (draft; TODO numbers) | ⏳ |
| 2 | Judge-accessible code repository or archive | GitHub `TurdiyevIslombek/koz` (to create) | ☐ |
| 3 | Pinned dependencies, clear build, deployment and test instructions | `README.md`, `requirements.txt`, `web/package-lock.json`, `deploy/` | ✅ (check from a fresh clone) |
| 4 | Architecture diagram with the OpenCV 5 and AWS parts (and agent parts) | `docs/architecture.svg` | ✅ |
| 5 | A working web endpoint, or an arranged live screen-share | `https://<Elastic IP>/` after Oct 19 | ☐ |
| 6 | Public or unlisted video, **5 minutes at most**, showing the team, the app working, its architecture and principal results | `docs/VIDEO.md` (2:45 plan) | ☐ |
| 7 | Evaluation evidence, with failure cases or limitations | `docs/TRIALS.md`, report section 8 | ⏳ |

**Agentic Vision award ($1,000), extra evidence:** an agent workflow diagram (perception → decision
→ action), a trace showing OpenCV 5 output changing a later decision or action, and an evaluation of
task success, failure handling, observability and human control. Devpost adds: using an AI coding
assistant to write the entry is not an agentic workflow, so the report keeps the product's agent
loop and our use of Claude and Codex clearly apart (`AI_LOG.md`).

**Best Use of COOL award:** COOL must run the core vision work on AWS Graviton. Ours runs on the
owner's computer by design (frames never leave the device), so **not pursued** (Islombek, Oct 17).

## Now → Sunday (Oct 17–18)

| Item | Owner | Date | Status |
|---|---|---|---|
| Fix the 5 motor-safety findings (MS-1…5), tests first | C | Oct 17 | ✅ |
| Codex re-review: 3 more holes found, fixed with tests | C | Oct 17 | ✅ |
| Codex confirms those 3 follow-up fixes (its quota ran out at 22:24 Oct 17) | X | Oct 18 morning | ⏳ |
| Decide: make the repo public, and which author email the history shows (B: noreply email, personal lines out of every commit) | I | Oct 17 | ✅ |
| History rewritten (backup in `_backups/`), final file list shown; create the public repo and push after your yes | C | Oct 17–18 | ⏳ |
| `docs/SUNDAY.md` (a)–(f): portfolio recordings, stop test, motor_listener, 10 chase trials, original back | I | Oct 18 | ☐ |
| Set `speed_cap` and `stop_cm` from the stop-test lines; write them in TRIALS.md | C | Oct 18 | ☐ |
| Write the 10 chase trials in TRIALS.md; option B passes at **≥ 7 of 10** | C | Oct 18 | ☐ |

## AWS (Oct 18–20)

| Item | Owner | Date | Status |
|---|---|---|---|
| `web/server/cloud.mjs`, HTTPS origin checks, `/api/health`, Linux build (`.collab/specs/aws-review.md`) | X | Oct 18 | ☐ |
| DynamoDB storage (or NDJSON, and the report says which) and the 30-day totals | X | Oct 19 | ☐ |
| Judges' read-only view; cloud Setup privacy line | X | Oct 19 | ☐ |
| The web's eye from the local preview (`.collab/specs/web-eye-preview.md`; runner side done) | X | Oct 20 | ☐ |
| Remove the 3 personal paths in `web/design/references.md` (done in the history rewrite) | C | Oct 17 | ✅ |
| Option B time box: ≥ 7/10, else switch to option A and say so | I decides, C builds A | Oct 19 | ☐ |
| `docs/AWS_DAY.md` steps 1–9 ($1 budget first) | I | Oct 19 | ☐ |
| Bedrock planner score on the 40 sentences (bar 18/20 each) into TRIALS.md | C | Oct 19 | ☐ |
| Measure: event delay to a phone, "offline" time after unplugging, cost so far → report section 7 | I + C | Oct 20 | ☐ |
| Decide: keep the stack running through judging (Oct 27 – Nov 9; about $15/month, credits) | I | Oct 20 | ☐ |

## Trials and evidence (Oct 20–24; not Oct 22)

| Item | Owner | Date | Status |
|---|---|---|---|
| Classroom counter: 10 trials, counted by hand vs Ko'z (a classroom with permission, or the shop sentence at home) | I | Oct 20–21 | ☐ |
| Privacy guard: trials 1–10 and S1–S2 (`TRIALS.md`), with the live stop time | I | Oct 20–21 | ☐ |
| Face blur on real faces: your clip in `tests/fixtures/private/face.mp4` (stays on the Mac) | I | Oct 20 | ☐ |
| A fresh set of 20 planner sentences nobody has seen, scored once, no tuning before | I writes, C scores | Oct 20 | ☐ |
| The agent's adjust step on the live camera (an orange-red ball, "find the red ball") | I | Oct 20 | ☐ |
| Check the Uzbek and Russian texts (`docs/TEXTS.md`) | I | Oct 21 | ☐ |
| Agent workflow diagram (`docs/agent-workflow.svg`) and a trace from a live run | C | Oct 23 | ☐ |
| Contract: which crossing direction counts as "in" (open item) | C + X | Oct 23 | ☐ |

## Report, video, submission (Oct 23–26)

| Item | Owner | Date | Status |
|---|---|---|---|
| Fill every TODO in the report with measured numbers only; failures stay | C | Oct 24 | ☐ |
| Read the whole report; you must be able to explain every part | I | Oct 25 | ☐ |
| Film (`docs/VIDEO.md`, outside the bedroom, adults who agreed) | I | Oct 24 | ☐ |
| Edit to under 3:00 (Devpost limit 5:00), privacy check, upload (public or unlisted) | I | Oct 25 | ☐ |
| Fresh clone from GitHub, follow the README exactly, all tests pass | C | Oct 25 | ☐ |
| Repo, video and endpoint links in the report and README | C | Oct 25 | ☐ |
| Devpost form: name, tagline, description, links, video, images (check the form's own fields) | I | Oct 26 | ☐ |
| **Submit** (and check the endpoint and video open in a private window) | I | **Oct 26 evening** | ☐ |
| Keep the endpoint up and the Mac reachable for a screen-share during judging | I | Oct 27 – Nov 9 | ☐ |
| After judging: delete the stack and the Bedrock key, check billing (`docs/AWS_DAY.md`) | I | Nov 10 | ☐ |

## Decisions (Oct 17)

- Repo: public, option B (history rewritten: GitHub noreply email, personal lines removed from every commit).
- COOL award: skipped.
- AWS compute grant: not received, so no check-in was needed.
