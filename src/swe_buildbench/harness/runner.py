"""Orchestrates a single evaluation run end-to-end."""

from __future__ import annotations

import logging
import shutil
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
from swe_buildbench.harness.platform import resolve_host_home
from swe_buildbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
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
        host_home = resolve_host_home()
        config = ContainerConfig(
            image=adapter.image_tag,
            environment=adapter.environment(api_key_env),
            command=adapter.invoke_command(
                prompt_path=PurePosixPath(CONTAINER_PROMPT),
                work_dir=PurePosixPath(CONTAINER_WORKSPACE),
            ),
            volumes=adapter.credential_mounts(host_home),
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

        # --- 6. Run hidden tests ---
        # The eval's conftest.py handles cmake build + executable discovery
        # via the --implementation-root pytest option.
        report_path = extract_dir / "test-report.json"
        tests, test_summary = run_hidden_tests(
            test_dir=task.test_dir,
            submission_dir=submission_dir,
            report_path=report_path,
        )

        # --- 7. Derive build result from test outcomes ---
        build_test = next(
            (t for t in tests if "test_build" in t.node_id or "builds_successfully" in t.node_id),
            None,
        )
        build_result = BuildResult(
            success=build_test.outcome == "passed" if build_test else test_summary.total > 0,
            duration_seconds=build_test.duration_seconds if build_test else 0.0,
        )

        # --- 8. Score ---
        correctness = compute_correctness(test_summary)
        coverage = compute_self_test_coverage(submission_dir)
        quality = compute_code_quality(submission_dir)
        scores = compute_task_score(correctness, coverage, quality)

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


