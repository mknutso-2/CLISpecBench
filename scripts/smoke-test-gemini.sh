#!/usr/bin/env bash
# Smoke-test Gemini CLI authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh)
#   - Logged in to Gemini CLI on the Windows host
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
#
# Run from Git Bash:
#   bash scripts/smoke-test-gemini.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

echo "--- Testing: Gemini CLI ---"
$DOCKER_CMD run --rm \
    -v "${WIN_HOME}/.gemini/oauth_creds.json:/tmp/gemini-auth/oauth_creds.json:ro" \
    -v "${WIN_HOME}/.gemini/google_accounts.json:/tmp/gemini-auth/google_accounts.json:ro" \
    -v "${WIN_HOME}/.gemini/settings.json:/tmp/gemini-auth/settings.json:ro" \
    -w /workspace \
    swe-buildbench-gemini-cli:latest \
    bash -c '
        mkdir -p /root/.gemini
        cp /tmp/gemini-auth/* /root/.gemini/
        echo "{\"projects\":{}}" > /root/.gemini/projects.json
        gemini -p "respond with just the word hello"
    '
echo "PASS: Gemini CLI"
