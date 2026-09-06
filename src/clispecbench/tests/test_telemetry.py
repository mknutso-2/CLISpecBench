"""Accounting and migration regressions using recorded CLI event shapes."""
# pyright: reportUnknownMemberType=false, reportPrivateUsage=false

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from clispecbench.agents.codex_cli import (
    TOOL_CALLS_DEFINITION,
    CodexCLIAdapter,
    count_tool_calls,
)
from clispecbench.harness.backfill import backfill_telemetry
from clispecbench.harness.results import TokenUsage, load_result
from clispecbench.tests.test_results import _make_run_result


def _stream(*events: dict[str, Any]) -> str:
    return "\n".join(json.dumps(e) for e in events)


def _item(kind: str, id: str, phase: str = "completed", **details: Any) -> dict[str, Any]:
    return {"type": f"item.{phase}", "item": {"type": kind, "id": id, **details}}


def test_tool_calls_count_edits_search_mcp_failed_and_unfinished_once() -> None:
    events = _stream(
        {"type": "turn.started"},
        _item("command_execution", "a", "started"),
        _item("command_execution", "a", status="failed", exit_code=1),
        _item("file_change", "b", "started"),
        _item("file_change", "b", changes=[{"path": "a"}, {"path": "b"}]),
        _item("file_change", "b", changes=[{"path": "a"}, {"path": "b"}]),
        _item("web_search", "c"),
        _item("mcp_tool_call", "d", "started"),
        _item("agent_message", "e"),
        _item("reasoning", "f"),
        _item("todo_list", "g", "started"),
        _item("todo_list", "g", "updated"),
        _item("todo_list", "g"),
    )
    assert count_tool_calls([events, events]) == 6


def test_tool_count_unknown_is_not_zero() -> None:
    assert count_tool_calls([]) is None
    assert count_tool_calls(["CLI failed to start"]) is None
    assert count_tool_calls([_stream(_item("future_tool", "a"))]) is None
    assert count_tool_calls([_stream({"type": "turn.started"})]) == 0


@pytest.mark.parametrize("cache", [0, 13])
def test_reasoning_and_cache_write_preserved_without_changing_total(
    tmp_path: Path, cache: int
) -> None:
    logs = _stream(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": cache,
                "reasoning_output_tokens": 20,
            },
        }
    )
    usage = CodexCLIAdapter().parse_token_usage(tmp_path, logs)
    assert usage is not None
    assert usage.total_tokens == 150
    assert usage.reasoning_output_tokens == 20
    assert usage.cache_read_input_tokens == 0
    assert usage.cache_creation_input_tokens == cache
    result = _make_run_result("codex-cli", usage)
    result.artifacts.telemetry = ["sessions", "codex-events.jsonl"]
    result.metadata.grading_status = "completed"
    path = tmp_path / "result.json"
    result.write(path)
    restored = load_result(path)
    assert restored.token_usage == usage
    assert restored.artifacts == result.artifacts
    assert restored.metadata.grading_status == "completed"


@pytest.mark.parametrize("matching", [True, False])
def test_enrichment_requires_matching_aggregate(tmp_path: Path, matching: bool) -> None:
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "rollout.jsonl").write_text(
        _stream(
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 100 if matching else 99,
                            "output_tokens": 50,
                            "cached_input_tokens": 0,
                            "reasoning_output_tokens": 20,
                            "cache_write_input_tokens": 0,
                        }
                    },
                },
            }
        )
    )
    usage = CodexCLIAdapter().parse_token_usage(
        tmp_path,
        _stream(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_input_tokens": 0,
                },
            }
        ),
    )
    assert usage is not None
    assert usage.reasoning_output_tokens == (20 if matching else None)
    assert usage.cache_creation_input_tokens == (0 if matching else None)
    assert usage.total_tokens == 150
    assert usage.is_partial is False


def test_historical_missing_reasoning_is_unknown(tmp_path: Path) -> None:
    result = _make_run_result("codex-cli", TokenUsage(100, 50))
    path = tmp_path / "result.json"
    result.write(path)
    data = json.loads(path.read_text())
    for key in ("reasoning_output_tokens", "tool_calls_definition"):
        data["token_usage"].pop(key)
    data["artifacts"].pop("telemetry")
    path.write_text(json.dumps(data))
    usage = load_result(path).token_usage
    assert usage is not None
    assert usage.reasoning_output_tokens is None
    assert usage.total_tokens == 150


def test_backfill_preview_apply_idempotence_and_publication_matching(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    published = tmp_path / "published"
    published.mkdir()
    path = runs / "eval1" / "run1" / "result.json"
    result = _make_run_result("codex-cli", TokenUsage(100, 50, tool_calls=1))
    result.write(path)
    publication = published / "run99.json"
    payload = json.loads(path.read_text())
    payload["editorial"] = {"commentary": "Preserve me", "status": "Complete"}
    publication.write_text(json.dumps(payload))
    (path.parent / "transcript.jsonl").write_text(
        _stream(
            _item("command_execution", "a"),
            _item("file_change", "b"),
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "reasoning_output_tokens": 20,
                    "cache_write_input_tokens": 0,
                },
            },
        )
    )
    original = path.read_bytes()
    preview = backfill_telemetry(runs, published)
    assert preview[0]["status"] == "would_update"
    assert path.read_bytes() == original
    assert len(preview[0]["changes"]) == 2
    assert backfill_telemetry(runs, published, apply=True)[0]["status"] == "updated"
    updated = json.loads(publication.read_text())
    assert updated["token_usage"]["tool_calls"] == 2
    assert updated["token_usage"]["tool_calls_definition"] == TOOL_CALLS_DEFINITION
    assert updated["token_usage"]["reasoning_output_tokens"] == 20
    for key in payload.keys() - {"token_usage"}:
        assert updated[key] == payload[key]
    assert backfill_telemetry(runs, published, apply=True)[0]["status"] == "unchanged"


@pytest.mark.parametrize("problem", ["missing", "unknown", "duplicate", "mismatch"])
def test_backfill_skips_insufficient_or_ambiguous_evidence(tmp_path: Path, problem: str) -> None:
    runs = tmp_path / "runs"
    path = runs / "run1" / "result.json"
    result = _make_run_result("codex-cli", TokenUsage(100, 50, tool_calls=1))
    result.write(path)
    published = tmp_path / "published"
    published.mkdir()
    result.write(published / "run1.json")
    if problem != "missing":
        kind = "unknown" if problem == "unknown" else "file_change"
        (path.parent / "transcript.jsonl").write_text(_stream(_item(kind, "a")))
    if problem == "duplicate":
        result.write(runs / "run2" / "result.json")
    if problem == "mismatch":
        result.metadata.model = "wrong"
        result.write(published / "run1.json")
    before = path.read_bytes()
    audit = backfill_telemetry(runs, published, apply=True)
    assert audit[0]["status"] == "skipped"
    assert path.read_bytes() == before


@pytest.mark.parametrize("grading_status", ["completed", "failed"])
def test_dashboard_rejects_failed_grading_and_exports_breakdowns(
    tmp_path: Path, grading_status: str
) -> None:
    result = _make_run_result(
        "codex-cli",
        TokenUsage(
            100,
            50,
            tool_calls=2,
            tool_calls_definition=TOOL_CALLS_DEFINITION,
            reasoning_output_tokens=20,
        ),
    )
    result.metadata.grading_status = grading_status
    result.write(tmp_path / "run1.json")
    script = Path(__file__).resolve().parents[3] / "published_results/web/build_results_json.py"
    output = tmp_path / "dashboard.json"
    process = subprocess.run(
        [sys.executable, str(script), "--published-root", str(tmp_path), "--output", str(output)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if grading_status == "failed":
        assert process.returncode == 1
        assert "grading failed" in process.stderr
        assert not output.exists()
    else:
        assert process.returncode == 0, process.stderr
        row = json.loads(output.read_text())["rows"][0]
        assert row["reasoning_output_tokens"] == 20
        assert row["tools"] == 2
        assert row["tool_calls_definition"] == TOOL_CALLS_DEFINITION
