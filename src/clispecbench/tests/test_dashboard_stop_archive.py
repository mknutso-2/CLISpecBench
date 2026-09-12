"""Historical stop summaries survive rebuilds without borrowing another run."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


@pytest.fixture
def builder() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "dashboard_stop_archive_test", root / "published_results/web/build_results_json.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def publication(
    tmp_path: Path, builder: ModuleType, monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, dict[str, Any]]:
    published = tmp_path / "published_results"
    web = published / "web"
    web.mkdir(parents=True)
    path = published / "iges-py/codex-cli/example_max/run1.json"
    path.parent.mkdir(parents=True)
    metadata: dict[str, Any] = {
        "run_uid": "generation-uid", "task": "iges-py", "agent": "codex-cli",
        "agent_version": "0.126.0", "model": "example", "effort": "max",
        "prompt_variant": "base", "run_number": 1, "timestamp": "2026-04-27T00:00:00Z",
        "eval_version": "1.0.15", "prompt_content_sha": "prompt-sha",
        "docker_image_sha": "generation-image", "exit_reason": "completed",
    }
    payload = {"metadata": metadata, "test_summary": {"passed": 3, "total": 10},
               "token_usage": {"input_tokens": 100, "output_tokens": 20,
                               "reported_cost_usd": 1.25}}
    path.write_text(json.dumps(payload))
    archive = {
        "schema_version": 1,
        "baseline_artifact": {"revision": "a" * 40, "path": "dashboard.json",
                              "sha256": "b" * 64},
        "entries": {path.relative_to(published).as_posix(): {
            "run_uid": metadata["run_uid"],
            "generation_identity": {
                key: metadata.get(key) for key in builder.GENERATION_IDENTITY_FIELDS
            },
            "baseline_publication_sha256": "c" * 64,
            "stop": {"agent_stop_reason": "context_window_exhausted",
                     "agent_stop_label": "Context limit", "agent_stop_message": "context window"},
        }},
    }
    monkeypatch.setattr(builder, "DEFAULT_STOP_ARCHIVE", web / "agent-stop-archive.v1.json")
    builder.DEFAULT_STOP_ARCHIVE.write_text(json.dumps(archive))
    return path, web, payload


def event_log(
    path: Path, web: Path, metadata: dict[str, Any], *, uid: str, eval_number: int = 1,
) -> Path:
    del path
    base = web.parent.parent / "transient_results" / metadata["task"] / metadata["agent"]
    model = metadata["model"] + "_" + metadata["effort"]
    folder = base / model / f"eval{eval_number}" / f"run{metadata['run_number']}"
    folder.mkdir(parents=True)
    (folder / "result.json").write_text(json.dumps({"metadata": {"run_uid": uid}}))
    result = folder / "codex-events.jsonl"
    result.write_text(json.dumps({"type": "turn.completed"}) + "\n")
    return result


def test_missing_transcripts_preserve_archived_stop_and_numeric_fields(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, _ = publication
    before = path.read_bytes()
    row = builder.build_row(path, web)
    assert row["agent_stop_reason"] == "context_window_exhausted"
    assert row["agent_stop_label"] == "Context limit"
    assert row["agent_stop_message"] == "context window"
    assert row["agent_stop_source"] == "archived-codex-events"
    assert (row["score_count"], row["score_total"], row["score_pct"]) == (3, 10, 30.0)
    assert (row["input_tokens"], row["output_tokens"], row["cost_usd"]) == (100, 20, 1.25)
    assert path.read_bytes() == before


def test_absent_archive_uses_result_fallback(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    builder.DEFAULT_STOP_ARCHIVE.unlink()
    stop = builder.agent_stop_info(path, web, payload)
    assert stop["agent_stop_reason"] == "finished"
    assert stop["agent_stop_source"] == "result-json"


@pytest.mark.parametrize("field", [
    "run_uid", "task", "agent_version", "model", "effort", "prompt_variant",
    "run_number", "timestamp", "eval_version", "prompt_content_sha", "docker_image_sha",
])
def test_archive_identity_mismatch_does_not_apply(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]], field: str,
) -> None:
    path, web, original = publication
    payload = copy.deepcopy(original)
    payload["metadata"][field] = "different"
    stop = builder.agent_stop_info(path, web, payload)
    assert stop["agent_stop_source"] == "result-json"
    assert stop["agent_stop_reason"] == "finished"


def test_archive_is_bound_to_publication_path(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    other = path.with_name("run2.json")
    assert builder.agent_stop_info(other, web, payload)["agent_stop_source"] == "result-json"


def test_matching_local_events_take_precedence(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    metadata = payload["metadata"]
    event_log(path, web, metadata, uid=metadata["run_uid"])
    stop = builder.agent_stop_info(path, web, payload)
    assert stop["agent_stop_reason"] == "finished"
    assert stop["agent_stop_source"] == "codex-events"


def test_wrong_uid_event_log_is_never_borrowed(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    event_log(path, web, payload["metadata"], uid="another-generation")
    assert builder.transient_event_log_for(path, web.parent, payload["metadata"]) is None
    stop = builder.agent_stop_info(path, web, payload)
    assert stop["agent_stop_source"] == "archived-codex-events"


def test_matching_uid_wins_over_later_unrelated_candidate(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    metadata = payload["metadata"]
    expected = event_log(path, web, metadata, uid=metadata["run_uid"])
    event_log(path, web, metadata, uid="unrelated", eval_number=2)
    assert builder.transient_event_log_for(path, web.parent, metadata) == expected


def test_missing_candidate_identity_cannot_match_known_uid(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    candidate = event_log(path, web, payload["metadata"], uid="another-generation")
    (candidate.parent / "result.json").write_text("[]")
    assert builder.transient_event_log_for(path, web.parent, payload["metadata"]) is None


def test_matching_incomplete_local_log_is_not_overridden(
    builder: ModuleType, publication: tuple[Path, Path, dict[str, Any]],
) -> None:
    path, web, payload = publication
    candidate = event_log(path, web, payload["metadata"], uid=payload["metadata"]["run_uid"])
    candidate.write_text(json.dumps({"type": "turn.started"}) + "\n")
    stop = builder.agent_stop_info(path, web, payload)
    assert stop["agent_stop_source"] == "codex-events"
    assert stop["agent_stop_reason"] == "unknown"
