# Ko'z — tell a camera what job to do

## For judges: 5 minutes

With **Git and Python 3.13** installed, paste this **one command** into a terminal in a
directory that does not already contain `koz/` (macOS/Linux; internet needed for dependencies):

```bash
git clone https://github.com/TurdiyevIslombek/koz.git koz && cd koz && bash scripts/judge_demo.sh
```

It creates a virtual environment, installs the pinned packages, downloads and verifies the
45 MB privacy model, then runs the actual agent on [our 132 KB drawn clip](samples/orange-red-ball.mp4).
Allow about five minutes depending on downloads. No camera, robot, Node.js, account or API key is
needed. The clip has an orange-red ball, no people and no audio; the rule planner is selected
explicitly. Privacy and face-blur models remain enabled. This is OpenCV processing video frames,
not the browser's synthetic event replay.

Watch **plan → test → adjust → run**: the initial red range reports `target lost`, the first
`target_visible` check fails, the agent changes `color_finder.hue_center` from `0` to `13`,
revision 2 finds the ball, and the next check says `pass … -> run`. It runs for four more seconds
and exits automatically. A final `Adjusted: … (target_visible: lost -> …, pass)` records the result.
To repeat from this clone: `bash scripts/judge_demo.sh`. The clip is drawn test input, not a
measurement of real-world accuracy. [Fresh-clone verification](docs/JUDGE_VERIFICATION.md).

**Live website: [https://16.178.45.27](https://16.178.45.27)** (direct
[judges' view](https://16.178.45.27/#live)). No judge login is needed. Choose **English** in the
top-right language selector. After the owner shares a job, **Live job** shows its status, coarse
target position or counts, privacy state and a diagram; **Trials & proof** shows its agent
decisions/adjustments and the saved trial summaries the owner selected. Judges have read-only
access: no camera video, prompts, device tokens or job controls. If sharing is off, it says
**Not shared yet**; **Explore demo** opens a labelled synthetic sample. If the runner is offline,
live readings become unknown rather than presenting old values as current.

**Owner: turn on sharing** (English labels):

1. Open the live website → **English** → **Owner sign-in** → enter the owner password → **Sign in**.
2. With the camera computer connected, close the dialog, open **Set up a job**, choose the camera,
   enter a job and click **Test it**. Wait for the plan and job status in **Live job**.
3. Click **Connect device** → scroll to **Share with judges** → tick the saved trial summaries
   you want public → **Share current job with judges**. The button requires an existing job.
4. Open [https://16.178.45.27/#live](https://16.178.45.27/#live) in a private/incognito window to
   verify the judges' view. Sharing covers only that job and those summaries; share again after
   starting a different job. **Connect device → Stop sharing** withdraws it.

If the camera computer is not paired yet: **Connect device → Create runner token**, then start
`start-koz-cloud.command` on the camera computer and paste the token when asked. An already paired
device needs no new token. Local `http://127.0.0.1:4173` mode does not offer judges' sharing.

**Expected test skips:** a fresh clone with models and regression photos fetched normally skips
two Uno compile tests (optional `tools/bin/arduino-cli` absent) and one private person-video test
(`tests/fixtures/private/` deliberately stays off Git). The public ball clip does not replace a
real-person detector check. Missing Places365 photos/model or `clang++` cause additional skips;
use `pytest -q -rs` below to see every reason.

Describe a camera job in plain words (Uzbek, Russian or English). Ko'z turns it into a
recipe of tested OpenCV 5 blocks, runs it on live frames, checks the results and adjusts.
Faces are blurred, private rooms stop the camera, and frames never leave the device.

Built for the OpenCV AI Competition 2026 by Islombek Turdiyev (Tashkent, Uzbekistan).
Technical report: [docs/REPORT.md](docs/REPORT.md) · architecture: [docs/architecture.svg](docs/architecture.svg) ·
every measured result and failure: [docs/TRIALS.md](docs/TRIALS.md).

## What is in this repository

| Folder | What |
|---|---|
| `koz/` | The runner (Python, OpenCV 5): privacy guard, face blur, the blocks, recipe checks, the agent loop, the fly brain, the motors action |
| `web/` | The web app (Node.js): setup chat, live view, trials, recipe export and import ([web/README.md](web/README.md)) |
| `contracts/` | The runner ↔ web contract: `recipe.schema.json` and `events.md` |
| `firmware/` | Arduino sketches: `motor_listener` (the car), `stop_test` (speed cap and stopping distance), `camera_stream` (ESP32-CAM video and serial bridge; Wi-Fi settings stay private) |
| `samples/` | Public drawn ball clip and its provenance; regenerate with `scripts/make_judge_clip.py` |
| `deploy/` | AWS: one CloudFormation stack and its installer ([docs/AWS_DAY.md](docs/AWS_DAY.md)) |
| `tests/` | Python tests; they also run the firmware's safety rules and the real sketch on a fake Arduino |
| `docs/` | Report, trials, texts in three languages, video plan |

## Install (exact versions)

Tested on macOS 27 (MacBook Air M3, 8 GB), no GPU. Python 3.13.5; Node.js 25.1 (22 or newer works;
the AWS server installs 22); for the car only, arduino-cli 1.5.1 with the `arduino:avr` 1.8.8 core.

Install Git and Python 3.13 first (including `venv`; on macOS use the Python 3.13 installer
from [python.org](https://www.python.org/downloads/)). The web app additionally needs Node.js 22+
and npm. Verify with `git --version`, `python3.13 --version`, `node --version` and `npm --version`.
Native firmware tests need `clang++` (on macOS, `xcode-select --install` supplies it).
All blocks below run from the repository root, `koz/`, entered by the judge command above.
If you already cloned elsewhere, enter that root once. The web commands use a subshell so
copying the blocks in order keeps you at the root. The judge command already completes the
three Python installation steps below; repeating them is safe.

```bash
python3.13 -m venv .venv
```
```bash
.venv/bin/python -m pip install -r requirements.txt
```
```bash
.venv/bin/python scripts/fetch_models.py
```
`requirements.txt` pins every Python package, OpenCV 5.0.0 included. `fetch_models.py` downloads the
scene model (45 MB, below) and refuses it unless its SHA-256 matches; the two other models are in git.

The web app (every package pinned by `web/package-lock.json`):
```bash
(cd web && npm ci && npm run build)
```

The car's firmware (only with the robot): put arduino-cli 1.5.1 in `tools/bin/`
(https://arduino.github.io/arduino-cli), then
```bash
tools/bin/arduino-cli core install arduino:avr@1.8.8
```
```bash
tools/bin/arduino-cli lib install Servo@1.3.0
```

## Test

```bash
.venv/bin/python scripts/fetch_test_photos.py
```
```bash
.venv/bin/python -m pytest -q -rs
```
```bash
(cd web && npm test)
```
`fetch_test_photos.py` reads the official Places365 archive until it has the 71 photos the privacy
guard's regression test uses (about 80 MB; their copyright belongs to their owners, so they are not
in git; without them that test is skipped). The Python tests need no camera or board: hardware is mocked. The firmware tests need
`clang++` (Xcode command line tools); the two "compiles for the Uno" tests are skipped without
`tools/bin/arduino-cli`. One optional real-person video test also skips when
`tests/fixtures/private/` contains no private clip. Those recordings are intentionally not
published; all public fixture tests still run. See **For judges** above for the full skip explanation.

## Run

- **Everything on one computer:** double-click `start-koz.command` (the runner and the web app; type the
  job in the browser). Details below.
- **The runner alone:** `.venv/bin/python -m koz.server --i-own-this-camera --window`
  (`--help` lists the cameras, the car, school and strict mode, and `--cloud` for AWS).
- **On AWS:** [deploy/README.md](deploy/README.md) and the click list in [docs/AWS_DAY.md](docs/AWS_DAY.md).

## Live demo (your camera)

```bash
.venv/bin/python scripts/live_demo.py --i-own-this-camera
```
A window shows what Ko'z sees: faces blurred, a ring on the red object. It runs anywhere and
stops on what it sees (a bed, a toilet, a covered lens...), with the reason. q quits; macOS asks
for camera access the first time. Add `--job counter` to count people crossing a line instead
(`--school` for school mode), and `--strict` for schools and public cameras (listed places only).

## Agent demo: type the job in plain words

Double-click `demo-agent.command`, or:

```bash
.venv/bin/python scripts/agent_demo.py --i-own-this-camera "find the red ball"
.venv/bin/python scripts/agent_demo.py --i-own-this-camera "Sinfga kirgan o'quvchilarni sana, yuzlarni xiralashtir"
```
Ko'z prints its plan in the job's language, tries the recipe on the camera for 3 s, checks the
OpenCV numbers (is the ball visible? are the counts known?), changes one setting if the check
fails (at most 3 tries) and runs. Every step is printed as one line: observation → decision →
new setting → result. Requests Ko'z refuses (who is this person, a hidden camera, age or gender)
stop before the camera opens. `--video samples/orange-red-ball.mp4 --planner rules --no-window --seconds 4`
uses the public recording instead of the camera and stops automatically. Any other existing,
readable video can be supplied with `--video`; a missing or undecodable file reports
`VIDEO_UNREADABLE: video file not found or unreadable.`

Which planner reads the sentence: NVIDIA Nemotron on Nebius Token Factory if `NEBIUS_API_KEY=...`
is in `.env` (only the sentence is sent; `NEBIUS_MODEL` picks the model), then Amazon Nova 2 Lite on
Amazon Bedrock (EU Regions) if `AWS_BEARER_TOKEN_BEDROCK=...` is, else the rule planner
(fixed word lists, Uzbek in both alphabets, Russian, English). `--planner ollama` tries Gemma 4 on
this Mac through [Ollama](https://ollama.com) (`gemma4:e2b-it-qat`, 4.3 GB; nothing leaves the Mac),
but on Oct 15 it got 14 of 20 test sentences right with the camera running, against 18 for the
rule planner, so it isn't the default (`docs/TRIALS.md`). If an AI planner fails, the rules answer. Whichever it is, the AI only picks the job, colour
and refusal: the recipe and the plan text come from fixed templates, and any refusal wins. The
terminal prints which planner made each plan.

To see the same public clip's real events in the local browser, complete the web install above.
In one terminal at the repository root, run:

```bash
.venv/bin/python -m koz.server --i-own-this-camera --planner rules --video samples/orange-red-ball.mp4
```

In a second terminal at the repository root, run:

```bash
(cd web && npm run dev)
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173), choose **English → Set up a job**,
type `find the red ball` and click **Test it**. **Live job** shows the measurements;
**Trials & proof** shows the adjustment chain. Each new job reopens the clip from the start.
Use Ctrl+C in each terminal to stop the servers. This local owner view is separate from
the publicly shared AWS view described at the top.

## Everything at once: `start-koz.command`

Double-click `start-koz.command`. It starts the runner and the web app and opens the Setup
page: type the job there and watch it run. Everything shows in the browser: the numbers, the plan,
the adjustments, and the camera view in the eye (faces blurred), which the runner sends only over
this computer's own socket (`ws://127.0.0.1:8765/v1/preview`, contract section 14); it is never
stored and never sent to the cloud. For a car job, arm the motors by pressing Enter in the launcher's
Terminal window (never from the web). `KOZ_WINDOW=1` also opens the runner's own camera window.
Close the Terminal window to stop both. (Needs Node.js 22+ for the web app.)

The runner alone: `.venv/bin/python -m koz.server --i-own-this-camera [--window]`, a WebSocket
at `ws://127.0.0.1:8765` (this computer only) that sends every event exactly as in
`contracts/events.md` and accepts the 4 commands. Browsers can't connect to it directly; the
web app's own server does.

## The fly-brain car (demo 1)

Islombek's robot car (Arduino Uno + L298N, ESP32-CAM) chases a coloured ball with a simulation of
2,282 real fruit-fly neurons. Ko'z shows the brain a "threat" on the side without the ball, so the
fly's own escape turn steers it toward the ball (`koz/brains/flybrain/`).

1. Measure the speed cap and the stopping distance once: `firmware/stop_test/README.md`.
2. Upload `firmware/motor_listener` (its README). It starts disarmed and stops by itself.
3. Run, with the board on the USB cable and the ESP32-CAM stream (`--upside-down`: the car's camera
   is mounted upside down, like `CAMERA_FLIP` in the original `config.py`):
   ```bash
   .venv/bin/python scripts/agent_demo.py --i-own-this-camera --camera http://192.168.4.1:81/stream --upside-down --motors auto "Qizil koptokni quv"
   ```
   It asks you to press Enter to arm the motors (only a person at this computer can). Or start
   the runner with `--motors auto --camera esp32_cam=http://192.168.4.1:81/stream --upside-down esp32_cam` and
   press Enter in its Terminal to arm (or A in its window with `--window`); then type the job in the web app.

## Models and credits

**Fruit-fly brain.** The neuron model and its constants come from Shiu et al. 2024, "A Drosophila
computational brain model reveals sensorimotor processing" (*Nature*); their code
(github.com/philshiu/Drosophila_brain_model) is under the MIT License, copyright (c) 2023 Philip Shiu
and Nico Spiller. The wiring (`koz/brains/flybrain/original/brain/locomotion/`, a 2,282-neuron circuit)
is derived from the FlyWire connectome v783 (Dorkenwald et al. 2024, Schlegel et al. 2024, *Nature*),
whose published data is under **CC BY-NC 4.0** (attribution; non-commercial use only). The
simulation itself is Islombek's numpy version for the car.

**Face detection: YuNet**, from OpenCV Zoo (`models/face_detection_yunet`).
MIT License, copyright (c) 2020 Shiqi Yu. In this repo as
`koz/models/face_detection_yunet_2023mar.onnx`, with its license in `koz/models/YUNET_LICENSE`.

**Person detection (classroom counter): NanoDet-Plus**, from OpenCV Zoo
(`models/object_detection_nanodet`), trained on COCO by RangiLyu (https://github.com/RangiLyu/nanodet).
Apache License 2.0. In this repo, unchanged, as `koz/models/object_detection_nanodet_2022nov.onnx`,
with its license in `koz/models/NANODET_LICENSE`. Ko'z uses only its "person" class.

**Scene classification (privacy guard): ResNet18 trained on Places365**, by the MIT CSAIL
Places team. The pretrained Places365 models are released under the Creative Commons
Attribution license (CC BY).

> B. Zhou, A. Lapedriza, A. Khosla, A. Oliva and A. Torralba.
> "Places: A 10 million Image Database for Scene Recognition."
> IEEE Transactions on Pattern Analysis and Machine Intelligence, 2017.
> Project page: http://places2.csail.mit.edu · Code: https://github.com/CSAILVision/places365

Changes made by Ko'z: the original `resnet18_places365.pth.tar` was converted to ONNX
with `scripts/convert_places365.py`, which adds the original input normalisation in front
and a softmax at the end. The weights are unchanged. The converted file is published as a
GitHub Release asset (not in git) and fetched by `scripts/fetch_models.py`.
The category list `koz/models/categories_places365.txt` comes from the same repository
(MIT License, copyright (c) 2017 Bolei Zhou and MIT CSAIL Computer Vision; see
`koz/models/PLACES365_LICENSE`).

**Places365 test photos.** The privacy guard's regression tests use 71 photos from the
Places365 validation set; their copyright belongs to their owners, so they are not in this
repo (`scripts/fetch_test_photos.py` downloads them). Islombek Turdiyev signed the Places
team's request form for the original Places365 data on Oct 14, 2026
(http://places2.csail.mit.edu/download.html).

## Licence

The Ko'z code is under the MIT License ([LICENSE](LICENSE)). Some files keep their own licences
([NOTICE](NOTICE)): the FlyWire-derived wiring of the fly brain stays under **CC BY-NC 4.0**
(non-commercial use, with credit), the models under MIT / Apache 2.0 / CC BY, and the fonts under the
SIL Open Font License.
