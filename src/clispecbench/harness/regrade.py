"""Rejudge preserved source without rewriting the model's historical run.

A regrade is a separate observation of old source under a new rubric. It is
deliberately not a RunResult: its generation prompt, tokens, and completion
state belong to the original run, not to the grading environment recorded here.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from clispecbench.harness.hashing import ContentHash, hash_paths, write_manifest
from clispecbench.harness.results import Scores, TestOutcome, TestSummary
from clispecbench.harness.scoring import (
    TEST_RUNNER_IMAGE,
    ScoringError,
    compute_correctness,
    compute_subscores,
    compute_task_score,
    parse_json_report,
    run_hidden_tests,
)
from clispecbench.harness.task import resolve_task


class RegradeError(RuntimeError):
    """A regrade could not be safely prepared or completed."""


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise RegradeError(f"Expected a JSON object: {path}")
    return cast(dict[str, Any], value)


def _source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        # Following links could read outside the preserved submission or let
        # staging writes reach its original source. Reject rather than alter it.
        if path.is_symlink():
            raise RegradeError(f"Source contains a symlink; cannot snapshot safely: {relative}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise RegradeError(f"Source contains a non-regular file: {relative}")
    if not files:
        raise RegradeError(f"Source contains no files: {root}")
    return files


def hash_source(root: Path) -> ContentHash:
    """Hash every preserved file, without guessing which directories are generated.

    A submission can legitimately import authored ``build/helper.py`` or use
    vendored dependencies. Excluding names such as build/target/node_modules
    would change the program being graded. Explicit file entries also preserve
    caches in this manifest instead of applying test-suite cache exclusions.
    """
    entries = [
        (f"source/{path.relative_to(root).as_posix()}", path) for path in _source_files(root)
    ]
    # Empty directories may be authored runtime inputs too. Nonempty directory
    # topology is implicit in file paths; record empty leaves explicitly.
    entries.extend(
        (f"source/{path.relative_to(root).as_posix()}", path)
        for path in root.rglob("*")
        if path.is_dir() and not any(path.iterdir())
    )
    return hash_paths(sorted(entries, key=lambda entry: entry[0]))


def _artifact_path(run_dir: Path, name: object, *, directory: bool | None = False) -> Path:
    if not isinstance(name, str) or not name:
        raise RegradeError("Missing or invalid source/artifact path in original result")
    relative = Path(name)
    path = (run_dir / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(run_dir):
        raise RegradeError(
            f"Artifact must be relative to and contained in the run directory: {name}"
        )
    present = (
        path.is_file() or path.is_dir()
        if directory is None
        else (path.is_dir() if directory else path.is_file())
    )
    if not present:
        raise RegradeError(f"Original artifact is missing: {path}")
    return path


def _repository_state(repo_root: Path) -> dict[str, object]:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    try:
        return {
            "revision": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--untracked-files=normal")),
        }
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"revision": None, "dirty": None, "error": str(exc)}


def _grading_environment(repo_root: Path, *, use_docker: bool) -> dict[str, object]:
    environment: dict[str, object] = {
        "mode": "docker" if use_docker else "local-diagnostic",
        "host_platform": platform.platform(),
        "host_python": sys.version,
        "host_python_executable": sys.executable,
    }
    if use_docker:
        from clispecbench.harness.docker import DockerSandbox

        sandbox = DockerSandbox()
        try:
            if not sandbox.image_exists(TEST_RUNNER_IMAGE):
                sandbox.build_image(repo_root / "docker" / "base.Dockerfile", TEST_RUNNER_IMAGE)
            image_sha = sandbox.get_image_sha(TEST_RUNNER_IMAGE)
            if not image_sha.startswith("sha256:"):
                raise RegradeError("Could not resolve an immutable grader image ID")
            environment.update(docker_image_tag=TEST_RUNNER_IMAGE, docker_image_sha=image_sha)
        finally:
            sandbox.cleanup()
    return environment


def _validate_grade(tests: list[TestOutcome], summary: TestSummary, report_path: Path) -> None:
    """Defend the artifact boundary against a partial or inconsistent scorer."""
    raw = _read_object(report_path)
    if raw.get("exitcode") not in (0, 1):
        raise ScoringError("Grader report does not describe a completed pytest run")
    if not tests or len({test.node_id for test in tests}) != len(tests):
        raise ScoringError("Grader returned empty or duplicate test outcomes")
    parsed_tests, parsed_summary = parse_json_report(report_path)
    if tests != parsed_tests or summary != parsed_summary or summary.total != len(tests):
        raise ScoringError("Grader outcomes and report disagree")
    raw_summary = raw.get("summary")
    if not isinstance(raw_summary, dict):
        raise ScoringError("Grader report summary is not an object")
    raw_summary = cast(dict[str, Any], raw_summary)
    if raw_summary.get("total") != summary.total:
        raise ScoringError("Grader report total does not match all outcomes")
    collected = raw_summary.get("collected")
    if collected is not None and collected != summary.total:
        raise ScoringError("Grader did not report every collected test")
    if any(
        test.outcome not in {"passed", "failed", "skipped", "error", "xfailed", "xpassed"}
        for test in tests
    ):
        raise ScoringError("Grader returned an unknown test outcome")


def regrade_submission(
    original_result: Path,
    output_dir: Path,
    *,
    repo_root: Path,
    use_docker: bool = True,
) -> dict[str, Any]:
    """Write an independent regrade artifact; never mutate original artifacts.

    A grader failure is persisted with null scores and then raises RegradeError.
    Input/refusal errors occur before creating any output. Docker is the default;
    local execution is explicitly a host-dependent diagnostic.
    """
    original_result = original_result.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    if not original_result.is_file():
        raise RegradeError(f"Original result does not exist: {original_result}")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise RegradeError(f"Output directory must be new or empty: {output_dir}")
    try:
        original_bytes = original_result.read_bytes()
        original = _read_object(original_result)
        metadata = original["metadata"]
        artifacts = original["artifacts"]
        if not isinstance(metadata, dict) or not isinstance(artifacts, dict):
            raise RegradeError("Original result needs metadata and artifacts objects")
        metadata = cast(dict[str, Any], metadata)
        artifacts = cast(dict[str, Any], artifacts)
        if not isinstance(metadata.get("run_uid"), str) or not metadata["run_uid"]:
            raise RegradeError("Original run_uid is missing")
        task_id = metadata.get("task")
        if not isinstance(task_id, str):
            raise RegradeError("Original task identifier is missing")
        task = resolve_task(repo_root, task_id)
        source = _artifact_path(original_result.parent, artifacts.get("source_dir"), directory=True)
        # A published JSON without its source/session artifacts is not a saved
        # submission. Never silently discover a different run to fill the gap.
        for key in ("transcript", "network_audit"):
            if artifacts.get(key) is not None:
                _artifact_path(original_result.parent, artifacts[key])
        telemetry = artifacts.get("telemetry", [])
        if not isinstance(telemetry, list):
            raise RegradeError("Original telemetry artifact paths must be a list")
        for entry in cast(list[object], telemetry):
            # Codex preserves its richer session as a directory alongside
            # individual event/report files. Both are valid telemetry artifacts.
            _artifact_path(original_result.parent, entry, directory=None)
        source_hash = hash_source(source)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RegradeError(f"Invalid original result: {exc}") from exc
    if output_dir.is_relative_to(original_result.parent):
        raise RegradeError("Output directory must be outside the original run directory")
    if output_dir.is_relative_to(task.test_dir):
        raise RegradeError("Output directory must be outside the canonical test suite")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "original-result.json").write_bytes(original_bytes)
    source_snapshot = output_dir / "source"
    # Preserve empty directories, permissions, and all file bytes. Copy links
    # as links if one appears after validation; the hash recheck rejects it
    # without following it into an unrelated directory.
    shutil.copytree(source, source_snapshot, symlinks=True)
    write_manifest(output_dir / "source-manifest.sha256", source_hash)
    # Keep the precise rubric used here even while another agent edits tests.
    test_snapshot = output_dir / "tests"
    shutil.copytree(
        task.test_dir,
        test_snapshot,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".pytest_cache"),
    )
    test_hash = hash_paths([("tests", test_snapshot)])
    write_manifest(output_dir / "test-suite-manifest.sha256", test_hash)
    harness_entries = [
        ("src/clispecbench", repo_root / "src" / "clispecbench"),
        ("pyproject.toml", repo_root / "pyproject.toml"),
        ("docker/base.Dockerfile", repo_root / "docker" / "base.Dockerfile"),
    ]
    harness_hash = hash_paths(harness_entries)
    write_manifest(output_dir / "harness-manifest.sha256", harness_hash)
    grading: dict[str, Any] = {
        "task": task.task_id,
        "language": task.language,
        "eval_version": task.version,
        "test_suite_sha": test_hash.sha256,
        "harness_content_sha": harness_hash.sha256,
        "repository": _repository_state(repo_root),
        "environment": {"mode": "docker" if use_docker else "local-diagnostic"},
        "started_at": datetime.now(UTC).isoformat(),
        "status": "failed",
        "error": None,
    }
    result: dict[str, Any] = {
        "artifact_type": "clispecbench.regrade",
        "schema_version": "1.0",
        "regrade_uid": str(uuid.uuid4()),
        "original": {
            "run_uid": metadata["run_uid"],
            "result_path": str(original_result),
            "result_sha256": hashlib.sha256(original_bytes).hexdigest(),
            "generation_metadata": metadata,
            "scores": original.get("scores"),
            "test_summary": original.get("test_summary"),
            "source_content_sha": source_hash.sha256,
        },
        "grading": grading,
        "source_exclusions": {
            "directory_names": [],
            "suffixes": [],
        },
        "tests": [],
        "test_summary": None,
        "scores": asdict(Scores()),
        "artifacts": {
            "original_result": "original-result.json",
            "source_dir": "source",
            "source_manifest": "source-manifest.sha256",
            "test_dir": "tests",
            "test_suite_manifest": "test-suite-manifest.sha256",
            "harness_manifest": "harness-manifest.sha256",
            "test_report": None,
        },
    }
    report_path = output_dir / "test-report.json"
    try:
        if hash_source(source_snapshot) != source_hash:
            raise RegradeError("Source changed while its snapshot was copied")
        environment = _grading_environment(repo_root, use_docker=use_docker)
        grading["environment"] = environment
        image = cast(str | None, environment.get("docker_image_sha"))
        # Build/run only a disposable copy. The output wrapper matches agent
        # workspaces and the ordinary Docker grader's package layout.
        with tempfile.TemporaryDirectory(prefix="clispecbench-regrade-") as staging:
            staged_source = Path(staging) / "submission" / "output"
            shutil.copytree(source_snapshot, staged_source)
            tests, summary = run_hidden_tests(
                test_snapshot,
                staged_source,
                report_path,
                language=task.language,
                use_docker=use_docker,
                docker_image=image,
            )
        _validate_grade(tests, summary, report_path)
        if original_result.read_bytes() != original_bytes or hash_source(source) != source_hash:
            raise RegradeError("Original result/source changed during grading")
        if hash_source(source_snapshot) != source_hash:
            raise RegradeError("Pristine source snapshot changed during grading")
        if hash_paths([("tests", test_snapshot)]) != test_hash:
            raise RegradeError("Test snapshot changed during grading")
        if hash_paths(harness_entries) != harness_hash:
            raise RegradeError(
                "Harness files changed during grading; regrade with a stable checkout"
            )
        scores = compute_task_score(compute_correctness(summary))
        scores.extension_scores.update(compute_subscores(tests))
        result.update(tests=[asdict(test) for test in tests], test_summary=asdict(summary))
        result["test_summary"]["total"] = summary.total
        result["scores"] = asdict(scores)
        grading["status"] = "completed"
    except Exception as exc:
        grading["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        grading["finished_at"] = datetime.now(UTC).isoformat()
        if report_path.is_file():
            result["artifacts"]["test_report"] = "test-report.json"
        (output_dir / "regrade.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    if grading["status"] != "completed":
        raise RegradeError(f"{grading['error']} (audit: {output_dir / 'regrade.json'})")
    return result
