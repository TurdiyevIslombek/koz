# Ko'z design brief

Read this before any UI work in `web/`. The bar: it must look like a real product a careful team shipped, not like AI output.

## Who uses it
A shop owner in a bazaar, a teacher, a farmer, a student with a robot kit. Mostly non-technical, often on a phone, often in Uzbek. They want one thing: "is my camera doing its job right now?"

## The three screens (MVP)
1. **Setup chat.** Describe the job in Uzbek, Russian or English → Ko'z answers with a plain-language plan ("I will count people crossing the door line. Faces are blurred. Nothing is saved as video.") → one button: "Test it". Show the recipe as readable steps, never raw JSON (JSON only behind "Show details").
2. **Live job.** The single most important screen. Big, calm status: Running / Paused / Stopped / Unknown, with the reason in one sentence. The current number (people counted, ball found) large. Privacy state always visible (guard approved, faces blurred, camera on). Stop button always in the same place.
3. **Trials & proof.** The table of trials (pass/fail, duration, error code in plain words) and the agent's adjust chain: observation → decision → new setting → result. This screen is for judges; it must make the Agentic Vision loop obvious in 10 seconds.
Plus: recipe export/import (a file), language switch (Oʻzbek / Русский / English).

## Hard rules against "AI slop"
- No purple/blue gradients, no glowing orbs, no glassmorphism, no emoji as icons, no stock "AI brain" imagery, no hero sections. This is a tool; it opens on the job.
- No generic "Inter + rounded-lg + soft shadow everywhere" look. Borders and shadows only where they separate something.
- Copy is short, plain and specific. Buttons say what happens ("Test it", "Stop camera", "Export recipe"). No "Unleash", "Supercharge", "AI-powered magic".
- Every number shows its state: a measured 0 looks different from Unknown (a dash plus "camera not answering").
- Real content in every mockup (real Uzbek and Russian text, real counts), never lorem ipsum.

## Must-haves
- **Fonts must cover Uzbek Latin and Cyrillic.** Test these exact strings: "Oʻzbekiston, gʻisht, sh, ch" (with ʻ U+02BB) and "Камера включена". Candidates with Cyrillic: Golos Text, Onest, Manrope, IBM Plex Sans; a mono with Cyrillic for numbers (JetBrains Mono). Choose and justify.
- Status colors mean something and are used for nothing else: running, paused/warning, stopped/blocked, unknown (neutral). Pass WCAG AA contrast. Never color alone: always an icon or word too.
- Light and dark themes.
- Works at phone width (360 px) first, then desktop.
- Uzbek text runs ~20–30% longer than English: no fixed-width buttons that break.
- Calm motion only: status changes may fade; nothing bounces.

## Personality
Trustworthy, calm, local. Think of a well-made instrument (a scale in a bazaar, a good thermometer), not a sci-fi dashboard. One accent color; the rest neutral. A small touch of identity is welcome (the name Ko'z, the eye), not decoration everywhere.

## Tools to use
- **Design skills installed on this Mac** (Islombek added design-quality skills such as "taste" and "impeccable"): load and follow them before designing, and run their review/audit step on every mockup before showing it. If a name differs, list the installed skills and use the design ones.
- **Look at real products first, then design.** Search the web for 5–8 real interfaces in this space and write 2 lines on what each does well: camera/security apps (UniFi Protect, Apple Home cameras, Nest), calm tool UIs (Linear, Stripe dashboard, Vercel), status-first displays (Apple Weather, airport boards). Collections such as Mobbin, Refero or Godly are fine for browsing. Save the notes in `web/design/references.md`. Learn patterns; never copy a layout, logo or brand.
- Check contrast with a real contrast checker, and look at each mockup at 360 px and in dark mode before calling it done.

## Process
1. Codex: make **two different directions** as static HTML mockups of the Live job screen only, in `web/design/direction-a.html` and `direction-b.html`, with real Uzbek text and both themes. Explain each in 3 lines.
2. Islombek picks one (or mixes).
3. Codex builds all three screens in that direction. Claude reviews contrast, language coverage, phone width and the Unknown/0 states with `/collab-review`.
