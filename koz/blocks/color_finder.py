"""color_finder: finds the biggest patch of one colour (for example, the red ball).

How it works:
1. Convert the frame from BGR to HSV: hue = which colour, saturation = how strong,
   value = how bright. OpenCV's hue runs 0..179 and wraps around, so 0 and 179 are
   both red.
2. Keep pixels whose hue is within hue_half_width of hue_center (measured around that
   circle) and that are colourful enough (saturation_min) and bright enough (value_min).
3. Remove pixel-sized noise with a morphological "opening" (shrink the mask, then grow it).
4. Find the connected patches and keep the largest. If it covers less than
   min_area_ratio of the frame, the target is "lost".
5. Say where it is: left, center or right.
The exact position stays on this computer (the fly brain will steer with it); only the
label is ever sent."""
from dataclasses import dataclass

import cv2
import numpy as np

from .. import policy
from .base import Block


@dataclass(frozen=True)
class Target:
    label: str          # left | center | right | lost
    x: float | None     # 0 = left edge, 1 = right edge (local only)
    y: float | None     # 0 = top, 1 = bottom (local only)
    area_ratio: float   # share of the frame the patch covers; 0 when lost


LOST = Target("lost", None, None, 0.0)


class ColorFinder(Block):
    type = "color_finder"
    _KERNEL = np.ones((3, 3), np.uint8)

    def __init__(self, settings):
        self.hue_center = settings["hue_center"]
        self.hue_half_width = settings["hue_half_width"]
        self.saturation_min = settings["saturation_min"]
        self.value_min = settings["value_min"]
        self.min_area_ratio = settings["min_area_ratio"]

    def process(self, ctx):
        ctx.results[self.type] = self.find(ctx.image)

    def find(self, image):
        hue, sat, val = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
        distance = np.abs(hue.astype(np.int16) - self.hue_center)
        distance = np.minimum(distance, 180 - distance)   # the short way around the hue circle
        mask = ((distance <= self.hue_half_width) & (sat >= self.saturation_min)
                & (val >= self.value_min)).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._KERNEL)

        count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if count <= 1:   # label 0 is the background
            return LOST
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        area_ratio = stats[biggest, cv2.CC_STAT_AREA] / mask.size
        if area_ratio < self.min_area_ratio:
            return LOST
        height, width = mask.shape
        x = (centroids[biggest][0] + 0.5) / width
        y = (centroids[biggest][1] + 0.5) / height
        return Target(_label(x), float(x), float(y), float(area_ratio))


def _label(x):
    if x < 0.5 - policy.TARGET_CENTER_HALF_WIDTH:
        return "left"
    if x > 0.5 + policy.TARGET_CENTER_HALF_WIDTH:
        return "right"
    return "center"
