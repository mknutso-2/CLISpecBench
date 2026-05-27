#!/usr/bin/env bash
# Smoke-test Google Antigravity CLI authentication inside its Docker container.
#
# Prerequisites:
#   - Docker images built (scripts/build-docker-images.sh antigravity-cli)
#   - Antigravity CLI auth available to the container. On Windows, host-side
#     `agy` login stores OAuth in Credential Manager. Docker auth currently
#     requires the equivalent JSON at
#     ~/.gemini/antigravity-cli/antigravity-oauth-token, which contains a
#     plaintext OAuth refresh token and must not be committed or logged.
#   - Version 1.0.2 still cannot force model/effort by flag, does not expose
#     token usage, and --print output remains unreliable when stdout is captured
#     by a non-TTY subprocess.
#
# Run from Git Bash:
#   bash scripts/smoke-test-antigravity.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/smoke-test-common.sh"

HOST_HOME="${WIN_HOME:-${HOME}}"
mount_args=()
if [ -d "${HOST_HOME}/.gemini/antigravity-cli" ]; then
    mount_args+=(
        -v "${HOST_HOME}/.gemini/antigravity-cli:/root/.gemini/antigravity-cli:rw"
    )
fi
if [ -d "${HOST_HOME}/.gemini/config" ]; then
    mount_args+=(
        -v "${HOST_HOME}/.gemini/config:/root/.gemini/config:rw"
    )
fi

echo "--- Testing: Antigravity CLI ---"
status=0
output="$(
    $DOCKER_CMD run --rm \
        -t \
        "${mount_args[@]}" \
        -e BROWSER=/bin/true \
        -e NO_COLOR=1 \
        -e TERM=dumb \
        -w /workspace \
        clispecbench-antigravity-cli:latest \
        bash -c 'set -o pipefail
            agy --dangerously-skip-permissions --print-timeout 30s \
                --log-file /tmp/antigravity-smoke.log \
                --print "respond with just the word hello" 2>&1 \
                | tee /tmp/antigravity-smoke-output.log
            status="${PIPESTATUS[0]}"
            if grep -Eiq "Authentication required|authentication timed out|auth timed out" \
                /tmp/antigravity-smoke-output.log /tmp/antigravity-smoke.log 2>/dev/null; then
                exit 1
            fi
            exit "$status"'
)" || status=$?

printf "%s\n" "$output"
if printf "%s\n" "$output" | grep -Eiq "Authentication required|authentication timed out|auth timed out"; then
    echo "ERROR: Antigravity CLI auth is not available inside the container." >&2
    exit 1
fi
if [ "$status" -ne 0 ]; then
    exit "$status"
fi
printf "%s\n" "$output" | grep -qi "hello"
echo "PASS: Antigravity CLI"
