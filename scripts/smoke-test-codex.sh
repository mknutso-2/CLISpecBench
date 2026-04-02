#!/usr/bin/env bash
# Smoke-test Codex CLI authentication inside a Docker container.
#
# Auth files:
#   ~/.codex/auth.json  — OAuth tokens (mount only this file, not the
#                         whole dir, to avoid read-only filesystem errors)
#
# Notes:
#   - Requires ca-certificates package (node:22-slim lacks root CAs that
#     Codex's Rust TLS stack needs for chatgpt.com).
#   - Requires git + an initialized repo in the workspace.
#   - Connects to chatgpt.com (not api.openai.com).
#
# Run from Git Bash:
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-codex.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Codex CLI ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.codex/auth.json:/root/.codex/auth.json:ro" \
    -w /workspace \
    node:22-slim \
    bash -c "
        apt-get update -qq && apt-get install -y -qq ca-certificates git > /dev/null 2>&1
        npm install -g @openai/codex 2>/dev/null
        git init /workspace > /dev/null 2>&1
        codex exec 'respond with just the word hello'
    "
echo "PASS: Codex CLI"
