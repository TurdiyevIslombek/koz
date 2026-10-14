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
.venv/bin/python -m pytest -q
```

`fetch_models.py` downloads the scene model (below) and refuses it unless its SHA-256 matches.

## Models and credits

**Face detection: YuNet**, from OpenCV Zoo (`models/face_detection_yunet`).
MIT License, copyright (c) 2020 Shiqi Yu. In this repo as
`koz/models/face_detection_yunet_2023mar.onnx`, with its license in `koz/models/YUNET_LICENSE`.

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
