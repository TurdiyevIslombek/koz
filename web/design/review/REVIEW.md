# Mockup review · 14 October 2026

Scope: the two static Live job directions. This is a design review, not a claim that the camera system or real app has been built or tested.

## Results

- **96 browser cases** across A/B, light/dark, 8 sample states, Uzbek/Russian/English, 360×800, 375×812, 800×360 landscape, 768×1024, and 1440×960. The matrix also includes 200% text-size stress cases. No horizontal overflow or JavaScript errors in the final run.
- **axe-core 4.10.3:** zero reported WCAG A/AA violations in 32 direction/theme/state combinations. Some contrast checks were marked incomplete by axe, so explicit foreground/background calculations supplemented the result; this is not a full conformance certification.
- **48 contrast pairs:** all meet their threshold. Lowest checked text contrast is **5.37:1**; lowest checked control outline contrast is **4.11:1**. Text target: 4.5:1; non-text control boundary target: 3:1. Exact values are in `audit.json`.
- **Keyboard:** visible skip link, visible focus ring, and Space activation of the theme button passed in both directions. Native links, selects, buttons, and disclosures retain keyboard semantics.
- **Extra narrow width:** both directions also fit at 320 px. Both files open directly via `file://`, without a server, installation, or build.
- **Fonts:** inspected font character maps and actual Chromium rendered-font attribution. Golos Text and JetBrains Mono render their own Latin/Cyrillic; bundled IBM Plex supplies missing U+02BB through the fallback stacks. No system font is used for either prescribed test string in the inspected A body/mono samples. Font-proof screenshots were visually inspected for both directions and both themes.
- **Motion:** no animation, polling, flashing status dot, or auto-changing mock data. Reduced-motion media is respected.

## Direction A review

The warm surface and larger reading establish a clear status → reason → count order. Status is expressed through a word and symbol, and the fixed footer keeps camera, guard, blur, and Stop available while scrolling. At 360 px the current count fits above the footer; secondary readings and context remain vertically scrollable. No gradients, shadows, hero section, or nested card grid.

The selected type hierarchy, muted copy, and all four status colors were checked in light and dark modes. Long translated labels wrap, and the design toolbar now wraps at enlarged text sizes. A is the recommended direction for the broad, non-technical audience.

## Direction B review

The rectangular status panel, dark readout, tabular numbers, and divided crossing cells make a visibly different operational instrument. It presents more readings together on a phone and uses a separate protection column on desktop. The reading surface stays dark in the light theme, deliberately giving numbers a defined physical location.

The compact spacing was checked at 360 px in both themes and in Russian. The count is never differentiated by color alone; the same measurement wording and unavailable-state rules apply. B is the stronger choice for a user who values density.

## State and contract review

- Measured zero uses `0` and an explicit measurement label; current unknown values use `—` and a cause.
- Offline does not claim stopped and does not leave the camera, privacy guard, or face blur visibly confirmed.
- Privacy rechecking is a pause. A privacy block uses the fixed contract error message.
- Incomplete coverage is labelled next to the cumulative crossing counts.
- A Stop click changes only the request feedback to pending. The job remains Running until an explicit device-confirmed sample state is chosen.
- No remote preview, unsupported capabilities, identity data, raw JSON, protection switches, or fabricated evaluation evidence.

## Corrections made during review

1. Reduced phone spacing in B to make the secondary counts easier to see.
2. Fixed A's enlarged-text toolbar overflow and reserved room for action feedback.
3. Corrected font fallback declarations after inspecting actual rendered fonts; refreshed all screenshots and reran the affected layout/contrast checks.
4. Kept a persistent, visible static-mockup label and explained sample-only controls.

## Evidence and limits

`comparison.html` / `comparison.png` show the two directions in both themes. The other PNG files capture phone states, desktop layouts, Cyrillic content, and font proofs. `audit.json` and `keyboard.json` contain the measurements.

Applied the installed UI/UX Pro Max pre-delivery checklist and Accessibility testing guidance to both directions. Screen-reader output, Safari, physical phone hardware, and real camera behavior were not tested. The user still needs to choose a direction before any real application implementation.
