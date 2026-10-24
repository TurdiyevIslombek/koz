"""Draw the public judge fixture. No camera, downloaded images, people or audio.

Run with .venv/bin/python scripts/make_judge_clip.py to regenerate the checked-in MP4.
The hue stays constant: a successful second round must come from the agent's setting
change, not a conveniently redder ball appearing later in the recording.
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "samples" / "orange-red-ball.mp4"
WIDTH, HEIGHT, FPS, SECONDS = 320, 240, 10, 18


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    writer = cv2.VideoWriter(str(OUTPUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not create the sample MP4")
    # A lightly textured, drawn grey stage; only the ball has a strong colour.
    rng = np.random.default_rng(11)
    grey = np.tile(np.linspace(100, 170, WIDTH), (HEIGHT, 1)) + rng.normal(0, 3, (HEIGHT, WIDTH))
    background = np.repeat(np.clip(grey, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
    cv2.line(background, (0, 185), (WIDTH - 1, 185), (190, 190, 190), 2)
    try:
        for i in range(FPS * SECONDS):
            frame = background.copy()
            x = round(160 + 60 * np.sin(2 * np.pi * i / (FPS * 12)))
            cv2.ellipse(frame, (x, 174), (27, 5), 0, 0, 360, (80, 80, 80), -1)
            cv2.circle(frame, (x, 140), 27, (0, 110, 255), -1, cv2.LINE_AA)
            writer.write(frame)
    finally:
        writer.release()
    if OUTPUT.stat().st_size >= 2_000_000:
        raise RuntimeError("Judge clip must stay below 2 MB")
    print(f"{OUTPUT.relative_to(ROOT)}: {SECONDS} s, {OUTPUT.stat().st_size:,} bytes, drawn locally")


if __name__ == "__main__":
    main()
