"""Build dashboard data from curated published run JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from clispecbench.harness.pricing import estimate_cost
from clispecbench.harness.status import INCLUDED_NON_COMPLETED_STATUSES

DEFAULT_PUBLISHED_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results-published.json")
DEFAULT_STOP_ARCHIVE = Path(__file__).with_name("agent-stop-archive.v1.json")

# These describe the original generation, so regrading or editorial changes
# cannot transfer a historical stop message to a different submission.
GENERATION_IDENTITY_FIELDS = (
    "task", "agent", "agent_version", "model", "effort", "prompt_variant",
    "run_number", "timestamp", "eval_version", "prompt_content_sha", "docker_image_sha",
)

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

OMIT_AGENT_STOP_REASONS = {
    "usage_limit",
    "stream_disconnect",
    "auth_failure",
    "credential_error",
    "local_interruption",
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


def number(value: object) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    return None


def integer(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def cost_usd(model: str, usage: dict[str, Any]) -> float | int | None:
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


def run_number(path: Path, metadata: dict[str, Any]) -> str:
    stem = path.stem
    if stem.startswith("run") and stem[3:].isdigit():
        return stem[3:]
    value = metadata.get("run_number")
    return str(value) if value is not None else ""


def result_link(web_dir: Path, path: Path) -> str:
    return "../" + path.resolve().relative_to(web_dir.parent.resolve()).as_posix()


def iter_jsonl_dicts(path: Path) -> Iterator[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield cast(dict[str, Any], event)


def classify_agent_stop_message(message: str) -> tuple[str, str] | None:
    text = message.strip()
    if not text:
        return None
    lowered = text.lower()
    if (
        "output token maximum" in lowered
        or "output token cap" in lowered
        or ("per-response" in lowered and "token cap" in lowered)
    ):
        return "output_token_limit", "Output token cap"
    if (
        "context window" in lowered
        or "ran out of room" in lowered
        or "input exceeds the context" in lowered
    ):
        return "context_window_exhausted", "Context limit"
    if "usage limit" in lowered or "you've hit your limit" in lowered or "usage cap" in lowered:
        return "usage_limit", "Usage limit"
    if (
        "stream disconnected" in lowered
        or "idle timeout" in lowered
        or "websocket" in lowered
        or "connection reset" in lowered
    ):
        return "stream_disconnect", "Stream disconnect"
    return None


def transient_event_log_for(
    path: Path, published_root: Path, metadata: dict[str, Any]
) -> Path | None:
    repo_root = published_root.parent
    task = metadata.get("task") or path.parts[-4]
    agent = metadata.get("agent") or ""
    model = metadata.get("model") or ""
    effort = metadata.get("effort") or ""
    run_number_value = metadata.get("run_number") or run_number(path, metadata)
    run_dir_name = f"run{run_number_value}"
    model_dir = f"{model}_{effort}" if effort else model
    base = repo_root / "transient_results" / task / agent / model_dir
    if not base.is_dir():
        return None

    candidates = sorted(base.glob(f"eval*/{run_dir_name}/codex-events.jsonl"))
    if not candidates:
        return None

    run_uid = metadata.get("run_uid")
    if run_uid is not None:
        if not isinstance(run_uid, str) or not run_uid:
            return None
        for candidate in candidates:
            result_path = candidate.parent / "result.json"
            if not result_path.is_file():
                continue
            try:
                result_payload = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(result_payload, dict):
                continue
            result_metadata = cast(dict[str, Any], result_payload).get("metadata")
            if not isinstance(result_metadata, dict):
                continue
            result_metadata = cast(dict[str, Any], result_metadata)
            if result_metadata.get("run_uid") == run_uid:
                return candidate
        # A publication run number can differ from the original transient run
        # number. Never substitute another generation's latest event log.
        return None

    return candidates[-1]


def archived_codex_agent_stop(
    path: Path, published_root: Path, metadata: dict[str, Any]
) -> dict[str, str] | None:
    """Recover only an identity-matched summary from the versioned dashboard.

    This archive retains an earlier derived observation, not a local transcript.
    It is consulted only after matching local canonical events are unavailable.
    """
    if not DEFAULT_STOP_ARCHIVE.is_file():
        return None
    archive: object = json.loads(DEFAULT_STOP_ARCHIVE.read_text(encoding="utf-8"))
    if not isinstance(archive, dict):
        raise ValueError("Expected an agent-stop archive object")
    archive = cast(dict[str, Any], archive)
    if archive.get("schema_version") != 1 or not isinstance(archive.get("entries"), dict):
        raise ValueError("Unsupported agent-stop archive schema")
    baseline = archive.get("baseline_artifact")
    if not isinstance(baseline, dict) or not all(
        isinstance(cast(dict[str, Any], baseline).get(key), str)
        and cast(dict[str, Any], baseline)[key]
        for key in ("revision", "path", "sha256")
    ):
        raise ValueError("Agent-stop archive lacks baseline provenance")
    try:
        relative = path.resolve().relative_to(published_root.resolve()).as_posix()
    except ValueError:
        return None
    entry = cast(dict[str, Any], archive["entries"]).get(relative)
    if not isinstance(entry, dict):
        return None
    entry = cast(dict[str, Any], entry)
    run_uid = metadata.get("run_uid")
    if not isinstance(run_uid, str) or not run_uid or entry.get("run_uid") != run_uid:
        return None
    identity = {key: metadata.get(key) for key in GENERATION_IDENTITY_FIELDS}
    if entry.get("generation_identity") != identity:
        return None
    stop = entry.get("stop")
    keys = ("agent_stop_reason", "agent_stop_label", "agent_stop_message")
    if not isinstance(stop, dict) or not all(
        isinstance(cast(dict[str, Any], stop).get(key), str) for key in keys
    ):
        raise ValueError(f"Malformed archived stop summary for {relative}")
    result = {key: cast(dict[str, str], stop)[key] for key in keys}
    result["agent_stop_source"] = "archived-codex-events"
    return result


def codex_agent_stop(
    path: Path, published_root: Path, metadata: dict[str, Any]
) -> dict[str, str] | None:
    event_log = transient_event_log_for(path, published_root, metadata)
    if event_log is None:
        return None

    final_turn: dict[str, Any] | None = None
    for event in iter_jsonl_dicts(event_log):
        if event.get("type") in {"turn.completed", "turn.failed"}:
            final_turn = event

    if final_turn is None:
        return {
            "agent_stop_reason": "unknown",
            "agent_stop_label": "Unknown",
            "agent_stop_message": "",
            "agent_stop_source": "codex-events",
        }
    if final_turn.get("type") == "turn.completed":
        return {
            "agent_stop_reason": "finished",
            "agent_stop_label": "Finished",
            "agent_stop_message": "",
            "agent_stop_source": "codex-events",
        }

    error = final_turn.get("error")
    message = ""
    if isinstance(error, dict):
        message = str(cast(dict[str, Any], error).get("message") or "")
    elif isinstance(error, str):
        message = error
    classified = classify_agent_stop_message(message)
    if classified is None:
        classified = ("agent_turn_failed", "Agent error")
    reason, label = classified
    return {
        "agent_stop_reason": reason,
        "agent_stop_label": label,
        "agent_stop_message": message,
        "agent_stop_source": "codex-events",
    }


def agent_stop_info(path: Path, web_dir: Path, payload: dict[str, Any]) -> dict[str, str]:
    metadata: dict[str, Any] = payload.get("metadata") or {}
    editorial: dict[str, Any] = payload.get("editorial") or {}
    published_root = web_dir.parent.resolve()
    exit_reason = metadata.get("exit_reason") or ""

    if metadata.get("agent") == "codex-cli":
        from_events = codex_agent_stop(path, published_root, metadata)
        if from_events is not None:
            return from_events
        archived = archived_codex_agent_stop(path, published_root, metadata)
        if archived is not None:
            return archived

    message_candidates = [
        metadata.get("agent_last_message") or "",
        editorial.get("last_message") or "",
        metadata.get("notes") or "",
        editorial.get("commentary") or "",
    ]
    for message in message_candidates:
        classified = classify_agent_stop_message(message)
        if classified is not None:
            reason, label = classified
            return {
                "agent_stop_reason": reason,
                "agent_stop_label": label,
                "agent_stop_message": message,
                "agent_stop_source": "result-json",
            }

    if exit_reason == "completed":
        return {
            "agent_stop_reason": "finished",
            "agent_stop_label": "Finished",
            "agent_stop_message": "",
            "agent_stop_source": "result-json",
        }

    status = editorial.get("status") or exit_reason or "Error"
    return {
        "agent_stop_reason": exit_reason or "error",
        "agent_stop_label": status,
        "agent_stop_message": metadata.get("agent_last_message")
        or editorial.get("last_message")
        or "",
        "agent_stop_source": "result-json",
    }


def build_row(path: Path, web_dir: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata: dict[str, Any] = payload.get("metadata") or {}
    summary: dict[str, Any] = payload.get("test_summary") or {}
    usage: dict[str, Any] = payload.get("token_usage") or {}
    stats: dict[str, Any] = payload.get("source_stats") or {}
    editorial: dict[str, Any] = payload.get("editorial") or {}
    regrade: dict[str, Any] = payload.get("regrade") or {}
    grading: dict[str, Any] = regrade.get("grading") or {}
    grading_environment: dict[str, Any] = grading.get("environment") or {}
    exit_reason = metadata.get("exit_reason") or ""
    status = editorial.get("status") or ("Complete" if exit_reason == "completed" else exit_reason)

    task = metadata.get("task") or path.parts[-4]
    eval_name, language = task_eval_language(task)
    run_id = run_number(path, metadata)
    passed = summary.get("passed", 0) or 0
    total = summary.get("total", 0) or 0
    score_pct = round((passed / total) * 100, 3) if total else None
    grading_status = grading.get("status", metadata.get("grading_status"))
    if grading_status not in (None, "completed"):
        score_pct = None
    input_tokens = usage.get("input_tokens") or 0
    output_tokens = usage.get("output_tokens") or 0
    total_tokens = usage.get("total_tokens")
    if total_tokens is None:
        total_tokens = input_tokens + output_tokens
    stop_info = agent_stop_info(path, web_dir, payload)

    return {
        "task": task,
        "language": language,
        "agent": metadata.get("agent") or "",
        "agent_version": metadata.get("agent_version") or "",
        "served_model": metadata.get("served_model") or "",
        "model": metadata.get("model") or "",
        "effort": metadata.get("effort") or "",
        "prompt_variant": metadata.get("prompt_variant") or "base",
        "run_id": run_id,
        "eval": eval_name,
        "eval_instance": f"run{run_id}" if run_id else "",
        "eval_version": grading.get("eval_version") or metadata.get("eval_version") or "",
        "generation_eval_version": metadata.get("eval_version") or "",
        "comparison_cohort": regrade.get("comparison_cohort")
        or editorial.get("comparison_cohort")
        or "",
        "grading_image_sha": grading_environment.get("docker_image_sha")
        or metadata.get("docker_image_sha")
        or "",
        "regrade_uid": regrade.get("regrade_uid") or "",
        "exit_reason": exit_reason,
        "grading_status": grading_status,
        "status": status,
        **stop_info,
        "notes": (
            editorial.get("notes") or metadata.get("notes") or editorial.get("commentary") or ""
        ),
        "score_count": passed,
        "score_total": total,
        "score_pct": score_pct,
        "wall_min": round((metadata.get("wall_clock_seconds") or 0) / 60, 3),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": usage.get("reasoning_output_tokens"),
        "total_tokens": total_tokens,
        "cost_usd": cost_usd(metadata.get("model") or "", usage),
        "tools": usage.get("tool_calls"),
        "tool_calls_definition": usage.get("tool_calls_definition"),
        "files": stats.get("file_count"),
        "loc": stats.get("lines_of_code"),
        "result_link": result_link(web_dir, path),
        "transcript_link": "",
        "last_message": editorial.get("last_message") or "",
    }


def sort_key(row: dict[str, Any]) -> tuple[str, str, str, str, int]:
    effort = row["effort"] or ""
    run_id = int(row["run_id"]) if str(row["run_id"]).isdigit() else 0
    return (row["task"], row["agent"], row["model"], effort, run_id)


def main() -> None:
    args = parse_args()
    published_root = args.published_root.resolve()
    web_dir = args.output.resolve().parent
    rows: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    invariant_violations: list[tuple[Path, str, str]] = []

    # Every published row must be either exit_reason="completed" or carry an
    # editorial status in the canonical model_* taxonomy from
    # clispecbench.harness.status. The publish CLI enforces this at the gate,
    # so a row that fails this check here means one of:
    #   - a legacy file was published before the gate existed,
    #   - someone bypassed the gate (hand-edit, manual file copy, etc.),
    #   - the gate itself has a hole.
    # Any of those is a real bug — fail loudly here so the dashboard can't
    # silently drift behind a broken state.
    for path in sorted(published_root.rglob("run*.json")):
        if "web" in path.relative_to(published_root).parts:
            continue
        row = build_row(path, web_dir)
        if row["grading_status"] not in (None, "completed"):
            invariant_violations.append((path, "grading failed", row.get("status") or ""))
            continue
        if row.get("agent_stop_reason") in OMIT_AGENT_STOP_REASONS:
            omitted.append(row)
            continue
        if (
            row["exit_reason"] == "completed"
            or row.get("status") in INCLUDED_NON_COMPLETED_STATUSES
        ):
            rows.append(row)
        else:
            invariant_violations.append(
                (path, row.get("exit_reason") or "", row.get("status") or "")
            )

    if invariant_violations:
        print(
            "ERROR: published_results contains rows that are neither "
            "exit_reason=completed nor a recognized model_* status.\n"
            "These violate the policy that the publish CLI gate exists to "
            "prevent. Resolve before regenerating the dashboard:\n",
            file=sys.stderr,
        )
        for path, exit_reason, status in invariant_violations:
            rel = path.relative_to(published_root)
            print(
                f"  {rel}: exit_reason={exit_reason!r}, editorial.status={status!r}",
                file=sys.stderr,
            )
        print(
            "\nValid model_* statuses: " + ", ".join(sorted(INCLUDED_NON_COMPLETED_STATUSES)),
            file=sys.stderr,
        )
        print(
            "See .claude/skills/run-eval/SKILL.md and "
            "clispecbench.harness.status for the canonical taxonomy.",
            file=sys.stderr,
        )
        sys.exit(1)

    rows.sort(key=sort_key)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": (
            "CLISpecBench curated published run JSON files from published_results/**/run*.json"
        ),
        "rows_are_official_completed_runs": True,
        "omits_user_environment_stops": True,
        "completed_count": len(rows),
        "omitted_count": len(omitted),
        "rows": rows,
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(rows)} completed rows and omitted "
        f"{len(omitted)} user/environment stops to {args.output}"
    )


if __name__ == "__main__":
    main()
