# ESP32-CAM stream and serial bridge

The AI-Thinker ESP32-CAM sketch serves a test page on port 80, MJPEG video at
`http://<camera-ip>:81/stream`, status at `/status`, and the Arduino serial bridge
on TCP port 82. It tries the two configured networks and reconnects after a drop.

The `koz-flash-off-v1` build holds the white illuminator's GPIO4 LOW as the first
setup operation, using the ESP32 GPIO hold function. It has no light-on control.
The serial banner and `/status` identify this build. The platform's brownout
protection is left enabled. Access-point credentials are no longer printed to serial.
GPIO hold reference: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html

On Oct 26 the owner reported a hot LED area and a hand burn, although the previous
source already wrote GPIO4 LOW once during setup. The cause is unconfirmed. A
compiled/uploaded flash-off build does not prove the board or its supply is sound.
Keep the camera isolated from the car until the disconnected camera power lead is
verified at 5 V. Only reconnect a cooled, undamaged module; disconnect immediately
if its white light remains on or it heats rapidly. A damaged module needs replacement.

Copy `wifi_settings.example.h` to `wifi_settings.h` in this directory and fill in
your 2.4 GHz Wi-Fi credentials and fallback access-point password (at least eight
characters). Leave both hotspot values empty if unused. The private header is
git-ignored. These are local camera-network credentials, not AWS settings.

From the repository root, with arduino-cli and the ESP32 core installed:

```bash
tools/bin/arduino-cli compile --fqbn esp32:esp32:esp32cam firmware/camera_stream
```

Compilation does not flash a board. Use your board's actual serial port when uploading.
This is the Ko'z copy; the original car project is not required to build it.
