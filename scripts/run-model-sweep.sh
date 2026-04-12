#!/usr/bin/env bash
# Run a SWE-BuildBench eval across all models for one or more agents.
#
# Usage:
#   ./scripts/run-model-sweep.sh --task wordcount [--agents claude-code,codex-cli,gemini-cli] [--runs 1]
#
# Reads model lists from models/<agent>.txt (format: model,effort per line).
# Results are written to results/<task>/<agent>/<model>/run-N.json.
# A consolidated CSV is written at the end.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
TASK=""
AGENTS="claude-code,codex-cli,copilot-cli,gemini-cli"
RUNS=1
TIMEOUT=1800
OUTPUT_DIR="results"

usage() {
    echo "Usage: $0 --task <task> [--agents <a,b,c>] [--runs N] [--timeout S] [--output-dir DIR]"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --task) TASK="$2"; shift 2 ;;
        --agents) AGENTS="$2"; shift 2 ;;
        --runs) RUNS="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

[[ -z "$TASK" ]] && { echo "Error: --task is required"; usage; }

IFS=',' read -ra AGENT_LIST <<< "$AGENTS"

echo "=== SWE-BuildBench Model Sweep ==="
echo "Task:    $TASK"
echo "Agents:  ${AGENT_LIST[*]}"
echo "Runs:    $RUNS"
echo "Timeout: ${TIMEOUT}s"
echo ""

TOTAL=0
PASSED=0
FAILED=0

for AGENT in "${AGENT_LIST[@]}"; do
    MODEL_FILE="$REPO_ROOT/models/${AGENT}.txt"
    if [[ ! -f "$MODEL_FILE" ]]; then
        echo "WARNING: No model file found at $MODEL_FILE, skipping $AGENT"
        continue
    fi

    echo "--- Agent: $AGENT ---"

    while IFS= read -r line; do
        # Skip comments and blank lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue

        # Parse model,effort
        MODEL=$(echo "$line" | cut -d',' -f1)
        EFFORT=$(echo "$line" | cut -d',' -f2)

        [[ -z "$MODEL" ]] && continue

        TOTAL=$((TOTAL + 1))

        echo ""
        echo ">>> Running: $AGENT / $MODEL (effort=${EFFORT:-none})"

        # Build the command
        CMD=(uv run swe-buildbench run
            --task "$TASK"
            --agent "$AGENT"
            --model "$MODEL"
            --runs "$RUNS"
            --timeout "$TIMEOUT"
            --output-dir "$OUTPUT_DIR"
        )
        if [[ -n "$EFFORT" ]]; then
            CMD+=(--effort "$EFFORT")
        fi

        # Run and capture exit code
        if "${CMD[@]}"; then
            echo "<<< PASSED: $AGENT / $MODEL"
            PASSED=$((PASSED + 1))
        else
            echo "<<< FAILED: $AGENT / $MODEL (exit code: $?)"
            FAILED=$((FAILED + 1))
        fi
    done < "$MODEL_FILE"
done

echo ""
echo "=== Sweep Complete ==="
echo "Total: $TOTAL  Passed: $PASSED  Failed: $FAILED"

# Consolidate results
CSV_OUT="$OUTPUT_DIR/${TASK}-sweep.csv"
echo ""
echo "Consolidating results to $CSV_OUT ..."
uv run python "$REPO_ROOT/scripts/consolidate-results.py" \
    --results-dir "$OUTPUT_DIR" \
    --task "$TASK" \
    --output "$CSV_OUT"

echo ""
echo "Done. Results CSV: $CSV_OUT"
