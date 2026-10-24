# ESP32-CAM stream and serial bridge

The AI-Thinker ESP32-CAM sketch serves a test page on port 80, MJPEG video at
`http://<camera-ip>:81/stream`, status at `/status`, and the Arduino serial bridge
on TCP port 82. It tries the two configured networks and reconnects after a drop.

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
