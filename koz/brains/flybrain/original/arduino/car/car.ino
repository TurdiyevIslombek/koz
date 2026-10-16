// Fly-brain car: ONE sketch for all 3 stages. The laptop app picks the stage.
//
// Laptop -> Arduino                         Arduino -> laptop
//   MODE,0   stop                             READY            after power-up
//   MODE,1   stage 1: if-else, here           MODE,n           stage changed
//   MODE,2   stage 2: laptop drives, sonar    P,L|C|R,cm,ms    one sonar ping (direction, distance, time)
//   MODE,3   stage 3: laptop drives, camera   W,left,right     wheel speeds (stage 1)
//                                             STUCK            stage 1 stuck reflex fired
//                                             TRAP,why         stage 1 big escape (deadend / repeat)
//   M,L,R    wheel speeds -255..255 (stage 2 and 3)
//   LOOK,L / LOOK,C / LOOK,R   point the servo (only when stopped, for testing)

#include <Servo.h>

// ---------- pins ----------
const int TRIG = A0, ECHO = A1;          // HC-SR04
const int SERVO_PIN = 3;                 // servo signal (orange/yellow wire)
const int ENA = 5, IN1 = 7, IN2 = 8;     // L298N, left motors
const int ENB = 6, IN3 = 9, IN4 = 10;    // L298N, right motors

// ---------- servo ----------
const int LEFT_DEG = 135, CENTER_DEG = 90, RIGHT_DEG = 45;   // if "L" looks right: swap LEFT_DEG and RIGHT_DEG
const unsigned long SETTLE_MS = 110;     // wait for the servo to arrive before each ping (was 150)

// ---------- safety / start ----------
const unsigned long WATCHDOG_MS = 300;   // stage 2/3: no M note for 300 ms -> motors stop
const byte START_MODE = 0;               // 1 = start stage 1 by itself at power-up (no laptop)

// ---------- stage 1 rules ----------
const int STOP_CM = 25;                  // something ahead closer than this: back up and turn
const int SIDE_CM = 20;                  // something at a side closer than this: veer away
const int FAST = 200, SLOW = 90, TURN = 180;
const unsigned long BACK_MS = 400, SPIN_MS = 350;

// ---------- stuck reflex (stage 1) ----------
// Driving forward, but the distance ahead stays the same for 1.5 s -> the car is stuck
// (a corner caught on something). Back up longer, turn, try again. Tells the laptop "STUCK".
const int STUCK_CM = 4;                  // ahead changed less than this ...
const unsigned long STUCK_MS = 1500;     // ... for this long = stuck
const unsigned long ESCAPE_BACK_MS = 700;

// ---------- short-term memory (stage 1) ----------
// The car has no map (it can't measure where it is), but it remembers what happened in the last
// few seconds: escapes close together are "the same trap". Then it keeps turning the SAME way
// (no left-right-left dithering in a corner) and turns further each time; the 3rd time, or in a
// dead end (blocked ahead, left AND right), it backs up longer and turns about half a circle.
const int DEADEND_CM = 35;               // after backing up, both sides still < this = dead end
const int CLOSE_CM = 10;                 // a side this close: pivot away instead of a gentle curve
const unsigned long MEMORY_MS = 8000;    // escapes less than 8 s apart = the same trap
const unsigned long BIG_BACK_MS = 800;   // big escape: back up this long ...
const byte BIG_SPIN = 3;                 // ... and spin 3 x SPIN_MS (tune: about half a circle)

Servo servo;
byte mode = 0;
char line[32];
byte lineLen = 0;
unsigned long lastCommand = 0;
int wheelL = 0, wheelR = 0;
unsigned long lastWheelReport = 0;

const char SCAN_DIR[4] = {'L', 'C', 'R', 'C'};
byte scanIdx = 0;
bool scanning = false;
unsigned long servoMovedAt = 0;
int distL = 400, distC = 400, distR = 400;
bool freshCenter = false;

// Missed-echo filter: the HC-SR04 sometimes hears no echo and reads 400 ("nothing there")
// even when a wall is close. ONE 400 right after a close reading is treated as a miss:
// we keep the last value once. Two 400s in a row are believed.
const int MISS_NEAR_CM = 150;
bool missed[3] = {false, false, false};  // L, C, R

byte s1State = 0;                        // 0 drive, 1 back up, 2 spin, 3 wait for a fresh center reading
unsigned long s1Until = 0;
bool spinRight = true;
byte trapCount = 0;                      // escapes in the current trap
unsigned long lastEscape = 0;
bool lastTurnRight = true;
bool sameTrap = false, bigEscape = false;


int stuckRef = -1;                       // the distance ahead when it last changed (-1 = unknown)
unsigned long stuckSince = 0;

void resetStuck() {
  stuckRef = -1;
  stuckSince = millis();
}

void stuckWatch(int cm) {                // called with every distance measured straight ahead
  if (cm >= 400) {                       // nothing in range: can't tell if we move
    resetStuck();
  } else if (stuckRef < 0 || abs(cm - stuckRef) > STUCK_CM) {
    stuckRef = cm;                       // it changed: we are moving
    stuckSince = millis();
  }
}

int angleOf(char d) {
  if (d == 'L') return LEFT_DEG;
  if (d == 'R') return RIGHT_DEG;
  return CENTER_DEG;
}

int readCm() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  unsigned long us = pulseIn(ECHO, HIGH, 25000UL);
  if (us == 0) return 400;
  unsigned long cm = us / 58;
  return cm > 400 ? 400 : (int)cm;
}

// ---------- motors ----------
// These motors don't turn at all below about MIN_PWM: they just buzz. So any real command is lifted
// into MIN_PWM..255 (keeping its order: a bigger command is still faster). Tune: the smallest
// speed at which the car still rolls on your floor (VS Code task "Check motors").
const int MIN_PWM = 80;

int lift(int speed) {
  int a = abs(speed);
  if (a < 12) return 0;                                // tiny = stop
  int out = MIN_PWM + (long)a * (255 - MIN_PWM) / 255;
  return speed > 0 ? out : -out;
}

void setSide(int en, int a, int b, int speed) {
  speed = lift(constrain(speed, -255, 255));
  if (speed >= 0) {
    digitalWrite(a, HIGH);
    digitalWrite(b, LOW);
    analogWrite(en, speed);
  } else {
    digitalWrite(a, LOW);
    digitalWrite(b, HIGH);
    analogWrite(en, -speed);
  }
}

void drive(int left, int right) {
  wheelL = constrain(left, -255, 255);
  wheelR = constrain(right, -255, 255);
  setSide(ENA, IN1, IN2, wheelL);
  setSide(ENB, IN3, IN4, wheelR);
}

bool timeReached(unsigned long t) {
  return (long)(millis() - t) >= 0;
}

void setMode(byte m) {
  mode = m;
  drive(0, 0);
  s1State = 0;
  resetStuck();
  lastEscape = 0;                        // a new stage forgets old traps
  trapCount = 0;
  scanning = (m == 1 || m == 2);
  scanIdx = 0;
  servo.write(scanning ? angleOf(SCAN_DIR[0]) : CENTER_DEG);
  servoMovedAt = millis();
  lastCommand = millis();
  Serial.print("MODE,");
  Serial.println(m);
}

void scanStep() {
  if (!scanning) return;
  if (millis() - servoMovedAt < SETTLE_MS) return;
  char d = SCAN_DIR[scanIdx];
  int cm = readCm();
  int i = (d == 'L') ? 0 : (d == 'R') ? 2 : 1;
  int prev = (i == 0) ? distL : (i == 2) ? distR : distC;
  if (cm >= 400 && prev < MISS_NEAR_CM && !missed[i]) {
    cm = prev;                           // probably a missed echo: keep the last value once
    missed[i] = true;
  } else {
    missed[i] = false;
  }
  if (d == 'L') distL = cm;
  else if (d == 'R') distR = cm;
  else { distC = cm; freshCenter = true; stuckWatch(cm); }
  Serial.print("P,");
  Serial.print(d);
  Serial.print(',');
  Serial.print(cm);
  Serial.print(',');
  Serial.println(millis());
  scanIdx = (scanIdx + 1) % 4;
  servo.write(angleOf(SCAN_DIR[scanIdx]));
  servoMovedAt = millis();
}

void startEscape(unsigned long backMs) {
  sameTrap = lastEscape != 0 && millis() - lastEscape < MEMORY_MS;
  trapCount = sameTrap ? trapCount + 1 : 1;
  lastEscape = millis();
  bigEscape = trapCount >= 3;                          // 3rd escape in the same trap: big one
  if (bigEscape) {
    Serial.println("TRAP,repeat");
    trapCount = 0;
  }
  s1State = 1;
  s1Until = millis() + (bigEscape && backMs < BIG_BACK_MS ? BIG_BACK_MS : backMs);
  drive(-TURN, -TURN);
}

void stage1() {
  if (s1State == 1) {                                  // backing up
    drive(-TURN, -TURN);
    if (timeReached(s1Until)) {
      s1State = 2;
      // the sides were measured again while backing up: blocked left AND right = dead end
      if (!bigEscape && distL < DEADEND_CM && distR < DEADEND_CM) {
        Serial.println("TRAP,deadend");
        bigEscape = true;
      }
      // same trap as a moment ago: keep the same direction; otherwise toward the side with more space
      spinRight = sameTrap ? lastTurnRight : (distR > distL);
      lastTurnRight = spinRight;
      byte times = bigEscape ? BIG_SPIN : (sameTrap ? 2 : 1);
      s1Until = millis() + SPIN_MS * times;
    }
    return;
  }
  if (s1State == 2) {                                  // spinning
    if (spinRight) drive(TURN, -TURN);
    else drive(-TURN, TURN);
    if (timeReached(s1Until)) {
      s1State = 3;
      freshCenter = false;
      drive(0, 0);
    }
    return;
  }
  if (s1State == 3) {                                  // stand still until the sensor has looked ahead again
    drive(0, 0);
    if (freshCenter) {
      s1State = 0;
      resetStuck();
    }
    return;
  }
  if (stuckRef >= 0 && millis() - stuckSince > STUCK_MS) {   // stuck: back up longer, then turn
    Serial.println("STUCK");
    resetStuck();
    startEscape(ESCAPE_BACK_MS);
    return;
  }
  if (distC < STOP_CM) {
    startEscape(BACK_MS);
  } else if (distL < SIDE_CM) {
    drive(FAST, distL < CLOSE_CM ? -SLOW : SLOW);      // something on the left: veer (or pivot) right
  } else if (distR < SIDE_CM) {
    drive(distR < CLOSE_CM ? -SLOW : SLOW, FAST);      // something on the right: veer (or pivot) left
  } else {
    drive(FAST, FAST);
  }
}

void reportWheels() {
  if (millis() - lastWheelReport < 200) return;
  lastWheelReport = millis();
  Serial.print("W,");
  Serial.print(wheelL);
  Serial.print(',');
  Serial.println(wheelR);
}

void handleLine() {
  if (strncmp(line, "MODE,", 5) == 0) {
    int m = atoi(line + 5);
    if (m >= 0 && m <= 3) setMode((byte)m);
    return;
  }
  if (strncmp(line, "LOOK,", 5) == 0) {
    if (mode == 0) servo.write(angleOf(line[5]));
    return;
  }
  if (line[0] == 'M' && line[1] == ',') {
    if (mode != 2 && mode != 3) return;
    char* comma = strchr(line + 2, ',');
    if (!comma) return;
    *comma = 0;
    drive(atoi(line + 2), atoi(comma + 1));
    lastCommand = millis();
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
      line[lineLen] = ch;
      lineLen++;
    } else {
      lineLen = 0;
    }
  }
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
  Serial.println("READY");
  setMode(START_MODE);
}

void loop() {
  readSerial();
  scanStep();
  if (mode == 1) {
    stage1();
    reportWheels();
  }
  if ((mode == 2 || mode == 3) && millis() - lastCommand > WATCHDOG_MS) drive(0, 0);
}
