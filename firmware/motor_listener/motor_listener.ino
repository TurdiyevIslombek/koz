// motor_listener: the only sketch Ko'z drives the car with (CLAUDE.md rule 11). Arduino Uno + L298N +
// HC-SR04 on the servo (pointed straight ahead), wired as in Islombek's car (PINS.txt).
// It does nothing by itself: it receives wheel speeds over the USB cable and applies the safety
// rules in motor_logic.h. Islombek's physical power switch is the last safety layer.
//
// Laptop -> Arduino (115200 baud, one line each)      Arduino -> laptop
//   ARM        enable the motors (the laptop sends it     READY                 after power-up (disarmed)
//              only when a person arms them by hand)    S,state,reason,cm     every 100 ms: 0/1, why it is
//   DISARM     motors off until the next ARM                                   off (RUNNING if not), distance
//   M,L,R      wheel commands -255..255                                        (cm -1 = no echo yet)
//   STOP       motors off now (stays armed)
// Faults (WATCHDOG, OBSTACLE, NO_ECHO: see motor_logic.h) disarm; only a new ARM enables the motors.
//
// Commands are exact lines (motor_logic.h: parseCommand); anything else is ignored.
//
// The numbers marked MEASURE come from firmware/stop_test (see its README). Until they are
// measured, these defaults are deliberately slow and careful.
#include <Servo.h>
#include "motor_logic.h"

const int TRIG = A0, ECHO = A1;          // HC-SR04
const int SERVO_PIN = 3;
const int CENTER_DEG = 90;               // straight ahead (car.ino CENTER_DEG)
const int ENA = 5, IN1 = 7, IN2 = 8;     // L298N, left motors
const int ENB = 6, IN3 = 9, IN4 = 10;    // L298N, right motors

// Islombek's battery and motors (his car.ino, Oct 18): a 9.5 V pack, and the L298N loses about 2 V,
// so the motors could get 7.5 V. Yellow TT motors are made for 3-6 V: commands are lifted into
// MIN_PWM..MAX_PWM, which gives them 1.8-6 V. Measure the pack with a multimeter and write it here.
const float BATTERY_V = 9.5;
const float MOTOR_MAX_V = 6.0, MOTOR_MIN_V = 1.8, DRIVER_DROP_V = 2.0;
const float MOTOR_SUPPLY_V = BATTERY_V - DRIVER_DROP_V;
const int MAX_PWM = 255.0 * MOTOR_MAX_V / MOTOR_SUPPLY_V > 255 ? 255 : (int)(255.0 * MOTOR_MAX_V / MOTOR_SUPPLY_V);   // 204
const int MIN_PWM = (int)(255.0 * MOTOR_MIN_V / MOTOR_SUPPLY_V);                                                     // 61
const int RAMP_PER_MS = 2;                 // soft start: 0 -> full speed in about 0.1 s (car.ino)
const uint32_t REVERSE_PAUSE_MS = 40;      // a change of direction waits this long at a stop

MotorSettings settings = {
  /* speed_cap   */ 120,     // MEASURE: the fastest command whose stopping distance you accept
  /* reverse_cap */ 90,      // backwards is blind: slower
  /* min_pwm     */ MIN_PWM, // below this the motors only buzz
  /* stop_cm     */ 35,      // MEASURE: stopping distance at speed_cap + reaction distance + 10 cm
  /* watchdog_ms */ 250,     // rule 11: no fresh command for 250 ms -> motors off
  /* missing_echoes_block */ 3,
  /* max_pwm     */ MAX_PWM, // 6 V: the motors' highest safe voltage
};
MotorLogic logic(settings);
SoftStart soft(RAMP_PER_MS, REVERSE_PAUSE_MS);
Servo servo;

const unsigned long PING_EVERY_MS = 50;
const unsigned long PING_TIMEOUT_US = 25000UL;   // no echo within 25 ms (~4 m): nothing there
const uint32_t PING_BLOCK_MS = 26;               // the longest a ping can hold up the loop
const unsigned long REPORT_EVERY_MS = 100;
const int SERIAL_BYTES_PER_LOOP = 64;            // a flood of bytes can't keep the loop from the watchdog
unsigned long lastPing = 0, lastReport = 0;
LineReader reader;

int readCm() {                            // 0 = no echo (nothing within ~4 m, or the sensor failed)
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  unsigned long us = pulseIn(ECHO, HIGH, PING_TIMEOUT_US);
  if (us == 0) return 0;
  unsigned long cm = us / 58;
  return cm > 400 ? 400 : (int)cm;
}

void setSide(int en, int a, int b, int pwm) {
  digitalWrite(a, pwm > 0 ? HIGH : LOW);
  digitalWrite(b, pwm < 0 ? HIGH : LOW);
  analogWrite(en, pwm < 0 ? -pwm : pwm);
}

void applyMotors() {
  int left, right;
  uint32_t now = millis();
  logic.output(now, &left, &right);    // the safety rules decide what may run
  soft.apply(now, &left, &right);      // then speeding up is gentle; stopping stays immediate
  setSide(ENA, IN1, IN2, left);
  setSide(ENB, IN3, IN4, right);
}

void handleLine(const char* line) {     // exact commands only (motor_logic.h: parseCommand)
  Command c = parseCommand(line);
  if (c.kind == CMD_ARM) logic.arm();
  else if (c.kind == CMD_DISARM) logic.disarm();
  else if (c.kind == CMD_STOP) logic.command(0, 0, millis());
  else if (c.kind == CMD_MOVE) logic.command(c.left, c.right, millis());
}

void readSerial() {
  for (int n = 0; n < SERIAL_BYTES_PER_LOOP && Serial.available(); n++) {
    if (reader.feed(Serial.read())) handleLine(reader.buf);
  }
}

void setup() {
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT); pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  setSide(ENA, IN1, IN2, 0);             // starts stopped, before anything else
  setSide(ENB, IN3, IN4, 0);
  servo.attach(SERVO_PIN);
  servo.write(CENTER_DEG);
  Serial.begin(115200);
  Serial.println("READY");
}

// The motor deadline is checked first, after every piece of work, and a ping (which blocks for up to
// 26 ms) only starts if the motors' lease covers it; otherwise it waits for the next command. So the
// motors stop at most 250 ms after the last command (review MS-4).
void loop() {
  logic.expire(millis());
  applyMotors();
  readSerial();
  applyMotors();
  uint32_t now = millis();
  if (now - lastPing >= PING_EVERY_MS && logic.leaseCovers(now, PING_BLOCK_MS)) {
    lastPing = now;
    logic.echo(readCm());
    applyMotors();                       // the new distance counts at once
  }
  if (millis() - lastReport >= REPORT_EVERY_MS) {
    lastReport = millis();
    Serial.print("S,");
    Serial.print((int)logic.state);
    Serial.print(',');
    Serial.print(reasonName(logic.reason));
    Serial.print(',');
    Serial.println(logic.distance_cm);
  }
}
