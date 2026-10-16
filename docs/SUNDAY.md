# Sunday: the car, in this order

About 3 hours. Your physical switch within reach the whole time; nobody and no pets in front of the
car; a room that is not your bedroom. Commands run in Terminal in the Ko'z folder
(`~/AI/competitions/opencv-flybrain`) unless they say otherwise.

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
the right. For each trial: **Trials** page → start the trial → **Setup**: type
`Qizil koptokni quv` → **Test** → press **A** in the "Ko'z runner" window → watch for up to 20 s →
**q** → finish the trial as pass or fail.

**Pass** = it touches the ball, or stops facing it within about 20 cm, within 20 s, without hitting
anything else. Film every trial with your phone (the video needs the best real take).

## e. What to send me

- The `MOVED` and `RESULT` lines (step b), and which camera option worked (step c4).
- For each trial: pass or fail, the seconds, and for a fail what happened (lost the ball, spun,
  zig-zagged away, stopped by the obstacle rule, a privacy stop, the picture froze).
- The fps number at the top of the Ko'z window, and the last 30 Terminal lines after any failed trial.
- Keep the videos on your phone. Don't send `.env` or anything with a token.

Then I write the numbers into `docs/TRIALS.md` and the report. If it doesn't chase reliably
(your call; mine would be at least 7 of 10), we switch to option A by Oct 19, as agreed.

## f. Put the original car.ino back

1. D0 wire still out. In `~/Downloads/flybrain_car`: `bash upload_car.sh`.
2. **Plug the ESP32-CAM wire back into D0.** USB cable out, battery on.
3. `bash run.sh` and check stage 1 drives as before.
4. Check nothing in your car folder changed (in Terminal):
   ```bash
   cd ~/Downloads && shasum -a 256 -c --quiet ~/AI/competitions/_backups/flybrain_car_2026-10-16.sha256 && echo "all 187 unchanged"
   ```
   (New run files in `runs/` are fine. A `.DS_Store` line only means Finder changed its view settings.)
