"""line_counter: counts people crossing a line, for example a classroom door.

It follows each person from frame to frame with a simple tracker: a box in the new
frame is matched to the earlier box it overlaps most, if that overlap (IoU,
"intersection over union" = shared area / combined area) is at least TRACK_MIN_IOU.
Each followed person gets a number that exists only here, in memory, and is forgotten
TRACK_FORGET_S after they were last seen. Numbers are never saved or sent (rule 4);
only the two totals leave this block.

Which way is "entered": for the line from A to B, side(P) = cross(B - A, P - A), with
x to the right and y downwards. A person whose box centre goes from the negative side
to the positive side has entered; the other way, exited. Example: A = top middle,
B = bottom middle: walking from right to left on screen is "entered".
Only crossings through the segment A-B count, and the place a person is first seen
is never a crossing. Known limit: someone standing on the line and swaying can be
counted in and then out again."""
from dataclasses import dataclass

from .. import policy
from .base import Block


@dataclass(frozen=True)
class Crossings:
    entered: int
    exited: int


@dataclass
class _Track:          # one followed person (local only)
    box: tuple
    point: tuple       # box centre, 0..1 across the frame
    side: float        # last side of the line that wasn't exactly on it (0 = not known yet)
    seen: float        # frame time when last matched


class LineCounter(Block):
    type = "line_counter"

    def __init__(self, settings):
        self._a, self._b = (tuple(p) for p in settings["line"])
        self._tracks = []
        self.entered = self.exited = 0

    def process(self, ctx):
        height, width = ctx.image.shape[:2]
        people = ctx.results["person_detector"]
        self._tracks = [t for t in self._tracks if ctx.t - t.seen <= policy.TRACK_FORGET_S]
        matches = _match([p.box for p in people], [t.box for t in self._tracks])
        followed = []
        for i, person in enumerate(people):
            x0, y0, x1, y1 = person.box
            point = ((x0 + x1) / 2 / width, (y0 + y1) / 2 / height)
            side = _cross(self._a, self._b, point)
            track = self._tracks[matches[i]] if i in matches else None
            if track is None:
                followed.append(_Track(person.box, point, side, ctx.t))
                continue
            if side * track.side < 0 and _segments_cross(track.point, point, self._a, self._b):
                if track.side < 0:
                    self.entered += 1
                else:
                    self.exited += 1
            track.box, track.point, track.seen = person.box, point, ctx.t
            if side != 0:
                track.side = side
            followed.append(track)
        unmatched = [t for j, t in enumerate(self._tracks) if j not in matches.values()]
        self._tracks = followed + unmatched   # unmatched ones wait until TRACK_FORGET_S
        ctx.results[self.type] = Crossings(self.entered, self.exited)


def _cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _segments_cross(p, q, a, b):
    """True if the move p -> q passes through the segment a-b (its ends count)."""
    return _cross(p, q, a) * _cross(p, q, b) <= 0


def _iou(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    shared = w * h
    return shared / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - shared)


def _match(new_boxes, old_boxes):
    """Greedy matching, best overlaps first: {new index: old index}."""
    pairs = sorted(((_iou(n, o), i, j) for i, n in enumerate(new_boxes) for j, o in enumerate(old_boxes)),
                   reverse=True)
    matches, used = {}, set()
    for overlap, i, j in pairs:
        if overlap < policy.TRACK_MIN_IOU:
            break
        if i not in matches and j not in used:
            matches[i] = j
            used.add(j)
    return matches
