"""Build dashboard data from curated published run JSON files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from clispecbench.harness.pricing import estimate_cost

DEFAULT_PUBLISHED_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results-published.json")

EVAL_NAMES = {
    "bibtex": "BibTeX",
    "cncsim": "CNCSIM",
    "gedcom": "GEDCOM",
    "ical": "ICal",
    "iges": "IGES",
    "las": "LAS",
    "marc21": "MARC21",
    "rs274": "RS274",
    "wordcount": "WordCount",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build results-published.json from published run JSON files.",
    )
    parser.add_argument(
        "--published-root",
        type=Path,
        default=DEFAULT_PUBLISHED_ROOT,
        help="Root published_results directory (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path for generated dashboard JSON (default: %(default)s).",
    )
    return parser.parse_args()


def task_eval_language(task: str) -> tuple[str, str]:
    if "-" not in task:
        return EVAL_NAMES.get(task, task), ""
    eval_id, language = task.rsplit("-", 1)
    return EVAL_NAMES.get(eval_id, eval_id), language.upper()


def number(value) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    return None


def integer(value) -> int | None:
    if isinstance(value, int):
        return value
    return None


def cost_usd(model: str, usage: dict) -> float | int | None:
    reported = number(usage.get("reported_cost_usd"))
    if reported is not None:
        return reported

    estimated = number(usage.get("estimated_cost_usd"))
    if estimated is not None:
        return estimated

    input_tokens = integer(usage.get("input_tokens"))
    output_tokens = integer(usage.get("output_tokens"))
    if input_tokens is None or output_tokens is None:
        return None

    return estimate_cost(
        model,
        input_tokens,
        output_tokens,
        integer(usage.get("cache_read_input_tokens")) or 0,
        integer(usage.get("cache_creation_input_tokens")) or 0,
    )


def run_number(path: Path, metadata: dict) -> str:
    stem = path.stem
    if stem.startswith("run") and stem[3:].isdigit():
        return stem[3:]
    value = metadata.get("run_number")
    return str(value) if value is not None else ""


def result_link(web_dir: Path, path: Path) -> str:
    return "../" + path.resolve().relative_to(web_dir.parent.resolve()).as_posix()


def build_row(path: Path, web_dir: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata") or {}
    summary = payload.get("test_summary") or {}
    usage = payload.get("token_usage") or {}
    stats = payload.get("source_stats") or {}
    editorial = payload.get("editorial") or {}

    task = metadata.get("task") or path.parts[-4]
    eval_name, language = task_eval_language(task)
    run_id = run_number(path, metadata)
    passed = summary.get("passed", 0) or 0
    total = summary.get("total", 0) or 0
    score_pct = round((passed / total) * 100, 3) if total else None
    input_tokens = usage.get("input_tokens") or 0
    output_tokens = usage.get("output_tokens") or 0
    total_tokens = usage.get("total_tokens")
    if total_tokens is None:
        total_tokens = input_tokens + output_tokens

    return {
        "task": task,
        "language": language,
        "agent": metadata.get("agent") or "",
        "model": metadata.get("model") or "",
        "effort": metadata.get("effort") or "",
        "run_id": run_id,
        "eval": eval_name,
        "eval_instance": f"run{run_id}" if run_id else "",
        "eval_version": metadata.get("eval_version") or "",
        "exit_reason": metadata.get("exit_reason") or "",
        "score_count": passed,
        "score_total": total,
        "score_pct": score_pct,
        "wall_min": round((metadata.get("wall_clock_seconds") or 0) / 60, 3),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd(metadata.get("model") or "", usage),
        "tools": usage.get("tool_calls"),
        "files": stats.get("file_count"),
        "loc": stats.get("lines_of_code"),
        "result_link": result_link(web_dir, path),
        "transcript_link": "",
        "last_message": editorial.get("last_message") or "",
    }


def sort_key(row: dict) -> tuple:
    effort = row["effort"] or ""
    run_id = int(row["run_id"]) if str(row["run_id"]).isdigit() else 0
    return (row["task"], row["agent"], row["model"], effort, run_id)


def main() -> None:
    args = parse_args()
    published_root = args.published_root.resolve()
    web_dir = args.output.resolve().parent
    rows = []
    excluded = []

    for path in sorted(published_root.rglob("run*.json")):
        if "web" in path.relative_to(published_root).parts:
            continue
        row = build_row(path, web_dir)
        if row["exit_reason"] == "completed":
            rows.append(row)
        else:
            excluded.append(row)

    rows.sort(key=sort_key)
    excluded.sort(key=sort_key)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": "CLISpecBench curated published run JSON files from published_results/**/run*.json",
        "rows_are_official_completed_runs": True,
        "completed_count": len(rows),
        "excluded_count": len(excluded),
        "rows": rows,
        "excluded_runs": excluded,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} completed rows and {len(excluded)} excluded rows to {args.output}")


if __name__ == "__main__":
    main()
