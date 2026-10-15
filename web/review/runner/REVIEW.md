# Local runner and launcher verification · 2026-10-15

- **23 Node tests passed** and the production bundle built successfully.
- A fresh launcher start became healthy; a second launch reused the same checkout's server. Root `open-web.command` is executable and passed `zsh -n`. The browser-opening command uses macOS `open`; the automated launcher test suppressed the actual browser launch.
- The fixture replay delivered measured zero, crossings, `PRIVATE_BATHROOM`, and a full matching adjustment chain through a real local WebSocket and the browser's event stream. All four commands returned on the same socket with matching command IDs.
- Socket close immediately cleared live values. Silent heartbeat loss did so after three seconds. Reconnection with status alone did not resurrect old counts; a fresh observation was required. Offline commands were rejected and never resent.
- Stop cancelled queued replay steps. Replay history/saved summaries were isolated from real history. A real service occupying the runner port was not replaced.
- The 360 px browser workflow passed with **zero JavaScript errors, zero axe violations and no horizontal overflow** (`browser.json`). Captures: `privacy-stop.png`, `disconnected.png`.

This verifies the web adapter against the synthetic recorded fixture and a controlled WebSocket server, not Claude's unfinished runner or measured camera behavior. No shared contract or core implementation files were changed. `open-web.command` is the owner's explicitly requested root-level exception; all implementation lives in `web/`.
