#!/usr/bin/env bash
# Smoke-test that CLI agents can authenticate inside Docker containers.
# Runs each agent's individual smoke test from the agent registry and reports
# combined results.
#
# Prerequisites:
#   - Docker Engine running in WSL2 (see install-docker-wsl.sh)
#   - Logged in to each CLI on the Windows host
#   - OPENROUTER_API_KEY exported for the OpenCode/OpenRouter smoke test
#   - uv installed (used to read the agent registry)
#
# Run from Git Bash:
#   bash scripts/smoke-test-docker-auth.sh
#
# Or from PowerShell / CMD:
#   wsl -d Ubuntu -- bash /mnt/c/Git/CLISpecBench/scripts/smoke-test-docker-auth.sh
#
# Run a single agent:
#   bash scripts/smoke-test-claude.sh
#   bash scripts/smoke-test-codex.sh
#   bash scripts/smoke-test-copilot.sh
#   bash scripts/smoke-test-gemini.sh
#   OPENROUTER_API_KEY=... bash scripts/smoke-test-opencode.sh
#
# Note: Running all registered scripts sequentially takes several minutes (each agent pulls
# npm packages and makes an API call). Run individual scripts to debug.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mapfile -t smoke_scripts < <(
    cd "$REPO_ROOT" && uv run python scripts/list-auth-smoke-scripts.py
)

if [ "${#smoke_scripts[@]}" -eq 0 ]; then
    echo "ERROR: No auth smoke scripts registered."
    exit 1
fi

passed=0
failed=0

for rel_script in "${smoke_scripts[@]}"; do
    rel_script="${rel_script%$'\r'}"
    agent="$(basename "$rel_script" .sh)"
    agent="${agent#smoke-test-}"
    echo ""
    if bash "$REPO_ROOT/$rel_script"; then
        ((passed++))
    else
        echo "FAIL: ${agent}"
        ((failed++))
    fi
done

echo ""
echo "=== Results: $passed passed, $failed failed ==="
[ "$failed" -eq 0 ]
