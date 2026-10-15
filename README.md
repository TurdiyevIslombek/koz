# Ko'z — tell a camera what job to do

Describe a camera job in plain words (Uzbek, Russian or English). Ko'z turns it into a
recipe of tested OpenCV 5 blocks, runs it on live frames, checks the results and adjusts.
Faces are blurred, private rooms stop the camera, and frames never leave the device.

Work in progress for the OpenCV AI Competition 2026.

## Run the tests

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_models.py
.venv/bin/python scripts/fetch_test_photos.py
.venv/bin/python -m pytest -q
```

`fetch_models.py` downloads the scene model (below) and refuses it unless its SHA-256 matches.
`fetch_test_photos.py` downloads 71 real Places365 photos for the privacy guard's
regression test (not in git: their copyright belongs to their owners).

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
stop before the camera opens. `--video clip.mp4` uses a recording instead of the camera.

Which planner reads the sentence: NVIDIA Nemotron on Nebius Token Factory if `NEBIUS_API_KEY=...`
is in `.env` (only the sentence is sent; `NEBIUS_MODEL` picks the model), else the rule planner
(fixed word lists, Uzbek in both alphabets, Russian, English). `--planner ollama` tries Gemma 4 on
this Mac through [Ollama](https://ollama.com) (`gemma4:e2b-it-qat`, 4.3 GB; nothing leaves the Mac),
but on Oct 15 it got 14 of 20 test sentences right with the camera running, against 18 for the
rule planner, so it isn't the default (`docs/TRIALS.md`). If an AI planner fails, the rules answer. Whichever it is, the AI only picks the job, colour
and refusal: the recipe and the plan text come from fixed templates, and any refusal wins. The
terminal prints which planner made each plan.

## Everything at once: `start-koz.command`

Double-click `start-koz.command`. It starts the runner and the web app and opens the Setup
page: type the job there and watch it run. The numbers, the plan and the adjustments show in the
browser; the camera view (faces blurred) shows in the "Ko'z runner" window, where q stops the
job. Close the Terminal window to stop both. (Needs Node.js 22+ for the web app.)

The runner alone: `.venv/bin/python -m koz.server --i-own-this-camera [--window]`, a WebSocket
at `ws://127.0.0.1:8765` (this computer only) that sends every event exactly as in
`contracts/events.md` and accepts the 4 commands. Browsers can't connect to it directly; the
web app's own server does.

## Models and credits

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
