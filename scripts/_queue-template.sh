#!/bin/bash
# Self-serializing queue template for batched swe-buildbench runs.
#
# This file is a TEMPLATE, not a runnable queue. Workflow:
#
#   1. Copy this file:  cp scripts/_queue-template.sh scripts/_queue-<your-tag>.sh
#      (matching `_queue-*.sh` is gitignored except this template, so the copy
#      stays out of git automatically.)
#   2. Edit the copy: set AGENT, fill the `queue=( ... )` array with the
#      task|model|effort|label items you want to run.
#   3. Launch in the background. Each `swe-buildbench run` is itself
#      backgrounded inside the loop so the queue advances as soon as a slot
#      frees; the wrapper waits for all children before exiting:
#
#        bash scripts/_queue-<your-tag>.sh > logs/queue-<your-tag>.log 2>&1 &
#
#      Per-item logs land at logs/queue_${label}.log .
#   4. When the queue completes, delete the copy:  rm scripts/_queue-<your-tag>.sh
#
# Concurrency: the queue waits until fewer than MAX_CONCURRENT swe-buildbench
# containers are running before launching the next item. Default is 2.
#
# Prerequisites: WSL2 dockerd reachable at tcp://localhost:2375 (see
# CLAUDE.md "Starting the WSL2 Docker daemon" for the bring-up procedure).

set -u
export DOCKER_HOST=tcp://localhost:2375

# ---- Customize per copy ----------------------------------------------------
AGENT="codex-cli"      # codex-cli | claude-code | gemini-cli | copilot-cli
MAX_CONCURRENT=2

# Queue items, format: task|model|effort|label
# `label` is used in the per-item log filename and in queue progress lines.
queue=(
  # "rs274-cpp|gpt-5.4|xhigh|5.4-cpp"
  # "rs274-py|gpt-5.4|xhigh|5.4-py"
)
# ---------------------------------------------------------------------------

mkdir -p logs

count_active() {
  uv run python -c "
import docker
try:
    c = docker.DockerClient(base_url='tcp://localhost:2375')
    cs = [x for x in c.containers.list() if 'swe-buildbench' in x.attrs['Config']['Image']]
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

if [ "${#queue[@]}" -eq 0 ]; then
  echo "ERROR: queue is empty. Edit this script's queue=( ... ) array." >&2
  exit 2
fi

for item in "${queue[@]}"; do
  IFS='|' read -r task model effort label <<< "$item"
  echo "[$(date -Iseconds)] QUEUE: waiting for slot before $label"
  wait_for_slot
  echo "[$(date -Iseconds)] QUEUE: launching $label (task=$task model=$model effort=$effort agent=$AGENT)"
  (
    uv run swe-buildbench run \
      --task "$task" \
      --agent "$AGENT" \
      --model "$model" \
      --effort "$effort" \
      --runs 3 \
      >> "logs/queue_${label}.log" 2>&1
    rc=$?
    echo "[$(date -Iseconds)] QUEUE: $label finished (exit=$rc)"
  ) &
  # Give Docker a moment to register the new container before next slot check
  sleep 45
done

wait
echo "[$(date -Iseconds)] QUEUE: all items complete"
