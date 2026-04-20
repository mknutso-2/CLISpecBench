#!/usr/bin/env bash
# Smoke-test Claude Code authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - Logged in to Claude Code on the Windows host
#
# Auth files:
#   ~/.claude/.credentials.json  — OAuth tokens
#   ~/.claude.json               — config file (must be mounted or stdout
#                                  gets warning messages mixed into output)
#
# Run from Git Bash:
#   bash scripts/smoke-test-claude.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Claude Code ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.claude:/root/.claude:ro" \
    -v "${WIN_HOME}/.claude.json:/root/.claude.json:ro" \
    clispecbench-claude-code:latest \
    claude --print 'respond with just the word hello'
echo "PASS: Claude Code"
