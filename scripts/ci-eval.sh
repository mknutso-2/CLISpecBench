#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "eval-tests" job.
# With no arguments, runs every eval target sequentially for local use.
# In GitHub Actions, the eval-tests matrix invokes one target per job.
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

run_target() {
  local target="$1"
  case "${target}" in
    bibtex-cpp)
      run_eval "BibTeX (cpp)" Evals/BibTeX/tests --language=cpp
      ;;
    gedcom-py)
      run_eval "GEDCOM (py)" Evals/GEDCOM/tests --language=py
      ;;
    ical-cpp)
      run_eval "ICal (cpp)" Evals/ICal/tests --language=cpp
      ;;
    iges-cpp)
      run_eval "IGES (cpp)" Evals/IGES/tests --language=cpp
      ;;
    las-py)
      run_eval "LAS (py)" Evals/LAS/tests --language=py
      ;;
    marc21-py)
      run_eval "MARC21 (py)" Evals/MARC21/tests --language=py
      ;;
    wordcount-cpp)
      run_eval "WordCount (cpp)" Evals/WordCount/tests --language=cpp
      ;;
    rs274-cpp)
      # The cpp reference has known v2.0 feature gaps (motion trace and
      # full-circle center-format arcs without in-plane axis words). Those
      # tests are deselected here and exercised against the py reference below.
      run_eval "RS274 (cpp)" Evals/RS274/tests --language=cpp \
        -m "not trace" -k "not full-circle-no-axis-words"
      ;;
    rs274-py)
      run_eval "RS274 (py)" Evals/RS274/tests --language=py
      ;;
    all)
      run_target bibtex-cpp
      run_target gedcom-py
      run_target ical-cpp
      run_target iges-cpp
      run_target las-py
      run_target marc21-py
      run_target wordcount-cpp
      run_target rs274-cpp
      run_target rs274-py
      ;;
    *)
      echo "Unknown eval target: ${target}" >&2
      echo "Expected one of: all, bibtex-cpp, gedcom-py, ical-cpp, iges-cpp, las-py, marc21-py, wordcount-cpp, rs274-cpp, rs274-py" >&2
      exit 2
      ;;
  esac
}

run_target "${1:-all}"
