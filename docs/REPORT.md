# Ko'z: tell a camera what job to do

**Technical report, OpenCV AI Competition 2026. Draft of Oct 16.**
Islombek Turdiyev (Tashkent, Uzbekistan). Every measured number below comes from
`docs/TRIALS.md`, which also keeps the failures. **TODO** marks numbers that are not measured yet
(the robot car, live trials, AWS); they stay TODO until they are measured.

Architecture diagram: `docs/architecture.svg`. Repository: TODO (public GitHub link).
Live endpoint: TODO (`https://<Elastic IP>/`, Oct 19).

---

## 1. Problem

Cheap cameras are everywhere in Uzbekistan: a $10 ESP32-CAM, an old phone, the camera a shop
already has. Making one *do a job* ("tell me when the red ball is in view", "count pupils coming
in", "make the car chase the ball") still needs a programmer who knows computer vision. A shop
owner or a teacher can describe the job in a sentence but can't write the code.

AI models can now turn a sentence into code, but free code written by a language model is the
wrong answer for a camera: it can't be tested in advance, and it can be talked into doing
something harmful (identify a person, film a bathroom, remove the blur because "it works better").

**Ko'z** ("eye" in Uzbek) lets a person describe a camera job in plain words (Uzbek in both
alphabets, Russian or English). An agent turns it into a **recipe**: a short JSON list of tested
OpenCV 5 blocks and their settings. Ko'z runs the recipe on live frames, checks the OpenCV numbers,
changes one setting if the check fails (at most 3 tries), and connects the result to an action
(a dashboard, or motors). Recipes can be exported and imported by anyone with a similar camera.

## 2. Users

| User | Job in their words | What Ko'z builds |
|---|---|---|
| A teacher | "Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir" (count pupils entering, blur faces) | privacy guard → face blur → person detector → line counter; school mode (counts only) |
| A shop owner | "Сколько людей зашло в магазин?" (how many people came in?) | the same counter, without school mode |
| A maker or student with a robot | "Qizil koptokni quv" (chase the red ball) | privacy guard → face blur → colour finder → fly brain → motors |
| Anyone with the same camera | imports someone's recipe file | the same recipe, checked again on import |

Requests Ko'z refuses, before any camera opens: who a person is, reading plates or documents,
age, gender or emotion, watching one person, hidden cameras, filming bathrooms or bedrooms, and
jobs where Ko'z would be the only protection (a child alone, fire, medical). Each refusal has a
fixed code and a fixed message in Uzbek, Russian and English (`contracts/events.md` section 11,
`docs/TEXTS.md`).

## 3. Architecture

See `docs/architecture.svg`. Three parts, joined by one written contract
(`contracts/recipe.schema.json` + `contracts/events.md`, agreed before either side was built):

1. **The runner** (`koz/`, Python 3.13, on the owner's computer). Everything that touches
   pixels: capture, the privacy guard, face blur, the OpenCV 5 blocks, the agent loop, the fly
   brain and motor safety. Frames never leave this computer.
2. **The web app** (`web/`, Node 22, on AWS). Owner login, the setup chat, live status, the
   trial dashboard, recipe export and import. It receives only contract events: numbers, fixed
   labels and rounded minutes. It has no field for an image. When the web app runs on the owner's
   own computer instead, its "eye" can also show a small live preview (contract section 14): only
   frames the privacy guard approved, after face blur, at most 640 px and 15 per second, over that
   computer's own socket. It is never stored, never sent over the cloud link and never shown to
   judges; a test checks every message the cloud link sends.
3. **The motor board** (`firmware/motor_listener/`, Arduino Uno + L298N). It accepts only
   "left speed, right speed" over USB and stops by itself.

**Every frame, in this fixed order** (`koz/runner.py`):

    capture → allowed-area mask → privacy guard → face blur → the recipe's blocks → actions

Only frames the privacy guard has **approved** reach face blur and the blocks. The guard and face
blur are *locked* blocks: first and second in every recipe; no recipe, adjustment or import can
remove, move or tune them (`koz/policy.py`).

**A recipe** (made by the rule planner for "Qizil koptokni quv"):

```json
{"version": 1, "language": "uz", "camera": {"source": "device_camera", "size": "320x240", "fps": 15},
 "blocks": [{"type": "privacy_guard", "settings": {}},
            {"type": "face_blur", "settings": {}},
            {"type": "color_finder", "settings": {"hue_center": 0, "hue_half_width": 10,
             "saturation_min": 120, "value_min": 70, "min_area_ratio": 0.002}}],
 "brain": {"type": "flybrain", "settings": {"turn_gain": 1.0, "deadband": 0.1}},
 "actions": [{"type": "dashboard"}, {"type": "motors", "max_speed_ratio": 0.25}],
 "privacy": {"school": false}}
```

`koz/recipe.py` checks every recipe (from the planner, from each adjust round and from every
import): strict JSON, the schema, an allowlist of blocks and setting ranges, size limits, and it
rejects unknown fields, code, URLs, file paths and model files. The runner only runs checked
recipes. Camera address, "I own this camera", the allowed area and motor limits are **local
setup**: they never come from a recipe, an import or the cloud.

**Who built it.** Islombek directed the project and made every decision. Two AI engineers wrote
the code in separate lanes: Claude Code (Anthropic) the runner, firmware and tests; Codex (OpenAI)
the web app and reviews. Every substantial AI contribution and Islombek's decision about it is in
`AI_LOG.md`.

## 4. How OpenCV 5 is used

OpenCV 5.0.0 (`opencv-python==5.0.0.93`) does all image analysis at runtime; the runner refuses
to start on another major version. Three neural networks run through OpenCV's DNN module, all on
the CPU of a MacBook Air, no GPU.

| Step | OpenCV 5 | Why |
|---|---|---|
| Capture | `VideoCapture` (laptop camera, RTSP, recorded clips); `imdecode` for each JPEG of the ESP32-CAM's MJPEG stream (only the newest frame is kept) | Old frames must never look current |
| Allowed area | `fillPoly` + `bitwise_and` | Pixels outside the owner's area are black before any block sees them |
| Privacy guard: room | `dnn.readNetFromONNX` + `blobFromImage`, ResNet18 trained on **Places365** (365 kinds of places) | Is this a bathroom or a bedroom? |
| Privacy guard: objects | `dnn.readNet` + `dnn.NMSBoxes`, **NanoDet-Plus** (COCO) | Is a bed, a toilet or a sink in view? |
| Privacy guard: covered lens | `cvtColor` to grey, mean and spread over the allowed area | A dark or flat picture is never approved |
| Privacy guard: camera moved | `resize` to a 32 × 24 grey thumbnail, compared with the last check | Check again on the next frame, not in 3 s |
| Face blur | `FaceDetectorYN` (**YuNet**), then each face shrunk to 6 × 6 averages with `INTER_AREA` and enlarged smoothly with `INTER_CUBIC` | Only 36 averages of a face survive, so it can't be sharpened back; smooth (not hard squares) so the person detector still sees a person |
| Colour finder | `cvtColor` to HSV, a hue band, `morphologyEx` (opening), `findContours`, `contourArea`, `arcLength`, `minEnclosingCircle`, `moments` | The biggest *round* patch of one colour → left / center / right / lost |
| Object finder | the same NanoDet-Plus, one COCO class from a fixed list (phone, backpack, bag, bottle…), then `cvtColor` to HSV on the middle of the box for an asked colour | Where the thing is → left / center / right / lost; never people or animals, never the car's input |
| Person detector | the same NanoDet-Plus, "person" class only | People in the allowed area, boxes stay local |
| Line counter | geometry on the detector's boxes (overlap tracking, which side of the line) | Entered / exited counts, no identities |
| Local preview | `rectangle`, `putText`, `imshow`; `resize` + `imencode` (JPEG) for the web's eye on the same computer | The owner sees the blurred view; nothing is saved |

Each model is pinned by SHA-256; a missing or changed file stops the job. The NanoDet decoder
follows OpenCV Zoo's, with one change for OpenCV 5, which returns the outputs in a different order
(matched by shape).

**OpenCV output drives the agent.** The adjust step (`koz/agent/tuner.py`) reads the HSV values of
the frames that just failed and moves the colour band to the hue it measured; the fly brain gets
its input from the colour finder's position; the privacy guard's result decides whether any block
runs at all. This is the "Agentic Vision" part: OpenCV's numbers change the agent's next recipe
and the car's next wheel command.

## 5. The agent: words → recipe → check → adjust → run

`koz/agent/loop.py`, contract section 9.

1. **Plan.** A refusal check runs first, with fixed rules for all three languages (Uzbek Cyrillic
   is read as Uzbek Latin). Then the planner picks from a fixed menu: the job (find a colour,
   chase a colour, count people, or refuse), the colour and school mode. That is all an AI planner
   may choose. The recipe and the plan's text come from fixed templates, never from the model, and
   any refusal (by a rule or by the model) wins. Planners: fixed word lists (the default); NVIDIA
   Nemotron on Nebius Token Factory; Amazon Nova 2 Lite on Bedrock (section 7). The planner gets
   only the typed sentence: never pixels, never text read from the camera (so a sign held up to the
   camera can't instruct it).
2. **Try** the recipe on live frames for 3 s, with the privacy guard on.
3. **Check** the OpenCV numbers: is the target visible (and, for the car, kept in the middle)? Are
   the counts known (not "unknown")?
4. **Adjust** one listed setting from what OpenCV measured (a hue, a saturation limit, the fly
   brain's turn gain), never a safety setting, and check the new recipe again.
5. After 3 failed tries the job stays off (`ADJUSTMENT_LIMIT`). A privacy stop ends the job; it is
   never "adjusted".

Every step is a contract event (observation → decision citing those observations → new recipe
revision → observation under the new revision), so the dashboard can show the chain.

## 6. Demo 1: the fly-brain car

Islombek's robot car (Arduino Uno, L298N, 4 gear motors, ultrasonic sensor, ESP32-CAM) is driven by
a simulation of a real fruit-fly brain circuit: 2,282 neurons wired from the FlyWire connectome
(v783), with the neuron model of Shiu et al. 2024 (*Nature*). Nothing in it is trained; the weights
are the fly's synapse counts. Islombek built the simulation and the car before Ko'z (his stages
1–3); Ko'z uses a copy and never changes the original.

The fly's own escape reflex steers: looming (something growing fast) on one eye makes it turn away.
So Ko'z shows the brain a "threat" on the eye **opposite** the ball, and the fly turns toward the
ball. Measured on the brain itself (`TRIALS.md`): looming on the left eye turns the car right, on
the right eye left; nothing seen drives straight (wheels 130 / 130); below about 20 Hz it doesn't
turn, 40 Hz curves, 60 Hz and more spins.

**Safety on the car** (`firmware/motor_listener/`): the board starts disarmed; only a person at the
computer arms it (a key press), never the cloud; 250 ms without a fresh command, driving forward
into an obstacle, or losing the distance sensor disarms it until a person re-arms it; speeds are
capped on the board and on the computer. Only the colour finder feeds the brain (never people).

| Car result | Value |
|---|---|
| Simulation: reaching a ball 2 m away from 0, ±25 and +40 degrees | about 3 s (simulation only; car speed assumed) |
| Simulation: ball never seen, on the right | still 101 cm away after 6 s (it searches left first) |
| Simulation: ball in the middle of the view | 26–37% of the time (it zig-zags) |
| Speed cap and stopping distance on the car (`firmware/stop_test`) | **TODO** |
| 10 chase trials on the car: reached the ball | **TODO** / 10, failures: **TODO** |
| Time to reach the ball (median) | **TODO** |
| Frames per second from the ESP32-CAM | **TODO** |
| Option B (the brain chases) vs the Oct 21 time box | **TODO** (reliable = at least 7 of 10 trials; if not by Oct 21, the brain only avoids obstacles and a simple pull steers, and the report says so) |

## 7. AWS

What runs on AWS (Asia Pacific, Sydney `ap-southeast-2`, the Region AWS gives new accounts from Uzbekistan; `deploy/`, one CloudFormation stack):

- **The web app** on one EC2 t3.micro (Ubuntu 24.04) behind Nginx with HTTPS (a Let's Encrypt
  certificate for the Elastic IP, renewed automatically). It checks every event against the
  contract, delivers the owner's 4 commands, and streams the live view to browsers.
- **DynamoDB** (table `koz-web`, made by the stack with the database's own auto-delete, TTL) for
  events (7 days), totals (30 days) and saved trial summaries. The web app's DynamoDB storage and
  the 30-day totals are **TODO** (Codex); today it keeps events in a local file and filters out and
  removes those older than 7 days.
- **Amazon Bedrock**: the AI planner option, Amazon Nova 2 Lite through the EU cross-region
  inference profile (requests stay in AWS EU Regions). It sees only the typed sentence.

The runner connects **out** to AWS over one WebSocket (`wss://…/v1/runner`, a runner token), so no
port on the owner's network is opened. The owner password is generated in AWS Secrets Manager; the
server has no SSH (Session Manager only), requires IMDSv2, uses an encrypted disk, and its role can
touch only its own table and password. If the computer goes offline, the dashboard shows
"Offline — job state unknown" within 3 s, never old numbers as live; reconnecting never replays a
command or re-arms motors.

| AWS result | Value |
|---|---|
| Deployed and reachable over HTTPS | **TODO** (Oct 19) |
| Event delay, camera computer → judge's browser | **TODO** |
| Offline shown after unplugging the computer | **TODO** s |
| Bedrock planner on the 40 test sentences | **TODO** / 20 and **TODO** / 20 (bar: 18 / 20 each, as for Gemma), **TODO** s per plan |
| Cost for the competition period | **TODO** (AWS Billing) |

## 8. Evaluation

Measured so far (all from `docs/TRIALS.md`). Failures are listed with the results.

### 8.1 Privacy guard on 71 real photos

Places365 validation photos (`tests/test_scene_photos.py`; a test fails if more private photos get
through). **Default** = run anywhere, stop on what you see; **strict** = only listed public places
(schools and public cameras).

| Photos | Default | Strict |
|---|---|---|
| Bathrooms (12) | 9 stopped, **3 run** | all stopped |
| Bedrooms (11) | 10 stopped, **1 runs** | all stopped |
| Desks / home offices (12) | 10 run; the 2 with a bed in view stopped | 3 run |
| Kitchens (13) | all run | none run |
| Classrooms (11) / shops (12) | all run | 9 / 7 run |

So by default **4 of the 23 private photos get through**: no bed or toilet is visible and the room
model isn't confident (e.g. a bathroom read as "closet 0.35", one as "wet_bar 0.51"). Strict mode
stops all 23. NanoDet found a bed in 7 of 11 bedroom photos and a toilet in 7 of 12 bathrooms.

### 8.2 How fast it stops (recorded clips)

| Clip | Stopped after the toilet / bed came into view |
|---|---|
| Quick turn from a desk to a toilet | 0.07 s (one frame) |
| Quick turn from a desk to a bed | 0.07 s |
| Moving-car setting | 0.20 s (worst case about 0.57 s) |
| Slow 1 s pan to a toilet | before the toilet was half in view |
| **Live camera** | **TODO** |

Speed on the MacBook Air (640 × 480, guard + face blur + colour finder): 87–93 frames per second
with a still view, 82–86 while the camera swings (the camera itself gives about 30).

### 8.3 Failures found and fixed

| Live test | What went wrong | Fix |
|---|---|---|
| #1 (Oct 14) | **A bathroom with a visible toilet was approved.** The camera's first frames were dark; the room model said "catacomb" and the old rule approved anything not on a private list | Dark or flat frames are never approved; the first second is dropped; checks every few seconds instead of every 120 s |
| #2 (Oct 15) | Every job stopped at home: the desk is in a bedroom | Stop on objects actually seen (bed, toilet, sink) |
| #3 (Oct 15) | Strict mode never started at home (his room read as "airplane_cabin 0.37") | Default: run anywhere, stop on what you see; strict mode only for schools and public cameras |
| #4 (Oct 15) | Held on a toilet for 5+ s, it kept running (checked every 10 s) | Objects every 0.5 s, the room every 3 s, and on the next frame when the camera moves |
| Desk (Oct 16) | 93 stops in 5 minutes at the desk: private rooms together 0.42–0.46, nothing seen | Limit raised to 0.55 (Islombek's decision): 43 stops in the first 100 s, then 191 s without a stop. Demos are filmed outside the bedroom |
| Counter (Oct 22) | "0 people in view" with Islombek in the picture, face blurred | Two causes, measured on public-domain sample photos (not camera frames). (1) The hard 6 × 6 squares hid the head's shape: a person scoring 0.88 fell to 0.29 (Koʻz counts from 0.5); the same averages enlarged smoothly keep 0.69, and every person found before the blur was found after it, at 4 sizes. (2) When head and shoulders fill the picture, NanoDet finds no person even unblurred: the Live page now says "people Koʻz detects" and that people count from the waist up. Test: `tests/test_blur_keeps_people.py` |
| AWS link (Oct 22) | The runner stopped after "find a colour" found nothing | The website accepted `run` only after `pass`, refused the new "start and wait" decision, and its reply crashed the runner (a class loaded twice by `python -m`). Both fixed; every job's events are now checked by the website's own validator in a test |

Also found: in clips made by gluing two photos side by side, NanoDet saw a "bed" at 0.40–0.44
while panning across the seam (a false stop, on the safe side).

### 8.4 The planner

| Test | Result |
|---|---|
| 20 sentences (5 English, 5 Russian, 5 Uzbek Latin, 5 Uzbek Cyrillic, 3 refusals), camera running | Rule planner **18/20**; Gemma 4 on the laptop **14/20** (refused every counting job), 5.5 s median per plan. The rule planner stayed the default |
| Islombek's 20 fresh sentences, scored before any fix | 20/20, but 4 of 7 refusals only because no job word matched (an AI planner would have seen them) |
| The same after new refusal rules | 20/20, every refusal by a rule. **Tuned on this set: not a fair score** |
| A fresh, unseen set | **TODO** |
| Bedrock (Nova 2 Lite) | **TODO** (section 7) |

### 8.5 The agent's adjust step (test clips)

On drawn test clips: asked for red, the ball looks orange-red → `hue_center` 0 → 13 → found, runs.
No ball at all → one change, then `CHECK_FAILED`. A change that never helps → 3 rounds, then
`ADJUSTMENT_LIMIT`. From the Setup page on a recorded clip: "Yashil koptokni top" → `hue_center`
60 → 77 → found. **On a live camera: TODO.**

### 8.6 Trials still to run (10 per demo)

| Demo | Trials | Result |
|---|---|---|
| 1. Fly-brain car chases the red ball | 10 | **TODO** |
| 2. Classroom counter, faces blurred (counted vs counted by hand) | 10 | **TODO** |
| 3. Privacy guard (`TRIALS.md` trials 1–10, S1–S2) | 12 | **TODO** |
| Face blur on real faces | — | **TODO** |

## 9. Limitations

- **The privacy guard is an alarm, not proof.** By default 4 of 23 private photos get through; a
  bed mostly out of view or a toilet behind a door can be missed; Places365 has no toilet class.
  At a desk in a bedroom it can stop often. Strict mode stops all 23 but refuses most homes.
- **Software can't prove who owns a camera or where it points.** Ko'z asks the owner to confirm
  ownership and draw the allowed area, and says so.
- **Face blur is not yet tested on real faces** (TODO). The colour finder counts any round thing
  of that colour (a red plate, a red lamp). The object finder (Oct 22) is **not yet measured on
  real things**; small things far away (a phone across the room) are hard for NanoDet at 320 px,
  and "silver" is read as grey. Someone swaying on the counting line can be counted in
  and out. **People who fill the picture are not counted** (sitting close to the camera, head and
  shoulders only): the counter is for people seen from the waist up, e.g. at a door.
- **The fly-brain car is measured only in simulation so far.** It zig-zags toward the ball.
- **The planner scores above were tuned on the sentences they were measured on**; a fresh set is
  needed for an honest number.
- **Text crosses borders.** The setup sentence passes through AWS Sydney, and with an AI
  planner goes to AWS EU Regions (Bedrock) or Nebius. No approved cross-border route under
  Uzbekistan's personal-data law is set up; frames and biometric data never leave the device.
- ESP32-CAM video on the local network is not encrypted. The computer must stay awake for live
  results. One owner per deployment.

## 10. Responsible use

Safety lives in fixed code, not in the AI (`CLAUDE.md`, rules agreed Oct 14):

| Rule | In code |
|---|---|
| The AI can only choose from a menu | job, colour, school mode or refusal; recipe and texts from templates; every recipe checked again (`koz/recipe.py`) |
| Private rooms stop the camera | privacy guard before every block; any error, missing model or slow check stops the job |
| No identity, ever | no blocks for face recognition, plates, documents or matching people; counting numbers live in memory and expire seconds after a person leaves |
| No profiling | no age, gender, emotion or ethnicity; no per-person timers or scores |
| School mode | faces blurred, counts only, strict guard |
| Frames never leave the device; no audio | no code writes frames to disk; the microphone is never opened |
| The cloud gets numbers, not pictures | the event format has no field for images, names, free text or track numbers |
| Stale means "unknown", not 0 | late frames → `unknown`; motors stop |
| Motors stop by themselves | disarmed at start, 250 ms watchdog, obstacle stop, armed only by a person |
| Data deletes itself | events after 7 days (built in the web app's local storage; DynamoDB TTL on AWS: TODO), totals after 30 (TODO) |

Refused jobs never run (section 2). Trials run in Islombek's home or places he has permission to
film, with nobody undressed or asleep in view; the video is filmed outside the bedroom, only with
people who agreed.

## 11. Future work (not built)

- **QR-code membership door (no faces stored).** A gym, club or library door that opens for a
  member who shows a QR code on their phone: OpenCV's `QRCodeDetector` reads the code, Ko'z checks it
  against the owner's member list and drives the lock. Nobody's face is stored, matched or recognised;
  the person presents the code on purpose. It is **not built**, and it would need a decision first:
  reading a member's code identifies that member, which rule 4 (no identity, no badge reading) forbids
  today, and a door lock is the kind of actuator rule 11 keeps out. Before building, it needs its own
  rules (the code is checked and forgotten, no visit history, a manual way in for everyone).

- **Open-vocabulary detection: find anything from words.** Today the object finder knows a fixed
  list (NanoDet's COCO classes: phone, backpack, bottle…), so "find my keys" is refused. An
  open-vocabulary detector (YOLO-World or OWL-ViT style, run with OpenCV DNN where it can) would take
  the owner's words as the class name. The same rules would hold: no people, animals or private
  objects as targets, the word list checked in code, never the car's input.
- **Several cameras in one job.** Today a job runs on one chosen camera (the Mac, the robot's
  ESP32-CAM or a phone). A job over two or three cameras (a shop's door and its till; a classroom's
  two doors) needs one privacy guard per camera, counts merged without identities (no matching a
  person between cameras, which rule 4 forbids), and a stop on any camera to hold the whole job.
- **Exam-integrity mode, privacy first.** For a school exam: the owner draws **seat zones**, and Koʻz
  watches zones, not people. It raises an alert when a zone shows something agreed in advance (two
  people in one seat zone, a seat zone empty for longer than agreed, a phone on a desk; zone
  timers only, never a timer per person), and **a human checks every alert**: Koʻz never accuses anyone. No names, no faces (blurred
  first, as today), no per-student scores or rankings (rule 5). Optional evidence: a few blurred
  frames around an alert, kept **only on the local computer**, deleted by themselves after a set
  time (e.g. 7 days) unless the teacher keeps one for a review. Visible signs in the room say the
  camera is on and what it looks for. **This would change today's rule that nothing is saved**
  (rule 8: no code writes frames to disk), so it needs Islombek's decision, the school's consent
  process and new rules before any code: who may see the evidence, for how long, and how a student
  can ask about it.

## 12. Reproduce

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
.venv/bin/python scripts/fetch_test_photos.py
.venv/bin/python -m pytest -q
```

Then `start-koz.command` (runner + web app on one computer), or the commands in `README.md`. AWS:
`deploy/README.md` and `docs/AWS_DAY.md`. Every dependency is pinned (`requirements.txt`,
`web/package-lock.json`).

## 13. Credits

Fruit-fly neuron model: Shiu et al. 2024, *Nature* (code MIT, Philip Shiu and Nico Spiller).
Wiring: FlyWire connectome v783 (Dorkenwald et al. 2024, Schlegel et al. 2024, *Nature*; data
CC BY-NC 4.0, non-commercial). YuNet (MIT, Shiqi Yu) and NanoDet-Plus (Apache 2.0, RangiLyu) from
OpenCV Zoo. ResNet18 Places365 (CC BY; Zhou et al., *IEEE TPAMI* 2017). Full notes in `README.md`.
