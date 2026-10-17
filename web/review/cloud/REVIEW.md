# Cloud verification — 2026-10-17

Scope: `.collab/specs/aws-review.md`; implementation and evidence in `web/` only.

- Build passed; complete web suite: **48 passed**. Cloud tests use real HTTP/WebSocket connections on loopback and an in-memory implementation of the SDK's low-level DynamoDB operations. No AWS endpoint or hardware is accessed.
- Tests cover exact HTTPS origin/Host and trusted-loopback proxy checks, Secure/HttpOnly/SameSite cookies, configuration/password handling, Bedrock and camera wire format, same-socket commands, no durable prompts/tokens/passwords, anonymous write rejection, job/summary scoping, public SSE withdrawal, delayed old-job events, restart freshness, database failures and TTL filtering.
- DynamoDB adapter tests cover conditional duplicate transactions, bounded cursor pages with scope validation, known crossing increases, occupancy/trial/evaluation exclusion, UTC-day rollover, gap/disconnect markers, 30-day TTL and durable summary deletion. The adapter uses the pinned SDK command classes; actual IAM/table behavior still needs the deployment integration check.
- Chromium browser pass through a local HTTPS proxy with a temporary self-signed test certificate: English/Russian/Uzbek at 360 px, light/dark Setup, exact Bedrock privacy copy, camera selection, owner login/pairing, sharing off by default, read-only judge controls, privacy-stop and disconnect behavior, and both tabs after web restart. No JavaScript errors or horizontal overflow. `browser.json` records the pass; screenshots were inspected.
- Clean temporary install: **`npm ci` → `node scripts/build.mjs` → `npm prune --omit=dev`** passed, and cloud/protocol imports work after esbuild is removed. A separate `npm ci --os=linux --cpu=x64 --ignore-scripts` resolved the Linux esbuild package from the lockfile and verified its ELF header. Results are in `install.json`.

Run `check-browser.mjs` with `KOZ_PLAYWRIGHT_MODULE` pointing at an installed Playwright module if necessary; `check-install.mjs` uses npm registry access and temporary copies. The test certificate and dependency copies are deleted afterward. These scripts do not modify the running application, runner or any AWS account.

Native checks ran on macOS / Node 25.1.0. The implementation targets Node 22+ and the lockfile includes Linux x64; no Linux execution, real DynamoDB, deployed Nginx/certificate or AWS load test is claimed. See `web/CLOUD.md` for the installer handoff and storage limits.
