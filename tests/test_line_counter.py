"""line_counter: counts crossings through the line, in the right direction, with no saved IDs."""
import numpy as np
import pytest

from helpers import HEIGHT, WIDTH, ScriptedPeople, walker
from koz import policy
from koz.blocks import Crossings, FrameContext, LineCounter, PersonDetector

DOOR = [[0.5, 0.0], [0.5, 1.0]]   # top middle -> bottom middle: right-to-left is "entered"


def count(script, line=DOOR, seconds_per_frame=0.1):
    detector = PersonDetector({"min_confidence": 0.5}, detector=ScriptedPeople(script))
    counter = LineCounter({"line": line})
    blank = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
    result = None
    for n in range(len(script)):
        ctx = FrameContext(blank, t=1000 + n * seconds_per_frame)
        detector.process(ctx)
        counter.process(ctx)
        result = ctx.results["line_counter"]
    return result


def frames_of(*people):
    """Merge several walkers frame by frame."""
    return [[p[n] for p in people if n < len(p)] for n in range(max(len(p) for p in people))]


def test_right_to_left_is_entered():
    assert count(frames_of(walker(260, 60, 12))) == Crossings(entered=1, exited=0)


def test_left_to_right_is_exited():
    assert count(frames_of(walker(60, 260, 12))) == Crossings(entered=0, exited=1)


def test_someone_who_stays_on_one_side_is_not_counted():
    assert count(frames_of(walker(40, 120, 12))) == Crossings(0, 0)


def test_two_people_crossing_opposite_ways():
    assert count(frames_of(walker(260, 60, 12, y=70), walker(60, 260, 12, y=170))) == Crossings(1, 1)


def test_only_crossings_through_the_segment_count():
    top_half = [[0.5, 0.0], [0.5, 0.4]]   # the person walks across the bottom part instead
    assert count(frames_of(walker(260, 60, 12, y=180)), line=top_half) == Crossings(0, 0)


def test_a_person_gone_too_long_is_forgotten():
    """Seen on the right, gone for longer than TRACK_FORGET_S, then seen on the left:
    a new person, not a crossing."""
    gap = int(policy.TRACK_FORGET_S / 0.1) + 5
    script = [[(230, 60, 290, 180)]] * 3 + [[]] * gap + [[(30, 60, 90, 180)]] * 3
    assert count(script) == Crossings(0, 0)


def test_results_hold_totals_only():
    result = count(frames_of(walker(260, 60, 12)))
    assert set(vars(result)) == {"entered", "exited"}   # no person numbers leave the block


@pytest.mark.parametrize("seconds_per_frame", [0.05, 0.2])
def test_frame_rate_does_not_change_the_count(seconds_per_frame):
    assert count(frames_of(walker(260, 60, 12)), seconds_per_frame=seconds_per_frame) == Crossings(1, 0)
