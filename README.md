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
A window shows what Ko'z sees: faces blurred, a ring on the red object, and a private room
(bathroom, bedroom...) stops it with the reason. q quits; macOS asks for camera access the first time.
Add `--job counter` to count people crossing a line instead (`--school` for school mode).

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
