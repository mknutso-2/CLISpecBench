#!/usr/bin/env bash
# Smoke-test OpenCode authentication through OpenRouter inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - OPENROUTER_API_KEY exported in the shell that runs this script
#
# Optional:
#   - OPENCODE_SMOKE_MODEL, defaulting to openrouter/moonshotai/kimi-k2.6
#
# Run from Git Bash:
#   OPENROUTER_API_KEY=... bash scripts/smoke-test-opencode.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "ERROR: OPENROUTER_API_KEY must be set for the OpenCode/OpenRouter smoke test." >&2
    exit 2
fi

OPENCODE_SMOKE_MODEL="${OPENCODE_SMOKE_MODEL:-openrouter/moonshotai/kimi-k2.6}"
export OPENCODE_SMOKE_MODEL

echo "--- Testing: OpenCode via OpenRouter (${OPENCODE_SMOKE_MODEL}) ---"
$DOCKER_CMD run --rm \
    -e OPENROUTER_API_KEY \
    -e OPENCODE_SMOKE_MODEL \
    -e OPENCODE_DISABLE_AUTOUPDATE=1 \
    -e OPENCODE_DISABLE_DEFAULT_PLUGINS=1 \
    -e OPENCODE_DISABLE_CLAUDE_CODE=1 \
    -w /workspace \
    clispecbench-opencode:latest \
    bash -c 'set -o pipefail
        opencode run --pure --format json --model "$OPENCODE_SMOKE_MODEL" \
            --title clispecbench-smoke --dangerously-skip-permissions \
            "respond with just the word hello" 2>&1 | tee /tmp/opencode-smoke.jsonl
        if grep -q "\"type\":\"error\"" /tmp/opencode-smoke.jsonl; then
            exit 1
        fi
        grep -qi "hello" /tmp/opencode-smoke.jsonl'
echo "PASS: OpenCode via OpenRouter"
