#!/usr/bin/env bash
# Runs every GitHub Actions ci.yml job in sequence against the local tree.
# See each ci-<job>.sh for what the individual jobs do.

set -euo pipefail

here="$(dirname "$0")"
bash "$here/ci-lint.sh"
bash "$here/ci-unit.sh"
bash "$here/ci-container.sh"
bash "$here/ci-eval.sh"
