# Video: shot list (under 3 minutes)

Target **2:45** (the competition allows 5:00; you asked for under 3). About 350 spoken words in
English; the typing on screen is in Uzbek, with an English caption under it. Say only numbers
that are measured (`docs/TRIALS.md`); the car numbers are TODO until Sunday's trials.

## Where: never the bedroom

- **Every shot is filmed outside your bedroom**: kitchen, living room, hallway, the yard. The
  laptop's camera sees what the screen recording shows, so do the screen recordings at the kitchen
  table too, not at your desk (the guard would also stop there).
- **People:** only adults who agreed to be in the video, even blurred (family, friends 18+). No
  children: school mode needs the school's consent, which a video can't show.
- **Bathroom shot:** your own bathroom, empty, door open, nobody inside.
- **Shot 3 uses the shop sentence, not the teacher's.** The teacher's sentence turns on school mode,
  which always uses the strict guard: at home it stops ("not a listed public place"). Use the
  teacher's sentence only in a real classroom, with the school's permission.
- **Never on screen:** `.env`, the runner token, the owner password, a Terminal that printed them.
  The AWS address (`https://<IP>`) may be shown.
- The car demo uses the dashboard on the laptop (`start-koz.command`): the Mac is on the ESP32-CAM's
  own Wi-Fi, so it has no internet then. The AWS dashboard is shown in shots 2–5, on home Wi-Fi.

## Before filming

- [ ] Latest code; `start-koz.command` (local) or the runner with `--cloud` (AWS, `docs/AWS_DAY.md`
      step 8) works; you did one full practice run.
- [ ] A red ball, an orange-red ball (for the adjust shot), two adult volunteers.
- [ ] Screen: `Cmd + Shift + 5` → **Record Selected Portion** around the browser (the camera view is in
      its eye). Phone on a stand (or a friend) for the car and the doorway.
- [ ] Do Not Disturb on (no notifications in the recording).

## Shots

| # | Time | Camera / screen shows | You type or do | You say |
|---|---|---|---|---|
| 1 | 0:00–0:10 | **Phone:** the car on the floor turns toward the red ball and drives to it | Nothing (use the best take from Sunday's trials) | "This car has no program for chasing a ball. A simulated fruit-fly brain drives it, and I gave it the job in one sentence." |
| 2 | 0:10–0:28 | **You**, in the living room, ESP32-CAM in your hand | — | "Cameras cost ten dollars now. But making one do a job — count people, find something, drive a robot — still needs a programmer. And an AI that writes camera code freely can be talked into spying. Ko'z, Uzbek for 'eye', works differently." |
| 3 | 0:28–0:50 | **Screen:** the web app's Setup page (the `https://` address visible); the plan appears in Uzbek; the recipe steps show privacy guard → face blur → person detector → line counter | Type **Do'konga kirgan odamlarni sana** (caption: "Count the people who come into my shop") → **Test** | "I describe the job in Uzbek, Russian or English. The AI can only choose from a menu of tested OpenCV 5 blocks, and the privacy guard and face blur are locked into every recipe. No sentence can remove them." |
| 4 | 0:50–1:12 | **Phone at a doorway** (kitchen or hallway) + **screen:** the runner window with pixelated faces and the line; the Live page counting *entered 1, 2* | Two volunteers walk through, one after the other, crossing the middle of the view **from right to left** (that direction counts as entered) | "OpenCV 5 runs three neural networks on this laptop, with no GPU. Faces are pixelated before any block sees them. Only numbers go to the cloud on AWS: what Ko'z sends has no field for a picture." |
| 5 | 1:12–1:35 | **Screen:** the orange-red ball on the kitchen table; the Trials page shows the chain: not found → `hue_center` changed → found | Type **Qizil koptokni top** ("Find the red ball") | "When a check fails, the agent reads what OpenCV measured, changes one setting and tries again, at most three times. Here it moved the colour it looks for to the ball's real colour." *(Say only what the screen shows.)* |
| 6 | 1:35–1:58 | **Screen + laptop carried** from the kitchen to the open bathroom door: the runner window's red banner "a toilet is in view", the web shows "Bathroom view blocked." | Walk to the bathroom door with the laptop, camera facing in | "If the camera turns toward a bathroom, Ko'z stops by itself. It stops on what it sees: a toilet, a bed, a covered lens. It's an alarm, not proof: on 71 real photos the default let 4 of 23 private rooms through; strict mode, for schools, stopped all 23." |
| 7 | 1:58–2:10 | **Screen:** Setup shows the refusal "Odamlarni tanib olish taqiqlangan." (Identifying people is not allowed); the camera never turns on | Type **Bu odam kimligini aniqla** ("Find out who this person is") | "Some jobs it refuses before the camera even opens: who someone is, hidden cameras, age or gender." |
| 8 | 2:10–2:35 | **Screen** (laptop dashboard): you press **Enter** in the Terminal to arm the motors, then Setup with the plan in Uzbek. **Phone:** the car chases the ball and stops before the wall | Press **Enter** in the Terminal (arms the motors), then type **Qizil koptokni quv** ("Chase the red ball") → **Test** | "Same Ko'z, different blocks: the colour finder, then 2,282 neurons from the fly's real wiring diagram. Ko'z shows the fly a threat on the side away from the ball, and its escape reflex turns it toward the ball. Only a person can switch the motors on, and they stop by themselves. In ten trials it reached the ball **TODO** times." |
| 9 | 2:35–2:45 | **Screen:** `docs/architecture.svg`, then the AWS dashboard on your phone | — | "Frames never leave the device; the cloud gets numbers. Anyone with the same camera can import the recipe. Ko'z: tell a camera what job to do." |

If shot 5 finds the ball without any adjustment, keep that take and change the line to "It found
it on the first try"; don't stage a failure. If the car misses in shot 8, show a miss honestly or
use the best real take, and say the measured number.

## After filming

- Edit in iMovie (or CapCut): cut the shots together, add the English captions for the Uzbek
  typing, music low or none. Check the length is under **3:00**.
- Watch it once only for privacy: no unblurred face, no `.env`, token or password, nothing from
  the bedroom.
- Export 1080p and upload where the competition asks (Devpost takes a YouTube, Vimeo or Youku
  link). Public or unlisted is your decision. Send Claude the link for the report.
