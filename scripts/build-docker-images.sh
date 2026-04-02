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

# Resolve repo root relative to this script
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -d "/mnt/c/Users" ]; then
    DOCKER_CMD="docker"
else
    DOCKER_CMD="wsl -d Ubuntu -- docker"
fi

build_base() {
    echo "--- Building: swe-buildbench-base ---"
    $DOCKER_CMD build -t swe-buildbench-base:latest -f "$REPO_ROOT/docker/base.Dockerfile" "$REPO_ROOT/docker"
}

build_agent() {
    local agent="$1"
    local dockerfile="$REPO_ROOT/docker/agents/${agent}.Dockerfile"
    if [ ! -f "$dockerfile" ]; then
        echo "ERROR: No Dockerfile found at $dockerfile"
        return 1
    fi
    echo "--- Building: swe-buildbench-${agent} ---"
    $DOCKER_CMD build -t "swe-buildbench-${agent}:latest" -f "$dockerfile" "$REPO_ROOT/docker"
}

if [ $# -eq 0 ]; then
    # Build everything
    build_base
    for df in "$REPO_ROOT"/docker/agents/*.Dockerfile; do
        agent="$(basename "$df" .Dockerfile)"
        build_agent "$agent"
    done
elif [ "$1" = "base" ]; then
    build_base
else
    build_agent "$1"
fi

echo ""
echo "Done."
