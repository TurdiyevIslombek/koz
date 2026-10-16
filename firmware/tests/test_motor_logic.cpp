// Tests motor_logic.h on the Mac (no Arduino needed): clang++ -std=c++17 test_motor_logic.cpp && ./a.out
// (Not in the sketch folder: arduino-cli would compile it into the sketch.)
// Run by tests/test_firmware.py. Prints "all N checks passed" or the first failing check.
#include <cstdio>
#include <cstdlib>
#include "../motor_listener/motor_logic.h"

static int checks = 0;
#define CHECK(cond) do { checks++; if (!(cond)) { std::printf("FAILED line %d: %s\n", __LINE__, #cond); std::exit(1); } } while (0)

static MotorSettings settings() { return MotorSettings{120, 90, 80, 35, 250, 3}; }

static void out(MotorLogic& m, uint32_t t, int& l, int& r) { m.output(t, &l, &r); }

int main() {
  int l, r;
  {  // 1. starts disarmed: a command alone does nothing
    MotorLogic m(settings());
    m.echo(200);
    m.command(100, 100, 0);
    out(m, 10, l, r);
    CHECK(l == 0 && r == 0 && m.reason == NOT_ARMED && m.state == DISARMED);
  }
  {  // 2. armed, waiting for a first command, then lifted like car.ino's lift(), within the cap
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    out(m, 5000, l, r);
    CHECK(l == 0 && r == 0 && m.reason == WAITING && m.state == ARMED);   // waiting is not a fault
    m.command(100, 50, 6000);
    out(m, 6010, l, r);
    CHECK(m.reason == RUNNING);
    CHECK(l == liftToPwm(100, 80) && r == liftToPwm(50, 80));
    CHECK(l == 80 + 100 * 175 / 255);
  }
  {  // 3. watchdog: commands stop for more than 250 ms -> fault, disarmed, stays off until ARM
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    m.command(100, 100, 1000);
    out(m, 1250, l, r);
    CHECK(l > 0 && r > 0);
    out(m, 1251, l, r);
    CHECK(l == 0 && r == 0 && m.reason == WATCHDOG && m.state == DISARMED && m.fault == WATCHDOG);
    m.command(100, 100, 1300);                               // a new command doesn't re-arm
    out(m, 1301, l, r);
    CHECK(l == 0 && m.reason == WATCHDOG && isFault(m.reason));
    m.arm();                                                 // by hand
    CHECK(m.fault == RUNNING);
    m.command(100, 100, 1400);
    out(m, 1401, l, r);
    CHECK(l > 0 && m.reason == RUNNING);
  }
  {  // 4. speed caps: forward 120, backwards 90 (in command units, before lifting)
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    m.command(255, -255, 0);
    out(m, 1, l, r);
    CHECK(l == liftToPwm(120, 80) && r == liftToPwm(-90, 80));
  }
  {  // 5. obstacle closer than stop_cm: reversing and spinning are fine; forward is a fault
    MotorLogic m(settings());
    m.arm();
    m.echo(20);
    m.command(-80, -80, 0);
    out(m, 1, l, r);
    CHECK(l < 0 && r < 0 && m.reason == RUNNING);
    m.command(100, -100, 2);                                 // capped (100, -90): stays a pure spin
    out(m, 3, l, r);
    CHECK(l > 0 && l == -r && m.reason == RUNNING);
    m.command(100, 60, 4);                                   // a forward curve: fault
    out(m, 5, l, r);
    CHECK(l == 0 && r == 0 && m.reason == OBSTACLE && m.state == DISARMED);
    m.echo(200);                                             // clear again: still off until ARM
    m.command(100, 100, 6);
    out(m, 7, l, r);
    CHECK(l == 0 && m.reason == OBSTACLE);
  }
  {  // 6. the sensor can't see: no echo yet, or 3 missing in a row -> forward is a fault
    MotorLogic m(settings());
    m.arm();
    m.command(-80, -80, 0);
    out(m, 1, l, r);
    CHECK(l < 0 && m.reason == RUNNING);                     // backing away is allowed
    m.command(100, 100, 2);
    out(m, 3, l, r);
    CHECK(l == 0 && m.reason == NO_ECHO && m.state == DISARMED);
    m.arm();
    m.echo(200);
    m.echo(0); m.echo(0);
    m.command(100, 100, 4);
    out(m, 5, l, r);
    CHECK(l > 0);                                            // 2 missing: still the last distance
    m.echo(0);
    out(m, 6, l, r);
    CHECK(l == 0 && m.reason == NO_ECHO);
  }
  {  // 7. DISARM by command is not a fault; tiny commands are a stop; clamps
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    m.command(100, 100, 0);
    m.disarm();
    out(m, 1, l, r);
    CHECK(l == 0 && r == 0 && m.reason == NOT_ARMED && m.fault == RUNNING);
    m.arm();
    m.command(5, -5, 2);
    out(m, 3, l, r);
    CHECK(l == 0 && r == 0 && m.reason == RUNNING);
    m.command(9999, -9999, 4);
    CHECK(m.want_left == 255 && m.want_right == -255);
  }
  {  // 8. millis() wraps after ~49 days: the watchdog still works across the wrap
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    m.command(100, 100, (uint32_t)4294967200UL);
    out(m, (uint32_t)4294967290UL, l, r);
    CHECK(l > 0);
    out(m, (uint32_t)200, l, r);                             // 296 ms later, after the wrap
    CHECK(l == 0 && m.reason == WATCHDOG);
  }
  {  // 9. security review: a reversing turn that the caps would make creep forward -> a pure spin
    MotorLogic m(settings());
    m.arm();
    m.echo(20);                                              // obstacle ahead
    m.command(200, -250, 0);                                 // caps: (120, -90): would drift forward
    out(m, 1, l, r);
    CHECK(l == -r && l > 0 && m.reason == RUNNING);
    CHECK(l == liftToPwm(90, 80));
    m.command(255, 0, 2);                                    // a forward pivot: fault
    out(m, 3, l, r);
    CHECK(l == 0 && r == 0 && m.reason == OBSTACLE);
    m.arm();
    m.echo(200);                                             // clear: the command as capped
    m.command(200, -250, 4);
    out(m, 5, l, r);
    CHECK(l == liftToPwm(120, 80) && r == liftToPwm(-90, 80));
  }
  {  // 10. security review: tens of thousands of missing echoes never let forward through again
    MotorLogic m(settings());
    m.arm();
    m.echo(200);
    for (long i = 0; i < 70000; i++) m.echo(0);              // > 32767: an int would have wrapped
    CHECK(m.missing_echoes == 3 && m.distance_cm == -1);
    m.command(100, 100, 0);
    out(m, 1, l, r);
    CHECK(l == 0 && r == 0 && m.reason == NO_ECHO);
  }
  std::printf("all %d checks passed\n", checks);
  return 0;
}
