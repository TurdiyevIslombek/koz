# Tuesday, Oct 20: the car, in this order

(Moved from Sunday Oct 18, which went into fixing the car's hardware.) About 3 hours. Your physical switch within reach the whole time; nobody and no pets in front of the
car; a room that is not your bedroom. Commands run in Terminal in the Ko'z folder
(`~/AI/competitions/opencv-flybrain`) unless they say otherwise.

**Your hardware changed on Oct 18** (Claude read your car folder, read-only): a 9.5 V battery with
the motor power scaled to at most 6 V, a soft start, and stop-before-reverse in your `car.ino`. The
pins are the same (`QUIET_WIRING` is off; you confirmed no wires moved). Done on Oct 19, as you asked:
`motor_listener` and `stop_test` now cap the motors at 6 V for the 9.5 V pack, `motor_listener` has
your soft start and stop-before-reverse, and the Ko'z copy of your car code is today's version. If the
multimeter shows another voltage, change `BATTERY_V` at the top of both sketches before uploading.

**Your camera is mounted upside down** (`CAMERA_FLIP = True` in your car's `config.py`). Ko'z now
turns the picture too, with `--upside-down`. Without it, left and right would be swapped and the
brain would turn away from the ball.

## a. portfolio recordings: the ORIGINAL car first

Steps b and c replace the program on the Arduino, so record first. Nothing else has been uploaded
to the board, so it still has your `car.ino`.
1. Car wired as usual (Wi-Fi mode, the ESP32-CAM wire in Arduino D0). Unsure what's on the board?
   Pull the D0 wire, run `bash upload_car.sh` in `~/Downloads/flybrain_car`, plug the wire back.
2. In `~/Downloads/flybrain_car`: `bash run.sh`. Record stages 1–3 as planned. Close the app.

## b. Stop test (about 20 minutes)

1. **Pull the ESP32-CAM wire out of Arduino D0** (`PINS.txt`). It stays out until step f.
2. USB cable from the Arduino to the Mac. Follow `firmware/stop_test/README.md`: upload, `PING`,
   wheels in the air, `MOVE`, then `RUN` 3 times at each speed.
3. **Send me every `MOVED` and `RESULT` line, then wait.** I put your two numbers into
   motor_listener. If you can't reach me: go on with its careful defaults only if all three
   `RUN 120` slides were 25 cm or less; otherwise stop here.

## c. motor_listener, checked with the wheels in the air

1. `tools/bin/arduino-cli board list` shows the port. Upload (your port):
   ```bash
   tools/bin/arduino-cli compile --upload -p /dev/cu.usbmodem1101 --fqbn arduino:avr:uno firmware/motor_listener
   ```
2. Car on a box, wheels off the ground. Mac on the camera's own Wi-Fi (name and password:
   `HOW_TO_RUN.txt` in your car folder).
3. Start it:
   ```bash
   .venv/bin/python scripts/agent_demo.py --i-own-this-camera --camera http://192.168.4.1:81/stream --upside-down --motors auto "Qizil koptokni quv"
   ```
4. **Before you arm:** hold the ball on the car's **left**. In the Ko'z window it must be on the
   **left**. If it's on the right, try without `--upside-down`, or add `--mirror`. Tell me which worked.
5. Press Enter to arm. Ball on the left: the right wheels spin faster (it turns left). Ball on the
   right: the left wheels spin faster. Ball in the middle: both forward. No ball: it turns slowly,
   searching. Then pull the USB cable: the wheels must stop by themselves (in a quarter second).
   Anything else: stop and tell me what you saw.

## d. 10 chase trials (on the floor)

Start (one line):
```bash
KOZ_RUNNER_ARGS="--camera esp32_cam=http://192.168.4.1:81/stream --upside-down esp32_cam --motors auto" ./start-koz.command
```
Ball 1.5 m from the car: trials 1–4 straight ahead, 5–7 about 30° to the left, 8–10 about 30° to
the right. For each trial: **Trials** page → start the trial → press **Enter** in the Terminal window
(this arms the motors; a job won't start with them off) → **Setup**: type `Qizil koptokni quv` →
**Test** → watch for up to 20 s → **Stop job** in the browser → finish the trial as pass or fail.
The next trial (one job per trial): put the car back, start the next trial on the **Trials** page,
press **Enter** again, then **Try again** on the Live page (the same job, no typing).

**Pass** = it touches the ball, or stops facing it within about 20 cm, within 20 s, without hitting
anything else. Film every trial with your phone (the video needs the best real take).

## e. What to send me

- The `MOVED` and `RESULT` lines (step b), and which camera option worked (step c4).
- For each trial: pass or fail, the seconds, and for a fail what happened (lost the ball, spun,
  zig-zagged away, stopped by the obstacle rule, a privacy stop, the picture froze).
- The fps number at the top of the Ko'z window, and the last 30 Terminal lines after any failed trial.
- Keep the videos on your phone. Don't send `.env` or anything with a token.

Then I write the numbers into `docs/TRIALS.md` and the report. Reliable = **at least 7 of 10**
(your decision, in `docs/TRIALS.md`); 6 or fewer, and we switch to option A by Wed Oct 21 (the
time box moved from Oct 19 with the car day).

## f. Put the original car.ino back

1. D0 wire still out. In `~/Downloads/flybrain_car`: `bash upload_car.sh`.
2. **Plug the ESP32-CAM wire back into D0.** USB cable out, battery on.
3. `bash run.sh` and check stage 1 drives as before.
4. Check nothing in your car folder changed (in Terminal):
   ```bash
   cd ~/Downloads && shasum -a 256 -c --quiet ~/AI/competitions/_backups/flybrain_car_2026-10-18.sha256 && echo "all 202 unchanged"
   ```
   (This list is from Oct 18, after your hardware fixes; the Oct 16 one would flag those edits. New run
   files in `runs/` are fine. A `.DS_Store` line only means Finder changed its view settings.)

## g. The robot's camera as Ko'z's camera (the website eye shows what the robot sees)

Added Oct 22. Your stage-3 camera sketch already does what Ko'z needs: it streams MJPEG video at
`http://<camera address>:81/stream` (320 × 240). Ko'z reads that stream as its `esp32_cam` camera,
checks and blurs it on the Mac, and the website's eye box shows it **on this Mac only**
(`127.0.0.1`); the picture never goes to AWS. Your car folder is used **read-only**: nothing in
`~/Downloads/flybrain_car` is changed.

**One thing to know first.** With an empty Wi-Fi name (as now) the camera makes its own Wi-Fi,
`FlyCar-CAM`, at `192.168.4.1`. That Wi-Fi has no internet, so a Mac on it can't reach the AWS
website. Two ways:

- **For the AWS website (recommended):** put the camera on your home Wi-Fi (2.4 GHz), using a
  **copy** of your sketch (step 1). Then the Mac stays on home Wi-Fi with internet.
- **Local website only:** keep the camera's own Wi-Fi, join `FlyCar-CAM` on the Mac (name and
  password: `HOW_TO_RUN.txt` in your car folder) and use `start-koz.command` (the website on this
  Mac). Skip to step 2 and use `http://192.168.4.1:81/stream`.

**Safety:** Ko'z doesn't drive in these steps (no `--motors`), but the car's battery powers the
camera: keep your physical motor switch off, or the wheels in the air.

### 1. Camera on your home Wi-Fi, from a copy (once, about 5 minutes)

Don't use `upload_camera.sh` for this: when you answer "y" it writes the Wi-Fi into your original
folder. Instead, in Terminal:

```bash
mkdir -p ~/koz-camera-copy && cp -R ~/Downloads/flybrain_car/esp32cam/camera_stream ~/koz-camera-copy/
```

```bash
open -e ~/koz-camera-copy/camera_stream/wifi_settings.h
```

In TextEdit, type your home Wi-Fi name and password between the quotes of `WIFI_NAME` and
`WIFI_PASSWORD` (2.4 GHz only), save, close. This copy stays on your Mac: never put it in the Ko'z
folder, git, or a message.

ESP32-CAM on its ESP32-CAM-MB board, USB to the Mac, Arduino unplugged. Find its port:

```bash
tools/bin/arduino-cli board list
```

Upload the copy (put your port in place of `/dev/cu.usbserial-110`):

```bash
tools/bin/arduino-cli compile --fqbn esp32:esp32:esp32cam --upload -p /dev/cu.usbserial-110 ~/koz-camera-copy/camera_stream
```

If it fails: hold IO0 on the MB board, press and release RST, let go of IO0, run it again (the
same trick as your `upload_camera.sh`). Then read the address it prints (Ctrl+C to stop):

```bash
tools/bin/arduino-cli monitor -p /dev/cu.usbserial-110 -c baudrate=115200
```

It prints `CAMERA READY: http://<address>:81/stream`. Write the address down. (If it says it made
its own Wi-Fi, the name or password was wrong, or the network is 5 GHz only.) Put the camera back
on the car, powered from the LM2596 as before, and check in Safari that `http://<address>/` shows
video. **Close that Safari tab**: the camera sends its stream to one viewer at a time, and that
must be Ko'z.

Check your car folder is unchanged (as in step f):

```bash
cd ~/Downloads && shasum -a 256 -c --quiet ~/AI/competitions/_backups/flybrain_car_2026-10-18.sha256 && echo "all 202 unchanged"
```

To go back to the camera's own Wi-Fi later: `bash upload_camera.sh` in your car folder, answer "N".

### 2. Start Ko'z with both cameras (the Mac and the robot)

In Terminal, in the Ko'z folder (your address in place of `192.168.1.50`):

```bash
.venv/bin/python -m koz.server --i-own-this-camera --window --planner rules --cloud --camera mac_camera=0 --camera esp32_cam=http://192.168.1.50:81/stream --upside-down esp32_cam
```

This is `start-koz-cloud.command` plus the two cameras. `--upside-down esp32_cam` turns the
picture because your camera is mounted upside down (`CAMERA_FLIP = True` in your `config.py`), and
the privacy guard and blur see it the right way up. `http://flycar-cam.local:81/stream` usually
works too, if you'd rather not write the address.

### 3. See what the robot sees on the website

1. On this Mac, open the website and log in as the owner.
2. **Set up** → camera: **Robot camera (ESP32-CAM)**.
3. Type a job that doesn't drive, e.g. `Qizil koptokni top` (find the red ball), then **Test**.
4. The eye box on **Live** shows the robot's view, faces blurred, with the target ring.
5. Check left and right: hold the ball on the car's **left**; it must show on the **left**. If it's
   on the right, start again without `--upside-down esp32_cam`, or add `--mirror esp32_cam`.

If the eye stays empty: the stream has another viewer (close Safari and the car app), the Mac is
on another Wi-Fi than the camera, or the privacy guard is checking or has stopped (the Live page
says which). The chase itself (motors) is steps c–d; the camera part is the same.
