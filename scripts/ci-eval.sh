#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "eval-tests" job.
# Assumes g++-14 and cmake are already installed (CI installs them as a
# separate workflow step; local developers install them once).
# See also: ci-lint.sh, ci-unit.sh, ci-container.sh, ci-all.sh.

set -euo pipefail

echo "==> uv sync"
uv sync

run_eval() {
  local label="$1"
  shift
  echo "==> pytest ${label}"
  uv run pytest "$@" -v
}

run_eval "BibTeX (cpp)" Evals/BibTeX/tests --language=cpp
run_eval "GEDCOM (py)" Evals/GEDCOM/tests --language=py
run_eval "ICal (cpp)" Evals/ICal/tests --language=cpp
run_eval "IGES (cpp)" Evals/IGES/tests --language=cpp
run_eval "LAS (py)" Evals/LAS/tests --language=py
run_eval "MARC21 (py)" Evals/MARC21/tests --language=py
run_eval "WordCount (cpp)" Evals/WordCount/tests --language=cpp

# The cpp reference has known v2.0 feature gaps (motion trace and
# full-circle center-format arcs without in-plane axis words). Those
# tests are deselected here and exercised against the py reference below.
run_eval "RS274 (cpp)" Evals/RS274/tests --language=cpp \
  -m "not trace" -k "not full-circle-no-axis-words"
run_eval "RS274 (py)" Evals/RS274/tests --language=py
