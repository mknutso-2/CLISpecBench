#!/usr/bin/env bash
# Shared setup for smoke-test scripts. Sourced, not executed directly.
#
# Exports: WIN_HOME, DOCKER_CMD, MSYS_NO_PATHCONV
#
# Supports three environments:
#   1. Plain Linux (e.g. CI runners)     — docker runs directly, no Windows home
#   2. WSL on Windows                    — docker runs directly, Windows home under /mnt/c
#   3. Git Bash / MSYS on Windows        — docker must be invoked via WSL

# Disable MSYS automatic Unix→Windows path conversion so docker volume specs
# (/src:/dst) aren't mangled into Windows drive-letter syntax on Git Bash.
# No-op on Linux/macOS.
export MSYS_NO_PATHCONV=1

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
elif [ -n "${MSYSTEM:-}" ]; then
    # Running from Git Bash / MSYS on Windows — call docker via WSL
    WIN_HOME="/mnt/c/Users/${USERNAME}"
    DOCKER_CMD="wsl -d Ubuntu -- docker"
else
    # Plain Linux (CI runner, native Linux dev machine, etc.)
    WIN_HOME=""
    DOCKER_CMD="docker"
fi

export WIN_HOME DOCKER_CMD
