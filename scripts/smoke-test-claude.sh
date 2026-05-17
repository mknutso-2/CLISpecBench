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
# Mount individual credential files rather than the whole ~/.claude/ directory.
# Mounting the whole dir exposes ~/.claude/backups/ which causes claude 2.1.120+
# to hard-fail with exit 1 when it finds a backup but no ~/.claude.json present.
# Individual file mounts match what the harness does and avoid the backup issue.
# Run as the 'agent' user (same as harness) to use /home/agent as HOME.
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.claude/.credentials.json:/home/agent/.claude/.credentials.json:ro" \
    -v "${WIN_HOME}/.claude/settings.json:/home/agent/.claude/settings.json:ro" \
    clispecbench-claude-code:latest \
    bash -c "mkdir -p /home/agent/.claude && chown agent:agent /home/agent/.claude && su agent -c 'claude --print --dangerously-skip-permissions \"respond with just the word hello\"'"
echo "PASS: Claude Code"
