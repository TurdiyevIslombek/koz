"""object_finder: finds one kind of everyday thing (a phone, a backpack, a bottle...) with the same
NanoDet-Plus model on OpenCV 5 that counts people (COCO classes), optionally of one colour, and says
where it is: left / center / right / lost, like color_finder (Islombek, Oct 22: "track a silver
phone", "a blue backpack").

On this computer only: the boxes stay here; only the label (left/center/right/lost) is sent.
People and animals are never objects here (CLAUDE.md rules 4 and 11), and beds, toilets and sinks
belong to the privacy guard. Only a ball (color_finder) can steer the car (the schema's rule 11).

The colour check looks at the middle 60 % of the box (the edges are often background) in HSV: at
least COLOUR_SHARE of those pixels must be of the asked colour."""
import cv2
import numpy as np

from .base import Block
from .color_finder import LOST, Target, _label
from .person_detector import NanoDet

# COCO class numbers the object finder may look for (contracts/recipe.schema.json lists the same names).
OBJECTS = {"cell phone": 67, "backpack": 24, "handbag": 26, "suitcase": 28, "umbrella": 25, "bottle": 39,
           "cup": 41, "bowl": 45, "laptop": 63, "keyboard": 66, "mouse": 64, "remote": 65, "book": 73,
           "clock": 74, "chair": 56, "scissors": 76, "teddy bear": 77, "apple": 47, "banana": 46, "tv": 62,
           "vase": 75, "potted plant": 58, "bicycle": 1}
COLOUR_SHARE = 0.25
HUE_RANGES = {"red": [(0, 10), (170, 179)], "orange": [(11, 22)], "yellow": [(23, 34)], "green": [(35, 85)],
              "blue": [(86, 130)], "purple": [(131, 169)]}


def colour_matches(image, box, colour):
    """Is the middle of this box mostly the asked colour? "any" always is."""
    if colour == "any":
        return True
    x0, y0, x1, y1 = (int(v) for v in box)
    dx, dy = (x1 - x0) // 5, (y1 - y0) // 5
    middle = image[y0 + dy:y1 - dy, x0 + dx:x1 - dx]
    if middle.size == 0:
        return False
    hue, sat, val = (c.astype(np.int16) for c in cv2.split(cv2.cvtColor(middle, cv2.COLOR_BGR2HSV)))
    if colour == "white":
        hit = (sat < 40) & (val >= 180)
    elif colour == "black":
        hit = val < 60
    elif colour == "grey":   # grey and silver
        hit = (sat < 50) & (val >= 60) & (val < 210)
    else:
        hit = np.zeros(hue.shape, bool)
        for low, high in HUE_RANGES[colour]:
            hit |= (hue >= low) & (hue <= high)
        hit &= (sat >= 70) & (val >= 50)
    return hit.mean() >= COLOUR_SHARE


class ObjectFinder(Block):
    type = "object_finder"

    def __init__(self, settings, detector=None):
        self.class_id = OBJECTS[settings["object"]]
        self.colour, self.min_confidence = settings["colour"], settings["min_confidence"]
        # Load the model now, so a missing model stops the job before any frame is used.
        self.detector = detector if detector is not None else NanoDet()

    def find(self, image):
        """The most confident, largest thing of that kind (and colour), or LOST."""
        height, width = image.shape[:2]
        best = None
        for d in self.detector.detect(image, (self.class_id,), self.min_confidence):
            if not colour_matches(image, d.box, self.colour):
                continue
            area = (d.box[2] - d.box[0]) * (d.box[3] - d.box[1])
            if best is None or d.score * area > best[0]:
                best = (d.score * area, d.box, area)
        if best is None:
            return LOST
        _, box, area = best
        x, y = (box[0] + box[2]) / 2 / width, (box[1] + box[3]) / 2 / height
        return Target(_label(x), float(x), float(y), float(area / (width * height)))

    def process(self, ctx):
        ctx.results[self.type] = self.find(ctx.image)
