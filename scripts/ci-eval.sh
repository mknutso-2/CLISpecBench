#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "eval-tests" job.
# Assumes g++-14 and cmake are already installed (CI installs them as a
# separate workflow step; local developers install them once).
# See also: ci-lint.sh, ci-unit.sh, ci-container.sh, ci-all.sh.

set -euo pipefail

echo "==> uv sync"
uv sync
echo "==> pytest WordCount (cpp)"
uv run pytest Evals/WordCount/tests -v --language=cpp
# The cpp reference has known v2.0 feature gaps (motion trace and
# full-circle center-format arcs without in-plane axis words). Those
# tests are deselected here and exercised against the py reference below.
echo "==> pytest RS274 (cpp)"
uv run pytest Evals/RS274/tests -v --language=cpp \
  -m "not trace" -k "not full-circle-no-axis-words"
echo "==> pytest RS274 (py)"
uv run pytest Evals/RS274/tests -v --language=py
