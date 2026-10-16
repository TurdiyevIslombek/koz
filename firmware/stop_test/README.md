# Measure the speed cap and the stopping distance (about 20 minutes)

`motor_listener` needs two numbers from **your** car on **your** floor: the fastest speed you
allow (`speed_cap`) and how close an obstacle may get before forward is refused (`stop_cm`).
This sketch measures them. Send Claude all the `MOVED` and `RESULT` lines at the end.

**Safety first.** Your physical switch within reach. Nobody, and no pets, in front of the car.
A flat "wall" to drive at: a real wall or a big cardboard box. In the monitor, **any key + Enter
stops the motors at once**; the sketch also stops by itself after 5 s, before a wall closer than
25 cm (MOVE), and when the sonar gets no echo.

## 1. Upload (Arduino on the USB cable, car battery on)

In Terminal, in the project folder:
```bash
tools/bin/arduino-cli board list
```
Note the port of the Arduino Uno (for example `/dev/cu.usbmodem1101`). Then, with your port:
```bash
tools/bin/arduino-cli compile --upload -p /dev/cu.usbmodem1101 --fqbn arduino:avr:uno firmware/stop_test
```
```bash
tools/bin/arduino-cli monitor -p /dev/cu.usbmodem1101 -c baudrate=115200
```
You see `READY stop_test`. (The ESP32-CAM link on D0/D1 must not be connected while uploading.)

## 2. Check the sensor and the wheels (wheels in the air)

1. Hold a book 50 cm in front of the sensor; type `PING` + Enter. It should say about `PING,50`.
2. Put the car on a box, wheels off the ground. Type `MOVE 100`. Both sides must spin **forward**
   for 1 s. If one side spins backwards, swap that side's two motor wires on the L298N.

## 3. The slowest speed that moves the car (on the floor)

Put the car about 1.5 m from the wall, facing it. Type, one at a time, putting the car back if needed:
`MOVE 20`, `MOVE 40`, `MOVE 60`, `MOVE 80`. Each prints `MOVED,speed,cm`.
The smallest speed that moved it at least 5 cm is the slowest useful speed.

## 4. Stopping distance at each speed (on the floor)

Put the car **2 m** from the wall, facing it straight. Type `RUN 80`. It drives at the wall, cuts
the motors when the sonar reads 60 cm, waits 2 s and prints
`RESULT,speed,cut_cm,final_cm,stopping_cm,speed_cm_s` (`stopping_cm` = how far it slid).

Do **3 runs** at each speed, putting the car back at 2 m each time:
`RUN 80` ×3, `RUN 120` ×3, `RUN 160` ×3, and `RUN 200` ×3 only if you are comfortable with it.
Stop going faster when a speed feels too fast for a room with people in it.

## 5. Send Claude the lines

Copy every `MOVED` and `RESULT` line. Claude then sets, in `firmware/motor_listener/motor_listener.ino`:
- `speed_cap` = the fastest speed you are comfortable with whose slide is at most about 20 cm;
- `stop_cm` = the longest slide measured at that speed + 10 cm (margin);

and writes the numbers in `docs/TRIALS.md`. Until then motor_listener uses careful defaults
(`speed_cap` 120, `stop_cm` 35).
