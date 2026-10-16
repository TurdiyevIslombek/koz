# motor_listener (CLAUDE.md rule 11)

The only sketch Ko'z drives the car with. It receives wheel speeds over the USB cable and keeps the
safety rules in `motor_logic.h`: starts disarmed, motors off after 250 ms without a fresh command,
speed capped, no forward when something is closer than `stop_cm` or the sonar can't see. Your
physical switch is the last layer. Protocol: top of `motor_listener.ino`.

Before the first drive, measure `speed_cap` and `stop_cm` with `firmware/stop_test` (its README).

Upload (Arduino on USB; the ESP32-CAM link on D0/D1 disconnected):
```bash
tools/bin/arduino-cli compile --upload -p /dev/cu.usbmodem1101 --fqbn arduino:avr:uno firmware/motor_listener
```
Tests without a board: `.venv/bin/python -m pytest tests/test_firmware.py` (the safety rules run on
the Mac with clang++; both sketches compile for the Uno).

Islombek's original `car.ino` (stages 1–3) is untouched; a copy is in `koz/brains/flybrain/original/`.
