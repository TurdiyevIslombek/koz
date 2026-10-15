# Koʻz web · Nigoh

The selected D direction, built as three working screens: Setup, Live job, and Trials & proof. Uzbek, Russian, English; warm light and dark themes; local Onest font. All implementation and tests live in `web/`.

## Run

Requires Node 22.16+ and npm.

```sh
cd web
npm ci
npm run dev
```

Open `http://127.0.0.1:4173`. Without an owner password, real telemetry and commands are locked. **Explore demo** opens an explicitly labelled browser simulation. Direct preview: `http://127.0.0.1:4173/?demo=1#live`.

To enable the owner account, create `web/.env` (ignored by Git) containing `KOZ_OWNER_PASSWORD` with your own password, then restart. `PORT` optionally changes port 4173. The development server binds only to loopback and accepts loopback hostnames; it is not a public deployment configuration.

```sh
npm test
npm run build
npm start
```

The tests start ephemeral loopback servers. A sandbox may need permission for that. `npm run build` creates ignored `dist/`; it regenerates the recipe validator and all 38 fixed messages directly from the shared contract files without changing them.

## Connect a runner

1. Sign in with the owner password and open **Connect device**.
2. Create a runner token. It is displayed once; only its SHA-256 hash is retained. A new token disconnects the previous runner and revokes its token.
3. Put it in the device's `KOZ_RUNNER_TOKEN`. The runner opens `ws://127.0.0.1:4173/v1/runner` with `Authorization: Bearer <token>` for local development. Production needs HTTPS/WSS and a deployment-specific configuration.
4. Send the contract's initial `status`, then status every second. The dashboard accepts the seven event types and sends the four command types specified in `contracts/events.md`.

This is a single-owner web adapter. The core checkout currently exposes an event sink, with WebSocket transport and the planner/command loop still to be connected by the core engineer. The web endpoint has been tested with a protocol simulator; no hardware result is claimed.

## What the screens do

- **Setup:** accepts a bounded Uz/Ru/En job description, explains privacy and the Nebius text boundary, imports strict JSON recipes without starting them, shows readable steps and optional JSON, exports the exact recipe. Test sends `start_job`; there is no invented “preview planner” operation. Until a checked recipe arrives, the screen states the safety steps and waits. Previous recipes are labelled **Last checked plan**.
- **Live:** derives state from runner events. A known 0 is a measurement; unknown is a dash. An observation's `unknown_reason` uses the exact fixed message in section 11 of the contract, in the selected language. `null` means not configured. Coverage gaps remain visible. Offline starts after three seconds without a fresh status receipt. An accepted Stop command does not claim the job stopped; only a device status can confirm it.
- **Nigoh scene:** an original SVG diagram with rounded silhouettes, solid face blocks, a wide eye, an entry arrow and a 420 ms crossing pulse. The wire contract forbids images and person positions, so this is explicitly labelled a diagram. A rising entered count pulses the line. Demo mode also offers one illustrative crossing. Reduced motion suppresses animation. No camera images are requested or uploaded.
- **Trials:** ten rows per demo, owner-reported pass/fail/unknown, approximate duration in rounded minutes, fixed fault messages, start/finish/cancel, save/delete summaries. The full observation → decision → changed recipe → installed revision → next observation chain is necessary for the “OpenCV output changed the next action” label. Policy stops are separate. The sample chain and results are labelled synthetic.

Camera address, ownership confirmation, allowed-area mask and motor re-arm belong on the device. They cannot be imported through a recipe or set by this dashboard.

## Data and boundaries

`web/.data/` is ignored and created with owner-only permissions. Changed events persist in `events.ndjson` for up to seven days. Persistence records rounded minute times only; precise receipt times and unchanged status heartbeats remain in live memory. Expired records are filtered on reads and removed by maintenance. Saved summaries retain only the contract's allowlisted summary fields until deleted. Prompts are request-only memory; no analytics, frame uploads, media storage, or raw exception messages are used. Demo data is browser memory and disappears on exit/reload.

This is a **local implementation**, not an AWS deployment. Cloud database TTL, 30-day daily crossing aggregates, deployment secrets, TLS, and the real runner transport remain integration/deployment work. Current per-job entered/exited counters are displayed directly; occupancy is never summed into totals. Do not describe this local JSON storage as the contract's completed cloud retention system.

## Verification and design

- Node tests cover strict JSON, schema limits, exact unknown messages, state transitions, evidence completeness, auth, token revocation, WebSocket validation, commands and summary CRUD.
- Browser review covers three screens × two themes × three languages at 360 px, desktop, enlarged text, reduced motion, zero/unknown/offline/Stop, and the complete trial and import/export flow.
- See `review/REVIEW.md`, `review/audit.json`, and `DESIGN.md` for evidence and design decisions.
- `design/` preserves the earlier directions and reference research. D was selected by the owner; the landing page is deferred.

AI contribution: Codex implemented the web UI, local owner/runner adapter, contract-derived validators/messages, demo and tests on 2026-10-15. The owner selected Nigoh and requested its silhouette, eye, direction, pulse and light-theme refinements. Root `AI_LOG.md` is outside this task's edit lane.
