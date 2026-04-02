#!/usr/bin/env bash
# Build all Docker images for SWE-BuildBench.
#
# Builds the base image first (swe-buildbench-base:latest), then each
# agent image on top of it. Agent Dockerfiles use FROM swe-buildbench-base:latest,
# so the base must be built first.
#
# Run from Git Bash:
#   MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh
#
# Or from WSL:
#   bash /mnt/c/Git/SWE-BuildBench/scripts/build-docker-images.sh
#
# Build only the base image:
#   MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh base
#
# Build only one agent (base must already exist):
#   MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh claude-code
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

# Resolve repo root — use WSL-compatible path for docker commands
if [ -d "/mnt/c/Users" ]; then
    # Running inside WSL
    REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
else
    # Running from Git Bash — convert /c/ to /mnt/c/ for WSL docker
    REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    REPO_ROOT="/mnt/c${REPO_ROOT#/c}"
fi

build_base() {
    echo "--- Building: swe-buildbench-base ---"
    $DOCKER_CMD build -t swe-buildbench-base:latest -f "$REPO_ROOT/docker/base.Dockerfile" "$REPO_ROOT/docker"
}

build_agent() {
    local agent="$1"
    local dockerfile="$REPO_ROOT/docker/agents/${agent}.Dockerfile"
    echo "--- Building: swe-buildbench-${agent} ---"
    $DOCKER_CMD build -t "swe-buildbench-${agent}:latest" -f "$dockerfile" "$REPO_ROOT/docker"
}

# Check which Dockerfiles exist (use local path for file checks from Git Bash)
LOCAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ $# -eq 0 ]; then
    build_base
    for df in "$LOCAL_ROOT"/docker/agents/*.Dockerfile; do
        agent="$(basename "$df" .Dockerfile)"
        build_agent "$agent"
    done
elif [ "$1" = "base" ]; then
    build_base
else
    if [ ! -f "$LOCAL_ROOT/docker/agents/${1}.Dockerfile" ]; then
        echo "ERROR: No Dockerfile found at docker/agents/${1}.Dockerfile"
        exit 1
    fi
    build_agent "$1"
fi

echo ""
echo "Done."
