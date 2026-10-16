// motor_listener: the only sketch Ko'z drives the car with (CLAUDE.md rule 11). Arduino Uno + L298N +
// HC-SR04 on the servo (pointed straight ahead), wired as in Islombek's car (PINS.txt).
// It does nothing by itself: it receives wheel speeds over the USB cable and applies the safety
// rules in motor_logic.h. Islombek's physical power switch is the last safety layer.
//
// Laptop -> Arduino (115200 baud, one line each)      Arduino -> laptop
//   ARM        enable the motors                         READY                 after power-up (disarmed)
//   DISARM     motors off until the next ARM             S,state,reason,cm     every 100 ms: 0/1, why it is
//   M,L,R      wheel commands -255..255                                        stopped (RUNNING if not), distance
//   STOP       motors off now (stays armed)              (cm -1 = no echo yet)
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

MotorSettings settings = {
  /* speed_cap   */ 120,     // MEASURE: the fastest command whose stopping distance you accept
  /* reverse_cap */ 90,      // backwards is blind: slower
  /* min_pwm     */ 80,      // car.ino MIN_PWM: below this the motors only buzz
  /* stop_cm     */ 35,      // MEASURE: stopping distance at speed_cap + reaction distance + 10 cm
  /* watchdog_ms */ 250,     // rule 11: no fresh command for 250 ms -> motors off
  /* missing_echoes_block */ 3,
};
MotorLogic logic(settings);
Servo servo;

const unsigned long PING_EVERY_MS = 50;
const unsigned long REPORT_EVERY_MS = 100;
unsigned long lastPing = 0, lastReport = 0;
char line[32];
byte lineLen = 0;

int readCm() {                            // 0 = no echo (nothing within ~4 m, or the sensor failed)
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  unsigned long us = pulseIn(ECHO, HIGH, 25000UL);
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
  logic.output(millis(), &left, &right);
  setSide(ENA, IN1, IN2, left);
  setSide(ENB, IN3, IN4, right);
}

void handleLine() {
  if (strcmp(line, "ARM") == 0) logic.arm();
  else if (strcmp(line, "DISARM") == 0) logic.disarm();
  else if (strcmp(line, "STOP") == 0) logic.command(0, 0, millis());
  else if (line[0] == 'M' && line[1] == ',') {
    char* comma = strchr(line + 2, ',');
    if (!comma) return;
    *comma = 0;
    logic.command(atoi(line + 2), atoi(comma + 1), millis());
  }
}

void readSerial() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (lineLen > 0) {
        line[lineLen] = 0;
        handleLine();
      }
      lineLen = 0;
    } else if (lineLen < sizeof(line) - 1) {
      line[lineLen++] = ch;
    } else {
      lineLen = 0;                       // too long: not a command; drop it
    }
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

void loop() {
  readSerial();
  if (millis() - lastPing >= PING_EVERY_MS) {
    lastPing = millis();
    logic.echo(readCm());
  }
  applyMotors();
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
