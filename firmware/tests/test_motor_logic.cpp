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
    CHECK(l == 0 && r == 0 && m.reason == NOT_ARMED);
  }
  {  // 2. armed + a fresh command: lifted like car.ino's lift(), within the cap
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    out(m, 0, l, r);
    CHECK(l == 0 && r == 0 && m.reason == WATCHDOG);       // armed, but no command yet
    m.command(100, 50, 1000);
    out(m, 1010, l, r);
    CHECK(m.reason == RUNNING);
    CHECK(l == liftToPwm(100, 80) && r == liftToPwm(50, 80));
    CHECK(l == 80 + 100 * 175 / 255);
  }
  {  // 3. watchdog: no fresh command for more than 250 ms -> off; the next command restarts
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    m.command(100, 100, 1000);
    out(m, 1250, l, r);
    CHECK(l > 0 && r > 0);
    out(m, 1251, l, r);
    CHECK(l == 0 && r == 0 && m.reason == WATCHDOG);
    m.command(100, 100, 1300);
    out(m, 1301, l, r);
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
  {  // 5. obstacle closer than stop_cm: no forward, but reversing and turning on the spot work
    MotorLogic m(settings());
    m.arm();
    m.echo(20);
    m.command(100, 100, 0);
    out(m, 1, l, r);
    CHECK(l == 0 && r == 0 && m.reason == OBSTACLE);
    m.command(-80, -80, 2);
    out(m, 3, l, r);
    CHECK(l < 0 && r < 0 && m.reason == RUNNING);
    m.command(100, -100, 4);
    out(m, 5, l, r);
    CHECK(l > 0 && r < 0 && m.reason == RUNNING);
    m.command(100, 60, 6);                                   // a forward curve: still refused
    out(m, 7, l, r);
    CHECK(l == 0 && r == 0 && m.reason == OBSTACLE);
    m.echo(36);                                              // the way is clear again
    out(m, 8, l, r);
    CHECK(l > 0 && m.reason == RUNNING);
  }
  {  // 6. the sensor can't see (3 pings without an echo, or none yet): no forward
    MotorLogic m(settings());
    m.arm();
    m.command(100, 100, 0);
    out(m, 1, l, r);
    CHECK(l == 0 && m.reason == NO_ECHO);                    // no echo yet
    m.echo(200);
    out(m, 2, l, r);
    CHECK(l > 0);
    m.echo(0); m.echo(0);
    out(m, 3, l, r);
    CHECK(l > 0);                                            // 2 missing: still the last distance
    m.echo(0);
    out(m, 4, l, r);
    CHECK(l == 0 && m.reason == NO_ECHO);
    m.command(-80, -80, 5);
    out(m, 6, l, r);
    CHECK(l < 0 && r < 0);                                   // backing away is allowed
  }
  {  // 7. DISARM stops at once and needs a new ARM; tiny commands are a stop; clamps
    MotorLogic m(settings());
    m.echo(200);
    m.arm();
    m.command(100, 100, 0);
    m.disarm();
    out(m, 1, l, r);
    CHECK(l == 0 && r == 0 && m.reason == NOT_ARMED);
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
  std::printf("all %d checks passed\n", checks);
  return 0;
}
