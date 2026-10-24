# Judge verification — 25 October 2026 (Tashkent)

## Working-checkout validation

- Python 3.13.5, macOS 27, Apple silicon; Node 25.1.0, npm 11.6.2.
- Full Python suite: **547 passed, 1 skipped** (94.27 s). The skip is the optional private
  person video. All 71 Places365 regression photos and all three pinned models were present.
- Full web build and suite: **87 passed, 0 failed, 0 skipped**.
- Both Uno sketches compiled with `arduino:avr` 1.8.8 and Servo 1.3.0.
- ESP32-CAM sketch compiled with `esp32:esp32` 3.3.12 using a temporary copy and the
  placeholder Wi-Fi header: 1,170,093 bytes of flash, 61,888 bytes of global variables.
  No board was flashed and the real Wi-Fi header was not read or committed.

The first local Python run found the machine's missing Servo library (545 passed, two compile
failures, one skip). Servo 1.3.0 was then installed into `/private/tmp/koz-judge-arduino`, and the
complete suite above passed with `ARDUINO_DIRECTORIES_USER` pointing there. Socket tests need
localhost access; the tool sandbox's initial `EPERM` failures were resolved by permitting it.

The public website was inspected signed out: it displayed **Not shared yet**. Sharing clicks
in the README are checked against the app's labels and publication handler. The web suite
verifies sharing-off, selected-job/summary scope, read-only access, revocation and disconnects.
No production sharing settings or AWS files were changed. The original car folder was untouched.

This validates the software on a drawn recording and mocked hardware tests. It does not claim
a new physical robot trial, live camera measurement, or AWS deployment.
