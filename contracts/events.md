# Ko'z runner ↔ web contract, version 1

Status: agreed Oct 14. Claude and Codex each proposed one independently,
debated once and merged them; Islombek approved. It changes only when both
lanes agree.

Changes since then (both lanes agreed):
- Oct 14: `observation.unknown_reason` added (section 8.3), so the dashboard can say
  why an output is unknown.
- Oct 15: `status.state` `checking` now means "not approved yet, or confirming an object
  it saw once" (section 8.1). Routine privacy checks (every 0.5 s) no longer flip the
  status, which would have sent about 4 status events per second.
- Oct 15: optional `status.planner` (section 8.1), so the dashboard can show who made the
  plan. Proposed by Codex and Claude independently. Rollout: web accepts both shapes first,
  then the runner sends it on every status (on since Oct 16).
- Oct 16: `status.planner` may also be `bedrock` (Amazon Bedrock, the AWS planner); the web must
  accept it before a runner with a Bedrock key sends it.
- Oct 16: choosing a camera: optional `status.cameras` (section 8.1) and optional
  `start_job.data.camera_id` (section 10), fixed slots only. Proposed by Codex and Claude
  independently. Rollout: web accepts both first; the runner sends `cameras` only after that.

`recipe.schema.json` and this file are the contract together.
**MVP** = built by Oct 26. **stretch** = only if built; the dashboard must not
show a stretch feature as active unless `status.capabilities` lists it.

## 1. Who owns what

**koz/ (the runner, on the owner's computer):** capture, local setup, the
authoritative recipe checks, privacy guard, face blur, OpenCV 5 blocks,
counting tracks, planner calls, the check-and-adjust loop, local actions,
motor safety, and the events below.

**web/ (on AWS):** owner login, runner token, command delivery, event checks,
the Uz/Ru/En setup chat, live status, trial dashboard, recipe import/export,
storage, totals and expiry.

- Both sides reject unknown fields and unsupported versions.
- The runner checks every recipe again, even if web already accepted it.
- The account comes from the login or the runner token, never from a recipe,
  command or event.
- The planner can only propose recipes. It has no tools for the camera, files,
  network, firmware or actions.
- "Device" means the owner's computer plus its camera on the local network.
  Frames travel camera → computer over the LAN and never reach AWS or Nebius.
  ESP32-CAM video on the LAN is not encrypted; the report lists this as a limitation.

## 2. Recipe vs. local setup

A recipe holds portable processing settings only. These values exist **only**
in local setup:

| Local value | Notes |
|---|---|
| Camera adapter and address | ESP32-CAM MJPEG in the MVP; RTSP only if built |
| Camera password | Local secret; never exported or logged |
| "I own this camera" | The owner confirms it locally (rule 7) |
| Allowed-area mask | Non-empty polygon(s); pixels outside are blacked out before any block |
| Mount | `fixed` or `moving` |
| School | Local yes/no, asked explicitly |
| Motors | Serial port, tested speed cap, measured stopping distance |
| Motor arming | A local human action; starts disarmed |
| Planner key and model | Installation config, not recipe data |
| Recorded test video | For trials and tests; a recipe cannot pick its path |

Local setup is a step in koz/ (command line + an OpenCV window to draw the
mask). It must be local: drawing the mask needs a live frame, and frames never
leave the device.

- An imported recipe cannot carry any of these. No command can change them.
- **Import** = parse, check, preview. It never starts a job.
- **Export** = exactly the recipe object: no wrapper, no setup, no chat, no account.
- Effective school mode = `recipe.privacy.school` OR the local school setting.
  An import cannot switch off a local school setting.
- In school mode: only `privacy_guard`, `face_blur`, `person_detector`,
  `line_counter`; brain `none`; the only action is `dashboard`; outputs are
  aggregate counts only. The web shows "The school is responsible for consent."
- Ko'z does not claim to verify ownership, consent or where a camera points.

## 3. Checks the runner makes beyond the schema

**Parsing, before the schema:** at most 16 KiB of UTF-8; nesting at most 12
deep; reject duplicate keys, NaN, Infinity and invalid UTF-8. No type
conversion, no defaults, no repairs. Use the bundled schema only.

Every first plan, adjustment and import goes through, in order:
1. strict parsing,
2. `recipe.schema.json`,
3. the checks below,
4. local setup and capability checks,
5. the runtime privacy and freshness gates.

A recipe that passes the schema is not yet permission to run it.

**Checks:**
- Each block type appears at most once, in this order (any may be left out
  except the first two): `privacy_guard`, `face_blur`, `color_finder`,
  `motion_zone`, `person_detector`, `line_counter`, `looming`.
- `line_counter` needs `person_detector`. `flybrain` needs `color_finder`.
  `motors` only with `flybrain`.
- The fly brain reads `color_finder` (and `looming` when present) only, never
  person results or tracks.
- Alert `motion_detected` needs `motion_zone`; `count_changed` needs `person_detector`.
- `rect`: left < right and top < bottom. `line`: two different points.
- A stretch block that isn't built (`looming`) → `UNSUPPORTED_CAPABILITY`,
  never silently dropped.
- School limits apply even when school mode comes from local setup.
- A request with a forbidden purpose is refused even if a valid recipe could be
  built for it ("follow this man" → `IDENTITY_FORBIDDEN`). The planner's intent
  screening is imperfect; the schema and the block list are the hard limit.

**Processing order (fixed):**

    capture → allowed-area mask → privacy guard → face blur
            → other blocks in order → brain → actions

- Only APPROVED frames get past the guard. BLOCKED or UNKNOWN: drop the frame,
  outputs become unknown, motors stop.
- If face blur fails (for example, its model is missing), the frame goes no
  further (`BLUR_UNAVAILABLE`).

**Fixed limits** (in code, not in the recipe; proposed values, see OPEN-1):
- One newest-frame slot; process at most 640×480.
- A frame older than 500 ms when an action uses it → outputs unknown, actions
  pause, motors stop (`FRAME_STALE`).
- Privacy check at start and at least every 120 s. A check that takes more
  than 5 s → `PRIVACY_UNAVAILABLE`. Actions wait during a check; an old
  approval is never stretched past a due check.
- Counting track IDs live in memory only. Delete each within 5 s after the
  person leaves the view, and all of them at job end. Never send or save them,
  not even as hashes.
- Motor speed = the lower of `max_speed_ratio` and the local tested cap.
- Firmware: starts stopped; stops within 250 ms without a fresh command; the
  ultrasonic stop and the physical switch work without Python, AWS or the
  browser. A fault disarms; re-arming is local and by hand. No cloud command
  arms motors.
- Scene-change tripwire (**stretch**): fixed cameras only; reference frame in
  memory only; big change or covered lens → hold outputs, run the guard again.

## 4. What can never be sent

Runner events have **no field** for:
- frames, images, video, audio, thumbnails, media links;
- encoded media, embeddings or other number vectors;
- names, face identities, appearance, text read from the image (OCR);
- plates, documents, badges, body or walk matches;
- person IDs, track IDs (or their hashes), person boxes;
- age, gender, ethnicity, emotion, religion or any personal trait;
- per-person timers, scores, rankings, histories or paths;
- prompts, LLM explanations, exception text or any free text;
- camera addresses, file names, passwords, account IDs, place names;
- exact capture times.

Allowed strings: the enums in this contract; random protocol IDs (32 lowercase
hex characters, at least 128 random bits; they name sessions, jobs, commands
and trials, never people); the user's text inside `start_job` (a command, not
telemetry).

**The planner gets only:** the user's setup text, a checked recipe, and the
counts and labels this contract allows. Never pixels, OCR, scene-derived text
or track data.

**Setup text:** at most 2,000 characters. Kept only for the request in
progress; never written to databases, access logs, analytics or local logs.
The chat shows "Do not type names." and says the text goes to Nebius outside
Uzbekistan with no approved cross-border route set up (a report limitation).

## 5. Connection and login

**Runner token.** The logged-in owner clicks "Create runner token". Web shows
it once and stores only its hash. The owner pastes it into the local `.env` as
`KOZ_RUNNER_TOKEN`. A new token revokes the old one and closes its connections.
A runner token cannot send owner commands or read the dashboard.

**Connection.** One outbound WebSocket from the runner:

    wss://<web-origin>/v1/runner      Authorization: Bearer <runner token>

The web origin is local config, never recipe content. Nothing connects into the
owner's computer.
- JSON text messages only, at most 32 KiB each. Reject duplicate keys, invalid
  UTF-8 and non-finite numbers. No binary frames, uploads or media.
- A bad runner message → web sends
  `{"v":1,"type":"protocol_error","code":"INVALID_EVENT"}` and closes.
  A bad token → HTTP 401 `{"code":"AUTH_REQUIRED"}`.
- The runner sends `status` right after connecting and then every second.

**When the connection drops:**
- Web: after 3 s without `status` (by server receipt time, not the event's
  `minute`), show "Offline — job state unknown". Never show "stopped".
- Runner: keeps running locally. Local privacy and freshness faults still stop
  outputs; motor safety is local. It drops `status` and `observation` events
  older than 3 s and marks coverage `gapped`. It keeps `recipe`, `decision`,
  `fault`, `command_result` and `trial_result` events in a memory queue
  (at most 200) and sends them after reconnecting. If the queue overflows, the
  trial's evidence becomes `incomplete`.
- Late events never refresh the live status.
- Reconnecting never resumes or restarts a job, replays commands or re-arms
  motors. The runner sends its current status; a new job needs a new start.

## 6. Event envelope

Every runner event has exactly these fields:

| Field | Meaning |
|---|---|
| `v` | Exactly 1 |
| `type` | One of the 7 event types in section 8 |
| `session_id` | Random ID, new each time the runner starts |
| `seq` | 1, 2, 3 … one higher for each event in the session |
| `job_id` | Job ID from web, or null |
| `trial_id` | Trial ID from web, or null |
| `revision` | 1..3 or null (meaning per type, below) |
| `minute` | `floor(UTC Unix seconds / 60)` |
| `data` | A closed object for that type |

- `session_id` + `seq` is the duplicate key. A duplicate doesn't change expiry
  or totals.
- `revision` means: in `recipe`, the candidate; in `observation`, the revision
  actually running; in `decision`, the revision that produced the evidence; in
  `status`, the installed revision or null.
- Web rejects a `minute` more than 1 minute in the future. Web sets expiry
  (section 12); the runner cannot.

## 7. Shared value types

**Count** is exactly one of:

    {"state": "known",   "value": 0,    "reason": null}
    {"state": "unknown", "value": null, "reason": "FRAME_STALE"}

- `known`: `value` is an integer 0..2147483647. `0` means it measured zero.
- `unknown`: `value` is null; `reason` is a code from section 11. Inside an
  observation it equals that observation's `unknown_reason`.
- Unknown never enters totals or averages as 0.
- A top-level `null` instead of a Count means "not configured".

**SettingChange** is exactly `{"setting": …, "before": …, "after": …}`.
`setting` is one of:

    color_finder.hue_center       color_finder.hue_half_width
    color_finder.saturation_min   color_finder.value_min
    color_finder.min_area_ratio   motion_zone.pixel_delta
    motion_zone.min_changed_ratio person_detector.min_confidence
    brain.turn_gain               brain.deadband

`before` and `after` differ, stay inside the schema range and match the two
revisions exactly. An adjustment changes **one** setting. It cannot change
blocks, geometry, actions, speed, school mode, camera, language or setup.

**Check** — what the agent tests on live frames:

| Check | Pass | Fail | Unknown |
|---|---|---|---|
| `target_visible` | target left, center or right | target lost | target unknown |
| `target_centered` | target center | left, right or lost | target unknown |
| `counts_available` | all configured counts known | — | any count unknown |
| `motion_available` | motion detected or clear | — | motion unknown |
| `privacy_approved` | approved | blocked | unknown |

A check needs its output to be configured. Don't pick an unrelated check that
passes to hide one that failed.

**Labels:** `left`, `center`, `right`, `lost`, `detected`, `clear`, `risk`,
`approved`, `blocked`, `known`, `unknown`. They describe the scene coarsely,
never a person.

## 8. Runner events (7 types)

### 8.1 status

| Field | Values |
|---|---|
| `state` | `idle` · `planning` · `checking` · `evaluating` · `running` · `held` · `refused` |
| `camera_on` | true when capture is open |
| `privacy` | `approved` · `blocked` · `unknown` |
| `school` | effective school mode (true/false) |
| `motor` | `not_present` · `disarmed` · `enabled` · `stop_commanded` |
| `opencv_major` | 5, or null before OpenCV starts |
| `capabilities` | list from `rtsp`, `recorded_fixture`, `looming`, `scene_tripwire`; may be empty |
| `planner` | optional: `rules` · `ollama` · `nebius` · `bedrock` · null — who made this job's plan |
| `cameras` | optional: the camera slots set up on this runner, from `mac_camera` · `esp32_cam` · `phone_ip_camera`, each once; may be empty |

`planner` names the planner whose answer was used, after any fallback (Nebius → Ollama →
rules): `rules` also when the rule check refused the request before any AI model saw it. It
is null with no job, while planning, for an imported recipe, and when planning failed. It
stays the same through the job's adjustments (the tuner is not a planner) and resets with
each new job. No model names: they are free text. A missing field means "not reported",
never `rules`.

`cameras` lists what the runner's own command line set up (each slot is bound there to an
address that never leaves the runner); it doesn't promise the camera is reachable. A missing field
means a runner that can't choose (it uses its one camera).

`held` = outputs stopped; a new start is needed. `checking` = before the first
privacy approval, or while the guard confirms an object it saw once (frames held, outputs
unknown); it returns to `running` only after APPROVED with fresh frames. Routine privacy
checks while running don't change the status: they hold their frame for the few ms they
take, and a check that hangs still ends in a fault after 5 s.
`stop_commanded` does not claim the car physically stopped.

```json
{"v":1,"type":"status","session_id":"11111111111111111111111111111111","seq":13,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":2,"minute":29800000,
 "data":{"state":"evaluating","camera_on":true,"privacy":"approved","school":false,
         "motor":"enabled","opencv_major":5,"capabilities":[]}}
```

Web: show state, a "camera on" indicator, privacy state, school mode and motor
state. Keep the latest in memory. Store state changes for 7 days; never store
unchanged heartbeats.

### 8.2 recipe

Only fully checked recipes. Rejected candidates and raw planner output are
never sent.

| Field | Values |
|---|---|
| `origin` | `planner` · `import` · `adjustment` |
| `caused_by` | the `decision` seq for an adjustment, else null |
| `recipe` | the complete recipe object |

```json
{"v":1,"type":"recipe","session_id":"11111111111111111111111111111111","seq":12,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":2,"minute":29800000,
 "data":{"origin":"adjustment","caused_by":11,
  "recipe":{"version":1,"language":"uz",
   "camera":{"source":"device_camera","size":"320x240","fps":10},
   "blocks":[{"type":"privacy_guard","settings":{}},{"type":"face_blur","settings":{}},
     {"type":"color_finder","settings":{"hue_center":0,"hue_half_width":10,
       "saturation_min":120,"value_min":80,"min_area_ratio":0.01}}],
   "brain":{"type":"flybrain","settings":{"turn_gain":0.4,"deadband":0.1}},
   "actions":[{"type":"dashboard"},{"type":"motors","max_speed_ratio":0.15}],
   "privacy":{"school":false}}}}
```

Web: show blocks, settings and revision, marked "checked" until an observation
shows it running. Offer download of the exact `recipe` object. Store 7 days.

### 8.3 observation

From real processing: at most once per second, and at once when a check needs
evidence, an output becomes unknown, or `unknown_reason` changes (also back to null).
"Changes" compares with the last observation sent.

| Field | Values |
|---|---|
| `round` | 1..3 while evaluating a candidate; null in normal running |
| `privacy` | `approved` · `blocked` · `unknown` |
| `occupancy` | Count or null — people in the allowed area now |
| `entered` | Count or null — line crossings in, cumulative for this phase |
| `exited` | Count or null — line crossings out, cumulative for this phase |
| `coverage` | `complete` · `gapped` |
| `target` | `left` · `center` · `right` · `lost` · `unknown` · null |
| `motion` | `detected` · `clear` · `unknown` · null |
| `looming` | `risk` · `clear` · `unknown` · null (stretch) |
| `alert` | `motion_detected` · `count_changed` · null |
| `unknown_reason` | an error code from section 11, or null — why outputs are unknown |

- `unknown_reason` is set when any configured output is unknown, or when
  `privacy` is not `approved` (even if no output is configured). Otherwise it is
  null. `lost`, `clear` and a known 0 are measurements and need no reason; an old
  `gapped` coverage alone doesn't need one either.
- It names the actual cause: `FRAME_STALE`, `OVERLOADED`, the privacy gate's code,
  `BLUR_UNAVAILABLE`, `INTERNAL_ERROR` and so on. A stale frame before the first
  privacy check is `FRAME_STALE`, not `PRIVACY_UNAVAILABLE`.
- One cause per observation: every unknown Count in it has the same `reason`.
  Different causes for different outputs at the same time can't be expressed yet;
  that would need a later contract change.
- Counters reset between evaluation rounds. In normal running they start at 0
  after the job passes and don't reset.
- `coverage` becomes `gapped` after any stale or missing stretch and stays so
  for the phase; a later known value doesn't fill the hole.
- When the privacy gate closes, configured outputs become unknown with the
  matching code.
- Never sent: centroids, person boxes, raw scores, steering values, wheel speeds.

```json
{"v":1,"type":"observation","session_id":"11111111111111111111111111111111","seq":10,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":1,"minute":29800000,
 "data":{"round":1,"privacy":"approved","occupancy":null,"entered":null,"exited":null,
         "coverage":"complete","target":"right","motion":null,"looming":null,"alert":null,
         "unknown_reason":null}}
```

The same output a moment later, when a frame arrived too late:

```json
{"v":1,"type":"observation","session_id":"11111111111111111111111111111111","seq":11,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":1,"minute":29800000,
 "data":{"round":1,"privacy":"approved","occupancy":null,"entered":null,"exited":null,
         "coverage":"gapped","target":"unknown","motion":null,"looming":null,"alert":null,
         "unknown_reason":"FRAME_STALE"}}
```

Web: show configured counts and labels. Show unknown as "Unknown", never 0, with the
fixed message for `unknown_reason` (for example "Camera data is stale. Outputs
stopped."); null as "Not configured". Show coverage gaps next to totals. Alerts come from
the fixed template list only. Never sum `occupancy`. Store 7 days.

### 8.4 decision

One structured step of the check-and-adjust loop. Never LLM reasoning text.

| Field | Values |
|---|---|
| `round` | 1..3 |
| `evidence_seq` | 1–10 observation seqs from this session, job, revision and round |
| `check` | a Check |
| `result` | `pass` · `fail` · `unknown` |
| `next` | `run` · `adjust` · `stop` |
| `next_revision` | same revision for `run`; revision + 1 for `adjust`; null for `stop` |
| `change` | a SettingChange for `adjust`, else null |
| `code` | null for `run`/`adjust`; an error code for `stop` |

An `adjust` decision is sent only after the next candidate passed every check
and its single change was verified. The next `recipe` event refers to it.

```json
{"v":1,"type":"decision","session_id":"11111111111111111111111111111111","seq":11,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":1,"minute":29800000,
 "data":{"round":1,"evidence_seq":[10],"check":"target_centered","result":"fail",
         "next":"adjust","next_revision":2,
         "change":{"setting":"brain.turn_gain","before":0.5,"after":0.4},"code":null}}
```

Web: show observation → check result → next step, with the before/after number.
Label it "proposed adjustment" until the new revision runs. Store 7 days.

### 8.5 command_result

| Field | Values |
|---|---|
| `command_id` | from the command |
| `result` | `accepted` · `rejected` |
| `code` | null if accepted, else an error code |

`accepted` means the runner took the request, not that the job passed, the
motors moved or the car stopped.

```json
{"v":1,"type":"command_result","session_id":"11111111111111111111111111111111","seq":2,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":null,"minute":29800000,
 "data":{"command_id":"44444444444444444444444444444444","result":"accepted","code":null}}
```

Web: settle the pending command. Show the fixed message on rejection. Show a job
as running only after `status`/`observation` say so. Store 7 days.

### 8.6 fault

A refusal or a runtime safety stop.

| Field | Values |
|---|---|
| `code` | an error code from section 11 |
| `effect` | `off` (the job will not run) · `held` (stopped; needs a new start; motors need local re-arm) |

A scheduled privacy check is not a fault; a BLOCKED or UNKNOWN result is.

```json
{"v":1,"type":"fault","session_id":"11111111111111111111111111111111","seq":20,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":null,"minute":29800000,
 "data":{"code":"PRIVATE_BATHROOM","effect":"off"}}
```

Web: show the fixed message in the owner's language at once; mark live outputs
unknown; record it on the trial where relevant. Never show exception text,
rejected input or model output. Store 7 days.

### 8.7 trial_result

The result of one owner-run evaluation trial (10 per demo).

| Field | Values |
|---|---|
| `demo` | `red_ball` · `classroom` · `privacy_guard` |
| `index` | 1..10 |
| `result` | `pass` · `fail` · `unknown` |
| `basis` | exactly `owner_report` |
| `reason` | `none` · `missed_target` · `wrong_direction` · `count_mismatch` · `privacy_miss` · `safety_stop` · `interrupted` · `unknown` |
| `expected_count` | integer or null (classroom only) |
| `observed_count` | Count or null (classroom: `entered` during normal running; any gap → unknown) |
| `fault_code` | an error code or null |
| `evidence` | `complete` · `incomplete` (queue overflow or lost events) |
| `agent_changes` | 0–2 records, below |

Each `agent_changes` record has exactly: `from_revision` (1 or 2),
`to_revision` (+1), `check`, `before_label`, `change` (SettingChange),
`executed` (exactly true), `after_label`, `after_result`. The runner adds a
record only when observations prove both revisions ran and the decision used
the earlier observation.

- `pass` requires `reason` = `none`. For `red_ball` and `classroom`, an
  interrupted or unknown measurement can't pass.
- For `privacy_guard`, a refusal of the private scene is the expected pass.
- The runner may lower an unsupported pass to `unknown`; it never raises an
  owner's `fail` to `pass`.

```json
{"v":1,"type":"trial_result","session_id":"11111111111111111111111111111111","seq":16,
 "job_id":"22222222222222222222222222222222","trial_id":"33333333333333333333333333333333",
 "revision":2,"minute":29800001,
 "data":{"demo":"red_ball","index":1,"result":"pass","basis":"owner_report","reason":"none",
         "expected_count":null,"observed_count":null,"fault_code":null,"evidence":"complete",
         "agent_changes":[{"from_revision":1,"to_revision":2,"check":"target_centered",
           "before_label":"right","change":{"setting":"brain.turn_gain","before":0.5,"after":0.4},
           "executed":true,"after_label":"center","after_result":"pass"}]}}
```

Web: fill that demo's row 1..10. Show failures and unknowns, not only passes,
and show that the basis is the owner's report. Store 7 days; offer "Save
summary" and "Delete saved summary" (section 12).

## 9. The check-and-adjust loop (Agentic Vision evidence)

At most **3 evaluations** per job. Round 1 is the first candidate.

Each round: check the whole candidate → check local setup and safety gates →
install it → run it on live frames for at most 10 s → send observations → send
the decision. Safety gates stay on the whole time.

- A malformed, forbidden or unsafe proposal stops at once. It is never run
  "to see if it works".
- After a failed check in round 1 or 2, the planner may propose one
  SettingChange; the whole candidate is checked again.
- Round 3 fails → `stop` with `ADJUSTMENT_LIMIT`; outputs and motors stop; the
  job is held. No new loop starts by itself.
- Planner timeout → `PLANNER_UNAVAILABLE`. A failed check with no allowed fix →
  `CHECK_FAILED`.
- A failed check never gives the planner permission to weaken safety.

The dashboard shows the label **"OpenCV output changed the next action"** only
for a complete chain:

    observation (revision N)
    → decision citing that observation
    → recipe revision N+1 with the matching change
    → status: revision N+1 installed
    → observation produced under revision N+1

A proposal, an LLM explanation or a command acknowledgement alone doesn't earn
the label. A privacy stop is shown separately, as a policy stop.

Example: seq 10 target `right` (rev 1) → seq 11 `target_centered` fails, change
`brain.turn_gain` 0.5 → 0.4 → seq 12 rev 2 checked → seq 13 rev 2 installed →
seq 14 target `center` (rev 2) → seq 15 decision `pass`, `run`. This shows a
cause and effect, not that lower gain always works or that the car reached the
ball; the owner judges the physical result.

## 10. Commands (web → runner, 4 types)

| Field | Meaning |
|---|---|
| `v` | Exactly 1 |
| `type` | Exactly `command` |
| `command_id` | Random ID |
| `session_id` | The runner's current session |
| `job_id` | Target or new job ID, or null |
| `trial_id` | Open or new trial ID, or null |
| `expires_at` | Server Unix seconds: send time + 10 s (delivery only; never stored or given to the planner) |
| `command` | `start_job` · `stop_job` · `begin_trial` · `finish_trial` |
| `data` | A closed object for that command |

- Web creates the IDs after checking the owner's login and sends only to that
  owner's connected runner. It doesn't queue `start_job` while the runner is offline.
- The runner rejects expired (`COMMAND_EXPIRED`), wrong-session or
  wrong-state (`INVALID_COMMAND`, `BUSY`) commands.
- A repeated `command_id` gets the same `command_result` again and doesn't run twice.
- "Sent" is not "applied": web waits for `command_result`, then `status`/`observation`.

**start_job** — only when idle, held or refused; never replaces a running job.
`data` is exactly one of:

    {"input": "prompt", "language": "uz", "text": "Qizil koptokni quv."}
    {"input": "recipe", "recipe": { …a complete recipe object… }}

An imported recipe goes through the same checks and the same 3-round evaluation.
Both forms may add `"camera_id"`: one of the slots in `status.cameras`. Missing → the runner's
default (its first camera). Not a slot name → `INVALID_COMMAND`. A slot this runner hasn't set
up → `UNSUPPORTED_CAPABILITY`. A chosen camera that can't be opened or sends no first picture
→ fault `UNSUPPORTED_CAPABILITY` (the job doesn't run); one that stops sending later → outputs
`unknown` with `FRAME_STALE`. Never a silent switch to another camera. The recipe's `camera.source` stays `device_camera`:
recipes and imports never choose a camera.

**stop_job** — `data` is `{}`. Stops at once, before any planner work; cancels
pending evaluation and planner results; goes idle; sends `command_result` and
`status`. Repeating it is harmless. A late planner answer can't restart a
stopped job.

**begin_trial** — `data` is `{"demo": "classroom", "index": 1}`. Only with no
running job and no open trial; `job_id` null and a new `trial_id`. The next
`start_job` carries that `trial_id`, so a refusal or planning failure is
recorded in the trial. One job per trial.

**finish_trial** — `data` is
`{"result": "fail", "reason": "count_mismatch", "expected_count": 10}`
(enums from `trial_result`; `expected_count` may be null). The runner stops the
job, sends `trial_result` and closes the trial. To cancel a trial, finish it
with `unknown`, `interrupted`, null.

**Web only, no command needed:** import preview, recipe download, UI language,
saving/deleting a trial summary, reading history and totals.

**No command exists for:** camera addresses, the mask, ownership or school
setup; arming motors, raw wheel speeds or firmware upload; switching off
protections or editing recipe paths; screenshots, video, audio, files or shell
commands; changing expiry.

## 11. Error codes

The code is what travels. Each side looks up the message by code and language;
neither the runner nor the planner sends message text. No message repeats the
input that caused it. Unexpected exceptions become `INTERNAL_ERROR`; local logs
may hold codes and numbers only, never frames, prompts, passwords or personal data.

**Islombek: please check the Russian and Uzbek texts.**

| Code | Rule | When | English | Russian | Uzbek |
|---|---|---|---|---|---|
| `INVALID_RECIPE` | 1 | Bad JSON, unknown fields/blocks, code, URLs, paths, model files, wrong order, out-of-range or too large | Recipe is invalid. | Рецепт недопустим. | Retsept yaroqsiz. |
| `SAFETY_LOCKED` | 1 | Removing or weakening a locked protection | Safety settings are locked. | Настройки безопасности заблокированы. | Xavfsizlik sozlamalari qulflangan. |
| `ADJUSTMENT_LIMIT` | 1 | Round 3 did not pass | Three attempts failed. Job is off. | Три попытки не удались. Задание отключено. | Uch urinish muvaffaqiyatsiz. Vazifa o'chirildi. |
| `CHECK_FAILED` | 1 | Failed check with no allowed fix | Check failed. Job stopped. | Проверка не пройдена. Задание остановлено. | Tekshiruv o'tmadi. Vazifa to'xtatildi. |
| `PLANNER_UNAVAILABLE` | 1 | Planner down or timed out | Planner is unavailable. | Планировщик недоступен. | Rejalashtiruvchi ishlamayapti. |
| `PRIVATE_BATHROOM` | 2 | Scene check: bathroom | Bathroom view blocked. | Вид ванной заблокирован. | Hammom ko'rinishi bloklandi. |
| `PRIVATE_TOILET` | 2 | Scene check: toilet | Toilet view blocked. | Вид туалета заблокирован. | Hojatxona ko'rinishi bloklandi. |
| `PRIVATE_BEDROOM` | 2 | Scene check: bedroom | Bedroom view blocked. | Вид спальни заблокирован. | Yotoqxona ko'rinishi bloklandi. |
| `PRIVATE_CHANGING_ROOM` | 2 | Scene check: changing room | Changing-room view blocked. | Вид раздевалки заблокирован. | Kiyinish xonasi ko'rinishi bloklandi. |
| `PRIVACY_UNCERTAIN` | 2 | Low confidence or unclear scene | Scene safety is unknown. | Безопасность сцены неизвестна. | Ko'rinish xavfsizligi noma'lum. |
| `PRIVACY_UNAVAILABLE` | 2 | Guard model missing, failed or too slow | Privacy check is unavailable. | Проверка приватности недоступна. | Maxfiylik tekshiruvi ishlamayapti. |
| `BLUR_UNAVAILABLE` | 2, 6 | Face blur can't run | Face blur is unavailable. | Размытие лиц недоступно. | Yuzlarni xiralashtirish ishlamayapti. |
| `SCENE_CHANGED` | 3 (stretch) | Fixed camera's view changed | View changed. Outputs stopped. | Вид изменился. Выходы отключены. | Ko'rinish o'zgardi. Chiqishlar to'xtatildi. |
| `LENS_COVERED` | 3 (stretch) | Dark, flat image | Lens may be covered. | Возможно, объектив закрыт. | Obyektiv yopilgan bo'lishi mumkin. |
| `IDENTITY_FORBIDDEN` | 4 | Recognition, matching, plates, documents, badges, OCR, following a person | Identifying people is not allowed. | Идентификация людей запрещена. | Odamlarni tanib olish taqiqlangan. |
| `PROFILING_FORBIDDEN` | 5 | Traits, judging, per-person timers/scores, police or discipline reports | Judging or profiling people is not allowed. | Оценивать и профилировать людей запрещено. | Odamlarni baholash va profillash taqiqlangan. |
| `SCHOOL_COUNTS_ONLY` | 6 | Anything but counts in school mode | School mode allows counts only. | В школьном режиме разрешён только подсчёт. | Maktab rejimida faqat sanash mumkin. |
| `OWNERSHIP_REQUIRED` | 7 | "I own this camera" not confirmed | Confirm on this computer that you own the camera. | Подтвердите на этом компьютере, что камера ваша. | Kamera sizniki ekanini shu kompyuterda tasdiqlang. |
| `ALLOWED_AREA_REQUIRED` | 7 | Mask missing, invalid or empty | Draw the allowed area on this computer. | Отметьте разрешённую область на этом компьютере. | Ruxsat etilgan hududni shu kompyuterda belgilang. |
| `VIEW_FORBIDDEN` | 7 | Hidden camera, neighbour's property, other forbidden view | This camera use is not allowed. | Такое использование камеры запрещено. | Kameradan bunday foydalanish taqiqlangan. |
| `AUDIO_FORBIDDEN` | 8 | Microphone or audio request | Audio is not allowed. | Аудио запрещено. | Audio taqiqlangan. |
| `FRAMES_FORBIDDEN` | 8, 9 | Saving, screenshotting or sending frames or video | Saving or sending frames is not allowed. | Сохранять и передавать кадры запрещено. | Kadrlarni saqlash va yuborish taqiqlangan. |
| `INVALID_EVENT` | 9 | Forbidden or malformed event | Event data is not allowed. | Данные события недопустимы. | Hodisa ma'lumotlari yaroqsiz. |
| `AUTH_REQUIRED` | 9 | Missing or bad login or runner token | Sign in or connect the runner. | Войдите или подключите исполнитель. | Tizimga kiring yoki ijrochini ulang. |
| `FRAME_STALE` | 10 | Frame missing, frozen or late | Camera data is stale. Outputs stopped. | Данные камеры устарели. Выходы отключены. | Kamera ma'lumoti eskirgan. Chiqishlar to'xtatildi. |
| `OVERLOADED` | 10 | Processing over budget | Too much processing. Outputs stopped. | Обработка перегружена. Выходы отключены. | Ishlov berish haddan oshdi. Chiqishlar to'xtatildi. |
| `SOLE_PROTECTION_FORBIDDEN` | 10 | Ko'z as the only protection for a child, fire, medical or similar | Ko'z cannot be the only safeguard. | Ko'z не может быть единственной защитой. | Ko'z yagona himoya bo'la olmaydi. |
| `MOTOR_TARGET_FORBIDDEN` | 11 | Chasing or aiming at people or animals | Chasing people or animals is not allowed. | Преследовать людей или животных запрещено. | Odam yoki hayvonni quvish taqiqlangan. |
| `ACTUATOR_FORBIDDEN` | 11 | Locks, gates, shocks, sprays or other unapproved actuators | This device action is not allowed. | Это действие устройства запрещено. | Qurilmaning bu harakati taqiqlangan. |
| `MOTOR_NOT_ARMED` | 11 | Motors not armed locally | Arm the motors on this computer. | Включите моторы на этом компьютере. | Motorlarni shu kompyuterda yoqing. |
| `MOTOR_SAFETY_STOP` | 11 | Firmware timer, obstacle, switch or motor fault | Motor safety stop. | Защитная остановка моторов. | Motorlar xavfsizlik uchun to'xtadi. |
| `RETENTION_LOCKED` | 12 | Asking to keep data longer | Storage times are fixed. | Сроки хранения фиксированы. | Saqlash muddatlari o'zgarmaydi. |
| `UNSUPPORTED_CAPABILITY` | — | Block, camera type or OpenCV feature not available | This feature is not available. | Эта функция недоступна. | Bu imkoniyat mavjud emas. |
| `INVALID_COMMAND` | — | Unknown command, bad fields or wrong state | Command is invalid. | Команда недопустима. | Buyruq yaroqsiz. |
| `BUSY` | — | Another job or trial is active | Stop the current job first. | Сначала остановите текущее задание. | Avval joriy vazifani to'xtating. |
| `COMMAND_EXPIRED` | — | Command arrived after its expiry | Command expired. | Срок команды истёк. | Buyruq muddati tugadi. |
| `PROTOCOL_VERSION` | — | Unsupported contract version | Contract version is not supported. | Версия контракта не поддерживается. | Kontrakt versiyasi qo'llab-quvvatlanmaydi. |
| `INTERNAL_ERROR` | — | Unexpected failure | Internal error. Job stopped. | Внутренняя ошибка. Задание остановлено. | Ichki xato. Vazifa to'xtatildi. |

## 12. Storage and expiry

Web sets expiry; nothing the runner sends can change it. Use the cloud
database's built-in expiry, and also skip expired records in every read, total
and export (physical deletion can lag).

| Data | Kept |
|---|---|
| Changed `status`, `recipe`, `observation`, `decision`, `command_result`, `fault`, `trial_result` | 7 days |
| Unchanged `status` heartbeats | Live memory only |
| Daily totals of observed crossings | 30 days after that UTC day |
| A trial summary the owner chose to save | Until the owner deletes it |
| Setup text, frames, audio, identities, tracks, passwords | Never stored |
| Pending commands | Memory only, at most 10 s |

    event expires_at = min(event minute, receipt minute) × 60 + 604800
    total expires_at = end of that UTC day (Unix seconds) + 2592000

- Store the rounded minute only. Duplicates, reads and repeated saves never
  refresh expiry.
- **Daily totals:** only from normal running outside trials (`round` null,
  `trial_id` null). Use the increase in cumulative `entered`/`exited` per job
  (highest value seen), after removing duplicates. Never sum `occupancy`.
  Leave out unknown values. Mark a day `incomplete` if coverage was gapped,
  delivery broke, or the run ended without a final known counter. Label them
  "observed crossings", never an attendance register.
- **A saved trial summary** holds only: `trial_id`, `demo`, `index`, UTC date,
  `result`, `basis`, `reason`, `fault_code`, `evidence`, `expected_count`,
  `observed_count`, `agent_changes`. No minute times, session IDs, raw events,
  prompts, images, names, tracks or notes. Saving it doesn't keep the raw
  events longer.
- No long-lived backups of events in the MVP. Logs, caches and analytics must
  not keep copies longer than the table allows.

## 13. Open items

- **OPEN-1** — The limits in section 3 (640×480, 500 ms, 120 s, 5 s), the
  setting ranges in the schema and `max_speed_ratio` ≤ 0.25 are proposals, not
  measurements. Measure them on the real MacBook and car, together with the
  cost of running face blur on every frame (including the car). If one can't
  be met, fail closed; don't quietly relax it.
- **OPEN-2** — `brain.turn_gain` and `brain.deadband` must match the stage 2–3
  fly-brain code. Islombek gave its location on Oct 14. Next: copy what is
  needed into `koz/brains/flybrain/` and check. (The original is never modified.)
- **OPEN-3** — Islombek checks the Russian and Uzbek messages in section 11.
