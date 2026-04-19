#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "container-tests" job.
# Builds base + agent Docker images, then runs Docker-gated tests.
# See also: ci-lint.sh, ci-unit.sh, ci-eval.sh, ci-all.sh.

set -euo pipefail

# Disable MSYS automatic Unix→Windows path conversion so docker volume specs
# aren't mangled on Git Bash. No-op on Linux/macOS.
export MSYS_NO_PATHCONV=1

echo "==> uv sync"
uv sync
echo "==> build docker images"
bash scripts/build-docker-images.sh
echo "==> pytest (docker)"
uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent" -v
