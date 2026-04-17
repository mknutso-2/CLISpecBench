#!/bin/bash
# Self-serializing queue for the remaining CNCSim codex-cli evals.
# Waits for <2 swe-buildbench containers before launching each item.
# Launched as a background bash task; each swe-buildbench run is itself
# backgrounded so the loop can advance once the next slot frees.
set -u
export DOCKER_HOST=tcp://localhost:2375

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
    if [ "$n" -lt 2 ] 2>/dev/null; then
      return 0
    fi
    sleep 60
  done
}

# Queue format: task|model|effort|label
queue=(
  "cncsim-full-rs|gpt-5.4|xhigh|5.4-rs"
  "cncsim-full-rs|gpt-5.4-mini|xhigh|5.4-mini-rs"
  "cncsim-full-py|gpt-5.3-codex|xhigh|5.3-codex-py"
  "cncsim-full-rs|gpt-5.3-codex|xhigh|5.3-codex-rs"
)

for item in "${queue[@]}"; do
  IFS='|' read -r task model effort label <<< "$item"
  echo "[$(date -Iseconds)] QUEUE: waiting for slot before $label"
  wait_for_slot
  echo "[$(date -Iseconds)] QUEUE: launching $label (task=$task model=$model effort=$effort)"
  (
    uv run swe-buildbench run \
      --task "$task" \
      --agent codex-cli \
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
