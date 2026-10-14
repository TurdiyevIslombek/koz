# AI log — opencv-flybrain

Competitions ask how AI was used. One line per real contribution.

| Date | AI | What it did | What I changed or decided |
|---|---|---|---|
| 2026-10-13 | Claude | Set up this workspace, CLAUDE.md rules and the Claude–Codex bridge | Chose the competitions and the plan |
| 2026-10-14 | Claude + Codex | Refusal rules (/collab think): each wrote a list independently, debated once (Codex conceded 5 points; Codex corrected Claude on the 2026 Uzbek data-law change, which Claude then checked on lex.uz), merged into 12 rules. Claude replaced the v0 privacy section in CLAUDE.md | Retention 7 days for events, 30 for totals; chat to Nebius goes in the report's limitations + a "don't type names" UI note; chose which rules are MVP, simple or stretch; the rest is design only |
| 2026-10-14 | Claude + Codex | Contract v1 (/collab think): each proposed `contracts/recipe.schema.json` and `contracts/events.md` independently, debated once (Codex conceded 6 cuts and added connection-loss, token and fly-brain requirements). Claude merged them and checked the schema (3 good recipes pass, 24 rule-breaking ones are rejected) | Approved both files; 3 tries total per job; face blur on every recipe, including the car (measure its cost); `firmware/` is Claude's lane; will check the Russian and Uzbek messages |
| 2026-10-14 | Claude + Codex | KICKOFF 3: Claude built the first `koz/` core (recipe checks, privacy gate that fails closed, mock camera, local setup, color_finder, face_blur with OpenCV 5 YuNet, contract events, runner) and 87 tests on a recorded test video. Codex reviewed it (/collab-review) and found 11 issues; Claude fixed 9 and gave reasons for declining 2 | Approved downloading the YuNet face model (MIT, SHA-256 pinned) and committing it |
