#!/bin/bash
# Self-serializing queue template for batched clispecbench runs.
#
# This file is a TEMPLATE, not a runnable queue. Workflow:
#
#   1. Copy this file:  cp scripts/_queue-template.sh scripts/_queue-<your-tag>.sh
#      (matching `_queue-*.sh` is gitignored except this template, so the copy
#      stays out of git automatically.)
#   2. Edit the copy: set AGENT, fill the `queue=( ... )` array with the
#      task|model|effort|label items you want to run.
#   3. Launch in the background. Each `clispecbench run` is itself
#      backgrounded inside the loop so the queue advances as soon as a slot
#      frees; the wrapper waits for all children before exiting:
#
#        bash scripts/_queue-<your-tag>.sh > logs/queue-<your-tag>.log 2>&1 &
#
#      Per-item logs land at logs/queue_${label}.log .
#   4. When the queue completes, delete the copy:  rm scripts/_queue-<your-tag>.sh
#
# Concurrency: the queue waits until fewer than MAX_CONCURRENT containers
# matching CONCURRENCY_IMAGE_FILTER are running before launching the next
# item. Default filter is "clispecbench-${AGENT}" so unrelated work using a
# different agent image does not block the queue. Set the filter to plain
# "clispecbench" if you want to serialize against ALL clispecbench work on
# the host.
#
# Auth gate: if the queue uses claude-code, an auth smoke test runs before
# each queue item. If auth has expired (token rotation, etc.), the queue
# self-aborts so the operator can re-auth and resume rather than burning
# through the queue producing dead infra_auth runs. To exercise the gate
# per-run instead of per-item, split a `--runs N` invocation into N
# single-run queue items.
#
# Prerequisites: WSL2 dockerd reachable at tcp://localhost:2375 (see
# CLAUDE.md "Starting the WSL2 Docker daemon" for the bring-up procedure).
# On idle WSL hosts, the daemon may shut down between queue ticks; run
# `wsl -d Ubuntu -- sleep 36000 &` (disowned) as a keep-alive if you see
# transient ChunkedEncodingError or RemoteDisconnected from the harness.

set -u
export DOCKER_HOST=tcp://localhost:2375

# ---- Customize per copy ----------------------------------------------------
AGENT="codex-cli"      # codex-cli | claude-code | gemini-cli | copilot-cli
MAX_CONCURRENT=2

# Image filter for count_active. Default is the agent's own image so unrelated
# work (e.g. parallel codex runs while you're running claude-code) does not
# block. Set to "clispecbench" to serialize against ALL clispecbench work.
CONCURRENCY_IMAGE_FILTER="clispecbench-${AGENT}"

# Queue items, format: task|model|effort|label|runs
# `label` is used in the per-item log filename and in queue progress lines.
# `runs` defaults to 3 when omitted. Use 1 if you want the auth-gate to fire
# before each individual run (the harness has no per-run auth check inside
# `--runs N`, so a mid-sequence token expiration would slip through).
queue=(
  # "rs274-cpp|gpt-5.4|xhigh|5.4-cpp|3"
  # "rs274-py|gpt-5.4|xhigh|5.4-py|3"
)
# ---------------------------------------------------------------------------

mkdir -p logs

count_active() {
  uv run python -c "
import docker
try:
    c = docker.DockerClient(base_url='tcp://localhost:2375')
    cs = [x for x in c.containers.list() if '$CONCURRENCY_IMAGE_FILTER' in x.attrs['Config']['Image']]
    print(len(cs))
except Exception:
    print(99)
" 2>/dev/null || echo 99
}

wait_for_slot() {
  while true; do
    n=$(count_active)
    if [ "$n" -lt "$MAX_CONCURRENT" ] 2>/dev/null; then
      return 0
    fi
    sleep 60
  done
}

# Auth gate: run scripts/smoke-test-${AGENT}.sh if it exists. Fails if the
# CLI cannot authenticate (e.g. expired OAuth token), so the queue aborts
# before producing dead infra_* runs.
auth_smoke_test() {
  local script="$(dirname "$0")/smoke-test-${AGENT}.sh"
  if [ ! -x "$script" ] && [ ! -f "$script" ]; then
    return 0  # no smoke test for this agent — skip the gate
  fi
  bash "$script" > /tmp/queue-auth-smoke.log 2>&1
  return $?
}

if [ "${#queue[@]}" -eq 0 ]; then
  echo "ERROR: queue is empty. Edit this script's queue=( ... ) array." >&2
  exit 2
fi

for item in "${queue[@]}"; do
  IFS='|' read -r task model effort label runs <<< "$item"
  runs="${runs:-3}"
  echo "[$(date -Iseconds)] QUEUE: auth smoke-test before $label"
  if ! auth_smoke_test; then
    echo "[$(date -Iseconds)] QUEUE: AUTH SMOKE TEST FAILED before $label — aborting. Re-auth $AGENT and relaunch." >&2
    tail -10 /tmp/queue-auth-smoke.log >&2
    exit 3
  fi
  echo "[$(date -Iseconds)] QUEUE: auth ok"
  echo "[$(date -Iseconds)] QUEUE: waiting for slot before $label"
  wait_for_slot
  echo "[$(date -Iseconds)] QUEUE: launching $label (task=$task model=$model effort=$effort runs=$runs agent=$AGENT)"
  (
    uv run clispecbench run \
      --task "$task" \
      --agent "$AGENT" \
      --model "$model" \
      --effort "$effort" \
      --runs "$runs" \
      >> "logs/queue_${label}.log" 2>&1
    rc=$?
    echo "[$(date -Iseconds)] QUEUE: $label finished (exit=$rc)"
  ) &
  # Give Docker a moment to register the new container before next slot check
  sleep 45
done

wait
echo "[$(date -Iseconds)] QUEUE: all items complete"
