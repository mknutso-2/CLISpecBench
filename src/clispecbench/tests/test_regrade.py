"""Regrades preserve generation history and require a complete new judgment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from clispecbench.cli import _cmd_regrade  # pyright: ignore[reportPrivateUsage]
from clispecbench.harness.regrade import RegradeError, hash_source, regrade_submission
from clispecbench.harness.results import TestOutcome, TestSummary
from clispecbench.harness.scoring import ScoringError, parse_json_report


@pytest.fixture
def saved_run(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    task = repo / "Evals" / "WordCount"
    prompt = task / "prompt"
    (prompt / "docs").mkdir(parents=True)
    (prompt / "base-prompt.md").write_text("Count words.")
    (prompt / "technical-requirements-prompt.md").write_text("Run main.py.")
    shared = repo / "Evals" / "_shared"
    shared.mkdir()
    (shared / "language-requirements-py.md").write_text("Python")
    (task / "VERSION").write_text("9.0.1\n")
    tests = task / "tests"
    tests.mkdir()
    (tests / "test_words.py").write_text("def test_words(): assert True\n")
    original = tmp_path / "old-run" / "result.json"
    original.parent.mkdir()
    (original.parent / "source").mkdir()
    (original.parent / "source" / "main.py").write_text("print('authored source')\n")
    (original.parent / "transcript.jsonl").write_text('{"saved": true}\n')
    # Deliberate nonstandard whitespace proves byte preservation, not a decode /
    # dataclass / encode cycle that could change historical metadata and hashes.
    original.write_text(
        json.dumps(
            {
                "metadata": {
                    "run_uid": "original-run",
                    "task": "wordcount-py",
                    "eval_version": "9.0.0",
                    "test_suite_sha": "old-tests",
                    "prompt_content_sha": "old-prompt",
                },
                "artifacts": {"source_dir": "source", "transcript": "transcript.jsonl"},
                "scores": {"correctness": 0.25},
                "test_summary": {"passed": 1, "failed": 3, "total": 4},
            },
            indent=3,
        )
        + "\n"
    )
    return original, repo


def _completed_grader(
    test_dir: Path, source: Path, report: Path, **_kwargs: object
) -> tuple[list[TestOutcome], TestSummary]:
    assert source.name == "output"
    assert test_dir.name == "tests"
    # A build may modify its working source; this must be an isolated copy, not
    # either historical source or the pristine snapshot recorded in the audit.
    (source / "main.py").write_text("modified by build")
    report.write_text(
        json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 2, "collected": 2, "passed": 1, "failed": 1},
                "tests": [
                    {"nodeid": "test_words.py::test_one", "outcome": "passed", "duration": 0.1},
                    {
                        "nodeid": "test_words.py::test_two",
                        "outcome": "failed",
                        "duration": 0.2,
                        "call": {"longrepr": "expected two words"},
                    },
                ],
            }
        )
    )
    return parse_json_report(report)


def test_regrade_keeps_raw_history_and_pristine_source(
    saved_run: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, repo = saved_run
    original_bytes = original.read_bytes()
    source = original.parent / "source"
    source_bytes = (source / "main.py").read_bytes()
    (source / "build").mkdir()
    (source / "build" / "helper.py").write_text("VALUE = 42\n")
    (source / "empty-data").mkdir()
    before_hash = hash_source(source)
    grader = Mock(side_effect=_completed_grader)
    monkeypatch.setattr("clispecbench.harness.regrade.run_hidden_tests", grader)
    out = tmp_path / "regraded"
    result = regrade_submission(original, out, repo_root=repo, use_docker=False)

    assert original.read_bytes() == (out / "original-result.json").read_bytes() == original_bytes
    assert (
        (source / "main.py").read_bytes() == (out / "source/main.py").read_bytes() == source_bytes
    )
    assert hash_source(source) == before_hash == hash_source(out / "source")
    # Directory names are not evidence that their contents are generated:
    # authored imports must survive even under a conventional build/ directory.
    assert (out / "source/build/helper.py").read_text() == "VALUE = 42\n"
    assert (out / "source/empty-data").is_dir()
    assert "source/empty-data/  [EMPTY]" in before_hash.manifest
    assert not (out / "result.json").exists()  # cannot be picked up as a new model run
    assert result["original"]["result_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert result["original"]["run_uid"] == "original-run"
    assert result["original"]["generation_metadata"]["prompt_content_sha"] == "old-prompt"
    assert result["original"]["generation_metadata"]["eval_version"] == "9.0.0"
    assert result["grading"]["eval_version"] == "9.0.1"
    assert result["grading"]["environment"]["mode"] == "local-diagnostic"
    assert result["grading"]["status"] == "completed"
    assert result["scores"]["correctness"] == result["scores"]["task_score"] == 0.5
    assert result["scores"]["extension_scores"]["subscore.words.passed"] == 1.0
    assert result["tests"][1]["message"] == "expected two words"
    assert result["test_summary"] == {
        "passed": 1,
        "failed": 1,
        "skipped": 0,
        "error": 0,
        "total": 2,
    }
    payload = (out / "test-suite-manifest.sha256").read_text().split("\n", 1)[1]
    assert hashlib.sha256(payload.encode()).hexdigest() == result["grading"]["test_suite_sha"]
    assert (out / "tests/test_words.py").read_bytes() == (
        repo / "Evals/WordCount/tests/test_words.py"
    ).read_bytes()


def test_regrade_defaults_to_an_immutable_docker_image(
    saved_run: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, repo = saved_run
    sandbox = Mock()
    sandbox.get_image_sha.return_value = "sha256:pinned-image"
    monkeypatch.setattr("clispecbench.harness.docker.DockerSandbox", Mock(return_value=sandbox))
    grader = Mock(side_effect=_completed_grader)
    monkeypatch.setattr("clispecbench.harness.regrade.run_hidden_tests", grader)
    result = regrade_submission(original, tmp_path / "audit", repo_root=repo)
    assert grader.call_args.kwargs["use_docker"] is True
    assert grader.call_args.kwargs["docker_image"] == "sha256:pinned-image"
    assert result["grading"]["environment"]["docker_image_sha"] == "sha256:pinned-image"
    sandbox.cleanup.assert_called_once()


def test_regrade_accepts_retained_session_directory_and_event_file(
    saved_run: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, repo = saved_run
    sessions = original.parent / "sessions"
    sessions.mkdir()
    (sessions / "rollout.jsonl").write_text('{"type":"session_meta"}\n')
    (original.parent / "codex-events.jsonl").write_text('{"type":"turn.completed"}\n')
    data = json.loads(original.read_text())
    data["artifacts"]["telemetry"] = ["codex-events.jsonl", "sessions"]
    original.write_text(json.dumps(data))
    original_bytes = original.read_bytes()
    monkeypatch.setattr("clispecbench.harness.regrade.run_hidden_tests", _completed_grader)

    out = tmp_path / "audit"
    result = regrade_submission(original, out, repo_root=repo, use_docker=False)

    assert result["grading"]["status"] == "completed"
    assert original.read_bytes() == (out / "original-result.json").read_bytes() == original_bytes
    assert (sessions / "rollout.jsonl").read_text() == '{"type":"session_meta"}\n'


@pytest.mark.parametrize(
    "path_kind", ["nonempty", "inside-original", "missing-source", "missing-log"]
)
def test_invalid_destinations_and_missing_artifacts_do_not_start_grading(
    saved_run: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path_kind: str
) -> None:
    original, repo = saved_run
    out = tmp_path / "audit"
    if path_kind == "nonempty":
        out.mkdir()
        (out / "keep.txt").write_text("keep me")
    elif path_kind == "inside-original":
        out = original.parent / "audit"
    elif path_kind == "missing-source":
        (original.parent / "source").rename(original.parent / "source-absent")
    else:
        (original.parent / "transcript.jsonl").unlink()
    grader = Mock()
    monkeypatch.setattr("clispecbench.harness.regrade.run_hidden_tests", grader)
    with pytest.raises(RegradeError):
        regrade_submission(original, out, repo_root=repo, use_docker=False)
    grader.assert_not_called()
    if path_kind == "nonempty":
        assert (out / "keep.txt").read_text() == "keep me"
    else:
        assert not out.exists()


def test_symlink_source_is_rejected_without_following_or_modifying_it(
    saved_run: tuple[Path, Path], tmp_path: Path
) -> None:
    original, repo = saved_run
    (original.parent / "source/link.py").symlink_to(original.parent / "transcript.jsonl")
    with pytest.raises(RegradeError, match="symlink"):
        regrade_submission(original, tmp_path / "audit", repo_root=repo, use_docker=False)
    assert not (tmp_path / "audit").exists()


@pytest.mark.parametrize("failure_kind", ["exception", "empty", "partial", "inconsistent"])
def test_failed_or_partial_grader_has_no_valid_score_and_preserves_failure_audit(
    saved_run: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_kind: str
) -> None:
    original, repo = saved_run

    def grader(
        tests: Path, source: Path, report: Path, **kwargs: object
    ) -> tuple[list[TestOutcome], TestSummary]:
        if failure_kind == "exception":
            raise ScoringError("container stopped before report")
        outcomes, summary = _completed_grader(tests, source, report, **kwargs)
        if failure_kind == "empty":
            return [], TestSummary()
        if failure_kind == "inconsistent":
            return outcomes, TestSummary(passed=2)
        data = json.loads(report.read_text())
        data["summary"]["collected"] = 3
        report.write_text(json.dumps(data))
        return outcomes, summary

    monkeypatch.setattr("clispecbench.harness.regrade.run_hidden_tests", grader)
    out = tmp_path / "audit"
    with pytest.raises(RegradeError, match="audit:"):
        regrade_submission(original, out, repo_root=repo, use_docker=False)
    result: dict[str, Any] = json.loads((out / "regrade.json").read_text())
    assert result["grading"]["status"] == "failed"
    assert result["grading"]["error"]
    assert result["scores"]["correctness"] is None
    assert result["scores"]["task_score"] is None
    assert result["test_summary"] is None
    assert result["tests"] == []
    assert (out / "original-result.json").read_bytes() == original.read_bytes()


def test_cli_fails_when_grading_cannot_complete(
    saved_run: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original, repo = saved_run
    monkeypatch.setattr("clispecbench.cli._find_repo_root", lambda: repo)
    monkeypatch.setattr(
        "clispecbench.harness.regrade.run_hidden_tests",
        Mock(side_effect=ScoringError("bad grader")),
    )
    with pytest.raises(SystemExit) as exc:
        _cmd_regrade(argparse.Namespace(source=original, output_dir=tmp_path / "audit", local=True))
    assert exc.value.code == 1
    assert "bad grader" in capsys.readouterr().err


def test_harness_changes_during_grading_cannot_receive_a_valid_score(
    saved_run: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, repo = saved_run
    harness = repo / "src/clispecbench/runner.py"
    harness.parent.mkdir(parents=True)
    harness.write_text("# original grader\n")

    def grader(
        tests: Path, source: Path, report: Path, **kwargs: object
    ) -> tuple[list[TestOutcome], TestSummary]:
        completed = _completed_grader(tests, source, report, **kwargs)
        harness.write_text("# changed while grading\n")
        return completed

    monkeypatch.setattr("clispecbench.harness.regrade.run_hidden_tests", grader)
    out = tmp_path / "audit"
    with pytest.raises(RegradeError, match="Harness files changed"):
        regrade_submission(original, out, repo_root=repo, use_docker=False)
    result = json.loads((out / "regrade.json").read_text())
    assert result["scores"]["correctness"] is None
    assert result["artifacts"]["test_report"] == "test-report.json"


def test_local_integration_preserves_the_saved_source(
    saved_run: tuple[Path, Path], tmp_path: Path
) -> None:
    original, repo = saved_run
    # A tiny real pytest child process exercises invocation/report parsing with
    # no Docker or model calls. It checks the package wrapper and source target.
    test_dir = repo / "Evals/WordCount/tests"
    (test_dir / "conftest.py").write_text(
        "def pytest_addoption(parser):\n"
        "    parser.addoption('--language')\n"
        "    parser.addoption('--implementation-root')\n"
    )
    (test_dir / "test_words.py").write_text(
        "from pathlib import Path\n"
        "def test_saved_source(request):\n"
        "    source = Path(request.config.getoption('--implementation-root'))\n"
        "    assert source.name == 'output'\n"
        "    assert 'authored source' in (source / 'main.py').read_text()\n"
        "    (source / 'main.py').write_text('child changed staging')\n"
    )
    result = regrade_submission(original, tmp_path / "audit", repo_root=repo, use_docker=False)
    assert result["test_summary"]["total"] == result["test_summary"]["passed"] == 1
    assert "authored source" in (original.parent / "source/main.py").read_text()
