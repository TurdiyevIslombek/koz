# Live screen: every state (UX pass, Oct 18)

Islombek tested the web app live: it worked but confused him (stuck after a privacy stop, a vague
reason, two camera views, jargon). Claude owned `web/` for this pass. Design skill: impeccable
(polish); "taste" is not installed on this Mac. Brief: `docs/DESIGN.md`; system: `web/DESIGN.md`.

The contact sheets here show each state in Uzbek | Russian | English at 360 px, light and dark
(`<state>-<theme>.jpg`). Every state is real: `scripts/ui_states.py` runs the real Hub, agent loop,
runner and eye with scripted fakes (planner, guard, a DRAWN camera picture; nothing filmed), and
`shoot.mjs` drives Chrome, starting jobs from Setup and pressing Stop / Try again like a person.

```bash
cd web && npm run build && node server/index.mjs
```
```bash
node web/review/states/shoot.mjs /tmp/koz-shots
```
```bash
.venv/bin/python web/review/states/sheets.py /tmp/koz-shots
```
(`KOZ_SHOOT_WIDTH=1280` for desktop; extra arguments pick states.)

## Before → after

| # | Before | After |
|---|---|---|
| 1 | After a privacy stop Stop was greyed out and nothing could be done | Every state says **why** and **what to do**, with one obvious action where Stop always was: privacy stop → "A bed is in view. Point the camera away, then press Try again." + **Try again** / **New job**; refused → **New job** only; idle → **New job**; running, testing, planning, checking, camera lost → **Stop** |
| 2 | The web said "The device reported the job stopped" while the runner window said "this looks like a bedroom" | The runner sends `fault.seen` (bed / toilet / sink, contract 8.6); the web says "A bed is in view." or "This looks like a bedroom.", the runner window's words, in Uz/Ru/En. The reason now survives the `idle` that a later Stop or q sends (that idle was what erased it) |
| 3 | Two camera views (runner window + web eye) | `start-koz.command` opens no runner window (`KOZ_WINDOW=1` brings it back). The runner reads the launcher's Terminal, so **Enter there arms a car's motors**; before, it read an empty input and Enter did nothing. The web only shows how to arm |
| 4 | "Motors" on every job, an unexplained → by the title, "Evaluation measurement", "Request accepted", "Since job start · crossings", "people · Unknown" | Motors only for car jobs (with how to arm). No arrow. "Numbers from the test…", "The camera computer got it.", "Counted since the job started.", "people in view now · waiting for camera / just now / nobody in view" |
| 5 | An unknown count was a huge black bar | A calm, muted dash with "waiting for camera" (live) or "not counting now" (stopped) |
| 6 | The eye showed a small rectangle inside the eye | The picture fills the eye, clipped to its shape, fading in; closing removes it at once (no last frame) and shows a closed eye with a short reason ("Closed for privacy", "Checking the view", "Opens when the test starts"). No bounce |
| 7 | "Evaluating" | "Testing the setup… 2 s" with a 3-second bar and "Try 1 of 3", then "Checking the result…", then "Running" |

Also found by the screenshots and fixed: the Russian tab «Испытания и доказательства» broke mid-word
(now «Испытания»); «Попробовать снова» and the Uzbek "Qayta urinish" wrapped in the dock (now
«Повторить», equal-width buttons, no icon in the two-button row); the Russian countdown split
"2 / с"; "Plan by: not determined" showed before any plan; the dock said "on hold" / "unknown" for an
idle camera (now only "Camera off", and "checking" while confirming); "The camera computer got it."
stayed during the test (a start now settles when the job's planning/test status arrives); judges'
read-only view no longer shows "press Try again".

## Checks

- Every state reached in all 6 language/theme combinations (`shots.json` of each run), plus desktop
  (1280 px) for the privacy stop.
- impeccable detector: one finding, the eye's `<img>` without `src`: intentional (it stays `hidden`
  until a frame arrives, so no broken image shows).
- Contrast of new elements against the tokens: the closed-eye reason on dark ≈ 4.9:1, the muted dash
  and the motor hint above 4.5:1; buttons reuse the existing accent / stop tokens.
- Tests: `web/test/ux.test.mjs` (states, reasons, actions, the model keeping the reason, texts in
  three languages), `tests/test_runner.py` (fault.seen), `tests/test_live_demo.py` (launcher).
