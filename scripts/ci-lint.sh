#!/usr/bin/env bash
# Mirrors the GitHub Actions ci.yml "lint" job.
# See also: ci-unit.sh, ci-container.sh, ci-eval.sh, ci-all.sh.

set -euo pipefail

uv sync
uv run ruff check
uv run pyright
