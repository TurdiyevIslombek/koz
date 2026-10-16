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
//   5. The motors don't turn below about min_pwm, so commands are lifted into min_pwm..255 (as car.ino).
#pragma once
#include <stdint.h>   // uint32_t: millis() is 32 bits on the Uno; the same on the Mac in tests

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
};

inline int clampInt(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }
inline int absInt(int v) { return v < 0 ? -v : v; }

// car.ino's lift(): tiny commands are a stop; others keep their order inside min_pwm..255.
inline int liftToPwm(int command, int min_pwm) {
  int a = absInt(command);
  if (a < 12) return 0;
  int out = min_pwm + (int)((long)a * (255 - min_pwm) / 255);
  return command > 0 ? out : -out;
}

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

  void command(int left, int right, uint32_t now_ms) {
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
    if (now_ms - last_command_ms > s.watchdog_ms) { trip(WATCHDOG); return; }
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
    *pwm_left = liftToPwm(left, s.min_pwm);
    *pwm_right = liftToPwm(right, s.min_pwm);
    reason = RUNNING;
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
