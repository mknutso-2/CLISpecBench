"""Tests for the publish pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clispecbench.harness.publish import (
    PublishError,
    find_duplicate_publication,
    find_duplicate_publications,
    next_published_run_number,
    publish_result,
    published_runs_dir,
)
from clispecbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
)


def _make_result_file(path: Path, *, run_uid: str, task: str = "rs274-cpp",
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
    d = published_runs_dir(tmp_path, "rs274-cpp", "claude-code", "claude-opus-4-7", "max")
    assert d == tmp_path / "rs274-cpp" / "claude-code" / "claude-opus-4-7_max"


def test_published_runs_dir_omits_effort_when_none(tmp_path: Path) -> None:
    d = published_runs_dir(tmp_path, "rs274-cpp", "claude-code", "claude-opus-4-7", None)
    assert d == tmp_path / "rs274-cpp" / "claude-code" / "claude-opus-4-7"


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
        published_root / "rs274-cpp" / "claude-code" / "claude-opus-4-7_max" / "run1.json"
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

    target_dir = published_root / "rs274-cpp" / "claude-code" / "claude-opus-4-7_max"
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
        commentary="rs274-cpp-gpt-5.1-high-variance",
    )
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["editorial"]["commentary"] == "rs274-cpp-gpt-5.1-high-variance"


def test_find_duplicate_publication_tolerates_corrupt_files(tmp_path: Path) -> None:
    """Malformed publications in the tree must not crash or bypass the check."""
    published = tmp_path / "published" / "task" / "agent" / "model"
    published.mkdir(parents=True)
    (published / "run1.json").write_text("not json at all")
    (published / "run2.json").write_text("[]")
    (published / "run3.json").write_text('{"metadata": null}')
    (published / "run4.json").write_text(
        json.dumps({"metadata": {"run_uid": "present-uid"}})
    )

    assert find_duplicate_publication(tmp_path / "published", "missing") is None
    assert find_duplicate_publication(tmp_path / "published", "present-uid") == (
        published / "run4.json"
    )


def test_publish_ignores_corrupt_neighbors_when_scanning(tmp_path: Path) -> None:
    """A corrupt sibling file must not block publishing a fresh uid."""
    published_root = tmp_path / "published"
    corrupt_dir = published_root / "rs274-cpp" / "claude-code" / "claude-opus-4-7_max"
    corrupt_dir.mkdir(parents=True)
    (corrupt_dir / "run1.json").write_text("garbage")

    source = tmp_path / "t" / "result.json"
    _make_result_file(source, run_uid="fresh-uid")
    target = publish_result(
        source, published_root, status="Complete", last_message="clean publish",
    )
    assert target.exists()
    assert target.name == "run2.json"  # run1.json is the corrupt one; we skip to run2


def test_publish_rejects_when_invariant_broken(tmp_path: Path) -> None:
    """If the same run_uid appears in >1 published file, refuse to publish.

    That state is always a prior bug and overwriting one of them would just
    compound it. The tree must be fixed manually first.
    """
    published_root = tmp_path / "published"
    dir_a = published_root / "rs274-cpp" / "claude-code" / "model-a"
    dir_b = published_root / "rs274-cpp" / "claude-code" / "model-b"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)
    shared = {"metadata": {"run_uid": "shared-uid"}}
    (dir_a / "run1.json").write_text(json.dumps(shared))
    (dir_b / "run1.json").write_text(json.dumps(shared))

    source = tmp_path / "t" / "result.json"
    _make_result_file(source, run_uid="shared-uid")

    with pytest.raises(PublishError, match="more than one published file"):
        publish_result(
            source, published_root, status="Complete", last_message="x", force=True,
        )


def test_find_duplicate_publications_returns_all_matches(tmp_path: Path) -> None:
    published = tmp_path / "published"
    a = published / "task" / "agent" / "x"
    b = published / "task" / "agent" / "y"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    (a / "run1.json").write_text(json.dumps({"metadata": {"run_uid": "U"}}))
    (b / "run1.json").write_text(json.dumps({"metadata": {"run_uid": "U"}}))
    (b / "run2.json").write_text(json.dumps({"metadata": {"run_uid": "other"}}))

    matches = find_duplicate_publications(published, "U")
    assert len(matches) == 2
    assert all(p.name == "run1.json" for p in matches)


def test_publish_warns_on_missing_commentary(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    """Unknown commentary slug warns but does not block (same-PR workflow)."""
    import logging

    source = tmp_path / "t" / "result.json"
    _make_result_file(source, run_uid="uid-warn")

    with caplog.at_level(logging.WARNING, logger="clispecbench.harness.publish"):
        publish_result(
            source,
            tmp_path / "published",
            status="Complete",
            last_message="x",
            commentary="does-not-exist",
        )

    messages = [r.getMessage() for r in caplog.records]
    assert any(
        "commentary slug" in m and "does-not-exist" in m for m in messages
    )


def test_publish_with_matching_commentary_does_not_warn(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    published_root = tmp_path / "published"
    commentary_dir = published_root / "RS274" / "commentary"
    commentary_dir.mkdir(parents=True)
    (commentary_dir / "my-slug.md").write_text("notes")

    source = tmp_path / "t" / "result.json"
    _make_result_file(source, run_uid="uid-ok")

    with caplog.at_level(logging.WARNING, logger="clispecbench.harness.publish"):
        publish_result(
            source, published_root, status="Complete", last_message="x",
            commentary="my-slug",
        )

    messages = [r.getMessage() for r in caplog.records]
    assert not any("commentary slug" in m for m in messages)


def test_load_result_migrates_legacy_run_id(tmp_path: Path) -> None:
    """Pre-2.0 payloads with ``metadata.run_id`` must still load.

    The legacy run_id is dropped (fields it encoded are already structured in
    metadata) and run_uid defaults to empty — which makes the file
    unpublishable until the run is redone, by design.
    """
    from clispecbench.harness.results import load_result

    legacy_payload: dict[str, object] = {
        "schema_version": "1.1",
        "metadata": {
            "run_id": "rs274-cpp_claude-code_claude-opus-4-7_2026-04-02_run-1",
            "task": "rs274-cpp",
            "agent": "claude-code",
            "agent_version": "1.0.0",
            "prompt_variant": "base",
            "run_number": 1,
            "timestamp": "2026-04-02T00:00:00+00:00",
            "test_suite_version": "abc1234",
            "eval_version": "2.1.1",
            "harness_version": "0.1.0",
            "docker_image_sha": "sha256:test",
            "wall_clock_seconds": 1.0,
            "exit_reason": "completed",
            "model": "claude-opus-4-7",
            "effort": "max",
        },
        "token_usage": None,
        "build": {"success": True, "duration_seconds": 0.0, "diagnostics": ""},
        "tests": [],
        "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "error": 0},
        "scores": {},
    }
    source = tmp_path / "legacy" / "result.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(legacy_payload), encoding="utf-8")

    result = load_result(source)
    assert result.metadata.run_uid == ""
    assert not hasattr(result.metadata, "run_id")
    assert result.metadata.task == "rs274-cpp"
    assert result.metadata.model == "claude-opus-4-7"

    # And confirm publish refuses — the migrated file has no uid to carry.
    with pytest.raises(PublishError, match="no run_uid"):
        publish_result(
            source,
            tmp_path / "published",
            status="Complete",
            last_message="should reject",
        )
