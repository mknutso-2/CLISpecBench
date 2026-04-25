#!/usr/bin/env bash
# Smoke-test Claude Code authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - Logged in to Claude Code on the Windows host
#
# Auth files:
#   ~/.claude/.credentials.json  — OAuth tokens
#
# Note: ~/.claude.json is deliberately NOT mounted — it caches the user's
# claude.ai connector list (Gmail / GCal / Drive) and would leak `mcp__*`
# tools into the agent's tool catalog, contaminating eval runs. The CLI
# runs cleanly without it on current versions.
#
# Run from Git Bash:
#   bash scripts/smoke-test-claude.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Claude Code ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.claude:/root/.claude:ro" \
    clispecbench-claude-code:latest \
    claude --print 'respond with just the word hello'
echo "PASS: Claude Code"
