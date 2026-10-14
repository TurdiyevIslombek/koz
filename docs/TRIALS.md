# Trial list

Islombek runs and owns these trials (CLAUDE.md: 10 trials per demo, failures recorded).
Each trial is recorded with `begin_trial` / `finish_trial` (contracts/events.md, section 10).
Results go in the trial dashboard; failures are kept, not hidden.

## Privacy guard (demo 3) — draft

Point the camera at each scene, start a job, and record: result (pass/fail), the error
code shown, and how long until it stopped. Use your own home or a place you have
permission to film, with nobody undressed or asleep in view. Ko'z saves no frames.

| # | Scene | Expected |
|---|---|---|
| 1 | Home bathroom: sink and mirror | Refused, `PRIVATE_BATHROOM` |
| 2 | Bathroom: shower or bath visible | Refused, `PRIVATE_BATHROOM` |
| 3 | **Toilet stall** (only the stall walls and the toilet visible) | Refused. Places365 has no toilet class, so this is the hardest case; record what it says |
| 4 | Bedroom, bed visible | Refused, `PRIVATE_BEDROOM` |
| 5 | Child's room or a bed in a corner | Refused, `PRIVATE_BEDROOM` |
| 6 | Wardrobe / changing area | Refused, `PRIVATE_CHANGING_ROOM` |
| 7 | Start in an allowed room, then turn the camera to the bathroom door | Stopped at the next check (within 120 s); record the seconds |
| 8 | Lens covered, or a very dark room | Not approved (`PRIVACY_UNCERTAIN`) |
| 9 | Control: classroom | Approved, job runs |
| 10 | Control: shop, kitchen or living room | Approved, job runs |

The two thresholds in `koz/policy.py` (`SCENE_PRIVATE_SUM_BLOCKS`, `SCENE_MIN_TOP_PROB`)
are proposals; these trials are where they get measured and, if needed, changed.

## Fly-brain car (demo 1) and classroom counter (demo 2)

To be written.
