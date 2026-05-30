#!/usr/bin/env bash
# Smoke-test the LEGACY Claude Code image's authentication (claude-code 2.0.x,
# used for the deprecated 4.0-generation models). Mirrors smoke-test-claude.sh
# but targets clispecbench-claude-code-legacy:latest. The 2.0.x CLI has no
# --effort flag, so this invocation omits it.
#
# Run from Git Bash:
#   bash scripts/smoke-test-claude-legacy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Claude Code (legacy) ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.claude/.credentials.json:/home/agent/.claude/.credentials.json:ro" \
    -v "${WIN_HOME}/.claude/settings.json:/home/agent/.claude/settings.json:ro" \
    clispecbench-claude-code-legacy:latest \
    bash -c "mkdir -p /home/agent/.claude && chown agent:agent /home/agent/.claude && su agent -c 'claude --print --dangerously-skip-permissions \"respond with just the word hello\"'"
echo "PASS: Claude Code (legacy)"
