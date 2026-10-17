# Camera choice verification — 2026-10-16

Implemented `.collab/specs/web-camera-choice.md` against contract sections 8.1 and 10.

- `npm --prefix web run build` passed; `npm --prefix web test`: **36 passed**.
- Strict validation accepts optional unique `mac_camera`, `esp32_cam`, `phone_ip_camera` slots, including `[]`; rejects addresses, duplicates, extra fields and invalid slot values.
- API/WebSocket integration checks both start forms, exact selected slot delivery, and fixed `INVALID_COMMAND` / `UNSUPPORTED_CAPABILITY` rejections.
- `check-browser.mjs` passed in Chromium at 360 × 800: Uzbek/Russian/English labels, light/dark themes, prompt/import starts, reset after a real runner reconnection with a new session, one-slot auto-selection, and omission for empty/legacy statuses. No console exceptions or horizontal overflow.
- Inspected the light/dark Setup captures. The selector is a labelled native control with a 48 px minimum height. Browser evidence: `browser.json`, `setup-light-360.png`, `setup-dark-360.png`.

Run the browser harness with `KOZ_PLAYWRIGHT_MODULE` set to an installed Playwright entry point (or with Playwright available normally): `node web/review/cameras/check-browser.mjs`. It uses a temporary loopback mock runner; no real cameras or motors are accessed.

The web **accepts `status.cameras`**. Claude may enable `--report-cameras`. Physical camera opening and switching remain runner-side validation.
