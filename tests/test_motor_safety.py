"""Regression tests for Codex's motor safety review (.collab/reviews/motor-safety.md, Oct 16), one
section per finding. Each test was written first and failed on the code the review saw; the fix came
after. Mock hardware only: MockMotorLink, a fake serial port, fake cameras."""
import threading

import pytest
from helpers import FakeClock
from test_motors import FakePort

from koz.actions.motors import MotorsAction, SerialMotorLink
from koz.errors import KozError


# --- MS-3: a failed STOP skipped DISARM, said "disarmed" and let a new job drive without ARM ------------

class FlakyPort(FakePort):
    """A fake USB port whose writes of the listed lines fail (a cable that drops for a moment)."""

    def __init__(self):
        super().__init__()
        self.failing = set()

    def write(self, data):
        if data.decode().strip() in self.failing:
            raise OSError("injected USB write failure")
        super().write(data)


def armed_link(port, clock):
    link = SerialMotorLink(serial_port=port, clock=clock)
    link.arm_by_hand()
    link.handle_line("S,1,RUNNING,200")   # the board says: armed
    return link


def lines(port):
    return [w.strip() for w in port.written]


@pytest.mark.parametrize("failing", [{"STOP"}, {"DISARM"}, {"STOP", "DISARM"}])
def test_a_failed_stop_or_disarm_still_tries_the_other_and_locks_the_link(failing):
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    try:
        action = MotorsAction(link, .25, .2)
        action.drive((100, 100))
        port.failing = failing
        action.end()
        assert lines(port)[2:] == [line for line in ("STOP", "DISARM") if line not in failing]   # both tried
        assert action.status == "stop_commanded"            # never "disarmed" from a write that failed
        assert not link.armed and link.fault == "NO_LINK"   # latched, although the board's status is fresh
    finally:
        link.close()


def test_after_a_write_failure_only_a_person_can_make_it_drive_again():
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    try:
        MotorsAction(link, .25, .2).drive((100, 100))
        port.failing = {"STOP"}
        MotorsAction(link, .25, .2).end()
        port.failing = set()                     # the cable works again before the board's watchdog
        link.handle_line("S,1,RUNNING,200")      # and the board still says armed
        sent = len(port.written)
        with pytest.raises(KozError):
            MotorsAction(link, .25, .2).drive((100, 100))
        assert len(port.written) == sent         # nothing was sent: no new job without a new ARM
        link.arm_by_hand()                       # a person, on this computer
        link.handle_line("S,1,RUNNING,200")
        MotorsAction(link, .25, .2).drive((100, 100))
        assert lines(port)[-2:] == ["ARM", "M,20,20"]
    finally:
        link.close()


def test_a_reader_that_fails_means_no_link_at_once():
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    port.closed = True                           # the cable was pulled: readline() raises
    link._thread.join(1)
    assert link.fault == "NO_LINK" and not link.armed   # without waiting for the status to go stale
    with pytest.raises(KozError):
        MotorsAction(link, .25, .2).drive((100, 100))
    link.close()


def test_serial_writes_have_a_time_limit(monkeypatch):
    import serial
    opened = {}

    def fake_serial(*args, **kwargs):
        opened.update(kwargs)
        return FakePort()

    monkeypatch.setattr(serial, "Serial", fake_serial)
    link = SerialMotorLink("/dev/cu.fake")
    try:
        assert 0 < opened["write_timeout"] <= 0.25   # a blocked write can't hold up STOP / DISARM
    finally:
        link.close()


def test_threads_can_stop_while_another_drives():
    """The job thread drives while Stop arrives from the command thread: writes never interleave."""
    port, clock = FlakyPort(), FakeClock()
    link = armed_link(port, clock)
    try:
        action = MotorsAction(link, .25, .2)
        driver = threading.Thread(target=lambda: [action.drive((100, 100)) for _ in range(200)])
        driver.start()
        link.halt()
        driver.join(5)
        written = lines(port)
        stop = written.index("STOP")
        assert written[stop + 1] == "DISARM" and not any(w.startswith("M,") for w in written[stop:])
    finally:
        link.close()
