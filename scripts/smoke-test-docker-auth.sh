#!/usr/bin/env bash
# Smoke-test that CLI agents can authenticate inside Docker containers.
# Runs each agent's individual smoke test and reports combined results.
#
# Prerequisites:
#   - Docker Engine running in WSL2 (see install-docker-wsl.sh)
#   - Logged in to each CLI on the Windows host
#
# Run from Git Bash:
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-docker-auth.sh
#
# Or from PowerShell / CMD:
#   wsl -d Ubuntu -- bash /mnt/c/Git/SWE-BuildBench/scripts/smoke-test-docker-auth.sh
#
# Run a single agent:
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-claude.sh
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-codex.sh
#   MSYS_NO_PATHCONV=1 bash scripts/smoke-test-gemini.sh
#
# Note: Running all three sequentially takes 3-5 minutes (each agent pulls
# npm packages and makes an API call). Run individual scripts to debug.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

passed=0
failed=0

for agent in claude codex gemini; do
    echo ""
    if bash "$SCRIPT_DIR/smoke-test-${agent}.sh"; then
        ((passed++))
    else
        echo "FAIL: ${agent}"
        ((failed++))
    fi
done

echo ""
echo "=== Results: $passed passed, $failed failed ==="
[ "$failed" -eq 0 ]
