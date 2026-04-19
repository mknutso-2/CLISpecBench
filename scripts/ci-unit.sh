#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "unit-tests" job.
# See also: ci-lint.sh, ci-container.sh, ci-eval.sh, ci-all.sh.

set -euo pipefail

echo "==> uv sync"
uv sync
echo "==> pytest (unit)"
uv run pytest src/swe_buildbench/tests -m "not docker and not prompts_agent" -v
