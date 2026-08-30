#!/usr/bin/env bash
# Smoke-test Codex CLI authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - Logged in to Codex CLI on the Windows host
#
# Auth files:
#   ~/.codex/auth.json  — OAuth tokens (mount only this file, not the
#                         whole dir, so Codex can persist rotated refresh
#                         tokens without read-only filesystem errors)
#
# Notes:
#   - Requires git + an initialized repo in the workspace.
#   - Connects to chatgpt.com (not api.openai.com).
#
# Run from Git Bash:
#   bash scripts/smoke-test-codex.sh
#   bash scripts/smoke-test-codex.sh gpt-5.6-sol max
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

MODEL="${1:-}"
EFFORT="${2:-}"
if [[ -n "$EFFORT" && -z "$MODEL" ]]; then
    echo "Error: an effort requires a model argument" >&2
    exit 2
fi
if [[ -n "$MODEL" && ! "$MODEL" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Error: model may contain only letters, digits, dots, underscores, and hyphens" >&2
    exit 2
fi
if [[ -n "$EFFORT" && ! "$EFFORT" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Error: effort may contain only letters, digits, dots, underscores, and hyphens" >&2
    exit 2
fi

echo "--- Testing: Codex CLI ---"
ARGS=()
if [[ -n "$MODEL" ]]; then
    ARGS+=("$MODEL")
fi
if [[ -n "$EFFORT" ]]; then
    ARGS+=("$EFFORT")
fi
uv run python "$SCRIPT_DIR/smoke_test_codex.py" "${ARGS[@]}"
echo "PASS: Codex CLI"
