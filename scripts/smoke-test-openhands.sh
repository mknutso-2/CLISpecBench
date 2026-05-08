#!/usr/bin/env bash
# Smoke-test OpenHands authentication through OpenRouter inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh openhands)
#   - OPENROUTER_API_KEY exported in the shell that runs this script
#
# Optional:
#   - OPENHANDS_SMOKE_MODEL, defaulting to openrouter/deepseek/deepseek-v4-pro
#
# Run from Git Bash:
#   OPENROUTER_API_KEY=... bash scripts/smoke-test-openhands.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "ERROR: OPENROUTER_API_KEY must be set for the OpenHands/OpenRouter smoke test." >&2
    exit 2
fi

OPENHANDS_SMOKE_MODEL="${OPENHANDS_SMOKE_MODEL:-openrouter/deepseek/deepseek-v4-pro}"
export OPENHANDS_SMOKE_MODEL

echo "--- Testing: OpenHands via OpenRouter (${OPENHANDS_SMOKE_MODEL}) ---"
$DOCKER_CMD run --rm \
    -e OPENROUTER_API_KEY \
    -e LLM_API_KEY="$OPENROUTER_API_KEY" \
    -e LLM_MODEL="$OPENHANDS_SMOKE_MODEL" \
    -e PYTHONIOENCODING=utf-8 \
    -e PYTHONUTF8=1 \
    -e NO_COLOR=1 \
    -e TERM=dumb \
    -e OPENHANDS_SUPPRESS_BANNER=1 \
    -e OPENHANDS_PERSISTENCE_DIR=/tmp/openhands \
    -e OPENHANDS_CONVERSATIONS_DIR=/tmp/openhands/conversations \
    -e OPENHANDS_WORK_DIR=/workspace \
    -w /workspace \
    clispecbench-openhands:latest \
    bash -c 'set -o pipefail
        openhands --headless --json --always-approve --override-with-envs \
            -t "respond with just the word hello" 2>&1 | tee /tmp/openhands-smoke.jsonl
        if grep -q "\"kind\": \"ConversationErrorEvent\"\\|\"kind\":\"ConversationErrorEvent\"" /tmp/openhands-smoke.jsonl; then
            exit 1
        fi
        grep -qi "hello" /tmp/openhands-smoke.jsonl'
echo "PASS: OpenHands via OpenRouter"
