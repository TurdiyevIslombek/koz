"""The motors action (recipe "actions": [..., {"type": "motors", "max_speed_ratio": r}]; CLAUDE.md rule 11).

It sends the fly brain's wheel speeds to firmware/motor_listener over the USB cable. Safety is
layered:
  - the firmware: starts disarmed, a fault (250 ms without commands, forward into an obstacle,
    forward while the sonar can't see) disarms it, speed capped; Islombek's physical switch;
  - this action: speed = the lower of the recipe's max_speed_ratio and the locally tested cap
    (contract section 3); it stops the motors whenever the runner can't trust its outputs (stale
    frame, privacy check holding, slow processing) and disarms them when the job ends;
  - nothing here ARMS the motors. Arming is a local human action (contract: "Motor arming: a local
    human action; starts disarmed"), done with arm_by_hand() from the terminal or the runner window.
Wheel speeds never leave this computer."""
import threading
import time

from ..errors import KozError

FAULTS = ("WATCHDOG", "OBSTACLE", "NO_ECHO")    # firmware faults: they disarm the board
STATUS_FRESH_S = 0.5                           # the board reports every 100 ms; silence longer = link lost


class SerialMotorLink:
    """motor_listener over USB serial (115200 baud). `port` is the local config (e.g.
    "/dev/cu.usbmodem1101"), never from a recipe or the web. `serial_port` replaces the real
    port in tests. Opening the port resets the Uno: wait for READY."""

    def __init__(self, port=None, baud=115200, serial_port=None, ready_timeout_s=4.0, clock=time.monotonic):
        if serial_port is None:
            import serial   # pyserial, only needed with real hardware
            serial_port = serial.Serial(port, baud, timeout=0.1)
        self._port, self._clock = serial_port, clock
        self._lock = threading.Lock()
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

    def _send(self, text):
        try:
            self._port.write((text + "\n").encode("ascii"))
        except Exception:
            raise KozError("MOTOR_SAFETY_STOP", "the motor board can't be reached") from None

    @property
    def armed(self):
        return self.fault is None and self.state == 1

    @property
    def fault(self):
        """The firmware fault that disarmed it, "NO_LINK" if the board went silent, else None."""
        with self._lock:
            if self._seen_at is None or self._clock() - self._seen_at > STATUS_FRESH_S:
                return "NO_LINK"
            return self.reason if self.state == 0 and self.reason in FAULTS else None

    def arm_by_hand(self):
        """Only for a person's action on this computer (a key in the runner window, Enter in the terminal)."""
        self._send("ARM")

    def drive(self, left, right):
        self._send(f"M,{int(left)},{int(right)}")

    def stop(self):
        self._send("STOP")

    def disarm(self):
        self._send("DISARM")

    def close(self):
        self._running = False
        try:
            self._port.close()
        except Exception:
            pass


class MockMotorLink:
    """A stand-in for the board in tests: it remembers every line it was sent."""

    def __init__(self, armed=False):
        self.sent, self.state, self.reason, self.distance_cm, self.silent = [], 1 if armed else 0, "NOT_ARMED", 200, False

    @property
    def armed(self):
        return self.fault is None and self.state == 1

    @property
    def fault(self):
        if self.silent:
            return "NO_LINK"
        return self.reason if self.state == 0 and self.reason in FAULTS else None

    def arm_by_hand(self):
        self.sent.append("ARM")
        self.state, self.reason = 1, "WAITING"

    def drive(self, left, right):
        self.sent.append(f"M,{int(left)},{int(right)}")
        if self.state == 1:
            self.reason = "RUNNING"

    def stop(self):
        self.sent.append("STOP")

    def disarm(self):
        self.sent.append("DISARM")
        self.state, self.reason = 0, "NOT_ARMED"

    def trip(self, fault):
        """What the firmware does on a fault: disarm."""
        self.state, self.reason = 0, fault

    def close(self):
        pass


class MotorsAction:
    """Sends wheel speeds while the job may drive. status: disarmed / enabled / stop_commanded."""

    def __init__(self, link, max_speed_ratio, local_cap):
        self.link = link
        self.ratio = min(max_speed_ratio, local_cap)   # contract section 3: the lower of the two
        self.status = "enabled" if link.armed else "disarmed"
        self._ended = False

    def check(self):
        """Before the job starts and before every move: a fault or a disarmed board stops the job."""
        if self.link.fault is not None:
            raise KozError("MOTOR_SAFETY_STOP", f"motor board: {self.link.fault}")
        if not self.link.armed:
            raise KozError("MOTOR_NOT_ARMED")

    def drive(self, wheels):
        """wheels: the brain's (left, right), -255..255. Sent as wheel x ratio (the board lifts and caps)."""
        self.check()
        left, right = (int(round(w * self.ratio)) for w in wheels)
        self.link.drive(left, right)
        self.status = "enabled"

    def pause(self):
        """Outputs can't be trusted right now: motors stop, the job goes on."""
        if not self._ended:
            self.link.stop()
            self.status = "stop_commanded" if self.link.armed else "disarmed"

    def end(self):
        """The job stopped (for any reason): stop and disarm; the next job needs arming by hand."""
        if not self._ended:
            self._ended = True
            try:
                self.link.stop()
                self.link.disarm()
            except KozError:
                pass   # the board can't be reached: its watchdog stops the motors by itself
            self.status = "disarmed"
