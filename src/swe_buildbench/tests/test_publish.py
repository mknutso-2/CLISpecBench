"""Tests for the publish pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swe_buildbench.harness.publish import (
    PublishError,
    find_duplicate_publication,
    next_published_run_number,
    publish_result,
    published_runs_dir,
)
from swe_buildbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
)


def _make_result_file(path: Path, *, run_uid: str, task: str = "cncsim-cpp",
                     agent: str = "claude-code", model: str | None = "claude-opus-4-7",
                     effort: str | None = "max") -> RunResult:
    """Write a minimal RunResult to ``path`` and return it."""
    result = RunResult(
        metadata=RunMetadata(
            run_uid=run_uid,
            task=task,
            agent=agent,
            agent_version="1.0.0",
            prompt_variant="base",
            run_number=1,
            timestamp="2026-04-19T00:00:00+00:00",
            test_suite_version="abc1234",
            eval_version="2.1.1",
            harness_version="0.1.0",
            docker_image_sha="sha256:test",
            wall_clock_seconds=1.0,
            exit_reason="completed",
            model=model,
            effort=effort,
        ),
        token_usage=None,
        build=BuildResult(success=True, duration_seconds=0.0),
        tests=[],
        test_summary=TestSummary(),
        scores=Scores(),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    result.write(path)
    return result


def test_published_runs_dir_includes_model_effort(tmp_path: Path) -> None:
    d = published_runs_dir(tmp_path, "cncsim-cpp", "claude-code", "claude-opus-4-7", "max")
    assert d == tmp_path / "cncsim-cpp" / "claude-code" / "claude-opus-4-7_max"


def test_published_runs_dir_omits_effort_when_none(tmp_path: Path) -> None:
    d = published_runs_dir(tmp_path, "cncsim-cpp", "claude-code", "claude-opus-4-7", None)
    assert d == tmp_path / "cncsim-cpp" / "claude-code" / "claude-opus-4-7"


def test_next_published_run_number_empty_dir(tmp_path: Path) -> None:
    assert next_published_run_number(tmp_path / "missing") == 1
    (tmp_path / "empty").mkdir()
    assert next_published_run_number(tmp_path / "empty") == 1


def test_next_published_run_number_increments(tmp_path: Path) -> None:
    (tmp_path / "run1.json").write_text("{}")
    (tmp_path / "run3.json").write_text("{}")  # gaps are fine
    (tmp_path / "notes.md").write_text("ignored")
    assert next_published_run_number(tmp_path) == 4


def test_publish_writes_first_run_file_and_strips_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "transient" / "result.json"
    _make_result_file(source, run_uid="uid-1")
    published_root = tmp_path / "published"

    target = publish_result(
        source,
        published_root,
        status="Complete",
        last_message="Claims complete; built cleanly.",
    )

    expected = (
        published_root / "cncsim-cpp" / "claude-code" / "claude-opus-4-7_max" / "run1.json"
    )
    assert target == expected
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["metadata"]["run_uid"] == "uid-1"
    assert payload["editorial"] == {
        "status": "Complete",
        "last_message": "Claims complete; built cleanly.",
        "commentary": None,
    }
    assert "artifacts" not in payload


def test_publish_auto_increments_across_calls(tmp_path: Path) -> None:
    published_root = tmp_path / "published"
    for i in (1, 2, 3):
        source = tmp_path / f"t{i}" / "result.json"
        _make_result_file(source, run_uid=f"uid-{i}")
        publish_result(source, published_root, status="Complete", last_message=f"run {i}")

    target_dir = published_root / "cncsim-cpp" / "claude-code" / "claude-opus-4-7_max"
    names = sorted(p.name for p in target_dir.iterdir())
    assert names == ["run1.json", "run2.json", "run3.json"]


def test_publish_rejects_result_without_run_uid(tmp_path: Path) -> None:
    source = tmp_path / "transient" / "result.json"
    _make_result_file(source, run_uid="")  # legacy / pre-2.0
    published_root = tmp_path / "published"

    with pytest.raises(PublishError, match="no run_uid"):
        publish_result(source, published_root, status="Complete", last_message="x")


def test_publish_rejects_duplicate_run_uid_without_force(tmp_path: Path) -> None:
    published_root = tmp_path / "published"
    first = tmp_path / "a" / "result.json"
    _make_result_file(first, run_uid="shared-uid")
    publish_result(first, published_root, status="Complete", last_message="first")

    second = tmp_path / "b" / "result.json"
    _make_result_file(second, run_uid="shared-uid")
    with pytest.raises(PublishError, match="already published"):
        publish_result(second, published_root, status="Complete", last_message="second")


def test_publish_with_force_overwrites_duplicate(tmp_path: Path) -> None:
    published_root = tmp_path / "published"
    first = tmp_path / "a" / "result.json"
    _make_result_file(first, run_uid="shared-uid")
    first_target = publish_result(
        first, published_root, status="Complete", last_message="first",
    )

    second = tmp_path / "b" / "result.json"
    _make_result_file(second, run_uid="shared-uid")
    second_target = publish_result(
        second,
        published_root,
        status="Complete",
        last_message="second (re-publish)",
        force=True,
    )

    assert second_target == first_target  # same path, overwritten
    payload = json.loads(second_target.read_text(encoding="utf-8"))
    assert payload["editorial"]["last_message"] == "second (re-publish)"


def test_find_duplicate_publication_returns_none_when_missing(tmp_path: Path) -> None:
    assert find_duplicate_publication(tmp_path, "anything") is None
    assert find_duplicate_publication(tmp_path, "") is None


def test_publish_carries_commentary_slug(tmp_path: Path) -> None:
    source = tmp_path / "t" / "result.json"
    _make_result_file(source, run_uid="uid-commentary")
    target = publish_result(
        source,
        tmp_path / "published",
        status="Complete",
        last_message="see commentary",
        commentary="cncsim-cpp-gpt-5.1-high-variance",
    )
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["editorial"]["commentary"] == "cncsim-cpp-gpt-5.1-high-variance"
