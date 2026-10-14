"""One-time conversion: Places365 ResNet18 (a PyTorch checkpoint) -> ONNX that OpenCV 5 can load.

OpenCV 5 can't read Caffe or Torch model files, so this runs once, with a temporary
PyTorch install that is NOT part of Ko'z's requirements. Its output is published as a
GitHub Release asset; scripts/fetch_models.py downloads that file and checks its SHA-256.
Running this again may give a file with different bytes (export metadata), so the
published file, not a fresh conversion, is the one Ko'z pins.

Source: resnet18_places365.pth.tar from http://places2.csail.mit.edu/models_places365/
(MIT CSAIL Places project, CC BY). Changes made here, as CC BY asks us to say:
  - input: 1 x 3 x 224 x 224 RGB, values 0..255 (what cv2.dnn.blobFromImage gives with swapRB=True);
  - added in front: the original preprocessing (divide by 255, subtract the ImageNet mean,
    divide by the ImageNet standard deviation);
  - unchanged: the ResNet18 weights;
  - added at the end: softmax, so the output is 365 probabilities in the order of
    categories_places365.txt.

The checkpoint is a Python "pickle", a format that can hide code. It is loaded with
weights_only=True, which refuses to run any.

Usage, in a throwaway venv with torch, torchvision, onnx, onnxscript and opencv-python:
  python scripts/convert_places365.py CHECKPOINT OUT.onnx"""
import argparse
import hashlib
import sys

import cv2
import numpy as np
import torch
import torchvision

SOURCE_SHA256 = "2f4759217d470da2b803f8f66cd4488a066406b555a5fb95ee9a4663f9f05588"
MEAN = (0.485, 0.456, 0.406)   # ImageNet values the Places365 models were trained with
STD = (0.229, 0.224, 0.225)


class Places365(torch.nn.Module):
    def __init__(self, resnet):
        super().__init__()
        self.resnet = resnet
        self.register_buffer("mean", torch.tensor(MEAN).view(1, 3, 1, 1) * 255)
        self.register_buffer("std", torch.tensor(STD).view(1, 3, 1, 1) * 255)

    def forward(self, image):
        return torch.softmax(self.resnet((image - self.mean) / self.std), dim=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("checkpoint")
    parser.add_argument("out")
    args = parser.parse_args()

    with open(args.checkpoint, "rb") as f:
        if hashlib.sha256(f.read()).hexdigest() != SOURCE_SHA256:
            sys.exit("checkpoint is not the pinned file")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    state = {k.removeprefix("module."): v for k, v in checkpoint["state_dict"].items()}
    resnet = torchvision.models.resnet18(num_classes=365)
    resnet.load_state_dict(state)
    model = Places365(resnet).eval()
    torch.onnx.export(model, (torch.zeros(1, 3, 224, 224),), args.out, input_names=["image"],
                      output_names=["probabilities"], opset_version=17, dynamo=False)

    # Check: OpenCV 5 on the ONNX file must give the same answers as PyTorch.
    net = cv2.dnn.readNetFromONNX(args.out)
    rng = np.random.default_rng(0)
    worst, same_top = 0.0, 0
    for _ in range(20):
        bgr = rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)
        net.setInput(cv2.dnn.blobFromImage(bgr, 1.0, (224, 224), (0, 0, 0), swapRB=True))
        ours = net.forward().ravel()
        with torch.no_grad():
            rgb = torch.from_numpy(np.ascontiguousarray(bgr[:, :, ::-1].transpose(2, 0, 1))).float()[None]
            theirs = model(rgb).numpy().ravel()
        worst = max(worst, float(np.abs(ours - theirs).max()))
        same_top += int(ours.argmax() == theirs.argmax())
    with open(args.out, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print(f"OpenCV {cv2.__version__} vs PyTorch {torch.__version__}: largest difference {worst:.2e}, "
          f"same top class {same_top}/20")
    print(f"{args.out}  sha256 {digest}")
    if worst > 1e-4 or same_top != 20:
        sys.exit("OpenCV and PyTorch disagree; do not publish this file")


if __name__ == "__main__":
    main()
