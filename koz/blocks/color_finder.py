"""color_finder: finds the biggest round patch of one colour (for example, the red ball).

How it works:
1. Convert the frame from BGR to HSV: hue = which colour, saturation = how strong,
   value = how bright. OpenCV's hue runs 0..179 and wraps around, so 0 and 179 are
   both red.
2. Keep pixels whose hue is within hue_half_width of hue_center (measured around that
   circle) and that are colourful enough (saturation_min) and bright enough (value_min).
3. Remove pixel-sized noise with a morphological "opening" (shrink the mask, then grow it).
4. Find the outline of each patch. A patch counts as the target only if it looks like a ball:
   - big enough: at least min_area_ratio of the frame, and at least a circle of
     TARGET_MIN_RADIUS_PX (smaller shapes can't be judged);
   - round: "roundness" 4 pi area / perimeter^2 is 1 for a circle and low for ragged shapes;
   - filled: it fills most of the smallest circle around it (a square or a long strip doesn't).
     Only the part of that circle inside the frame counts, so a ball half out of view still can.
   The limits are fixed in koz/policy.py, so no recipe or adjustment can loosen them. Of the
   patches that pass, the largest is the target; with none, the target is "lost".
5. Say where it is: left, center or right.
The exact position stays on this computer (the fly brain will steer with it); only the
label is ever sent."""
import math
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
MIN_AREA_PX = math.pi * policy.TARGET_MIN_RADIUS_PX ** 2


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

        height, width = mask.shape
        min_area = max(self.min_area_ratio * mask.size, MIN_AREA_PX)
        best, best_area = None, 0.0
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:   # outer outlines only, so a highlight inside a ball doesn't matter
            area = cv2.contourArea(contour)
            pixels = area + cv2.arcLength(contour, True) / 2   # the outline runs through the edge pixels' centres
            if pixels >= min_area and pixels > best_area and looks_round(contour, area, width, height):
                best, best_area = contour, pixels
        if best is None:
            return LOST
        moments = cv2.moments(best)
        x = (moments["m10"] / moments["m00"] + 0.5) / width
        y = (moments["m01"] / moments["m00"] + 0.5) / height
        return Target(_label(x), float(x), float(y), float(best_area / mask.size))


def roundness(contour, area):
    """4 pi area / perimeter^2: about 0.9 for a ball's outline in pixels, lower for ragged shapes."""
    perimeter = cv2.arcLength(contour, True)
    return 4 * math.pi * area / perimeter ** 2 if perimeter else 0.0


def fill(contour, area, width, height):
    """How much of its smallest enclosing circle the patch fills, counting only the part of
    that circle inside the frame (so a ball cut off by the frame edge isn't penalised)."""
    (cx, cy), r = cv2.minEnclosingCircle(contour)
    x0, y0 = max(0, int(cx - r) - 1), max(0, int(cy - r) - 1)
    x1, y1 = min(width, int(cx + r) + 2), min(height, int(cy + r) + 2)
    disk = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.circle(disk, (round(cx - x0), round(cy - y0)), round(r), 255, -1)
    inside = cv2.countNonZero(disk)
    return area / inside if inside else 0.0


def looks_round(contour, area, width, height):
    return (roundness(contour, area) >= policy.TARGET_MIN_ROUNDNESS
            and fill(contour, area, width, height) >= policy.TARGET_MIN_FILL)


def _label(x):
    if x < 0.5 - policy.TARGET_CENTER_HALF_WIDTH:
        return "left"
    if x > 0.5 + policy.TARGET_CENTER_HALF_WIDTH:
        return "right"
    return "center"
