#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "lint" job.
# See also: ci-unit.sh, ci-container.sh, ci-eval.sh, ci-all.sh.

set -euo pipefail

echo "==> uv sync"
uv sync
echo "==> ruff"
uv run ruff check
echo "==> pyright"
uv run pyright
