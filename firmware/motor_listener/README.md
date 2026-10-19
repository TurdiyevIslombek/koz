# motor_listener (CLAUDE.md rule 11)

The only sketch Ko'z drives the car with. It receives wheel speeds over the USB cable and keeps the
safety rules in `motor_logic.h`: starts disarmed; a person arms it by hand on the laptop; a fault
(250 ms without a fresh command, forward into something closer than `stop_cm`, or forward while the
sonar can't see) disarms it until the next arm by hand; speed capped. Turning on the spot and reversing
next to an obstacle are allowed. Your
physical switch is the last layer. Protocol: top of `motor_listener.ino`.

Since Oct 19, as in Islombek's own `car.ino` after his Oct 18 hardware fixes: for a **9.5 V pack**
the motors get at most **6 V** (commands lift into PWM 61..204; set `BATTERY_V` to what the
multimeter reads), and a **soft start**: a side speeds up at most 2 PWM per millisecond, and a change
of direction stops first and waits 40 ms, so four motors never reverse at once and brown out the
Arduino and the camera. Slowing and stopping stay immediate (the 250 ms watchdog, obstacle stops,
faults and STOP never wait). Near an obstacle (or with the sensor blind) the soft start never adds up
to forward motion: one side waiting to reverse while the other still pushes forward would pivot the
car into the wall, so there both sides wait, and a spin away stays a pure spin (Oct 19 security
review). Tested on the Mac: `firmware/tests/` (logic and the real sketch).

Before the first drive, measure `speed_cap` and `stop_cm` with `firmware/stop_test` (its README).

Upload (Arduino on USB; the ESP32-CAM link on D0/D1 disconnected):
```bash
tools/bin/arduino-cli compile --upload -p /dev/cu.usbmodem1101 --fqbn arduino:avr:uno firmware/motor_listener
```
Tests without a board: `.venv/bin/python -m pytest tests/test_firmware.py` (the safety rules run on
the Mac with clang++; both sketches compile for the Uno).

Islombek's original `car.ino` (stages 1–3) is untouched; a copy is in `koz/brains/flybrain/original/`.
