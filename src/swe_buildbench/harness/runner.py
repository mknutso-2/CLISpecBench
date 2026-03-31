"""Orchestrates a single evaluation run end-to-end."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from swe_buildbench.agents.base import AgentAdapter
from swe_buildbench.harness.docker import (
    CONTAINER_OUTPUT,
    CONTAINER_PROMPT,
    CONTAINER_WORKSPACE,
    ContainerConfig,
    DockerSandbox,
)
from swe_buildbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
    TokenUsage,
    make_run_id,
    result_path,
)
from swe_buildbench.harness.scoring import (
    compute_code_quality,
    compute_correctness,
    compute_self_test_coverage,
    compute_task_score,
    run_hidden_tests,
)
from swe_buildbench.harness.task import TaskDefinition
from swe_buildbench.harness.workspace import prepare_workspace

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30 * 60  # 30 minutes


def run_evaluation(
    task: TaskDefinition,
    adapter: AgentAdapter,
    *,
    run_number: int = 1,
    prompt_variant: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT,
    output_dir: Path = Path("results"),
    api_key_env: dict[str, str] | None = None,
    skip_extensions: bool = False,
) -> RunResult:
    """Execute one complete evaluation run.

    1. Prepare workspace
    2. Run agent in Docker sandbox
    3. Build submission
    4. Run hidden tests
    5. Score
    6. Write result
    """
    if api_key_env is None:
        api_key_env = {}

    run_id = make_run_id(task.task_id, adapter.name, run_number)
    timestamp = datetime.now(UTC).isoformat()
    log.info("Starting run %s", run_id)

    sandbox = DockerSandbox()
    workspace: Path | None = None
    extract_dir: Path | None = None

    try:
        # --- 1. Prepare workspace ---
        workspace = prepare_workspace(task, prompt_variant)
        log.info("Workspace prepared at %s", workspace)

        # --- 2. Build image if needed ---
        if not sandbox.image_exists(adapter.image_tag):
            sandbox.build_image(adapter.dockerfile, adapter.image_tag)

        # --- 3. Create and run container ---
        config = ContainerConfig(
            image=adapter.image_tag,
            environment=adapter.environment(api_key_env),
            command=adapter.invoke_command(
                prompt_path=PurePosixPath(CONTAINER_PROMPT),
                work_dir=PurePosixPath(CONTAINER_WORKSPACE),
            ),
        )
        sandbox.create(config)
        sandbox.copy_in(workspace, CONTAINER_WORKSPACE)

        container_run = sandbox.start_and_wait(timeout_seconds)
        log.info(
            "Container finished: exit_code=%s timed_out=%s wall=%.1fs",
            container_run.exit_code,
            container_run.timed_out,
            container_run.wall_clock_seconds,
        )

        # --- 4. Extract agent output ---
        extract_dir = Path(tempfile.mkdtemp(prefix="swe-bb-extract-"))
        sandbox.copy_out(CONTAINER_OUTPUT, extract_dir)
        submission_dir = extract_dir / "output"

        # --- 5. Parse token usage ---
        token_usage: TokenUsage | None = None
        try:
            token_usage = adapter.parse_token_usage(extract_dir)
        except Exception:
            log.warning("Failed to parse token usage", exc_info=True)

        # --- 6. Build submission ---
        build_result = _build_submission(submission_dir, task)

        # --- 7. Run hidden tests ---
        tests = []
        test_summary = TestSummary()
        scores = Scores()

        if build_result.success:
            executable = _find_executable(submission_dir)
            if executable:
                report_path = extract_dir / "test-report.json"
                tests, test_summary = run_hidden_tests(
                    test_dir=task.test_dir,
                    executable=executable,
                    report_path=report_path,
                )

                # --- 8. Score ---
                correctness = compute_correctness(test_summary)
                coverage = compute_self_test_coverage(submission_dir, executable)
                quality = compute_code_quality(submission_dir)
                scores = compute_task_score(correctness, coverage, quality)
            else:
                log.error("No executable found after build")

        # --- 9. Assemble result ---
        exit_reason = "timeout" if container_run.timed_out else "completed"
        if container_run.exit_code and container_run.exit_code != 0:
            exit_reason = "error"

        metadata = RunMetadata(
            run_id=run_id,
            task=task.task_id,
            agent=adapter.name,
            agent_version="unknown",  # TODO: extract from container
            prompt_variant=prompt_variant or "base",
            run_number=run_number,
            timestamp=timestamp,
            test_suite_version="unknown",  # TODO: git SHA of test repo
            docker_image_sha="unknown",  # TODO: extract from image inspect
            wall_clock_seconds=container_run.wall_clock_seconds,
            exit_reason=exit_reason,
        )

        result = RunResult(
            metadata=metadata,
            token_usage=token_usage,
            build=build_result,
            tests=tests,
            test_summary=test_summary,
            scores=scores,
        )

        # --- 10. Write result ---
        out_path = result_path(output_dir, task.task_id, adapter.name, run_number)
        result.write(out_path)
        log.info("Result written to %s", out_path)

        return result

    finally:
        sandbox.cleanup()
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)
        if extract_dir is not None:
            shutil.rmtree(extract_dir, ignore_errors=True)


def _build_submission(submission_dir: Path, task: TaskDefinition) -> BuildResult:
    """Build the agent's submission using cmake."""
    import time

    build_dir = submission_dir / "build"
    build_dir.mkdir(exist_ok=True)

    t0 = time.monotonic()

    # Configure
    configure_result = subprocess.run(
        ["cmake", "-S", str(submission_dir), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    if configure_result.returncode != 0:
        return BuildResult(
            success=False,
            duration_seconds=time.monotonic() - t0,
            diagnostics=configure_result.stderr,
        )

    # Build
    build_result = subprocess.run(
        ["cmake", "--build", str(build_dir)],
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - t0

    return BuildResult(
        success=build_result.returncode == 0,
        duration_seconds=elapsed,
        diagnostics=build_result.stderr if build_result.returncode != 0 else "",
    )


def _find_executable(submission_dir: Path) -> Path | None:
    """Find the built executable in the submission directory.

    Looks for executables in build/, preferring ones with "cncsim" in the name.
    """
    build_dir = submission_dir / "build"
    if not build_dir.is_dir():
        return None

    candidates: list[Path] = []
    for p in build_dir.rglob("*"):
        if p.is_file() and _is_executable(p):
            candidates.append(p)

    if not candidates:
        return None

    # Prefer executables with "cncsim" in the name
    cncsim_candidates = [c for c in candidates if "cncsim" in c.name.lower()]
    if cncsim_candidates:
        return min(cncsim_candidates, key=lambda p: len(str(p)))

    return min(candidates, key=lambda p: len(str(p)))


def _is_executable(path: Path) -> bool:
    """Check if a file looks like a compiled executable."""
    # On Linux: check executable permission
    # On all platforms: skip known non-executable extensions
    skip_suffixes = {".o", ".a", ".so", ".dylib", ".cmake", ".txt", ".json", ".log"}
    if path.suffix.lower() in skip_suffixes:
        return False
    # Heuristic: no extension or known executable extensions
    return path.suffix == "" or path.suffix.lower() in {".exe", ".out"}
