# Judge verification — 25 October 2026 (Tashkent)

## Fresh GitHub clone: the exact README command

Verified commit **`3fe1978915e23db820efcd672e254e35e0b137bc`**, cloned from GitHub into
`/private/tmp/koz-judge-proof.ncfOeI/koz`. The following command ran in its empty parent directory:

```bash
git clone https://github.com/TurdiyevIslombek/koz.git koz && cd koz && bash scripts/judge_demo.sh
```

**Exit status 0; elapsed 176.94 seconds (2 minutes 57 seconds)** including clone, dependency
installation, model download and the agent run. Git and Python were already installed. An empty
pip cache was used; no virtual environment, `.env`, private clips, models or saved app data were
copied from the working checkout. Planner/runner credential environment variables were removed,
and the command explicitly selects `--planner rules`. The scene model was downloaded from its
public release and reported **SHA-256 matches**; YuNet and NanoDet came from Git.

Selected actual output (sequence IDs can vary with timing):

```text
Planners, in order: rule planner (no AI model)
Plan (en): I will look for a round red object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
#2    recipe    revision 1 from the planner: hue 0±10, saturation ≥ 120
#5    observe   round 1 revision 1: privacy approved, target lost
#10   decide    round 1: target_visible fail (from #5, #7, #8) -> adjust: color_finder.hue_center 0 -> 13
#11   recipe    revision 2 from the adjustment, because of decision #10: hue 13±10, saturation ≥ 120
#14   observe   round 2 revision 2: privacy approved, target right
#19   decide    round 2: target_visible pass (from #14, #15, #17) -> run
#20   status    running (revision 2)
Result: the job ran, then idle.
Adjusted: color_finder.hue_center 0 -> 13 (target_visible: lost -> right, pass)
```

The clip is 132,021 bytes, 18 seconds, 320 × 240 at 10 fps. SHA-256:
`e9ed5a53d5fe29e314e63f105fd3d2113621d382dcccdbcc4901cab442f28694`.
The ball's colour is constant across the clip: the setting change, not a changed input colour,
allows detection in revision 2. The privacy guard and face-blur models ran normally.

An empty npm cache was also used for `(cd web && npm ci && npm run build && npm test)`:
**87 passed, 0 failed, 0 skipped**. A shell assertion verified that the subshell left the working
directory at the repository root. All 71 regression photos downloaded with matching hashes.

After the documented setup, `.venv/bin/python -m pytest -q -rs` ran **twice consecutively**
in that same clone, with no cache cleanup or tracked-file edits between runs:

| Run | Passed | Skipped | Failed | Time |
| --- | ---: | ---: | ---: | ---: |
| First | 545 | 3 | 0 | 69.90 s |
| Second | 545 | 3 | 0 | 68.86 s |

Both runs reported exactly the documented skips:

```text
SKIPPED [2] tests/test_firmware.py:37: needs tools/bin/arduino-cli
SKIPPED [1] tests/test_person_detector.py:94: no local clip in tests/fixtures/private/
```

The suite includes the new real-model public-clip test, missing/corrupt-video CLI tests,
first-frame decoding tests and an early-end failure exit check. `git status --short` was empty
after the full verification. Raw logs are in `/private/tmp/koz-judge-proof.ncfOeI/`
(`judge-command.log`, `photos.log`, `web.log`, `python-1.log`, `python-2.log`); the decisive
results are preserved above because temporary files may be cleaned by the OS.

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
