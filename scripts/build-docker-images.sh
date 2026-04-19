#!/usr/bin/env bash
# Build all Docker images for SWE-BuildBench.
#
# Builds the base image first (swe-buildbench-base:latest), then each
# agent image on top of it. Agent Dockerfiles use FROM swe-buildbench-base:latest,
# so the base must be built first.
#
# Run from Git Bash:
#   bash scripts/build-docker-images.sh
#
# Or from WSL:
#   bash /mnt/c/Git/SWE-BuildBench/scripts/build-docker-images.sh
#
# Build only the base image:
#   bash scripts/build-docker-images.sh base
#
# Build only one agent (base must already exist):
#   bash scripts/build-docker-images.sh claude-code
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

# Resolve repo root — the path passed to docker must match however DOCKER_CMD
# invokes the daemon.  On Git Bash we delegate to docker inside WSL, so the
# path has to be converted to WSL form (/c/... → /mnt/c/...).  On native
# Linux and inside WSL, the local path is already correct.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -n "${MSYSTEM:-}" ] && [ ! -d "/mnt/c/Users" ]; then
    # Running from Git Bash / MSYS on Windows — convert /c/ to /mnt/c/
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
