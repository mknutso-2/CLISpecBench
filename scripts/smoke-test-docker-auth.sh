#!/usr/bin/env bash
# Smoke-test that CLI agents can authenticate inside Docker containers
# using volume mounts of host credential files.
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
set -euo pipefail

# Resolve Windows home directory when running inside WSL
if [ -d "/mnt/c/Users" ]; then
    # Running inside WSL — find the Windows user's home
    WIN_HOME="/mnt/c/Users/${SUDO_USER:-${USER}}"
    if [ ! -d "$WIN_HOME" ]; then
        # Fallback: look for a home with .claude in it
        for d in /mnt/c/Users/*/; do
            if [ -f "${d}.claude/.credentials.json" ]; then
                WIN_HOME="${d%/}"
                break
            fi
        done
    fi
    DOCKER_CMD="docker"
else
    # Running from Git Bash on Windows — call docker via WSL
    WIN_HOME="/mnt/c/Users/${USERNAME}"
    DOCKER_CMD="wsl -d Ubuntu -- docker"
fi

passed=0
failed=0

run_test() {
    local name="$1"
    shift
    echo ""
    echo "--- Testing: $name ---"
    if output=$("$@" 2>&1); then
        echo "PASS: $output"
        ((passed++))
    else
        echo "FAIL: $output"
        ((failed++))
    fi
}

# -------------------------------------------------------------------------
# Claude Code
#
# Auth files:
#   ~/.claude/.credentials.json  — OAuth tokens
#   ~/.claude.json               — config file (must be mounted or stdout
#                                  gets warning messages mixed into output)
#
# Notes:
#   - Read-only mount works; Claude Code does not need to write credentials.
#   - node:22-slim has enough CA certs for api.anthropic.com.
# -------------------------------------------------------------------------
run_test "Claude Code" \
    $DOCKER_CMD run --rm \
        -v "${WIN_HOME}/.claude:/root/.claude:ro" \
        -v "${WIN_HOME}/.claude.json:/root/.claude.json:ro" \
        node:22-slim \
        bash -c "npm install -g @anthropic-ai/claude-code 2>/dev/null && claude --print 'respond with just the word hello'"

# -------------------------------------------------------------------------
# Codex CLI
#
# Auth files:
#   ~/.codex/auth.json  — OAuth tokens (mount only this file, not the
#                         whole dir, to avoid read-only filesystem errors)
#
# Notes:
#   - Requires ca-certificates package (node:22-slim lacks root CAs that
#     Codex's Rust TLS stack needs for chatgpt.com).
#   - Requires git + an initialized repo in the workspace.
#   - Connects to chatgpt.com (not api.openai.com).
# -------------------------------------------------------------------------
run_test "Codex CLI" \
    $DOCKER_CMD run --rm \
        -v "${WIN_HOME}/.codex/auth.json:/root/.codex/auth.json:ro" \
        -w /workspace \
        node:22-slim \
        bash -c "
            apt-get update -qq && apt-get install -y -qq ca-certificates git > /dev/null 2>&1
            npm install -g @openai/codex 2>/dev/null
            git init /workspace > /dev/null 2>&1
            codex exec 'respond with just the word hello'
        "

# -------------------------------------------------------------------------
# Gemini CLI
#
# Auth files (mounted read-only to a staging dir, then copied into a
# writable ~/.gemini — Gemini CLI needs to write projects.json and other
# runtime state alongside the auth files):
#   ~/.gemini/oauth_creds.json     — OAuth tokens
#   ~/.gemini/google_accounts.json — account info
#   ~/.gemini/settings.json        — auth type selection
#
# Notes:
#   - Cannot mount ~/.gemini/:ro because CLI writes projects.json at startup.
#   - Must seed projects.json with {"projects":{}} or CLI crashes.
#   - Harmless libsecret warning (no keychain in container, uses file fallback).
# -------------------------------------------------------------------------
run_test "Gemini CLI" \
    $DOCKER_CMD run --rm \
        -v "${WIN_HOME}/.gemini/oauth_creds.json:/tmp/gemini-auth/oauth_creds.json:ro" \
        -v "${WIN_HOME}/.gemini/google_accounts.json:/tmp/gemini-auth/google_accounts.json:ro" \
        -v "${WIN_HOME}/.gemini/settings.json:/tmp/gemini-auth/settings.json:ro" \
        -w /workspace \
        node:22-slim \
        bash -c '
            mkdir -p /root/.gemini
            cp /tmp/gemini-auth/* /root/.gemini/
            echo "{\"projects\":{}}" > /root/.gemini/projects.json
            npm install -g @google/gemini-cli 2>/dev/null
            gemini -p "respond with just the word hello"
        '

# -------------------------------------------------------------------------
echo ""
echo "=== Results: $passed passed, $failed failed ==="
[ "$failed" -eq 0 ]
