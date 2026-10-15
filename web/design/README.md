# Koʻz · Live job design directions

Step 1 only. Open `direction-a.html` or `direction-b.html` directly in a browser; all fonts and assets are local. The files share `mockup.css` and `mockup.js`, so keep this directory together. No installation or build is needed.

## A · Tarozi

Warm paper tones, open space, and a large measurement give it the calm of a familiar instrument.  
Golos Text softens the labels; the status and its reason come before supporting counts.  
Best for a shop owner or teacher checking one job on a phone.

## B · Tablo

A compact information board with a dark numerical readout, firm rules, and aligned readings.  
IBM Plex Sans and JetBrains Mono make it feel precise; protection checks sit beside the readings on desktop.  
Best for someone who prefers a denser operational view.

**Recommendation: A.** Its simpler hierarchy answers “is my camera doing its job?” with less visual effort for the intended non-technical phone users. B is a credible alternative if precision and density matter more.

## Preview controls

Both directions start in Uzbek and follow the system theme. The top bar switches direction and light/dark theme; the language menu previews Uzbek, Russian, and English. “Namuna holati” below the Live screen switches running, measured zero, privacy checking, device-confirmed stopped, blocked, offline/unknown, incomplete counts, and pending stop.

The Stop button only previews a pending request. It never contacts a device. Select “Toʻxtatilgan · qurilma tasdiqlagan” to inspect the confirmed stopped fixture. The camera, guard, and blur summary stays visible in the bottom dock while scrolling.

Optional URL parameters: `?theme=dark&lang=uz&state=unknown`. Valid states: `running`, `zero`, `paused`, `stopped`, `blocked`, `unknown`, `gap`, `pending`.

References and typography decisions: [references.md](references.md). Review results and screenshots: [review/](review/).

## Contribution record

2026-10-14 · Codex · Read `CLAUDE.md`, `docs/DESIGN.md`, and both contracts; researched references; created and reviewed two static Live job directions. Islombek's direction choice is pending. Real application work has not started.

This contribution record is inside `web/` because the task explicitly limits edits to that lane. Root `AI_LOG.md` and the pre-existing change to `docs/DESIGN.md` were left untouched. No checkpoint commit was made because the current request is design-only and no files outside `web/` were to be modified.

## Round 2

Open `direction-c.html` (Ostona) or `direction-d.html` (Nigoh). Each is a static Live job mockup with light/dark themes and Uzbek/Russian/English. `?theme=light` or `?theme=dark` picks a theme; the top controls change it. “Oʻtishni koʻrsatish” plays one synthetic SVG crossing and updates the sample count. Reduced motion updates the result without moving or pulsing.

“Maketni tekshirish” exposes sample states and the Unicode font proof. Stop previews a pending request; it never pretends a device has confirmed a stop. A/B remain for comparison, with the U+02BB font fix applied.

The design decision and research are in `references.md`; review evidence is in `review/round2/`. No live camera, API, storage, setup, landing page or application was added. All changes for this round stay in `web/`.
