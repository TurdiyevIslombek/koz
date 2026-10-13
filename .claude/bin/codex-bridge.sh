#!/usr/bin/env bash
# codex-bridge.sh — Claude Code → Codex CLI bridge
# Based on github.com/AlessioZazzarini/claude-codex-collab (MIT license).
#
# Changed from the original (Oct 2026):
#   - build mode uses "-s workspace-write": current Codex CLI no longer accepts --full-auto
#   - stdin is closed (</dev/null) so Codex never waits for extra input
#   - --skip-git-repo-check so it also works in folders without git
#
# Usage:
#   codex-bridge.sh think "Your prompt here"
#   codex-bridge.sh build "Your prompt here"
#   codex-bridge.sh build "Implement this spec" .collab/specs/task.md
#
# Modes:
#   think — read-only. Codex reads files but changes nothing.
#   build — workspace-write. Codex can create/modify files inside this project only.

set -euo pipefail

MODE="${1:?Usage: codex-bridge.sh <think|build> \"prompt\" [spec-file]}"
PROMPT="${2:?Usage: codex-bridge.sh <think|build> \"prompt\" [spec-file]}"
SPEC_FILE="${3:-}"

# If a spec file is provided, prepend its contents to the prompt
if [[ -n "$SPEC_FILE" && -f "$SPEC_FILE" ]]; then
  PROMPT="## Build Spec
$(cat "$SPEC_FILE")

## Instructions
${PROMPT}"
fi

# Record each call (proves Codex was really used; .collab/ is git-ignored)
mkdir -p .collab && echo "$(date '+%Y-%m-%d %H:%M:%S') $MODE" >> .collab/bridge-calls.log

# Use the ChatGPT subscription login, never a paid API key
unset OPENAI_API_KEY

# Suppress OpenTelemetry crash (known Codex CLI bug)
export OTEL_SDK_DISABLED=true

case "$MODE" in
  think)
    exec codex exec --skip-git-repo-check -s read-only "$PROMPT" </dev/null
    ;;
  build)
    exec codex exec --skip-git-repo-check -s workspace-write "$PROMPT" </dev/null
    ;;
  *)
    echo "Error: Mode must be 'think' or 'build'. Got: $MODE" >&2
    exit 1
    ;;
esac
