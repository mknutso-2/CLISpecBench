#!/usr/bin/env bash
# Shared setup for smoke-test scripts. Sourced, not executed directly.
#
# Exports: WIN_HOME, DOCKER_CMD

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

export WIN_HOME DOCKER_CMD
