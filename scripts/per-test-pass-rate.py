#!/usr/bin/env python3
"""Per-test pass-rate CSV across all runs of a task family.

For each unique pytest ``node_id`` seen in ``transient_results/<task-prefix>*/**/result.json``,
emits one row with: attempted (total appearances), passed (outcome=="passed"),
failed, skipped, errored, pass_rate.

Useful for saturation analysis — if a test has many attempts and zero passes
across every model, it's the bottleneck.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from clispecbench.harness.results import load_result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="transient_results", help="Root results directory")
    parser.add_argument(
        "--task-prefix",
        default="rs274",
        help="Only include task folders whose names start with this (default: rs274)",
    )
    parser.add_argument("--output", "-o", default=None, help="Output CSV path (default: stdout)")
    parser.add_argument(
        "--exit-reason",
        default=None,
        help="If set, only count runs with this exit_reason (e.g. 'completed')",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.is_dir():
        print(f"Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    attempted: Counter[str] = Counter()
    by_outcome: dict[str, Counter[str]] = defaultdict(Counter)
    passing_runs: dict[str, list[str]] = defaultdict(list)
    runs_loaded = 0
    runs_skipped = 0
    exit_reason_counts: Counter[str] = Counter()

    for task_dir in sorted(results_dir.iterdir()):
        if not task_dir.is_dir() or not task_dir.name.startswith(args.task_prefix):
            continue
        for json_file in sorted(task_dir.rglob("result.json")):
            try:
                r = load_result(json_file)
            except Exception as exc:
                print(f"Warning: skipping {json_file}: {exc}", file=sys.stderr)
                runs_skipped += 1
                continue

            exit_reason_counts[r.metadata.exit_reason] += 1
            if args.exit_reason and r.metadata.exit_reason != args.exit_reason:
                continue

            run_label = str(json_file.parent.relative_to(results_dir)).replace("\\", "/")
            runs_loaded += 1
            for t in r.tests:
                attempted[t.node_id] += 1
                by_outcome[t.outcome][t.node_id] += 1
                if t.outcome == "passed":
                    passing_runs[t.node_id].append(run_label)

    if not attempted:
        print("No tests found.", file=sys.stderr)
        sys.exit(1)

    rows = []
    for node_id in sorted(attempted):
        n = attempted[node_id]
        p = by_outcome["passed"][node_id]
        row = {
            "node_id": node_id,
            "attempted": n,
            "passed": p,
            "failed": by_outcome["failed"][node_id],
            "skipped": by_outcome["skipped"][node_id],
            "errored": by_outcome["error"][node_id],
            "pass_rate": f"{p / n:.4f}",
        }
        # For tests with 1-5 passes, list each passing run in its own column;
        # empty for 0-pass and 6+-pass tests.
        rare = passing_runs[node_id] if 1 <= p <= 5 else []
        for i in range(5):
            row[f"pass_{i + 1}"] = rare[i] if i < len(rare) else ""
        rows.append(row)

    fieldnames = list(rows[0].keys())
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output:
            out.close()

    zero_pass = sum(1 for r in rows if r["passed"] == 0)
    print(
        f"Wrote {len(rows)} test rows from {runs_loaded} runs (skipped {runs_skipped} unreadable).",
        file=sys.stderr,
    )
    print(f"Tests with zero successes: {zero_pass}", file=sys.stderr)
    print("Exit-reason distribution across all runs scanned:", file=sys.stderr)
    for reason, count in sorted(exit_reason_counts.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}", file=sys.stderr)

    rare = [r for r in rows if 1 <= r["passed"] <= 5]
    if rare:
        print(
            f"\nTests with 1–5 successes ({len(rare)}) — runs that passed each:",
            file=sys.stderr,
        )
        for r in rare:
            print(f"  {r['node_id']}  ({r['passed']}/{r['attempted']})", file=sys.stderr)
            for run_label in passing_runs[r["node_id"]]:
                print(f"    - {run_label}", file=sys.stderr)


if __name__ == "__main__":
    main()
