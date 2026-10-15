# Trial list

Islombek runs and owns these trials (CLAUDE.md: 10 trials per demo, failures recorded).
Each trial is recorded with `begin_trial` / `finish_trial` (contracts/events.md, section 10).
Results go in the trial dashboard; failures are kept, not hidden.

## Privacy guard (demo 3) — draft

Point the camera at each scene, start a job, and record: result (pass/fail), the error
code shown, how long until it stopped, and **whether the owner-confirmed workspace was on**
(`--owner-workspace`; the window says "OWNER-CONFIRMED WORKSPACE"). A trial report without
that is incomplete. Trials 1–10 are run with it **off**.

Which file to double-click: trials 1–10 → `demo-blur.command` (strict); W1, W3, W4 →
`demo-desk.command` (workspace on). When Ko'z stops, a red banner says why. Use your own home or a place you have
permission to film, with nobody undressed or asleep in view. Ko'z saves no frames.

| # | Scene | Expected |
|---|---|---|
| 1 | Home bathroom: sink and mirror | Refused, `PRIVATE_BATHROOM` |
| 2 | Bathroom: shower or bath visible | Refused, `PRIVATE_BATHROOM` |
| 3 | **Toilet stall** (only the stall walls and the toilet visible) | Refused. Places365 has no toilet class, so this is the hardest case; record what it says |
| 4 | Bedroom, bed visible | Refused, `PRIVATE_BEDROOM` |
| 5 | Child's room or a bed in a corner | Refused, `PRIVATE_BEDROOM` |
| 6 | Wardrobe / changing area | Refused, `PRIVATE_CHANGING_ROOM` |
| 7 | Start in an allowed room, then turn the camera to the bathroom door | Stopped at the next check (within 10 s); record the seconds |
| 8 | Lens covered, or a very dark room | Not approved (`PRIVACY_UNCERTAIN`) |
| 9 | Control: classroom | Approved, job runs |
| 10 | Control: shop or office | Approved, job runs (a kitchen or living room is "uncertain": not on the allowlist) |

### Owner-confirmed workspace (your desk and the robot arena)

With `--owner-workspace` the guard approves the room on your word, unless a private room is
likely or the frame is too dark. Measured limit: on 2 of 23 real bathroom and bedroom photos
the model gives private rooms almost nothing (a bathroom read as "bank_vault 0.69"), so a
workspace would approve them. W3 checks that on your own bathroom.

| # | Scene (workspace **on**) | Expected |
|---|---|---|
| W1 | Your desk | Approved, window says "OWNER-CONFIRMED WORKSPACE" |
| W2 | The robot arena, car camera | Approved, same label |
| W3 | Start at your desk, then turn the camera to the bathroom | Stopped at the next check (within 10 s); record what the scene line said |
| W4 | Lens covered | Not approved (`PRIVACY_UNCERTAIN`) |

The guard's limits in `koz/policy.py` (`ALLOWED_SCENES`, `SCENE_PRIVATE_TOP5_BLOCKS`,
`SCENE_PRIVATE_SUM_BLOCKS`, `SCENE_MIN_TOP_PROB`, `SCENE_MIN_BRIGHTNESS`, `SCENE_MIN_CONTRAST`)
were set on 46 real photos (below); these trials check them on your own rooms.

## Failure found in live test #1 and how it was fixed (Oct 14)

**What happened.** First live run of `demo-blur.command`: the privacy guard **approved a
bathroom with the toilet clearly visible**. The scene line said "catacomb 0.5–0.6" for
every scene (own room: catacomb 0.50; bathroom: catacomb 0.61, privacy approved).

**What was checked.**
- *Weights.* All 102 weights loaded strictly (the `module.` prefix stripped; nothing missing
  or extra); the BatchNorm statistics are real numbers. The model is not partly random.
- *Pipeline.* On 5 real Places365 photos, Ko'z's ONNX in OpenCV 5 gave the same top 3 as
  the original PyTorch model with the authors' own preprocessing (PIL resize to 224, /255,
  ImageNet mean and standard deviation, RGB); largest difference 0.026. Colour order is
  right: feeding BGR instead visibly changes the answers.
- *Dark frames.* The same photos made very dark came out as catacomb, jail cell, burial
  chamber and attic (a shop: catacomb 0.93), which is the live pattern.

**Cause** (most likely; the next live run confirms it):
1. The guard judged only the first frame, and a MacBook camera's first frames are dark
   while its exposure settles, so it saw a "catacomb".
2. The rule approved any place that wasn't on the private list, and "catacomb" isn't.
3. The next check was 120 s away, so the approval held while the camera saw the bathroom.

Real photos showed the same weakness without darkness: the old rule also approved a
bathroom read as "bank_vault 0.69" and a bedroom read as "kennel/outdoor 0.37".

**Fix** (`koz/scene.py`, `koz/policy.py`, `koz/capture.py`):
- **Allowlist.** Approve only when the top guess is a listed public or work place
  (classroom, shop, market, office, corridor, lobby, street, yard, farm...) at 0.30 or more.
  Everything else is "uncertain" and stops the job.
- **Block** when any private room is in the top 5 above 0.10, and (as before) when the top
  guess is private or private rooms together reach 15 %.
- **Too dark or too flat is never approved:** brightness below 40 or contrast below 20
  (0–255 grey, over the allowed area only).
- **Camera warm-up:** a live camera's first second of frames is dropped.
- **Check every 10 s** instead of every 120 s (one check takes about 10 ms).

**Regression test.** `tests/test_scene_photos.py` uses 46 real Places365 validation photos
(12 bathrooms, 11 bedrooms, 11 classrooms, 12 shops) and a dark copy of each. It fails if
any bathroom or bedroom, or any dark frame, is approved. Put back the old rule and it fails
6 of its 7 checks; with the fix it passes. Classrooms approved: 9 of 11; shops: 7 of 12 (the
rest are "uncertain", a safe stop). The photos' copyright belongs to their owners, so they
aren't in git: `scripts/fetch_test_photos.py` downloads exactly the listed files. The
Places team asks users of the original Places365 data to sign a form on
http://places2.csail.mit.edu/download.html; Islombek signed it on Oct 14.

**Still open.**
- Re-run this live test (bathroom, your room, your desk). The scene line now updates every 10 s.
- Living room and kitchen stay off the allowlist (Islombek's decision); his desk and the
  robot arena use the owner-confirmed workspace instead (above).

**Security review, same day.** Private rooms get mistaken for places on the allowlist (a
dark bedroom: "staircase 0.36"; a real bathroom: "corridor 0.11"). Removed staircase,
entrance hall and home office; corridor, lobby and elevator lobby now need 0.50. The photo
test still passes, with the same approvals (classrooms 9/11, shops 7/12).
- The stricter guard will stop more often by mistake ("uncertain"); the trials measure how often.

## Live test #2: guard too sensitive at home (Oct 15)

**What happened.** Every launcher, including `demo-desk.command`, stopped at home with
"private room". Islombek's desk is in his bedroom: the room check put a bedroom class in
its top 5 above 0.10, and that rule stopped even the owner-confirmed workspace.

**Fix: stop on things the guard actually sees** (`koz/privacy.py`, every job, at start and
on every recheck, before any block):
- **Object check** with the NanoDet model Ko'z already has (COCO classes 59 bed, 61 toilet,
  71 sink; checked on real photos). A bed or a toilet at 0.40 or more in 2 of the last 3
  checks stops Ko'z, and the banner names it: "a bed is in view. Ko'z does not run in
  bedrooms." Seen once, the guard holds every frame and checks the next frames first, so
  nothing runs while it is unsure. A sink stops it only when the room check also has
  bathroom or shower in its top 3.
- **Workspace mode** relies on the object check plus darkness. The room check stops it only
  when it is confident: a private room is the top guess at 0.50 or more, or private rooms
  together reach 0.40. The "top 5 above 0.10" rule no longer applies there.
- **Strict mode** keeps every rule it had and adds the object check.
- **Debug line** on screen and in the terminal on every check: top 3 room guesses, the
  objects seen, the result.

**Measured on 71 real Places365 photos** (`tests/test_scene_photos.py`):

| Photos | Strict | Workspace |
|---|---|---|
| Bathrooms (12) | all stopped (7 by a toilet, 1 by a sink) | 10 stopped, **2 approved** |
| Bedrooms (11) | all stopped (7 by a bed) | 10 stopped, **1 approved** |
| Desks / home offices (12) | 3 run | 10 run; the 2 with a bed in view stopped |
| Kitchens (13) | 12 uncertain, 1 stopped | all run, including one with a sink |
| Classrooms (11) / shops (12) | 9 / 7 run, as before | all run |

**Honest limit.** The object check only works on what it can see: a bed mostly out of view,
or a toilet behind a door, can be missed (NanoDet found a bed in 7 of 11 bedroom photos and a
toilet in 7 of 12 bathrooms). So the room check stays as a backup. In workspace mode that
backup is weaker on purpose: 3 of 23 private photos were approved (a bathroom read as
"closet 0.35", one as "bank_vault 0.69", a bedroom as "kennel/outdoor 0.37"), up from 2
before this change. A test fails if that number grows. The strict guard still stops all 23.

**Codex review (same day)** found three ways the new check could let a frame through, all
fixed and tested: after "bed seen, then not seen" the guard resumed before its 3-check window
was done (it now keeps checking every frame until a stop is no longer possible); a broken
NanoDet answer was read as "nothing seen" (it is now a failed check, which stops Ko'z); and a
detection at exactly 0.40 was dropped by OpenCV's box merging (now kept).

## Fly-brain car (demo 1) and classroom counter (demo 2)

To be written.
