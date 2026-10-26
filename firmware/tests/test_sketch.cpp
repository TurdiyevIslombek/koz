// Runs the REAL motor_listener.ino on the Mac against a tiny fake Arduino: a clock that only moves
// when the test says so, the sonar (a ping blocks the loop for as long as the echo takes), the motor
// pins and the USB serial port. Adapted from Codex's review probe (web/review/motors/firmware_probe.cpp,
// motor safety review, Oct 16). It checks the sketch's own loop, not only motor_logic.h:
//   MS-4  the motors stop within 250 ms of the last command, even when a ping blocks the loop, a late
//         command waits in the serial buffer, or millis() wraps;
//   MS-5  an overlong or malformed line is never a command (it can't re-arm a faulted board).
// Build and run (tests/test_firmware.py does this):
//   clang++ -std=c++17 -Wall -Wextra -Werror -I firmware/tests/stubs firmware/tests/test_sketch.cpp && ./a.out
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

using byte = unsigned char;
constexpr int A0 = 14, A1 = 15, HIGH = 1, LOW = 0, OUTPUT = 1, INPUT = 0;

static uint32_t now_ms = 0;
static unsigned long echo_us = 11600;   // what the sonar hears (11600 us = 2 m); 0 = nothing
static int pings = 0;
static int pwm[20];
static uint32_t ena_off_at = UINT32_MAX;  // when the left motor's PWM last went from on to off
static std::vector<std::pair<uint32_t, int>> writes;   // (time, PWM) of every write to ENA

unsigned long millis() { return now_ms; }
void digitalWrite(int, int) {}
void pinMode(int, int) {}
void delayMicroseconds(unsigned long) {}
void analogWrite(int pin, int value) {
  if (pin == 5 && pwm[5] > 0 && value == 0) ena_off_at = now_ms;
  if (pin == 5) writes.push_back({now_ms, value});
  pwm[pin] = value;
}
unsigned long pulseIn(int, int, unsigned long timeout) {   // blocks while it listens
  pings++;
  unsigned long us = (echo_us == 0 || echo_us > timeout) ? timeout : echo_us;
  now_ms += (uint32_t)((us + 999) / 1000);
  return echo_us > timeout ? 0 : echo_us;
}
struct FakeSerial {
  std::string input;
  size_t pos = 0;
  int available() { return pos < input.size(); }
  int read() { return pos < input.size() ? (unsigned char)input[pos++] : -1; }
  void begin(long) {}
  template <class T> void print(T) {}
  template <class T> void println(T) {}
  void feed(const std::string& data) { input = data; pos = 0; }
} Serial;

#include "../motor_listener/motor_listener.ino"
static_assert(ENA == 5, "the fake analogWrite watches pin 5 (ENA)");

static int checks = 0;
#define CHECK(cond) do { checks++; if (!(cond)) { std::printf("FAILED line %d: %s\n", __LINE__, #cond); std::exit(1); } } while (0)

static void send(const std::string& text) {   // the laptop writes; the loop reads it (64 bytes or more per call)
  Serial.feed(text);
  for (int i = 0; i < 100 && Serial.available(); i++) { loop(); now_ms++; }
  loop();                            // and keeps running a millisecond more (the soft start's first step)
  now_ms++;
}

static void reset(uint32_t start_ms = 0) {
  now_ms = start_ms;
  lastPing = lastReport = start_ms;
  echo_us = 11600;
  pings = 0;
  std::memset(pwm, 0, sizeof pwm);
  ena_off_at = UINT32_MAX;
  logic = MotorLogic(settings);
  soft = SoftStart(RAMP_PER_MS, REVERSE_PAUSE_MS);
  writes.clear();
  send("\n");                        // ends any half line left by the previous scenario
  logic.echo(200);
}

static void runFor(uint32_t ms) {   // the loop runs about once a millisecond, plus any ping
  uint32_t end = now_ms + ms;
  while ((int32_t)(end - now_ms) > 0) { loop(); now_ms++; }
}

static uint32_t armAndMove() {      // returns when the move command was handled
  send("ARM\n");
  Serial.feed("M,60,60\n");
  uint32_t at = now_ms;
  loop();
  now_ms++;
  loop();                            // the soft start (Oct 18) ramps from the next millisecond
  now_ms++;
  CHECK(logic.state == ARMED && pwm[ENA] > 0);
  return at;
}

static void watchdogChecks() {
  // --- MS-4: the 250 ms watchdog holds for the sketch itself ---------------------------------------
  {  // Codex's case: last command at 1 ms, and a ping that would block from 250 ms
    reset();
    send("ARM\n");
    now_ms = 1;
    Serial.feed("M,60,60\n");
    loop();
    now_ms = 2;                      // the soft start (Oct 18) ramps from the next millisecond
    loop();
    CHECK(pwm[ENA] > 0);
    echo_us = 24000;                 // a far wall: a valid echo that takes 24 ms
    now_ms = 250;
    lastPing = 200;                  // a ping is due
    loop();
    now_ms++;
    loop();
    CHECK(pwm[ENA] == 0 && logic.fault == WATCHDOG);
    CHECK(ena_off_at - 1 <= 250);
  }
  {  // commands stop while the sonar keeps blocking for 24 ms every ping: off within 250 ms
    reset();
    echo_us = 24000;
    uint32_t at = armAndMove();
    runFor(400);
    CHECK(pwm[ENA] == 0 && logic.fault == WATCHDOG && logic.state == DISARMED);
    CHECK(ena_off_at - at <= 250);
  }
  {  // a command that arrives after the lease ran out can't revive it
    reset();
    send("ARM\n");
    now_ms = 0;
    Serial.feed("M,60,60\n");
    loop();
    now_ms = 251;
    Serial.feed("M,60,60\n");        // late: it was already waiting in the serial buffer
    loop();
    CHECK(logic.fault == WATCHDOG && logic.state == DISARMED && pwm[ENA] == 0);
    now_ms = 260;
    Serial.feed("STOP\n");
    loop();
    CHECK(logic.fault == WATCHDOG && logic.state == DISARMED);   // still latched: only ARM clears it
  }
  {  // a late STOP the same way
    reset();
    send("ARM\n");
    now_ms = 0;
    Serial.feed("M,60,60\n");
    loop();
    now_ms = 250;
    Serial.feed("STOP\n");
    loop();
    CHECK(logic.fault == WATCHDOG && logic.state == DISARMED);
  }
  {  // millis() wraps (after ~49 days): still off within 250 ms
    reset(0xFFFFFF80u);
    echo_us = 24000;
    uint32_t at = armAndMove();
    runFor(400);
    CHECK(pwm[ENA] == 0 && logic.fault == WATCHDOG);
    CHECK(ena_off_at - at <= 250);
  }
  {  // normal driving (a command every 100 ms) never trips, and the sonar keeps pinging
    reset();
    echo_us = 24000;
    armAndMove();
    for (int i = 0; i < 30; i++) {
      runFor(99);
      Serial.feed("M,60,60\n");
    }
    runFor(1);
    CHECK(logic.state == ARMED && logic.reason == RUNNING && pwm[ENA] > 0 && pings >= 40);
  }
  {  // late but in time (every 240 ms): still running, and the sonar still pings
    reset();
    echo_us = 24000;
    armAndMove();
    for (int i = 0; i < 12; i++) {
      runFor(239);
      Serial.feed("M,60,60\n");
    }
    runFor(1);
    CHECK(logic.state == ARMED && logic.reason == RUNNING && pwm[ENA] > 0 && pings >= 30);
  }
  {  // a flood of serial bytes is read a bounded amount per loop, so the watchdog check keeps running
    reset();
    Serial.feed(std::string(1000, 'x'));
    loop();
    CHECK(Serial.pos <= 64);
  }
}

static void parserChecks() {
  // --- MS-5: only exact, short, well-formed lines are commands -------------------------------------
  {  // an overlong line ending in ARM is thrown away whole: the fault stays latched
    reset();
    logic.trip(WATCHDOG);
    send(std::string(32, 'x') + "ARM\nM,60,60\n");
    CHECK(logic.state == DISARMED && logic.fault == WATCHDOG && pwm[ENA] == 0);
    send(std::string(100, 'y') + "ARM\n");
    CHECK(logic.state == DISARMED && logic.fault == WATCHDOG);
    send("ARM\nM,60,60\n");          // a separate, valid ARM (a person, on the laptop)
    CHECK(logic.state == ARMED && pwm[ENA] > 0);
  }
  {  // malformed lines on an armed board: none of them moves it
    const char* bad[] = {"M,60junk,60junk", "M,60", "M,60,60,60", "M,,60", "M,60,", "M,-,5", "M,+5,5",
                         "M,99999,5", "M, 60,60", "M,60 ,60", "M60,60", "m,60,60", "ARMX", "arm", "ARM ",
                         " ARM", "STOPX", "DISARMED", "M,6O,60"};
    for (const char* line : bad) {
      reset();
      send("ARM\n");
      send(std::string(line) + "\n");
      CHECK(logic.reason == WAITING && pwm[ENA] == 0);
    }
    reset();
    send("ARM\n");
    send(std::string("M,60,60\0junk\n", 13));   // an embedded NUL
    CHECK(logic.reason == WAITING && pwm[ENA] == 0);
  }
  {  // a malformed line after a fault doesn't arm; a malformed DISARM can't be confused with ARM
    reset();
    logic.trip(OBSTACLE);
    send("ARMED\n");
    CHECK(logic.state == DISARMED && logic.fault == OBSTACLE);
  }
  {  // good lines, with CR LF, extra blank lines and negative numbers, still work
    reset();
    send("\r\nARM\r\n\r\nM,-60,250\r\n");
    CHECK(logic.state == ARMED && logic.want_left == -60 && logic.want_right == 250 && pwm[ENA] > 0);
    send("M,0300,-0300\n");                       // up to 4 digits; the logic caps to -255..255
    CHECK(logic.want_left == 255 && logic.want_right == -255);
    send("STOP\n");
    CHECK(logic.state == ARMED && pwm[ENA] == 0);
    send("DISARM\n");
    CHECK(logic.state == DISARMED);
  }
}

static void softStartChecks() {
  // --- PWM voltage estimate follows the configured supply; soft start; stop before reversing --------
  {  // full command: never above the 6 V PWM, and it ramps up instead of jumping
    reset();
    send("ARM\n");
    for (int i = 0; i < 40; i++) { Serial.feed("M,255,255\n"); loop(); now_ms += 5; }
    int highest = 0;
    for (auto& w : writes) highest = w.second > highest ? w.second : highest;
    CHECK(highest <= MAX_PWM && MAX_PWM * MOTOR_SUPPLY_V / 255.0 <= MOTOR_MAX_V);
    CHECK(writes.front().second < 30);                       // the first step is small
  }
  {  // a reversal goes to 0 at once, stays 0 for the pause, then ramps the other way
    reset();
    send("ARM\n");
    for (int i = 0; i < 40; i++) { Serial.feed("M,100,100\n"); loop(); now_ms += 5; }
    CHECK(pwm[ENA] > 0 && logic.want_left == 100);
    size_t mark = writes.size();
    uint32_t at = now_ms;
    for (int i = 0; i < 40; i++) { Serial.feed("M,-100,-100\n"); loop(); now_ms += 5; }
    size_t stop = mark;                                      // the loop that reads the command stops at once
    while (stop < writes.size() && writes[stop].second != 0) stop++;
    CHECK(stop < writes.size() && writes[stop].first == at);
    uint32_t moved = UINT32_MAX;
    for (size_t i = stop; i < writes.size(); i++) if (writes[i].second > 0) { moved = writes[i].first; break; }
    CHECK(moved != UINT32_MAX && moved - at >= REVERSE_PAUSE_MS);   // then waits before going backwards
  }
  {  // stopping is never delayed by the soft start: STOP and a fault cut the motors at once
    reset();
    send("ARM\n");
    for (int i = 0; i < 40; i++) { Serial.feed("M,100,100\n"); loop(); now_ms += 5; }
    Serial.feed("STOP\n");
    loop();
    CHECK(pwm[ENA] == 0);
  }
  {  // security review (Oct 19): the real sketch, a wall appears while driving: no forward motion after
    reset();
    send("ARM\n");
    for (int i = 0; i < 40; i++) { Serial.feed("M,100,100\n"); loop(); now_ms += 5; }
    echo_us = 20 * 58;               // 20 cm: closer than stop_cm
    bool forward = false, seen = false;
    for (int i = 0; i < 60; i++) {
      Serial.feed("M,100,-100\n");   // the brain asks to spin away
      loop();
      if (logic.forwardBlocked()) seen = true;   // from the next ping on, the sketch knows the wall
      if (seen && soft.out[0] + soft.out[1] > 0) forward = true;
      now_ms += 5;
    }
    CHECK(seen && !forward && soft.out[0] > 0 && soft.out[0] == -soft.out[1]);
  }
}

int main(int argc, char** argv) {   // no argument: everything; "ms4" or "ms5": that part only
  bool all = argc < 2;
  if (all || std::strcmp(argv[1], "ms4") == 0) watchdogChecks();
  if (all || std::strcmp(argv[1], "ms5") == 0) parserChecks();
  if (all || std::strcmp(argv[1], "soft") == 0) softStartChecks();
  std::printf("all %d sketch checks passed\n", checks);
  return 0;
}
