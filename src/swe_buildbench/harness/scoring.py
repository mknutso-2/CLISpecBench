"""Scoring pipeline: correctness, self-test coverage, code quality."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path, PurePosixPath

from swe_buildbench.harness.results import Scores, TestOutcome, TestSummary

log = logging.getLogger(__name__)

# Base Docker image tag — same image used to build agent containers,
# has cmake, g++, python3, pytest, and pytest-json-report.
TEST_RUNNER_IMAGE = "swe-buildbench-base"

# Paths inside the test-runner container (directly under /tmp which always exists)
_CONTAINER_TESTS = PurePosixPath("/tmp/tests")
_CONTAINER_SUBMISSION = PurePosixPath("/tmp/submission")
_CONTAINER_SRC = PurePosixPath("/tmp/src")
_CONTAINER_REPORT = PurePosixPath("/tmp/report.json")


# ---------------------------------------------------------------------------
# Correctness scoring — run hidden test suite via pytest
# ---------------------------------------------------------------------------


def run_hidden_tests(
    test_dir: Path,
    submission_dir: Path,
    report_path: Path,
    timeout_seconds: float = 600,
    use_docker: bool = True,
    language: str = "cpp",
) -> tuple[list[TestOutcome], TestSummary]:
    """Run the hidden test suite against an agent's submission.

    The eval's conftest.py handles preparing the submission (building it
    when applicable) and discovering the runnable command via the shared
    pytest plugin.  We pass ``--implementation-root`` pointing at the
    agent's source directory and ``--language`` so the plugin selects the
    right build backend.

    When *use_docker* is True (the default), tests run inside a Linux
    container so the build environment matches what the agent targeted.

    Uses ``pytest --json-report`` to capture per-test results.
    Returns the test outcomes and summary.
    """
    if use_docker:
        return _run_hidden_tests_docker(
            test_dir,
            submission_dir,
            report_path,
            timeout_seconds,
            language,
        )
    return _run_hidden_tests_local(
        test_dir,
        submission_dir,
        report_path,
        timeout_seconds,
        language,
    )


def _run_hidden_tests_local(
    test_dir: Path,
    submission_dir: Path,
    report_path: Path,
    timeout_seconds: float,
    language: str,
) -> tuple[list[TestOutcome], TestSummary]:
    """Run tests on the host (fallback for when Docker is unavailable)."""
    cmd = [
        "python",
        "-m",
        "pytest",
        str(test_dir),
        f"--implementation-root={submission_dir}",
        f"--language={language}",
        "--json-report",
        f"--json-report-file={report_path}",
        "-q",
    ]
    log.info("Running hidden tests (local): %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    log.info("pytest exited with code %d", result.returncode)

    return parse_json_report(report_path)


def _run_hidden_tests_docker(
    test_dir: Path,
    submission_dir: Path,
    report_path: Path,
    timeout_seconds: float,
    language: str,
) -> tuple[list[TestOutcome], TestSummary]:
    """Run tests inside a Docker container for cross-platform compatibility."""
    from swe_buildbench.harness.docker import (
        ContainerConfig,
        DockerSandbox,
    )

    # The test dir may reference helpers from the src/ package via conftest
    # imports (e.g. swe_buildbench.build). Find the repo src/ directory.
    src_dir = Path(__file__).resolve().parent.parent.parent  # -> src/

    # Create a .git marker so find_repo_root() succeeds in conftest fixtures
    cmd_str = (
        f"mkdir -p /tmp/.git"
        f" && python3 -m pytest {_CONTAINER_TESTS}"
        f" --implementation-root={_CONTAINER_SUBMISSION}"
        f" --language={language}"
        f" --json-report --json-report-file={_CONTAINER_REPORT}"
        " -q"
    )
    config = ContainerConfig(
        image=TEST_RUNNER_IMAGE,
        environment={"PYTHONPATH": str(_CONTAINER_SRC)},
        command=["bash", "-c", cmd_str],
        network_mode="none",
    )

    sandbox = DockerSandbox()
    try:
        # Build the base image if needed
        if not sandbox.image_exists(TEST_RUNNER_IMAGE):
            base_dockerfile = (
                Path(__file__).resolve().parent.parent.parent.parent / "docker" / "base.Dockerfile"
            )
            sandbox.build_image(base_dockerfile, TEST_RUNNER_IMAGE)

        sandbox.create(config)
        sandbox.copy_in(test_dir, _CONTAINER_TESTS)
        sandbox.copy_in(submission_dir, _CONTAINER_SUBMISSION)
        sandbox.copy_in(src_dir, _CONTAINER_SRC)

        run = sandbox.start_and_wait(timeout_seconds)
        log.info(
            "Test container finished: exit_code=%s wall=%.1fs",
            run.exit_code,
            run.wall_clock_seconds,
        )

        try:
            logs = sandbox.get_logs()
            if logs:
                log.debug("Test runner output:\n%s", logs[:3000])
        except Exception:
            pass

        # Extract the JSON report
        try:
            extract_dir = report_path.parent
            sandbox.copy_out(_CONTAINER_REPORT, extract_dir)
            # copy_out extracts into extract_dir with the archive name
            extracted = extract_dir / "report.json"
            if extracted.exists() and extracted != report_path:
                extracted.rename(report_path)
        except Exception:
            log.warning("Failed to extract test report from container", exc_info=True)

    finally:
        sandbox.cleanup()

    return parse_json_report(report_path)


def parse_json_report(report_path: Path) -> tuple[list[TestOutcome], TestSummary]:
    """Parse a pytest-json-report file into our result types."""
    if not report_path.is_file():
        log.error("JSON report not found at %s", report_path)
        return [], TestSummary()

    data = json.loads(report_path.read_text(encoding="utf-8"))
    tests: list[TestOutcome] = []
    summary = TestSummary()

    for test in data.get("tests", []):
        outcome_str: str = test.get("outcome", "error")
        node_id: str = test.get("nodeid", "unknown")
        duration: float = test.get("duration", 0.0)

        # Extract failure message if present
        message: str | None = None
        call_info = test.get("call", {})
        if call_info.get("longrepr"):
            message = str(call_info["longrepr"])

        tests.append(
            TestOutcome(
                node_id=node_id,
                outcome=outcome_str,
                duration_seconds=duration,
                message=message,
            )
        )

        if outcome_str == "passed":
            summary.passed += 1
        elif outcome_str == "failed":
            summary.failed += 1
        elif outcome_str == "skipped":
            summary.skipped += 1
        else:
            summary.error += 1

    return tests, summary


def compute_correctness(summary: TestSummary) -> float:
    """Compute the correctness score as pass rate.

    Returns 0.0 if there are no tests.
    """
    if summary.total == 0:
        return 0.0
    return summary.passed / summary.total


# ---------------------------------------------------------------------------
# Self-test coverage — run agent's own tests with coverage instrumentation
# ---------------------------------------------------------------------------


def compute_self_test_coverage(
    submission_dir: Path,
) -> float | None:
    """Compute line coverage of the agent's own tests against its code.

    Returns the coverage fraction, or ``None`` if the agent didn't write tests
    or coverage tooling is unavailable.
    """
    # Look for agent-written tests
    test_dirs = [
        submission_dir / "tests",
        submission_dir / "test",
    ]
    agent_test_dir = next((d for d in test_dirs if d.is_dir()), None)
    if agent_test_dir is None:
        log.info("No agent test directory found in submission")
        return None

    # For C++ projects, coverage requires rebuilding with --coverage.
    # This is a placeholder — the real implementation needs to:
    # 1. Rebuild with -fprofile-arcs -ftest-coverage
    # 2. Run agent tests
    # 3. Run gcov / lcov
    # 4. Parse coverage percentage
    log.info("Self-test coverage measurement not yet implemented")
    return None


# ---------------------------------------------------------------------------
# Code quality — LLM judge
# ---------------------------------------------------------------------------


def compute_code_quality(submission_dir: Path) -> float | None:
    """Evaluate code quality using an LLM judge.

    Returns the quality score, or ``None`` if evaluation is unavailable.
    """
    # Placeholder — the real implementation needs to:
    # 1. Discover source files in submission
    # 2. Load the quality rubric for the task language
    # 3. Send each file + guideline to an LLM judge
    # 4. Aggregate pass/fail/not-applicable results
    log.info("Code quality evaluation not yet implemented")
    return None


# ---------------------------------------------------------------------------
# Aggregate scoring
# ---------------------------------------------------------------------------


def compute_task_score(
    correctness: float,
    self_test_coverage: float | None,
    code_quality: float | None,
    correctness_weight: float = 0.6,
    coverage_weight: float = 0.2,
    quality_weight: float = 0.2,
) -> Scores:
    """Compute all scoring dimensions and the weighted task score."""
    # If a dimension is unavailable, redistribute its weight to correctness
    effective_correctness_weight = correctness_weight
    if self_test_coverage is None:
        effective_correctness_weight += coverage_weight
        coverage_weight = 0.0
    if code_quality is None:
        effective_correctness_weight += quality_weight
        quality_weight = 0.0

    task_score = effective_correctness_weight * correctness
    if self_test_coverage is not None:
        task_score += coverage_weight * self_test_coverage
    if code_quality is not None:
        task_score += quality_weight * code_quality

    return Scores(
        correctness=correctness,
        self_test_coverage=self_test_coverage,
        code_quality=code_quality,
        task_score=task_score,
    )
