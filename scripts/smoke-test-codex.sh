#!/usr/bin/env bash
# Smoke-test Codex CLI authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - Logged in to Codex CLI on the Windows host
#
# Auth files:
#   ~/.codex/auth.json  — OAuth tokens (mount only this file, not the
#                         whole dir, to avoid read-only filesystem errors)
#
# Notes:
#   - Requires git + an initialized repo in the workspace.
#   - Connects to chatgpt.com (not api.openai.com).
#
# Run from Git Bash:
#   bash scripts/smoke-test-codex.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Codex CLI ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.codex/auth.json:/root/.codex/auth.json:ro" \
    -w /workspace \
    swe-buildbench-codex-cli:latest \
    bash -c "git init /workspace > /dev/null 2>&1 && codex exec 'respond with just the word hello'"
echo "PASS: Codex CLI"
