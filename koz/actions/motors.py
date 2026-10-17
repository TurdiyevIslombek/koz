"""The motors action (recipe "actions": [..., {"type": "motors", "max_speed_ratio": r}]; CLAUDE.md rule 11).

It sends the fly brain's wheel speeds to firmware/motor_listener over the USB cable. Safety is
layered:
  - the firmware: starts disarmed, a fault (250 ms without commands, forward into an obstacle,
    forward while the sonar can't see) disarms it, speed capped; Islombek's physical switch;
  - this action: speed = the lower of the recipe's max_speed_ratio and the locally tested cap
    (contract section 3); it stops the motors whenever the runner can't trust its outputs (stale
    frame, privacy check holding, slow processing) and disarms them when the job ends;
  - nothing here ARMS the motors. Arming is a local human action (contract: "Motor arming: a local
    human action; starts disarmed"), done with arm_by_hand() from the terminal or the runner window;
  - the link LOCKS OUT (Codex's motor safety review, Oct 16): after Stop, the end of a job, or any
    failed USB write, it refuses every wheel command until a person arms it again, whatever the
    board's last status said. halt() always tries both STOP and DISARM, even if one fails.
Wheel speeds never leave this computer."""
import threading
import time

from ..errors import KozError

FAULTS = ("WATCHDOG", "OBSTACLE", "NO_ECHO")    # firmware faults: they disarm the board
STATUS_FRESH_S = 0.5                           # the board reports every 100 ms; silence longer = link lost
WRITE_TIMEOUT_S = 0.2                          # a blocked USB write gives up (and locks the link) after this


class SerialMotorLink:
    """motor_listener over USB serial (115200 baud). `port` is the local config (e.g.
    "/dev/cu.usbmodem1101"), never from a recipe or the web. `serial_port` replaces the real
    port in tests. Opening the port resets the Uno: wait for READY."""

    def __init__(self, port=None, baud=115200, serial_port=None, ready_timeout_s=4.0, clock=time.monotonic):
        if serial_port is None:
            import serial   # pyserial, only needed with real hardware
            serial_port = serial.Serial(port, baud, timeout=0.1, write_timeout=WRITE_TIMEOUT_S)
        self._port, self._clock = serial_port, clock
        self._lock = threading.Lock()        # the board's status (the reading thread writes it)
        self._write_lock = threading.Lock()  # one line at a time, so Stop can't interleave with a drive
        # Why wheel commands are refused until a person arms again: None, "stopped" (Stop, or the job
        # ended) or "link_lost" (a USB write or read failed).
        self.lockout = None
        self.state, self.reason, self.distance_cm, self._seen_at, self.ready = 0, "NOT_ARMED", -1, None, False
        self._running = True
        self._thread = threading.Thread(target=self._read, name="koz-motors", daemon=True)
        self._thread.start()
        end = clock() + ready_timeout_s
        while not self.ready and clock() < end:
            time.sleep(0.02)
        if not self.ready:
            self.close()
            raise KozError("MOTOR_SAFETY_STOP", "the motor board did not answer")

    def _read(self):
        while self._running:
            try:
                raw = self._port.readline()
            except Exception:   # the cable was pulled: the board stops by itself (watchdog)
                self.lockout = "link_lost"
                break
            if raw:
                self.handle_line(raw.decode("ascii", "replace").strip())

    def handle_line(self, line):
        """One line from the board: READY, or S,state,reason,cm."""
        with self._lock:
            if line == "READY":   # (re)started: always disarmed
                self.ready, self.state, self.reason, self._seen_at = True, 0, "NOT_ARMED", self._clock()
                return
            parts = line.split(",")
            if len(parts) == 4 and parts[0] == "S" and parts[1] in ("0", "1"):
                try:
                    cm = int(parts[3])
                except ValueError:
                    return
                self.ready = True
                self.state, self.reason, self.distance_cm, self._seen_at = int(parts[1]), parts[2], cm, self._clock()

    def _write(self, text):
        """One line to the board (hold _write_lock). False if it failed: then the link locks out."""
        try:
            self._port.write((text + "\n").encode("ascii"))
            return True
        except Exception:
            self.lockout = "link_lost"
            return False

    def _send(self, text):
        with self._write_lock:
            if not self._write(text):
                raise KozError("MOTOR_SAFETY_STOP", "the motor board can't be reached")

    @property
    def armed(self):
        return self.lockout is None and self.fault is None and self.state == 1

    @property
    def fault(self):
        """The firmware fault that disarmed it, "NO_LINK" if the board went silent or a write failed, else None."""
        with self._lock:
            if self.lockout == "link_lost" or self._seen_at is None or self._clock() - self._seen_at > STATUS_FRESH_S:
                return "NO_LINK"
            return self.reason if self.state == 0 and self.reason in FAULTS else None

    def arm_by_hand(self):
        """Only for a person's action on this computer (a key in the runner window, Enter in the terminal).
        The only way to clear a lockout."""
        with self._write_lock:
            if not self._write("ARM"):
                raise KozError("MOTOR_SAFETY_STOP", "the motor board can't be reached")
            self.lockout = None

    def drive(self, left, right, allowed=None):
        """Send wheel commands. False (nothing sent) while locked out by Stop, or if `allowed()` says no
        (the job was cancelled); raises if the link is lost."""
        with self._write_lock:   # checked under the same lock as halt(): a Stop is never overtaken
            if self.lockout == "stopped" or (allowed is not None and not allowed()):
                return False
            if self.lockout is not None or not self._write(f"M,{int(left)},{int(right)}"):
                raise KozError("MOTOR_SAFETY_STOP", "the motor board can't be reached")
            return True

    def stop(self):
        self._send("STOP")

    def disarm(self):
        with self._write_lock:
            if self.lockout is None:
                self.lockout = "stopped"
            self._write("DISARM")

    def halt(self):
        """Stop and disarm now, and refuse every drive until a person arms again. Tries both lines even
        if one fails; never raises. True only if both were written."""
        with self._write_lock:
            if self.lockout is None:
                self.lockout = "stopped"
            stopped = self._write("STOP")
            disarmed = self._write("DISARM")
        return stopped and disarmed

    def close(self):
        self._running = False
        try:
            self._port.close()
        except Exception:
            pass


class MockMotorLink:
    """A stand-in for the board in tests: it remembers every line it was sent. Same lockout as
    SerialMotorLink. `delayed_status=True`: DISARM doesn't change the reported state (a real board
    reports it up to 100 ms later)."""

    def __init__(self, armed=False, delayed_status=False):
        self.sent, self.state, self.reason, self.distance_cm, self.silent = [], 1 if armed else 0, "NOT_ARMED", 200, False
        self.delayed_status, self.lockout = delayed_status, None
        self._write_lock = threading.Lock()

    @property
    def armed(self):
        return self.lockout is None and self.fault is None and self.state == 1

    @property
    def fault(self):
        if self.silent or self.lockout == "link_lost":
            return "NO_LINK"
        return self.reason if self.state == 0 and self.reason in FAULTS else None

    def arm_by_hand(self):
        with self._write_lock:
            self.sent.append("ARM")
            self.state, self.reason, self.lockout = 1, "WAITING", None

    def drive(self, left, right, allowed=None):
        with self._write_lock:
            if self.lockout == "stopped" or (allowed is not None and not allowed()):
                return False
            if self.lockout is not None:
                raise KozError("MOTOR_SAFETY_STOP")
            self.sent.append(f"M,{int(left)},{int(right)}")
            if self.state == 1:
                self.reason = "RUNNING"
            return True

    def stop(self):
        with self._write_lock:
            self.sent.append("STOP")

    def disarm(self):
        with self._write_lock:
            self._disarm()

    def _disarm(self):
        self.lockout = self.lockout or "stopped"
        self.sent.append("DISARM")
        if not self.delayed_status:
            self.state, self.reason = 0, "NOT_ARMED"

    def halt(self):
        with self._write_lock:
            self.lockout = self.lockout or "stopped"
            self.sent.append("STOP")
            self._disarm()
        return True

    def trip(self, fault):
        """What the firmware does on a fault: disarm."""
        self.state, self.reason = 0, fault

    def close(self):
        pass


class MotorsAction:
    """Sends wheel speeds while the job may drive. status: disarmed / enabled / stop_commanded."""

    def __init__(self, link, max_speed_ratio, local_cap, cancelled=None):
        """`cancelled()` is True once the owner stopped this job: from then on nothing drives, even if
        a person arms the board again for the next job (re-review of MS-1)."""
        self.link = link
        self.ratio = min(max_speed_ratio, local_cap)   # contract section 3: the lower of the two
        self.status = "enabled" if link.armed else "disarmed"
        self._ended = False
        self._cancelled = cancelled or (lambda: False)

    def _may_drive(self):
        return not self._ended and not self._cancelled()

    def check(self):
        """Before the job starts and before every move: a fault or a disarmed board stops the job."""
        if self.link.fault is not None:
            raise KozError("MOTOR_SAFETY_STOP", f"motor board: {self.link.fault}")
        if not self.link.armed:
            raise KozError("MOTOR_NOT_ARMED")

    def drive(self, wheels):
        """wheels: the brain's (left, right), -255..255. Sent as wheel x ratio (the board lifts and caps).
        After end() or a Stop, nothing is sent (a frame that was already being processed can't drive)."""
        if not self._may_drive() or self.link.lockout == "stopped":
            return
        self.check()
        left, right = (int(round(w * self.ratio)) for w in wheels)
        if self.link.drive(left, right, allowed=self._may_drive):   # asked again under the write lock
            self.status = "enabled"

    def pause(self):
        """Outputs can't be trusted right now: motors stop, the job goes on."""
        if not self._ended:
            self.link.stop()
            self.status = "stop_commanded" if self.link.armed else "disarmed"

    def end(self):
        """The job stopped (for any reason): stop and disarm, and lock the link until a person arms it
        again. Never raises. If a line couldn't be written, the status says stop_commanded, not
        disarmed (the board's own watchdog then stops the motors within 250 ms)."""
        if not self._ended:
            self._ended = True
            try:
                done = self.link.halt()
            except Exception:
                done = False
            self.status = "disarmed" if done else "stop_commanded"


ARDUINO_USB_IDS = {0x2341, 0x2A03, 0x1A86, 0x0403, 0x10C4}   # Arduino, Arduino.org, CH340, FTDI, CP210x


def open_motor_board(port):
    """The board on the USB cable: `port` like "/dev/cu.usbmodem1101", or "auto" (the one Arduino found)."""
    if port == "auto":
        from serial.tools import list_ports
        found = [p.device for p in list_ports.comports() if p.vid in ARDUINO_USB_IDS]
        if len(found) != 1:
            raise KozError("MOTOR_SAFETY_STOP", "found %d Arduino boards; give the port" % len(found))
        port = found[0]
    return SerialMotorLink(port)

