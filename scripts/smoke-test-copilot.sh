#!/usr/bin/env bash
# Smoke-test GitHub Copilot CLI authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - Logged in to gh CLI on the Windows host (gh auth login)
#
# Auth:
#   Copilot CLI authenticates via COPILOT_GITHUB_TOKEN / GH_TOKEN env var.
#   The harness injects this from the host's gh auth token.
#
# Run from Git Bash:
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-copilot.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

# Get the GitHub token from gh CLI
GH_TOKEN=$(gh auth token 2>/dev/null || true)
if [ -z "$GH_TOKEN" ]; then
    echo "ERROR: No GitHub token found. Run 'gh auth login' first."
    exit 1
fi

echo "--- Testing: Copilot CLI ---"
$DOCKER_CMD run --rm \
    -e "COPILOT_GITHUB_TOKEN=$GH_TOKEN" \
    -w /workspace \
    swe-buildbench-copilot-cli:latest \
    bash -c "copilot -p 'respond with just the word hello' --yolo --silent"
echo "PASS: Copilot CLI"
