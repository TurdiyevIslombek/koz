# Cloud server — 17 October 2026

Implements `.collab/specs/aws-review.md`. Entry point: **`node server/cloud.mjs`**, from `web/`. Local `npm start` and `open-web.command` retain the localhost runner workflow. No AWS account actions or deployment were performed by this change.

## Installer interface

The existing installer/systemd service supplies these environment variables from `/etc/koz/env`:

| Variable | Value |
| --- | --- |
| `PORT` | `4173` by default; Node binds **127.0.0.1 only** |
| `KOZ_PUBLIC_ORIGIN` | Exact HTTPS origin, e.g. `https://<Elastic-IP>`; no trailing slash/path |
| `KOZ_OWNER_PASSWORD` | Installer-generated owner secret, 16–256 characters |
| `KOZ_DATA_DIR` | Absolute writable location, normally `/var/lib/koz` |
| `KOZ_TABLE` | `koz-web`, with string `pk` / `sk` and numeric TTL `expires_at` |
| `AWS_REGION` | `eu-central-1` |
| `NODE_ENV` | `production` |

The cloud entry point uses **DynamoDB**, not the NDJSON fallback. It does not write application data to the checkout or another filesystem path. Startup fails closed if configuration or initial table access fails. `/api/health` returns 200 once startup succeeds; loopback HTTP health checks work before the external HTTPS request path is used.

The owner password is consumed and removed from the Node process environment. Authentication retains only a random salt and scrypt digest in memory. Neither password nor sessions are written to DynamoDB. The source environment file remains managed by the installer. Runner pairing stores only a SHA-256 token hash; the token itself is returned once to the signed-in owner. No request-body/access logs, prompts, tokens or exception dumps are added.

Cookies are Secure, HttpOnly and SameSite=Strict in cloud mode. Mutations require the configured exact Origin; the public Host must match it. Forwarded HTTPS is trusted only from a loopback peer. The installer must keep Nginx on the same host and Node private. `/v1/runner` additionally requires the paired Bearer token, rejects browser Origin headers, and accepts strict contract JSON only. No media/upload routes exist.

## Owner and judges workflow

1. Open the HTTPS URL and sign in. Choose **Connect device → Create runner token**; put the one-time token in the Mac runner's private `KOZ_RUNNER_TOKEN` configuration. Claude's outbound mode connects to `wss://<IP>/v1/runner`.
2. Start the desired job. `status.planner` now accepts **`bedrock`**, alongside rules/Ollama/Nebius/null/legacy. Setup offers the reported camera slots and sends `camera_id` for both text and imported recipes. Cloud Setup explains AWS Frankfurt transit for every planner and AWS EU processing for Bedrock, in Uzbek/Russian/English. Prompt text is sent only over the active command socket and is never persisted.
3. In **Connect device**, choose any saved summaries to publish and click **Share current job with judges**. Sharing defaults off. Give judges `https://<IP>/#live`; use a separate/incognito browser to see their view. They get Live and Trials & proof, with no job controls. **Stop sharing** withdraws the view and resets connected viewers.

Public APIs are server-scoped to the explicitly selected `(session_id, job_id)` and selected saved-summary IDs. `/api/public/snapshot` and `/api/events/public` exclude other jobs, command results and pending commands. Every owner command, pairing-token operation, replay operation, publication change and save/delete remains authenticated. A later job is not automatically public. The public SSE path deliberately matches the installer's `/api/events` Nginx location, so buffering stays disabled.

Dropping the runner or receiving no status for three seconds clears live readings. Restarting the web server restores retained evidence but sets live freshness to zero and discards pending commands/sessions. A new observation is required; nothing is replayed. Signed-out cloud tabs reconnect to the read-only view; owner controls require signing in again. The local in-browser synthetic demo remains labelled and cannot drive the cloud runner; the local fake-server replay endpoint is unavailable in cloud mode.

## DynamoDB layout and retention

Pinned runtime SDK: **`@aws-sdk/client-dynamodb@3.1152.0`**. The SDK's default Node credential chain uses the EC2 instance role in this installer; no static AWS credentials are passed by the app. [AWS credential-chain documentation](https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/setting-credentials-node.html).

This deployment has one installed owner and one paired runner. The server fixes the owner/source prefix; requests and event fields never select an account. Event partitions are scoped to that source and a contract session; each row retains its checked job/trial scope. This supports ordered per-session history pagination without a secondary index.

| Record | Key pattern | Expiry |
| --- | --- | --- |
| Event | `pk=OWNER#primary#RUNNER#primary#SESSION#<session>`; `sk=EVENT#<padded seq>` | `min(event.minute, receipt minute) × 60 + 604800` |
| Latest status/recipe/fault | Source partition; `STATE#<type>` | Original event expiry, never refreshed by reads |
| Per-job daily observed crossings | Source partition; `TOTAL#<UTC date>#<session>#<job>` | End of that UTC day + 30 days |
| Cumulative counter checkpoint | Source partition; `COUNTER#<session>#<job>` | End of latest observed UTC day + 30 days |
| Owner-saved summary | Owner partition; `SUMMARY#<trial>` | No TTL; explicit delete |
| Pairing/publication configuration | Owner partition; `META` | No TTL; contains token hash, selected scopes and storage-health marker only |

Every read filters expired records, even before DynamoDB physically removes them. No unchanged status heartbeat is stored. Event writes and any crossing updates form one conditional transaction keyed by `(session, seq)`, so duplicates neither add counts nor renew expiry. Saved-summary writes are also conditional and preserve the original record. [AWS TTL filtering documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ttl-expired-items.html).

Daily rows count only increases in cumulative known `entered`/`exited` during normal running outside trials. Occupancy, evaluation and unknown values never add crossings. High-water checkpoints carry across UTC days. Rows remain `open` during a job; gaps, link loss and storage failure set `incomplete`. A consumer must label a daily result incomplete if **any included row is open or incomplete**, or a pagination cursor remains; sum across all pages to obtain a day total. These are observed crossings, not attendance. There is no totals chart in the existing three-screen UI.

The application restores up to 200 recent events plus current state and keeps at most 1,000 events in server/browser memory. The owner can open older evidence pages in Trials; `/api/history?session=<id>&limit=100&cursor=<opaque>` provides bounded pages (maximum 200). `/api/summaries?cursor=...` pages saved summaries; the UI loads 100 plus explicitly published summaries. `/api/totals?date=YYYY-MM-DD&cursor=...` pages per-job daily rows. Cursors cannot switch owner/session scope. A missing part of an adjust chain cannot earn the complete-chain label.

Live delivery does not await database writes. The persistence queue is capped at 100 operations; SDK requests have bounded timeouts/retries. A failed/dropped write shows **Proof is incomplete** and marks subsequently saved evidence incomplete; it does not fabricate successful persistence. The marker persists across normal restarts; an unclean prior shutdown also marks proof incomplete. There is no automatic “all proof repaired” claim or raw-data backup. Table throttling must still be checked during the real EC2 demonstration, especially with the planned 5 write units and transactional writes.

## Verification and remaining deployment checks

- Build and web tests: `npm run build && npm test` in `web/`.
- `review/cloud/check-browser.mjs`: real Chromium at 360 px, two themes, three languages, a **local test HTTPS proxy**, fake DynamoDB, mock runner, public scoping, privacy/disconnect and restart behavior. No camera or AWS account.
- `review/cloud/check-install.mjs`: clean `npm ci`, `node scripts/build.mjs`, `npm prune --omit=dev`, then imports cloud/protocol modules with dev dependencies removed. Separately resolves Linux x64 dependencies from the lockfile and checks the Linux esbuild ELF binary is installed.
- Test results and screenshots are in `review/cloud/`. Native execution used macOS; the Linux binary was resolved but not executed here. No live DynamoDB, EC2, IAM, Nginx production certificate or real runner deployment is claimed. Run the installer and a real integration check in AWS before sharing the production URL.

AI contribution: Codex built the web cloud entry point, DynamoDB adapter, proxy authentication, owner-controlled public view, Bedrock disclosure and tests on 2026-10-17. Edits stayed in `web/`; deployment/core/firmware/contracts remain Claude's lane.
