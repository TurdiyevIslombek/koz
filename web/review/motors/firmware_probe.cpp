// Compile the actual sketch against a tiny deterministic Arduino shim. No board is accessed.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
using byte = unsigned char;
constexpr int A0=14, A1=15, HIGH=1, LOW=0, OUTPUT=1, INPUT=0;
uint32_t now_ms=0;
int pwm[20] = {};
unsigned long millis() { return now_ms; }
void digitalWrite(int, int) {}
void pinMode(int, int) {}
void analogWrite(int pin, int value) { pwm[pin]=value; }
void delayMicroseconds(unsigned long) {}
unsigned long pulseIn(int, int, unsigned long timeout) { now_ms += timeout / 1000; return 0; }
struct FakeSerial {
  std::string input;
  size_t pos=0;
  int available() { return pos < input.size(); }
  char read() { return input[pos++]; }
  void begin(int) {}
  template<class T> void print(T) {}
  template<class T> void println(T) {}
  void feed(std::string data) { input=std::move(data); pos=0; }
} Serial;
#include "../../../firmware/motor_listener/motor_listener.ino"

void reset() {
  logic = MotorLogic(settings); lineLen=0; now_ms=0; lastPing=lastReport=0;
  Serial.feed(""); logic.echo(200); applyMotors();
}
int main() {
  reset(); logic.arm(); logic.command(60,60,1); now_ms=1; applyMotors();
  assert(pwm[ENA]>0);
  now_ms=250; lastPing=200; loop();
  assert(now_ms==275 && pwm[ENA]==0 && logic.fault==WATCHDOG);
  std::printf("sonar blocks watchdog: last command=1ms, PWM removed=275ms, age=274ms\n");

  reset(); logic.arm(); logic.command(60,60,0); applyMotors();
  now_ms=251; lastPing=251; Serial.feed("M,60,60\n"); loop();
  assert(logic.state==ARMED && logic.fault==RUNNING && pwm[ENA]>0);
  std::printf("251ms command gap: new M replaces expired timer before watchdog; still armed, PWM=%d\n",pwm[ENA]);

  reset(); logic.trip(WATCHDOG); Serial.feed(std::string(32,'x')+"ARM\nM,60,60\n"); loop();
  assert(logic.state==ARMED && logic.fault==RUNNING && pwm[ENA]>0);
  std::printf("overlong junk + ARM suffix clears watchdog fault and moves: PWM=%d\n",pwm[ENA]);

  reset(); logic.arm(); Serial.feed("M,60junk,60junk\n"); loop();
  assert(pwm[ENA]>0 && pwm[ENB]>0);
  std::printf("malformed numeric command accepted: PWM=%d,%d\n",pwm[ENA],pwm[ENB]);
}
