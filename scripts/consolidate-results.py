#!/usr/bin/env python3
"""Consolidate SWE-BuildBench result JSON files into a CSV summary."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from swe_buildbench.harness.results import load_result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate results into CSV")
    parser.add_argument("--results-dir", default="transient_results", help="Root results directory")
    parser.add_argument("--output", "-o", default=None, help="Output CSV path (default: stdout)")
    parser.add_argument("--task", default=None, help="Filter by task")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.is_dir():
        print(f"Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    rows: list[dict[str, str | int | float]] = []
    for json_file in sorted(results_dir.rglob("result.json")):
        try:
            r = load_result(json_file)
        except Exception as exc:
            print(f"Warning: skipping {json_file}: {exc}", file=sys.stderr)
            continue

        if args.task and r.metadata.task != args.task:
            continue

        rows.append(
            {
                "task": r.metadata.task,
                "agent": r.metadata.agent,
                "agent_version": r.metadata.agent_version,
                "model": r.metadata.model or "default",
                "effort": r.metadata.effort or "",
                "run": r.metadata.run_number,
                "exit_reason": r.metadata.exit_reason,
                "passed": r.test_summary.passed,
                "total": r.test_summary.total,
                "pass_rate": (
                    f"{r.test_summary.passed / r.test_summary.total:.1%}"
                    if r.test_summary.total > 0
                    else "n/a"
                ),
                "task_score": (
                    f"{r.scores.task_score:.3f}" if r.scores.task_score is not None else ""
                ),
                "input_tokens": r.token_usage.input_tokens if r.token_usage else "",
                "output_tokens": r.token_usage.output_tokens if r.token_usage else "",
                "cache_read_tokens": (
                    r.token_usage.cache_read_input_tokens
                    if r.token_usage and r.token_usage.cache_read_input_tokens
                    else ""
                ),
                "cache_write_tokens": (
                    r.token_usage.cache_creation_input_tokens
                    if r.token_usage and r.token_usage.cache_creation_input_tokens
                    else ""
                ),
                "total_tokens": (r.token_usage.total_tokens if r.token_usage else ""),
                "tool_calls": (
                    r.token_usage.tool_calls if r.token_usage and r.token_usage.tool_calls else ""
                ),
                "benchmark_cost": (
                    f"{r.benchmark_cost_usd:.4f}" if r.benchmark_cost_usd is not None else ""
                ),
                "benchmark_cost_source": r.benchmark_cost_source or "",
                "reported_cost": (
                    f"{r.token_usage.reported_cost_usd:.4f}"
                    if r.token_usage and r.token_usage.reported_cost_usd
                    else ""
                ),
                "estimated_cost": (
                    f"{r.token_usage.estimated_cost_usd:.4f}"
                    if r.token_usage and r.token_usage.estimated_cost_usd
                    else ""
                ),
                "wall_clock_s": f"{r.metadata.wall_clock_seconds:.1f}",
                "build_ok": r.build.success,
                "surgery": r.surgery or "",
                "notes": r.metadata.notes or "",
            }
        )

    if not rows:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    fieldnames = list(rows[0].keys())
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output:
            out.close()

    if args.output:
        print(f"Wrote {len(rows)} rows to {args.output}", file=sys.stderr)
    else:
        print(f"\n# {len(rows)} results", file=sys.stderr)


if __name__ == "__main__":
    main()
