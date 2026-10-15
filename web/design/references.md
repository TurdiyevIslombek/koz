# Interface references · 14 October 2026

These are observations from public product interfaces, screenshots, and first-party explanations, not claims about a logged-in account. The patterns below informed the mockups; no brand, layout, camera footage, or product asset was copied.

1. **[UniFi Protect](https://blog.ui.com/article/introducing-protect-7-0)** ([interface screenshot](https://cdn.blog.svc.ui.com/Protect_7_02_03ac06b291.jpg))  
   Clear grouping lets an operator distinguish the current view from supporting system information.  
   Apply that hierarchy to counts and protections; Koʻz's web contract excludes its video grid, identities, audio, and person filters.

2. **[Apple Home cameras](https://support.apple.com/guide/iphone/set-up-security-cameras-iph7bc5df9d9/ios)**  
   Camera names and freshness cues sit close to the thing being monitored; the phone view has a straightforward vertical reading order.  
   Keep the job name, state, and current count together, with concise labels and predictable controls.

3. **[Google Home / Nest live view](https://support.google.com/googlehome/answer/10065055?hl=en)**  
   The interface distinguishes a thumbnail from a live view, and offline from off, rather than treating every image as current.  
   Koʻz uses the same clarity of meaning: disconnected is “Nomaʼlum,” with a dash and unknown protection states.

4. **[Linear's interface refresh](https://linear.app/now/behind-the-latest-design-refresh)**  
   Supporting navigation recedes, and consistent action placement reduces searching; fewer separators leave the work visually dominant.  
   A applies this through open space and a quiet header; both keep Stop in a fixed bottom dock.

5. **[Stripe Dashboard](https://docs.stripe.com/dashboard/basics)**  
   The overview puts business numbers and items needing attention together, with deeper management elsewhere.  
   Keep Koʻz's current reading prominent and its meaning explicit; recipe steps can sit behind a disclosure.

6. **[Vercel project overview](https://vercel.com/changelog/preview-firewall-status-and-web-analytics-from-project-overview)**  
   Protection status and traffic summaries are visible at overview level; warnings are placed alongside the relevant system.  
   B uses compact aligned sections for readings and protection checks, without importing an engineering console's extra controls.

7. **[Apple Weather](https://support.apple.com/guide/iphone/check-the-weather-iph1ac0b35f/ios)**  
   A large current reading is understandable before the supporting details, with a clear progression down the phone screen.  
   A borrows that hierarchy for an actual measurement, omitting weather backgrounds, gradients, and decorative charts.

## Installed skill discovery and application

Searched installed `SKILL.md` files under `.agents/skills`, `.codex/skills`, `.claude/skills`, and the plugin cache. Neither “taste” nor “impeccable” was present under those names. Relevant installed alternatives included **design**, **ui-ux-pro-max**, **design-system**, **ui-styling**, **brand**, **accessibility**, and **web-quality-audit**.

Read and applied:

- `~/.claude/skills/design/SKILL.md`: choose the applicable UI discipline and keep icon treatment consistent.
- `~/.claude/skills/ui-ux-pro-max/SKILL.md`: ran its required design-system search and UX validation search; applied its visual, interaction, theme, and pre-delivery review checklists to each mockup.
- `~/.agents/skills/accessibility/SKILL.md`: semantic controls, labels, keyboard focus, contrast, reflow, and reduced motion.
- Sites' local-only workflow: buildless HTML, local preview and browser verification, no registration or publication.

The search's generic landing-page, glow, dark-only, and React Native suggestions conflict with this task. The user's static-HTML scope and `docs/DESIGN.md` take precedence. No animation library or framework was added.

## Round 1 typography (superseded by the Round 2 correction below)

**A: Golos Text.** Open shapes and a softer rhythm support a familiar, calm display. **B: IBM Plex Sans.** Narrower proportions and a firmer rhythm support the information-board direction. **Both: JetBrains Mono** for stable, legible numerical readings.

All three font files and their OFL licenses are bundled locally. Their Cyrillic coverage was checked against “Камера включена.” A cmap inspection found U+02BB missing from Golos Text and JetBrains Mono, so explicit font fallback stacks use the bundled IBM Plex Sans glyph for that code point. Both composite families therefore render the exact “Oʻzbekiston, gʻisht, sh, ch” without depending on an installed system font. Each page includes a font proof disclosure with both required strings in body and numerical families.

## Contract choices

- Only the Live job screen, a generic counting job, and presentation fixtures. No application shell, setup chat, trials, export/import, login, networking, storage, or deployment.
- Job title is mockup UI copy, not a place name or persisted user prompt from telemetry. Counts are illustrative, not measured trial evidence.
- `occupancy` is the current count. Entered/exited are cumulative **crossings since the current job began**, not unique people, attendance, or daily totals.
- Known zero is explicitly measured; unavailable current values are dashes. A sample with a gap labels the crossing totals incomplete.
- Paused is a scheduled privacy check. Blocked uses the contract's fixed bathroom fault message verbatim in all three languages. Protections never remain approved when the preview is offline.
- A stop request alone stays pending. The stopped fixture explicitly represents a later device status with camera capture off; no stop request is assumed to turn off capture.
- No remote video preview, identities, person boxes, safety toggles, unsupported features, or fabricated evaluation results.

## Round 2 — signature, not a SaaS skin

Browsed on 14 October 2026. These seven references were inspected in a browser, including their rendered pages. The observations below describe what was visible, not an assertion that every gallery entry was reviewed. No layouts, logos, code or media were copied.

| Reference | One idea taken | Translation into Koʻz |
|---|---|---|
| [Awwwards — Sites of the Day](https://www.awwwards.com/websites/sites_of_the_day/) | In the visible Huy Phan Vol.2 and Neutomni previews, the large type and a single strong graphic mass establish an identity before the smaller text. | Give the count a decisive scale and pair it with one recognisable scene shape. No marketing header or decorative card grid. |
| [Godly](https://godly.website/) → [Recent](https://recent.design/?ref=godly) | Godly currently redirects to Recent. Its Dessn branded UI preview shows a functional interface can carry a distinct visual world without changing the task. | Put Koʻz's personality into the view itself, while language selection and Stop remain familiar controls. |
| [Land-book](https://land-book.com/) | The gallery explicitly separates mobile compositions from whole websites; the visible mobile preview makes one statement in a narrow frame. | Compose a real 360 px screen: scene, state, large number; then let the supporting totals scroll. Desktop becomes two columns instead of a stretched phone. |
| [Igloo Inc.](https://www.igloo.inc/) | One spatial object owns the screen, and the surrounding controls are sparse. The central object carries the identity. | D's eye-shaped aperture is the single signature object. Keep the spatial storytelling inside the small scene; no 3D engine or scroll takeover. |
| [Anime.js](https://animejs.com/) | The homepage's coordinated mechanism and SVG examples make motion explain relationships between parts. | A silhouette crosses the counting line; exactly at the crossing, the count changes and the line pulses for 420 ms. No idle loop or animated number roulette. |
| [Teenage Engineering](https://teenage.engineering/) | The homepage's functional outline symbols and stark store signage feel physical and intentional, with very little interface chrome. | Draw the scene, masks and controls with a consistent line language. C's threshold acts like a marked doorway; controls stay direct and legible. |
| [Nothing](https://nothing.tech/) | The visible postal campaign carries a signature graphic language through the object and labels while navigation stays simple. | Use one recognisable shape for D's viewing aperture. Keep normal readable Onest for every Uzbek label; do not borrow Nothing's dotted lettering. |

### Two arguments

- **C · Ostona (threshold):** because the job counts a doorway crossing, the counting boundary becomes the visual anchor. A rectangular field preserves the widest view and puts a visible threshold before the readout.
- **D · Nigoh (gaze):** because Koʻz means “eye”, the privacy-safe field of view becomes an eye-shaped aperture. The oversized number balances the shape; there are no other brand ornaments.
- Both retain A's giant current count, explicit status/reason, and fixed Stop. Light is useful in a bright shop; dark is available for evening use. State colors remain reserved for status and Stop; blue marks the counting boundary and the sample action.

### Typography correction

The earlier fallback was technically complete but visually wrong. IBM Plex Sans assigns U+02BB a **0.600 em** advance. Onest natively covers the character with a **0.261 em** advance, the same as its normal left quotation mark. C and D use the locally bundled Onest variable font for all text and tabular numbers. A and B's interface text also now uses Onest; their existing numerical font falls back to Onest for Uzbek characters.

No Unicode replacement, inserted spacing, per-letter spans or negative-margin patch is used. “Koʻz”, “Oʻzbek”, “toʻxtatish”, “Oʻzbekiston, gʻisht, sh, ch” and “Камера включена” are included in each page's font proof. The original font is unmodified, with its [OFL license](assets/onest-OFL.txt) and [upstream source](https://github.com/google/fonts/tree/main/ofl/onest).

### Preview boundary

The view is an original, static SVG illustration with a user-triggered crossing. It is visibly labelled **SVG namuna**, and the review disclosure says no camera is connected. The few silhouettes represent the doorway crop, not all seven people in the counted area. Solid face rectangles are drawn over every silhouette; there are no real faces, names, identity boxes, photos or tracking IDs.

The existing cloud contract carries aggregates and fixed labels only, and specifically excludes images, tracks and coordinates. These files add no data transport and require no contract changes. A production moving view would need to stay on the local device or be separately agreed before implementation. A privacy mask alone is not permission to send images or silhouettes to the cloud. The judges' landing page remains out of scope.

### Audit method

Read the official [Taste skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md) and its screenshot critique, plus [Impeccable](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md)'s audit, craft floor and Operate guidance. Neither skill's launcher/detector is installed locally, so no official CLI pass is claimed. Apply their review criteria with browser evidence, a numerical contrast checker and axe-core instead.

Taste v2 explicitly excludes app screens: its marketing requirements for four photographs and extensive motion do not apply to this Live job screen. Its hierarchy, specificity, typography, mobile composition and collision checks do. Impeccable's Operate mode and the user's exact two-mockup request govern; no concept lottery, marketing page, framework, publication or real app was built. Audit results and visual critique are in [the Round 2 review](review/round2/REVIEW.md).
