// motor_logic.h - the safety rules of the motor listener (CLAUDE.md rule 11; contracts/events.md 3:
// "starts stopped; stops within 250 ms without a fresh command; ... A fault disarms; re-arming is
// local and by hand"), with no Arduino code in it, so they are tested on the Mac too
// (firmware/tests/test_motor_logic.cpp, run by tests/test_firmware.py).
//
// The laptop sends wheel commands -255..255 (like "M,L,R" in Islombek's car.ino). This file decides
// what the motors really get:
//   1. Disarmed at power-up and after DISARM: motors off. ARM enables them; the laptop sends ARM only
//      when a person arms the motors by hand on that computer (never from the web or a recipe).
//   2. Armed but no command yet: motors off (WAITING).
//   3. Faults (each one DISARMS, and the motors stay off until the next ARM by hand):
//        WATCHDOG  no fresh command for watchdog_ms (250) after commands started
//        OBSTACLE  asked to move forward while something is closer than stop_cm
//        NO_ECHO   asked to move forward while the sensor can't see (missing_echoes_block pings in a row)
//      Next to an obstacle, turning on the spot and reversing are not faults: one side forward and one
//      backwards becomes a pure spin (judged on the capped values: security review, Oct 16).
//   4. Speed cap: forward at most speed_cap, backwards at most reverse_cap (the sensor looks forward only).
//   5. The motors don't turn below about min_pwm, so commands are lifted into min_pwm..max_pwm (as car.ino);
//      max_pwm keeps the motors at their highest safe voltage (6 V on Islombek's 9.5 V pack, Oct 18).
//   6. The watchdog is a lease (motor safety review MS-4, Oct 16): the motors may run only while
//      now - last command < watchdog_ms. A command that arrives after the lease ran out trips the
//      fault first, so it can't revive the motors.
// Also here: the line parser (review MS-5). Only exact words and "M,<number>,<number>" are commands;
// a line that is too long or has a strange byte is thrown away whole, up to its end.
#pragma once
#include <stdint.h>   // uint32_t: millis() is 32 bits on the Uno; the same on the Mac in tests
#include <string.h>

enum MotorState { DISARMED = 0, ARMED = 1 };
enum StopReason { RUNNING = 0, NOT_ARMED = 1, WAITING = 2, WATCHDOG = 3, OBSTACLE = 4, NO_ECHO = 5 };
inline bool isFault(int r) { return r == 3 || r == 4 || r == 5; }

struct MotorSettings {
  int speed_cap;                  // largest forward command, 0..255 (measure it: firmware/stop_test)
  int reverse_cap;                // largest backwards command
  int min_pwm;                    // PWM below which the motors only buzz
  int stop_cm;                    // forward into something closer than this = fault (measure it)
  uint32_t watchdog_ms;           // no fresh command for this long -> fault
  int missing_echoes_block;       // this many pings in a row without an echo -> forward is a fault
  int max_pwm;                    // PWM that gives the motors their highest safe voltage (204: 6 V of 7.5 V)
};

inline int clampInt(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }
inline int absInt(int v) { return v < 0 ? -v : v; }

// car.ino's lift(): tiny commands are a stop; others keep their order inside min_pwm..max_pwm.
inline int liftToPwm(int command, int min_pwm, int max_pwm) {
  int a = absInt(command);
  if (a < 12) return 0;
  int out = min_pwm + (int)((long)a * (max_pwm - min_pwm) / 255);
  return command > 0 ? out : -out;
}

// Soft start, from Islombek's car.ino (Oct 18): four motors jumping to full power, or from forward to
// reverse, pull a current spike that dips the battery and restarts the Arduino and the camera. So a
// side speeds up at most ramp_per_ms PWM per millisecond, and a change of direction stops first and
// waits reverse_pause_ms. Slowing down and stopping are never delayed (a stop must not wait: the
// 250 ms watchdog, obstacles, faults and STOP still cut the power at once). Applied after MotorLogic.
struct SoftStart {
  int ramp_per_ms;
  uint32_t reverse_pause_ms;
  int out[2];            // what each side gets now
  int last_dir[2];       // the direction it last moved: 1, -1 (0 = never)
  uint32_t stopped_ms[2];
  uint32_t last_ms;
  bool started;

  SoftStart(int ramp, uint32_t pause)
      : ramp_per_ms(ramp), reverse_pause_ms(pause), out{0, 0}, last_dir{0, 0}, stopped_ms{0, 0}, last_ms(0), started(false) {}

  // *left, *right: MotorLogic's PWM for now; changed to what the motors may get now.
  void apply(uint32_t now_ms, int* left, int* right) {
    uint32_t dt = started ? now_ms - last_ms : 0;
    if (dt > 30) dt = 30;                       // after a long gap, no jump to full speed
    started = true;
    last_ms = now_ms;
    *left = side(0, *left, now_ms, dt);
    *right = side(1, *right, now_ms, dt);
  }

  int side(int i, int target, uint32_t now_ms, uint32_t dt) {
    int dir = target > 0 ? 1 : (target < 0 ? -1 : 0);
    int moving = out[i] > 0 ? 1 : (out[i] < 0 ? -1 : 0);
    if (dir == 0 || (moving != 0 && moving != dir)) {          // stop, or a reversal: stop first, at once
      if (moving != 0) stopped_ms[i] = now_ms;
      out[i] = 0;
      return 0;
    }
    if (moving == 0 && last_dir[i] != 0 && last_dir[i] != dir && now_ms - stopped_ms[i] < reverse_pause_ms)
      return 0;                                                 // reversing: wait for the pause
    last_dir[i] = dir;
    int want = absInt(target), have = absInt(out[i]);
    if (want <= have) have = want;                              // slowing down: at once
    else {
      long grow = (long)ramp_per_ms * (long)dt;
      have = want - have <= grow ? want : have + (int)grow;
    }
    out[i] = dir * have;
    return out[i];
  }
};

struct MotorLogic {
  MotorSettings s;
  MotorState state;
  int want_left, want_right;      // the latest command
  uint32_t last_command_ms;
  bool have_command;
  int distance_cm;                // latest echo; -1 = none yet
  int missing_echoes;
  StopReason reason;              // why the motors are off now (RUNNING if they are not)
  StopReason fault;               // the fault that disarmed it, kept until the next ARM (RUNNING = none)

  explicit MotorLogic(MotorSettings settings)
      : s(settings), state(DISARMED), want_left(0), want_right(0), last_command_ms(0),
        have_command(false), distance_cm(-1), missing_echoes(0), reason(NOT_ARMED), fault(RUNNING) {}

  void arm() { state = ARMED; fault = RUNNING; have_command = false; want_left = want_right = 0; }
  void disarm() { state = DISARMED; have_command = false; want_left = want_right = 0; }
  void trip(StopReason why) { disarm(); fault = why; reason = why; }

  // The lease ran out: armed, a command was given, and none came for watchdog_ms or more.
  bool leaseExpired(uint32_t now_ms) const {
    return state == ARMED && have_command && now_ms - last_command_ms >= s.watchdog_ms;
  }
  void expire(uint32_t now_ms) { if (leaseExpired(now_ms)) trip(WATCHDOG); }
  // True if the loop may block for block_ms (a sonar ping) without overrunning the lease.
  bool leaseCovers(uint32_t now_ms, uint32_t block_ms) const {
    return state != ARMED || !have_command || now_ms - last_command_ms + block_ms < s.watchdog_ms;
  }

  void command(int left, int right, uint32_t now_ms) {
    expire(now_ms);   // a late command can't revive a lease that already ran out (review MS-4)
    want_left = clampInt(left, -255, 255);
    want_right = clampInt(right, -255, 255);
    last_command_ms = now_ms;
    have_command = true;
  }

  // One ultrasonic ping: cm > 0, or 0 for "no echo".
  void echo(int cm) {
    if (cm <= 0) {
      // Count up to the limit only: an int is 16 bits on the Uno and would wrap after ~27 minutes
      // of missing echoes, which would allow forward again (security review, Oct 16).
      if (missing_echoes < s.missing_echoes_block) missing_echoes++;
      if (missing_echoes >= s.missing_echoes_block) distance_cm = -1;   // the old distance is no use now
    } else {
      missing_echoes = 0;
      distance_cm = cm;
    }
  }

  // The PWM each side gets now (+ = forward); `reason` says why it is off, or RUNNING.
  void output(uint32_t now_ms, int* pwm_left, int* pwm_right) {
    *pwm_left = *pwm_right = 0;
    if (state != ARMED) { reason = fault != RUNNING ? fault : NOT_ARMED; return; }
    if (!have_command) { reason = WAITING; return; }
    if (leaseExpired(now_ms)) { trip(WATCHDOG); return; }
    int left = clampInt(want_left, -s.reverse_cap, s.speed_cap);
    int right = clampInt(want_right, -s.reverse_cap, s.speed_cap);
    bool blind = missing_echoes >= s.missing_echoes_block || distance_cm < 0;
    if ((blind || distance_cm < s.stop_cm) && left + right > 0) {
      // Forward is not allowed here, judged on what the motors would really get (after the caps).
      // One side forward and one backwards becomes a pure spin on the spot (the smaller of the two),
      // so the car can still turn away; anything else that would move it forward is a fault.
      if ((left > 0) != (right > 0) && left != 0 && right != 0) {
        int a = absInt(left) < absInt(right) ? absInt(left) : absInt(right);
        left = left > 0 ? a : -a;
        right = right > 0 ? a : -a;
      } else {
        trip(blind ? NO_ECHO : OBSTACLE);
        return;
      }
    }
    *pwm_left = liftToPwm(left, s.min_pwm, s.max_pwm);
    *pwm_right = liftToPwm(right, s.min_pwm, s.max_pwm);
    reason = RUNNING;
  }
};

// --- the laptop's lines (review MS-5) ----------------------------------------------------------------
enum CommandKind { CMD_NONE, CMD_ARM, CMD_DISARM, CMD_STOP, CMD_MOVE };
struct Command { CommandKind kind; int left, right; };

// An optional '-' and 1 to 4 digits, nothing else (the logic caps the value to -255..255).
inline bool parseNumber(const char*& p, int* out) {
  bool negative = *p == '-';
  if (negative) p++;
  int digits = 0, value = 0;
  while (*p >= '0' && *p <= '9') {
    if (++digits > 4) return false;
    value = value * 10 + (*p - '0');
    p++;
  }
  if (digits == 0) return false;
  *out = negative ? -value : value;
  return true;
}

// "ARM", "DISARM", "STOP" or "M,<left>,<right>", exactly; anything else is CMD_NONE.
inline Command parseCommand(const char* line) {
  Command c = {CMD_NONE, 0, 0};
  if (strcmp(line, "ARM") == 0) c.kind = CMD_ARM;
  else if (strcmp(line, "DISARM") == 0) c.kind = CMD_DISARM;
  else if (strcmp(line, "STOP") == 0) c.kind = CMD_STOP;
  else if (line[0] == 'M' && line[1] == ',') {
    const char* p = line + 2;
    int left, right;
    if (!parseNumber(p, &left) || *p++ != ',') return c;
    if (!parseNumber(p, &right) || *p != 0) return c;
    c.kind = CMD_MOVE;
    c.left = left;
    c.right = right;
  }
  return c;
}

// Collects one line at a time. A line longer than SIZE - 1, or with a byte that isn't printable ASCII
// (a NUL, noise on the wire), is thrown away whole, up to its CR or LF: never its tail as a command.
struct LineReader {
  static const int SIZE = 32;
  char buf[SIZE];
  int len;
  bool bad;
  LineReader() : len(0), bad(false) { buf[0] = 0; }
  // True when a complete, good line is in buf (until the next feed).
  bool feed(int ch) {
    if (ch == '\n' || ch == '\r') {
      bool good = !bad && len > 0;
      buf[len] = 0;
      len = 0;
      bad = false;
      return good;
    }
    if (bad) return false;
    if (len >= SIZE - 1 || ch < 32 || ch > 126) { bad = true; return false; }
    buf[len++] = (char)ch;
    return false;
  }
};

inline const char* reasonName(StopReason r) {
  switch (r) {
    case RUNNING: return "RUNNING";
    case NOT_ARMED: return "NOT_ARMED";
    case WAITING: return "WAITING";
    case WATCHDOG: return "WATCHDOG";
    case OBSTACLE: return "OBSTACLE";
    case NO_ECHO: return "NO_ECHO";
  }
  return "?";
}
