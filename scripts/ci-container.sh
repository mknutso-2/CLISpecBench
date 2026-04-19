#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "container-tests" job.
# Builds base + agent Docker images, then runs Docker-gated tests.
# See also: ci-lint.sh, ci-unit.sh, ci-eval.sh, ci-all.sh.

set -euo pipefail

echo "==> uv sync"
uv sync
echo "==> build docker images"
# MSYS_NO_PATHCONV keeps Git Bash from mangling Docker volume paths on Windows;
# harmless on Linux/macOS.
MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh
echo "==> pytest (docker)"
uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent" -v
