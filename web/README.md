# Koʻz web · Nigoh

The selected D direction, built as three working screens: Setup, Live job, and Trials & proof. Uzbek, Russian, English; warm light and dark themes; local Onest font. All implementation and tests live in `web/`.

## Open without Terminal

Double-click **`open-web.command` in the project root**. It finds Node on the usual macOS paths, installs the pinned dependencies if needed, builds the app, starts the local server and opens the browser. Opening it again reuses this checkout's running server. It does not replace another service on the web port.

The launcher is the sole explicitly requested file outside `web/`. The application and launcher implementation remain inside `web/`. Node 22+ is required; a missing runtime or failed startup produces a dialog. Startup diagnostics go to ignored `web/.data/startup.log`, never camera data or prompts.

In the app, click **Yozuvni qayta koʻrish / Replay recording**. The recorded fixture shows measured zero, entries, a privacy stop, then a complete red-ball adjustment. Open **Trials & proof** for the chain. **Disconnect replay** stops the owned fake server and immediately makes the live view Unknown. To replay again while connected, use **Local runner → Replay again**.

For the real device, disconnect the replay and start Claude's runner at **`ws://127.0.0.1:8765`**. The app connects automatically; no page reload is needed. A service already on that port is never killed or replaced by the fake server.

## Development commands

```sh
cd web
npm ci
npm run dev
npm test
```

The browser uses `http://127.0.0.1:4173`. `npm run fake-runner` optionally runs the same fixture server separately on port 8765; the UI's replay button normally handles this for you. Close a separately launched fake server from its own process before starting the real runner. `npm run build` regenerates the validator and fixed messages from the read-only shared contract files.

`web/.env` may set `PORT` or `KOZ_OWNER_PASSWORD`. Without a password, the loopback-only development app creates an HttpOnly, SameSite owner session automatically. Cross-origin mutations are rejected. If a password is configured, the normal sign-in remains required. This local convenience is not a public/cloud authentication configuration.

## Runner connection

The web server is now a WebSocket **client** of `ws://127.0.0.1:8765`; browser updates use the existing same-origin event stream. This follows the owner's explicit local-transport request, overriding the connection direction in contract section 5 for this development mode. The event and command JSON formats are unchanged, and no files in `contracts/`, `koz/` or `firmware/` were edited.

- The runner sends a contract `status` first, then a heartbeat every second. All seven event types use the existing strict decoder, schema and fixed messages.
- `start_job`, `stop_job`, `begin_trial` and `finish_trial` go back on **the same WebSocket**, with web-generated IDs, the current session and a ten-second expiry. Accepted means delivery, not applied state.
- Socket close or browser event-stream failure clears live readings immediately. Three seconds without status also clears them. Heading: **Unknown**; reason: **Offline — job state unknown**. The recipe/history can remain available, but old live numbers cannot return when the socket reconnects. A new observation is required.
- Retry is once per second. There is no command queue, replay on reconnect, automatic job start or motor re-arm.
- The original token-authenticated inbound adapter remains available through `createApplication` for existing integration tests, but normal `npm start` uses the requested outbound local connection.

The fake server reads `fixtures/runner-session.json`, an explicitly **synthetic recorded wire fixture**, not a measured camera trial. Replay timing is recorded separately from the exact event objects. At playback, IDs/minutes are rebased and evidence sequence references remapped around heartbeats. It implements all four commands; Stop cancels the remaining recording so a later step cannot restart a job. The WebSocket handshake marks the source as replay without adding fields to contract events. Replay history and saved summaries stay in memory and are isolated from real history; they never become measured evidence.

## What the screens do

- **Setup:** accepts a bounded Uz/Ru/En job description, explains privacy and the Nebius text boundary, imports strict JSON recipes without starting them, shows readable steps and optional JSON, exports the exact recipe. Test sends `start_job`; there is no invented “preview planner” operation. Until a checked recipe arrives, the screen states the safety steps and waits. Previous recipes are labelled **Last checked plan**.
- **Live:** derives state from runner events. A known 0 is a measurement; unknown is a dash. An observation's `unknown_reason` uses the exact fixed message in section 11 of the contract, in the selected language. `null` means not configured. Coverage gaps remain visible. A connection drop clears live values immediately; a silent heartbeat gap does so after three seconds. An accepted Stop command does not claim the job stopped; only a device status can confirm it.
- **Nigoh scene:** an original SVG diagram with rounded silhouettes, solid face blocks, a wide eye, an entry arrow and a 420 ms crossing pulse. The wire contract forbids images and person positions, so this is explicitly labelled a diagram. A rising entered count pulses the line. Demo mode also offers one illustrative crossing. Reduced motion suppresses animation. No camera images are requested or uploaded.
- **Trials:** ten rows per demo, owner-reported pass/fail/unknown, approximate duration in rounded minutes, fixed fault messages, start/finish/cancel, save/delete summaries. The full observation → decision → changed recipe → installed revision → next observation chain is necessary for the “OpenCV output changed the next action” label. Policy stops are separate. The sample chain and results are labelled synthetic.

Camera address, ownership confirmation, allowed-area mask and motor re-arm belong on the device. They cannot be imported through a recipe or set by this dashboard.

## Data and boundaries

`web/.data/` is ignored and created with owner-only permissions. Changed events persist in `events.ndjson` for up to seven days. Persistence records rounded minute times only; precise receipt times and unchanged status heartbeats remain in live memory. Expired records are filtered on reads and removed by maintenance. Saved summaries retain only the contract's allowlisted summary fields until deleted. Prompts are request-only memory; no analytics, frame uploads, media storage, or raw exception messages are used. Demo data is browser memory and disappears on exit/reload.

This is a **local implementation**, not an AWS deployment. The localhost runner adapter is implemented and tested against the recorded fake server; actual camera measurements are not claimed. Cloud database TTL, 30-day daily crossing aggregates, deployment secrets, TLS, and validation with the real hardware runner remain integration/deployment work. Current per-job entered/exited counters are displayed directly; occupancy is never summed into totals. Do not describe this local JSON storage as the contract's completed cloud retention system.

## Verification and design

Latest runner/launcher pass: **23 tests passed**, build passed, and the 360 px replay browser check has no JavaScript errors, axe violations or horizontal overflow. See `review/runner/REVIEW.md`.

- Node tests cover strict JSON, schema limits, exact unknown messages, state transitions, evidence completeness, auth, token revocation, WebSocket validation, commands and summary CRUD.
- Browser review covers three screens × two themes × three languages at 360 px, desktop, enlarged text, reduced motion, zero/unknown/offline/Stop, and the complete trial and import/export flow.
- See `review/REVIEW.md`, `review/audit.json`, and `DESIGN.md` for evidence and design decisions.
- `design/` preserves the earlier directions and reference research. D was selected by the owner; the landing page is deferred.

AI contribution: Codex implemented the web UI, local owner/runner adapter, contract-derived validators/messages, demo and tests on 2026-10-15. The owner selected Nigoh and requested its silhouette, eye, direction, pulse and light-theme refinements. Root `AI_LOG.md` is outside this task's edit lane.
