#!/usr/bin/env bash
# Runs every GitHub Actions ci.yml job in sequence against the local tree.
# See each ci-<job>.sh for what the individual jobs do.

set -euo pipefail

here="$(dirname "$0")"

echo "#### ci: lint ####"
bash "$here/ci-lint.sh"
echo "#### ci: unit ####"
bash "$here/ci-unit.sh"
echo "#### ci: container ####"
bash "$here/ci-container.sh"
echo "#### ci: eval ####"
bash "$here/ci-eval.sh"
