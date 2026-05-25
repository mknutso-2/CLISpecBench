"""Build ignored local per-test dashboard data from published run JSON files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_RUNS_FILE = Path(__file__).with_name("results-published.json")
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("test-results-published.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Build the ignored local per-test JSON aggregate from published run results."),
    )
    parser.add_argument(
        "--runs-file",
        type=Path,
        default=DEFAULT_RUNS_FILE,
        help="Path to results-published.json (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output JSON path (default: %(default)s).",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def result_path(runs_file: Path, result_link: str) -> Path:
    if not result_link:
        raise ValueError("row has no result_link")
    return (runs_file.parent / result_link).resolve()


def run_key(row: dict[str, Any]) -> str:
    return "|".join(str(row.get(key, "")) for key in ("task", "agent", "model", "effort", "run_id"))


def pair_id(row: dict[str, Any]) -> str:
    return f"{row.get('agent', 'unknown')} / {row.get('model', 'unknown')}"


def eval_language(row: dict[str, Any]) -> str:
    return f"{row.get('eval') or 'Unknown'}-{row.get('language') or 'n/a'}"


def test_file(node_id: str) -> str:
    return node_id.split("::", 1)[0] if node_id else ""


def test_name(node_id: str) -> str:
    return node_id.rsplit("::", 1)[-1] if node_id else ""


def normalize_message(test: dict[str, Any]) -> str:
    message = test.get("message")
    return message if isinstance(message, str) else ""


def build_payload(runs_file: Path) -> dict[str, Any]:
    runs_payload = read_json(runs_file)
    official_rows = runs_payload.get("rows", [])
    if not isinstance(official_rows, list):
        raise ValueError(f"{runs_file}: expected a top-level rows array")

    runs: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    outcome_counts: dict[str, int] = {}
    unique_tests: set[tuple[str, str]] = set()

    for run_index, row in enumerate(official_rows):
        if not isinstance(row, dict):
            continue
        key = run_key(row)
        result_link = str(row.get("result_link", ""))
        path = result_path(runs_file, result_link)
        result = read_json(path)
        tests = result.get("tests", [])
        if not isinstance(tests, list):
            raise ValueError(f"{path}: expected tests to be an array")

        run = {
            "run_key": key,
            "task": row.get("task"),
            "eval": row.get("eval"),
            "language": row.get("language"),
            "eval_language": eval_language(row),
            "eval_instance": row.get("eval_instance"),
            "eval_version": row.get("eval_version"),
            "agent": row.get("agent"),
            "model": row.get("model"),
            "effort": row.get("effort"),
            "pair": pair_id(row),
            "run_id": row.get("run_id"),
            "score_count": row.get("score_count"),
            "score_total": row.get("score_total"),
            "score_pct": row.get("score_pct"),
            "result_link": result_link,
            "test_count": len(tests),
        }
        runs.append(run)

        passed = 0
        for ordinal, test in enumerate(tests):
            if not isinstance(test, dict):
                continue
            node_id = str(test.get("node_id") or "")
            outcome = str(test.get("outcome") or "unknown")
            if outcome == "passed":
                passed += 1
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            unique_tests.add((run["eval_language"], node_id))
            rows.append(
                {
                    "row_id": f"{key}|{ordinal}",
                    "run_key": key,
                    "run_index": run_index,
                    "task": run["task"],
                    "eval": run["eval"],
                    "language": run["language"],
                    "eval_language": run["eval_language"],
                    "eval_version": run["eval_version"],
                    "agent": run["agent"],
                    "model": run["model"],
                    "effort": run["effort"],
                    "pair": run["pair"],
                    "run_id": run["run_id"],
                    "result_link": result_link,
                    "test_id": node_id,
                    "test_file": test_file(node_id),
                    "test_name": test_name(node_id),
                    "outcome": outcome,
                    "duration_seconds": test.get("duration_seconds"),
                    "message": normalize_message(test),
                },
            )

        score_count = row.get("score_count")
        if isinstance(score_count, int) and score_count != passed:
            raise ValueError(
                f"{path}: score_count {score_count} does not match {passed} passed test outcomes",
            )

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": (
            "Official completed runs from results-published.json linked curated run JSON files"
        ),
        "completed_run_count": len(runs),
        "test_result_count": len(rows),
        "unique_test_count": len(unique_tests),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "runs": runs,
        "rows": rows,
    }


def main() -> None:
    args = parse_args()
    payload = build_payload(args.runs_file)
    # Keep the ignored local aggregate compact. The full per-test payload can be
    # hundreds of MB; pretty-printing has pushed real datasets above browser
    # string-size limits even though the underlying data is otherwise valid.
    args.output.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {payload['test_result_count']} test results across "
        f"{payload['completed_run_count']} runs to {args.output}",
    )


if __name__ == "__main__":
    main()
