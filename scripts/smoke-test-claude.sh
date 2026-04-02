#!/usr/bin/env bash
# Smoke-test Claude Code authentication inside a Docker container.
#
# Auth files:
#   ~/.claude/.credentials.json  — OAuth tokens
#   ~/.claude.json               — config file (must be mounted or stdout
#                                  gets warning messages mixed into output)
#
# Notes:
#   - Read-only mount works; Claude Code does not need to write credentials.
#   - node:22-slim has enough CA certs for api.anthropic.com.
#
# Run from Git Bash:
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-claude.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Claude Code ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.claude:/root/.claude:ro" \
    -v "${WIN_HOME}/.claude.json:/root/.claude.json:ro" \
    node:22-slim \
    bash -c "npm install -g @anthropic-ai/claude-code 2>/dev/null && claude --print 'respond with just the word hello'"
echo "PASS: Claude Code"
