"""Local device setup (CLAUDE.md rule 7; contracts/events.md section 2).

These values exist only on this computer. They never come from a recipe, an import or
the cloud. For now this holds the simple version: "I own this camera" and the allowed
area, plus strict mode. The setup screen that fills them in comes later."""
import math
from dataclasses import dataclass

import cv2
import numpy as np

from .errors import KozError


@dataclass(frozen=True)
class LocalSetup:
    owner_confirmed: bool    # the owner ticked "I own this camera"
    allowed_area: tuple      # polygons; each is a list of (x, y) points, 0..1 across the frame
    school: bool = False     # asked explicitly during setup
    mount: str = "fixed"     # "fixed" or "moving" (the car)
    # Strict mode (--strict, for schools and public cameras): the privacy guard approves only
    # listed public places (policy.ALLOWED_SCENES). School mode always implies it (runner).
    # Default: run anywhere, stop on what it sees (koz/privacy.py). Local only: never in a
    # recipe, so it can't be imported or sent.
    strict: bool = False
    # The car's tested speed cap, as a share of full speed (contract section 3: motor speed is the
    # lower of this and the recipe's max_speed_ratio). 0.15 until measured with firmware/stop_test.
    motor_cap: float = 0.15

    def check(self):
        if self.owner_confirmed is not True:
            raise KozError("OWNERSHIP_REQUIRED")
        if self.mount not in ("fixed", "moving") or type(self.school) is not bool \
                or type(self.strict) is not bool or type(self.motor_cap) not in (int, float) \
                or not 0 < self.motor_cap <= 0.25:
            raise KozError("INVALID_COMMAND", "bad local setup")
        if not self.allowed_area or not all(_good_polygon(p) for p in self.allowed_area):
            raise KozError("ALLOWED_AREA_REQUIRED")

    def mask(self, width, height):
        """255 inside the allowed area, 0 outside. The runner blacks out the 0 pixels
        before any block (even the privacy guard) sees the frame."""
        mask = np.zeros((height, width), np.uint8)
        scale = np.array([width - 1, height - 1], np.float64)
        polygons = [np.round(np.array(p, np.float64) * scale).astype(np.int32) for p in self.allowed_area]
        cv2.fillPoly(mask, polygons, 255)
        return mask


def _good_polygon(points):
    try:
        pts = [(float(x), float(y)) for x, y in points]
    except (TypeError, ValueError):
        return False
    if len(pts) < 3 or not all(math.isfinite(v) and 0 <= v <= 1 for p in pts for v in p):
        return False
    return cv2.contourArea(np.array(pts, np.float32)) > 0
