# Laptop trials — 25 October 2026

Run the laptop tests first; ESP32 camera and robot trials come later. Results belong in
`docs/my_trials.txt`, one line per trial. NOT RUN is a placeholder, never a result.
Replace each line only after Islombek reports the observation or recorded evidence is checked.
Keep failed attempts; a retake is a new, labelled attempt rather than a replacement success.
Islombek explicitly authorized a new laptop testing session after the earlier 13:00 Tashkent stop.

## Setup and recordings

Use the Mac camera, the rules planner, default privacy mode, and no motors. Start from a
well-lit normal room with no bed or toilet visible. Leave the laptop fixed for counting.
The owner website on this same Mac can show its locally blurred camera eye.
The website's planner label must be described honestly as built-in rules, not an AI model.

For demonstration footage, record the website with its eye enlarged: Shift-Command-5 →
Record Selected Portion → select the browser area → Options → Microphone: None → Record.
Stop with the menu-bar recording button. This records the screen while Ko'z uses the camera.
Do not open QuickTime's movie camera at the same time. Save recordings outside the tracked repo,
or inside the already ignored `tests/fixtures/private/` folder. Ko'z itself saves no videos.
Avoid showing login credentials or runner tokens. Keep the full evidence takes, including failures;
the submission can use shorter excerpts with results labelled accurately.

Apple instructions: https://support.apple.com/en-gb/guide/mac-help/mh26782/27/mac/27

## Counter — 10 trials, about 20–30 seconds of movement each

1. Frame yourself from at least the waist up, with room to walk on both sides of the vertical
   middle line. Do one unscored framing check first; stop it before trial 1.
2. Website: Trials & proof → Classroom counter → Begin trial. In Set up a job replace the
   example with `Do'konga kirgan odamlarni sana`. This avoids the school-mode strict room check.
   Choose the Mac camera if shown, then Test it.
3. Wait until Running, stand still on the right of the displayed line for 2 seconds, and note
   the starting IN and OUT values. Initial 3-second agent testing can already count movement,
   so use the difference from these starting values rather than assuming zero.
4. Cross right-to-left in the displayed camera view over about 3 seconds: IN should rise by 1.
   Pause 2 seconds, then cross left-to-right over about 3 seconds: OUT should rise by 1.
   Keep your torso visible continuously; do not hover on the line. Wait 2 seconds for the update.
5. Note both final values, stop the job, and report their differences against truth 1 IN / 1 OUT.
   A correct trial needs both directions right, with no extra counts. An unknown reading is
   unknown, not zero. Start a new job for each trial.
6. Trials & proof → Pass or Fail (Count mismatch when appropriate) → Expected count:
   the initial IN value plus 1 → Record result → Save summary. The website stores the total IN
   count, not the OUT count; report OUT separately for the text log.

Example only: `counter 1: in 1/1 out 1/1, pass, owner reported`.
The notation is Ko'z's measured increment / actual crossings. If only the face is visible,
the person detector can miss you; this is why waist-up framing matters.

## Privacy guard — 12 trials, default mode

Use the same counting prompt so the job can run without needing a ball. No crossings are needed.
For every trial, begin a fresh job in an ordinary view and let it run for 5 seconds. Then introduce
the test view and start timing when the object is clearly visible (or the lens is covered).
Use empty rooms: nobody undressed or asleep. For a sink trial, show the sink plus enough bathroom
context; a kitchen sink is not an equivalent test.

| Trials | View | Procedure and expected outcome |
|---|---|---|
| 1–3 | Toilet | Use three angles/distances. Hold each view for up to 10 seconds; expect a stop. |
| 4–5 | Bathroom sink | Two angles, without the toilet or bed in view; expect a stop. |
| 6–8 | Bed | Three angles/distances; expect a stop. |
| 9–10 | Lens fully covered | Cover after Running; hold up to 10 seconds; expect a stop. |
| 11–12 | Two normal rooms | Run for 30 seconds each; expect no stop. |

Objects are normally checked every 0.5 seconds, rooms every 3 seconds. The object-stop target
is within 1 second, but that is a target, not a measured live result. Record the actual delay:
within 1 s / slower / no stop after 10 s. A room-based stop may take longer. If still running
after 10 seconds, stop manually and record a miss. Count a normal-room refusal as a false stop.
Record the exact banner or fault code and `strict off`. Distinguish stopped-by-policy from a
camera/network error, and a privacy hold from a completed stop. If it stops before you introduce
the target, record that false stop and mark the intended transition not tested.

Example only: `privacy 6: bed, stopped yes, about 1 s, PRIVATE_BEDROOM, strict off, owner reported`.

Use the text file for all 12. The current website offers only 10 slots per category and can label
a correct covered-lens stop or a normal-room run as unknown: its privacy-pass rule requires a
PRIVATE_* fault. Preserve that website outcome separately; it must not replace what you observed.
The timestamp printed as 'after first seen' is measured from model detection, not necessarily
from the moment the object physically entered view. Use the recording to measure physical latency.

## Agent adjustment — 3 trials, about 15–20 seconds each

Type `find the red ball`, with an orange or pink ball already visible against a neutral background.
Keep the whole ball still and well lit during the initial test and any retest. Each evaluation is
3 seconds, with at most 3 rounds; allow roughly 15–20 seconds including startup.
Record the displayed setting change (especially hue_center before → after) and whether the ball
was subsequently found. Check Trials & proof for the observation → change → outcome chain.
Begin a new job from the original prompt each time, so an adjusted recipe is not reused.

Example only: `adjust 1: orange ball, hue 0->13, changed yes, found yes, owner reported`.
If it finds the ball immediately, record `changed no, found yes`; that proves detection, not
adjustment. If it adjusts but still misses, keep that failure. A Running banner alone does not
prove the ball was found: colour jobs can run while waiting for a target.

Only a green ball was available earlier. Red-to-green adjustment is intentionally outside the
tuner's allowed colour range. If no orange/pink ball is available, leave these trials NOT RUN.
The repository's orange-red sample can demonstrate adjustment separately, labelled recorded
synthetic input; it is not a live laptop-camera trial. Pink can also be too pale or already
within the red range, so no adjustment is guaranteed.

## Private face/person clip — 20 seconds, last

Stop the Ko'z job and close its camera view first. QuickTime Player → File → New Movie Recording
→ select the built-in camera → High quality → record 20 seconds → Stop → File → Save.
Save the source as `tests/fixtures/private/face.mov`. QuickTime uses a movie container;
do not merely rename a MOV file to MP4. Codex can convert it locally to `face.mp4`, remove audio,
and verify decoding once the recording exists. This folder is already git-ignored.

Frame face AND torso (waist up) for most of the clip, slowly turning or moving slightly.
The existing test using this file measures person detection in at least half the frames;
a face-only close-up would not fairly test it. It does not, by itself, verify face blurring.
This unblurred fixture stays private and is not submission footage.

Apple instructions: https://support.apple.com/en-gb/guide/quicktime-player/qtp356b55534/mac

## What gets saved

The website receives numeric events and fixed states. Clicking Begin trial before a job and
Record result afterwards creates a trial result; Save summary retains its summary. It cannot
observe the ground truth, exact physical stop latency, or your intended actions. The text file
therefore records owner observations alongside any verified software evidence. No live results
have been measured for this new test session yet.
