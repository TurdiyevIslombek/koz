# Nigoh · selected direction D

One signature: an eye-shaped counting diagram. The rest behaves like an instrument: one large reading, a plain status and a Stop control anchored to the bottom. No marketing surface or entrance choreography.

## Visual tokens

| Token | Dark | Light |
|---|---|---|
| Background | `#141614` | `#f2f1e9` |
| Secondary surface | `#20231f` | `#e8e8df` |
| Main ink | `#f1f0e7` | `#202820` |
| Secondary ink | `#b8bcb3` | `#53604f` |
| Rule | `#454b43` | `#b8bfb1` |
| Interactive accent | `#a8c2ff` | `#254dcc` |
| Running / pass | `#b9d5a8` | `#385b25` |
| Waiting / warning | `#edd28e` | `#785507` |
| Blocked / fail | `#ffc0b2` | `#9d3428` |
| Stop surface / text | `#f1d2c8` / `#602b21` | `#572c23` / `#fff0e8` |

The light palette inherits C's warm paper, gray-green surfaces and a single blue accent. Semantic colors only express state; all states also have words/icons. There are no gradients, glows, shadows or card grids.

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
