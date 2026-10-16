// stop_test: measures, on Islombek's car, the two numbers motor_listener needs (CLAUDE.md rule 11):
//   - how slow the car can go and still move (MOVE),
//   - how far it slides after the motors are cut, at each speed (RUN).
// Steps: firmware/stop_test/README.md. Same wiring as the car (PINS.txt). Type commands in the
// serial monitor (115200 baud). ANY key you type during a run stops the motors at once.
//
//   PING          distance ahead (median of 5 pings)
//   MOVE <speed>  drive forward for 1 s at <speed> (-255..255, like car.ino), then say how far it moved
//   RUN <speed>   drive at a wall at <speed>; cut the motors when the sonar reads CUT cm; wait 2 s;
//                 print RESULT,speed,cut_cm,final_cm,stopping_cm,speed_cm_s
//   CUT <cm>      where RUN cuts the motors (default 60)
#include <Servo.h>

const int TRIG = A0, ECHO = A1;
const int SERVO_PIN = 3, CENTER_DEG = 90;
const int ENA = 5, IN1 = 7, IN2 = 8;     // left motors
const int ENB = 6, IN3 = 9, IN4 = 10;    // right motors
const int MIN_PWM = 80;                  // as car.ino: commands are lifted into MIN_PWM..255
const unsigned long PING_EVERY_MS = 50;  // the same ping rhythm as motor_listener, so the
                                         // measured slide includes the same reaction delay
const unsigned long MAX_RUN_MS = 5000;   // a run never lasts longer than this
int cutCm = 60;

Servo servo;
char line[24];
byte lineLen = 0;

int readCm() {                            // 0 = no echo
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

int medianCm() {                          // 5 pings, the middle one (one bad echo can't spoil it)
  int v[5];
  for (int i = 0; i < 5; i++) { v[i] = readCm(); delay(30); }
  for (int i = 0; i < 5; i++)
    for (int j = i + 1; j < 5; j++)
      if (v[j] < v[i]) { int t = v[i]; v[i] = v[j]; v[j] = t; }
  return v[2];
}

int lift(int speed) {
  int a = abs(speed);
  if (a < 12) return 0;
  int out = MIN_PWM + (long)a * (255 - MIN_PWM) / 255;
  return speed > 0 ? out : -out;
}

void setSide(int en, int a, int b, int speed) {
  int pwm = lift(constrain(speed, -255, 255));
  digitalWrite(a, pwm > 0 ? HIGH : LOW);
  digitalWrite(b, pwm < 0 ? HIGH : LOW);
  analogWrite(en, abs(pwm));
}

void drive(int left, int right) {
  setSide(ENA, IN1, IN2, left);
  setSide(ENB, IN3, IN4, right);
}

bool keyPressed() {                       // any byte from the monitor = stop
  if (Serial.available()) {
    while (Serial.available()) Serial.read();
    return true;
  }
  return false;
}

void moveTest(int speed) {
  int before = medianCm();
  Serial.print("MOVE "); Serial.print(speed); Serial.print(": start "); Serial.print(before); Serial.println(" cm");
  drive(speed, speed);
  unsigned long start = millis();
  bool stopped = false;
  while (millis() - start < 1000) {
    if (keyPressed()) { stopped = true; break; }
    int cm = readCm();
    if (speed > 0 && cm > 0 && cm < 25) { stopped = true; break; }   // never into the wall
    delay(PING_EVERY_MS);
  }
  drive(0, 0);
  delay(800);
  int after = medianCm();
  Serial.print("MOVED,"); Serial.print(speed); Serial.print(','); Serial.print(before - after);
  Serial.println(stopped ? ",stopped early" : "");
}

void runTest(int speed) {
  if (speed <= 0) { Serial.println("RUN needs a forward speed, e.g. RUN 120"); return; }
  int start = medianCm();
  if (start == 0 || start < cutCm + 40) {
    Serial.print("Too close to start (or no echo): "); Serial.print(start);
    Serial.print(" cm. Put the car at least "); Serial.print(cutCm + 40); Serial.println(" cm from the wall.");
    return;
  }
  Serial.print("RUN "); Serial.print(speed); Serial.print(": start "); Serial.print(start); Serial.println(" cm");
  int prevCm = start, missing = 0, cut = -1;
  unsigned long prevT = millis(), began = millis();
  float speedCmS = 0;
  drive(speed, speed);
  while (millis() - began < MAX_RUN_MS) {
    if (keyPressed()) { drive(0, 0); Serial.println("stopped by key"); return; }
    delay(PING_EVERY_MS);
    int cm = readCm();
    unsigned long now = millis();
    if (cm == 0) {
      if (++missing >= 5) { drive(0, 0); Serial.println("no echo 5 times: stopped"); return; }
      continue;
    }
    missing = 0;
    if (prevCm > cm) speedCmS = 0.7 * speedCmS + 0.3 * ((prevCm - cm) * 1000.0 / (now - prevT));
    prevCm = cm;
    prevT = now;
    if (cm <= cutCm) { cut = cm; break; }
  }
  drive(0, 0);                            // the cut: what motor_listener does when it stops
  if (cut < 0) { Serial.println("did not reach the cut distance in 5 s (too slow, or no wall ahead)"); return; }
  delay(2000);
  int final = medianCm();
  Serial.print("RESULT,"); Serial.print(speed); Serial.print(','); Serial.print(cut); Serial.print(',');
  Serial.print(final); Serial.print(','); Serial.print(cut - final); Serial.print(',');
  Serial.println((int)speedCmS);
}

void handleLine() {
  if (strcmp(line, "PING") == 0) { Serial.print("PING,"); Serial.println(medianCm()); }
  else if (strncmp(line, "MOVE ", 5) == 0) moveTest(atoi(line + 5));
  else if (strncmp(line, "RUN ", 4) == 0) runTest(atoi(line + 4));
  else if (strncmp(line, "CUT ", 4) == 0) {
    cutCm = constrain(atoi(line + 4), 20, 150);
    Serial.print("CUT,"); Serial.println(cutCm);
  } else Serial.println("Commands: PING, MOVE <speed>, RUN <speed>, CUT <cm>");
}

void setup() {
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT); pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  drive(0, 0);
  servo.attach(SERVO_PIN);
  servo.write(CENTER_DEG);
  Serial.begin(115200);
  Serial.println("READY stop_test. Commands: PING, MOVE <speed>, RUN <speed>, CUT <cm>");
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (lineLen > 0) { line[lineLen] = 0; handleLine(); }
      lineLen = 0;
    } else if (lineLen < sizeof(line) - 1) {
      line[lineLen++] = ch;
    } else {
      lineLen = 0;
    }
  }
}
