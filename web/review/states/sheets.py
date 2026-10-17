"""Contact sheets of the Live-state screenshots: for each state and theme, Uzbek | Russian | English
side by side at 1x (360 px each). Input and output: the folder shoot.mjs wrote.
    .venv/bin/python web/review/states/sheets.py web/review/states/shots"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

folder = Path(sys.argv[1])
shots = json.loads((folder / "shots.json").read_text())
for state in dict.fromkeys(s["state"] for s in shots):
    for theme in ("light", "dark"):
        images = []
        for language in ("uz", "ru", "en"):
            image = cv2.imread(str(folder / f"{state}-{language}-{theme}.png"))
            images.append(cv2.resize(image, (360, round(image.shape[0] * 360 / image.shape[1])), interpolation=cv2.INTER_AREA))
        height = max(i.shape[0] for i in images)
        background = (233, 241, 242) if theme == "light" else (20, 22, 20)
        sheet = np.full((height, 360 * 3 + 2 * 12, 3), background, np.uint8)
        for n, image in enumerate(images):
            sheet[:image.shape[0], n * 372:n * 372 + 360] = image
        cv2.imwrite(str(folder / f"sheet-{state}-{theme}.png"), sheet)
print("sheets written")
