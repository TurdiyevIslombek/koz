# Nigoh · selected direction D

One signature: an eye-shaped counting diagram. The rest behaves like an instrument: one large reading, a plain status and a Stop control anchored to the bottom. No marketing surface or entrance choreography.

## Visual tokens (finished look, Oct 22)

Islombek, after the design review: easy to use and understand, cutting edge; it looked too plain,
with text too small and grey, not like a real app. Same direction D (eye, giant reading, Stop bar),
finished. The tokens live at the end of `src/styles.css` ("Visual pass").

| Token | Dark | Light |
|---|---|---|
| Background | `#0b0e0c` | `#f3f2eb` |
| Panel | `#141815` | `#ffffff` |
| Raised (inputs, tiles, active tab) | `#1d221e` | `#eceee5` |
| Main ink | `#f3f2ea` | `#1a201b` |
| Secondary ink | `#a9b0a5` | `#566052` |
| Rule / strong rule | `#262c27` / `#363e37` | `#dfe2d6` / `#c9cdbf` |
| Interactive accent | `#9cb7ff` | `#2348c4` |
| Running / pass | `#a6df8a` | `#2d6a1d` |
| Waiting / warning | `#f1cd70` | `#7a5600` |
| Blocked / fail | `#ff9e8b` | `#a12f1e` |
| Stop (solid) / text | `#cf3f2a` / `#fff` | `#c63a26` / `#fff` |
| Eye lens / rim / floor / figures / line | `#1f2923` / `#4b5e51` / `#364539` / `#c6d0c0` / `#7f9fff` | `#e5eae0` / `#c3cbbb` / `#cbd3c4` / `#6c7866` / `#2348c4` |

- **One level of panels** (20 px radius) instead of thin rules: the status, the reading, the
  diagram, the plan, the trials table, the windows. Panels never nest; tiles inside a panel (entered
  / exited) use the raised surface.
- **The status panel is tinted by its state** (9 % of the state colour over the panel, a 24 % inner
  line) and carries a round icon badge; the instruction ("what to do") sits in its own box; the
  planner is a small chip. Running green, waiting amber, stopped red, unknown neutral.
- **The eye is a dark lens** with bright figures and a vivid counting line (light theme: a pale
  lens with dark figures). On the AWS page it is titled "How Koʻz counts" and a cover label names
  the job state; the local page keeps "What Koʻz sees" with the real picture.
- **App controls:** a segmented tab switch (same weight active or not, so labels never jump or
  wrap), the connection as a pill with a dot, "Connect device" as a pill button, example chips,
  rounded inputs (12–18 px), a solid red Stop (56 px), the bottom bar frosted so content scrolls
  under it, its facts as chips.
- **Text:** nothing under 13 px (`.8125rem`); secondary text only for secondary facts.
- Semantic colours only express state; every state also has words and an icon. No gradients and no
  glows; the one soft shadow is on floating windows. A thick coloured side border is never used.

## Typography and structure

Onest is self-hosted with its OFL. Its native U+02BB is narrower than IBM Plex Sans's spacing-modifier glyph, so **Koʻz**, **Oʻzbek**, and **toʻxtatish** read naturally. No substitution of the user's Unicode text, invisible spacing tricks or negative tracking on labels. UI letter-spacing is zero; headings and large numerical readings have carefully limited tracking. Cyrillic and Latin share the same family.

At 360 px: compact brand/tools, three navigation links, task status, eye, large reading, then supporting counters. The fixed dock keeps camera/privacy state and Stop visible. At desktop: the eye and numerical readout sit side by side; Setup splits input/plan; Trials splits table/evidence. Enlarged text can wrap without horizontal page scrolling. Native form controls, dialogs and details remain keyboard operable.

## Scene and motion

The SVG has organic, rounded body contours and opaque face masks. People fit wholly inside a widened eye. The line and arrow remain geometrically clear. It is explicitly a counting diagram, never a claim that remote silhouettes or a video feed exist in the contract.

A crossing moves one illustrative person for 900 ms in demo mode and briefly pulses the line for 420 ms. Real telemetry pulses on a known increase in cumulative entered count. Reduced-motion users get the changed reading and announcement without movement. No perpetual motion.

## Truthful states

- Measured `0` is printed as zero with its label; unknown shows `—` plus the exact contract reason.
- Empty and unconfigured are different. A coverage gap survives a later known reading.
- Sent/accepted is not applied. Stop stays pending until the runner confirms state.
- Connection loss, or no heartbeat for 3 seconds, means Unknown with an offline reason; never stopped. Old readings are cleared and require a fresh observation after reconnect.
- Checked steps appear only from a recipe event or a locally validated import labelled as needing device validation.
- A synthetic demonstration is labelled on every screen. Real trials are owner-reported, not autonomous claims of success.
- Every Live state says why and what to do, with at most two actions in Stop's place; the first is the obvious one (Stop while anything runs; Try again + New job after a stop; New job after a refusal). A privacy stop names what the guard saw (`fault.seen`) and keeps that reason after a later idle.
- Unknown numbers are a calm muted dash plus "waiting for camera" or "not counting now", never a heavy bar.
- The local eye's picture fills the eye shape (clipped to it) and fades in; closing removes it at once and shows the closed eye with a short reason. Testing shows a 3-second bar and its try number.
- Tapping the open eye shows the same picture nearly full screen (a native modal dialog: Esc or a tap closes it); it closes at once whenever the eye closes. The eye element persists across re-renders, so it never blinks.

Reference research: `design/references.md`. The user's selected direction overrides generic design heuristics that would remove the giant count or the eye.
