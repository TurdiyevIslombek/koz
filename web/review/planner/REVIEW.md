# Planner and restart review · 2026-10-16

Implemented `.collab/specs/web-planner-and-live.md` in `web/` only.

- `status.planner`: rules, ollama, nebius, null, and the legacy missing field accepted through the real WebSocket → server → snapshot/SSE → browser path. Unknown fields and invalid planner values remain rejected. Missing is labelled “not reported”; null is “not determined”. Both Setup and Live show the report in Uzbek, Russian, and English.
- Setup disclosure: local processing for rules/Gemma, the existing Nebius disclosure for nebius, and “depends on the planner” for null/missing/stale status.
- Colour-only recipes with no robot brain show the target inside the existing Nigoh eye. Left/center/right move the marker; lost/unknown remove it. No counting line, entry arrow, people or counting-specific copy appears. Only `line_counter` enables the counting view. Positions disappear when outputs are held or disconnected.
- A tab stayed open through an actual web server restart. It showed reconnecting/Unknown, renewed the local owner session, preserved the Setup draft, and waited for a fresh measurement before showing zero. A restart with password protection requested sign-in and recovered after login. No commands were replayed.
- Persisted history after restart retains its original receipt times; the latest status is not misrepresented as an invalid epoch-zero event or a fresh measurement.

Validation: `npm --prefix web test` **32/32 passed**; build passed. Chromium at 360 × 800 checked all planner labels/disclosures in three languages, five target states in light/dark, no horizontal overflow, and no JavaScript errors. Inspected the saved target screenshots. These are synthetic contract events, not hardware/camera measurements.

Artifacts: `browser.json`, `target-dark-360.png`, `target-light-360.png`, `setup-light-360.png`. `check-browser.mjs` reproduces the browser check with temporary loopback servers, after `npm --prefix web run build`. It uses an installed Playwright and Chromium; set `KOZ_PLAYWRIGHT_MODULE` to an existing Playwright module path if it is outside this project. Run `node web/review/planner/check-browser.mjs`.
