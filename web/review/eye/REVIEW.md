# Local eye preview verification — 17 October 2026

Implemented `.collab/specs/web-eye-preview.md` against `contracts/events.md` section 14. Implementation and test edits are confined to `web/`; core, firmware and contracts were read only.

**Build and all 60 Node tests passed. Browser checks passed.** No camera, serial device, motors or AWS account was used. The browser test constructs a synthetic JPEG in memory with OpenCV; it does not record an actual camera trial.

## Verified boundaries

- One upstream `/v1/preview` connection, without Origin, shared by local owner tabs. Exact same-origin and loopback checks; requests without the owner session fail. Non-loopback HTTP requests fail even with a valid owner cookie. Cross-origin WebSocket handshakes fail.
- Binary JPEG framing, maximum width 320, maximum size 40 KiB; strict fixed closed-message shape/reasons, including duplicate-key rejection. Invalid upstream data closes/reconnects without retaining or forwarding it.
- Guard closed messages, held/non-running status, event or preview disconnect, job change and one-second expiry discard the last picture. A newly opened viewer waits for a new JPEG rather than giving an old frame a new lifetime.
- Logout and session expiry close existing eye sockets. Slow consumers cannot accumulate frames. Compression is disabled; the successful handshake has `Cache-Control: no-store` and no ETag.
- `localAccess:false` and cloud both return 404 for HTTP/WebSocket eye requests; no upstream preview connection is made. Cloud's runner rejects binary and image-bearing event input before ingestion/storage. Existing owner/public SSE paths contain only validated event objects and fixed transport metadata.
- Persistence during a preview session contains only the normal event/owner files, with no frame bytes, preview objects, base64 or image data URLs. Preview code has no file/database/log write path. No images were added to replay fixtures.
- Browser decoding happens through short-lived Blob URLs; old URLs are revoked on replacement/closure. Navigation away and hidden tabs drop the preview. Late socket callbacks cannot restore a discarded picture.

## Browser checks

`check-browser.mjs` / `browser.json`: Chromium at 360 × 800, all three languages and both themes; no JavaScript errors or horizontal overflow. The complete image fits within the eye using `object-fit: contain`. Checked checking/late messages, fixed bathroom refusal, Unknown target after a guard stop, preview/event disconnects, same-tab web restart, navigation and reduced-motion transition suppression.

No screenshots, traces, recordings, frame snapshots or media artifacts were saved. Result JSON contains only test names and booleans. Existing cloud/design screenshots predate this local preview and are not preview captures.

## Reproduce

```sh
npm --prefix web run build
npm --prefix web test
# Supply a local installed Playwright module path if it is not on normal module resolution:
KOZ_PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node web/review/eye/check-browser.mjs
```

The browser harness also uses the repository's `.venv/bin/python` and OpenCV solely to encode its synthetic in-memory image. It opens only ephemeral loopback ports, cleans up its servers/browser, and saves `browser.json` without media.

During development, the sandbox initially refused local listening sockets; tests were then run with local-network permission. One old event-reconnection fixture counted the new preview socket as an event connection; it now distinguishes `/v1/preview`. The recorded fake runner likewise reports a closed eye without starting another event replay. The complete suite passed after these fixes.

The relay validates headers and bounds; the runner remains responsible for approving, masking and blurring actual pixels. The owner's physical-camera demonstration is still required; this verification does not claim one.
