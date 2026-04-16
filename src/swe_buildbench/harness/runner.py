"""Orchestrates a single evaluation run end-to-end."""

from __future__ import annotations

import importlib.metadata
import logging
import shutil
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import docker.errors
from requests import exceptions as requests_exceptions

from swe_buildbench.agents.base import AgentAdapter
from swe_buildbench.harness.docker import (
    CONTAINER_OUTPUT,
    CONTAINER_PROMPT,
    CONTAINER_WORKSPACE,
    ContainerConfig,
    DockerSandbox,
)
from swe_buildbench.harness.hashing import hash_prompt_content, hash_test_suite
from swe_buildbench.harness.platform import resolve_host_home
from swe_buildbench.harness.results import (
    BuildResult,
    RunArtifacts,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
    TokenUsage,
    compute_source_stats,
    make_run_id,
    result_path,
    save_source_dir,
    save_transcript,
)
from swe_buildbench.harness.scoring import (
    compute_code_quality,
    compute_correctness,
    compute_self_test_coverage,
    compute_subscores,
    compute_task_score,
    run_hidden_tests,
)
from swe_buildbench.harness.task import TaskDefinition
from swe_buildbench.harness.workspace import prepare_workspace

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 24 * 60 * 60  # 24 hours — safety backstop, not a meaningful limit


def _git_sha() -> str:
    """Return the short git SHA of the current repo, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _harness_version() -> str:
    """Return the installed swe-buildbench package version."""
    try:
        return importlib.metadata.version("swe-buildbench")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _write_infrastructure_failure_result(
    *,
    out_path: Path,
    task: TaskDefinition,
    adapter: AgentAdapter,
    run_id: str,
    run_number: int,
    timestamp: str,
    prompt_variant: str | None,
    prompt_content_sha: str,
    test_suite_sha: str,
    wall_clock_seconds: float,
    docker_image_sha: str,
    diagnostics: str,
    notes: str,
) -> RunResult:
    metadata = RunMetadata(
        run_id=run_id,
        task=task.task_id,
        agent=adapter.name,
        agent_version=adapter.version,
        prompt_variant=prompt_variant or "base",
        run_number=run_number,
        timestamp=timestamp,
        test_suite_version=_git_sha(),
        eval_version=task.version,
        harness_version=_harness_version(),
        docker_image_sha=docker_image_sha,
        wall_clock_seconds=wall_clock_seconds,
        exit_reason="error",
        model=adapter.model,
        effort=adapter.effort,
        notes=notes,
        prompt_content_sha=prompt_content_sha,
        test_suite_sha=test_suite_sha,
    )
    result = RunResult(
        metadata=metadata,
        token_usage=None,
        build=BuildResult(
            success=False,
            duration_seconds=0.0,
            diagnostics=diagnostics,
        ),
        tests=[],
        test_summary=TestSummary(),
        scores=Scores(),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.write(out_path)
    log.warning("Wrote infrastructure failure result to %s", out_path)
    return result


def _safe_docker_image_sha(sandbox: DockerSandbox, image_tag: str) -> str:
    try:
        return sandbox.get_image_sha(image_tag)
    except Exception:
        log.debug("Failed to resolve Docker image SHA for %s", image_tag, exc_info=True)
        return "unknown"


def _docker_failure_note(exc: Exception) -> str:
    if isinstance(exc, docker.errors.BuildError):
        return "infrastructure_failure: Docker image build failed before scoring completed"
    if isinstance(exc, docker.errors.APIError):
        return "infrastructure_failure: Docker API error before scoring completed"
    if isinstance(exc, requests_exceptions.RequestException):
        return "infrastructure_failure: Docker request error before scoring completed"
    return "infrastructure_failure: Docker unavailable before scoring completed"


def run_evaluation(
    task: TaskDefinition,
    adapter: AgentAdapter,
    *,
    run_number: int = 1,
    eval_number: int = 1,
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

    run_id = make_run_id(task.task_id, adapter.name, run_number, adapter.model)
    timestamp = datetime.now(UTC).isoformat()
    log.info("Starting run %s", run_id)

    # Compute content hashes up-front so they're logged even if the run dies
    # later. These are cheap (sha256 over prompt + docs + tests).
    prompt_hash = hash_prompt_content(task, prompt_variant)
    test_hash = hash_test_suite(task)
    log.info(
        "Content hashes: prompt=%s test_suite=%s",
        prompt_hash.sha256[:12],
        test_hash.sha256[:12],
    )

    start_time = time.monotonic()
    out_path = result_path(
        output_dir,
        task.task_id,
        adapter.name,
        run_number,
        adapter.model,
        adapter.effort,
        eval_number,
    )

    sandbox: DockerSandbox | None = None
    workspace: Path | None = None
    extract_dir: Path | None = None
    container_logs: str = ""
    docker_image_sha = "unknown"

    try:
        sandbox = DockerSandbox()

        # --- 1. Prepare workspace ---
        workspace = prepare_workspace(task, prompt_variant)
        log.info("Workspace prepared at %s", workspace)

        # --- 2. Build image if needed ---
        if not sandbox.image_exists(adapter.image_tag):
            sandbox.build_image(adapter.dockerfile, adapter.image_tag)
        docker_image_sha = _safe_docker_image_sha(sandbox, adapter.image_tag)

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

        # Capture container logs (transcript + debugging)
        try:
            container_logs = sandbox.get_logs()
            if container_logs:
                log.debug("Container logs:\n%s", container_logs[:5000])
        except Exception:
            log.debug("Could not retrieve container logs", exc_info=True)

        # --- 4. Extract agent output ---
        extract_dir = Path(tempfile.mkdtemp(prefix="swe-bb-extract-"))
        try:
            sandbox.copy_out(CONTAINER_OUTPUT, extract_dir)
        except Exception:
            log.warning(
                "Failed to extract %s from container (agent may not have created it)",
                CONTAINER_OUTPUT,
                exc_info=True,
            )
        submission_dir = extract_dir / "output"
        submission_dir.mkdir(exist_ok=True)

        # --- 5. Extract telemetry and parse token usage ---
        for tpath in adapter.telemetry_paths:
            try:
                sandbox.copy_out(PurePosixPath(tpath), extract_dir)
            except Exception:
                log.debug("Telemetry path %s not found in container", tpath)

        token_usage: TokenUsage | None = None
        try:
            token_usage = adapter.parse_token_usage(extract_dir, container_logs)
        except Exception:
            log.warning("Failed to parse token usage", exc_info=True)

        # Always estimate cost from token counts + published pricing
        if token_usage is not None and adapter.model:
            from swe_buildbench.harness.pricing import estimate_cost

            token_usage.estimated_cost_usd = estimate_cost(
                adapter.model,
                token_usage.input_tokens,
                token_usage.output_tokens,
                token_usage.cache_read_input_tokens or 0,
                token_usage.cache_creation_input_tokens or 0,
            )

        # --- 6. Run hidden tests ---
        # The eval's conftest.py handles preparing the submission (build for
        # compiled languages, no-op for interpreted) and discovering the
        # runnable command via the shared pytest plugin.
        report_path = extract_dir / "test-report.json"
        tests, test_summary = run_hidden_tests(
            test_dir=task.test_dir,
            submission_dir=submission_dir,
            report_path=report_path,
            language=task.language,
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
        # Per-capability breakdown — passed/total per test file, stored in
        # extension_scores so it rides along without changing the Scores
        # schema. Surface with `swe-buildbench results --breakdown`.
        scores.extension_scores.update(compute_subscores(tests))

        # --- 9. Assemble result ---
        exit_reason = "timeout" if container_run.timed_out else "completed"
        if container_run.exit_code and container_run.exit_code != 0:
            exit_reason = "error"

        # Detect runs where the agent produced nothing useful
        if exit_reason == "completed" and token_usage is None and not any(submission_dir.iterdir()):
            exit_reason = "no_output"
            log.warning("Agent produced no tokens and no output files")

        # Extract last agent message for completeness assessment
        agent_last_message: str | None = None
        try:
            raw_msg = adapter.extract_last_agent_message(container_logs)
            if raw_msg:
                agent_last_message = raw_msg[:2000]
        except Exception:
            log.debug("Failed to extract last agent message", exc_info=True)

        metadata = RunMetadata(
            run_id=run_id,
            task=task.task_id,
            agent=adapter.name,
            agent_version=adapter.version,
            prompt_variant=prompt_variant or "base",
            run_number=run_number,
            timestamp=timestamp,
            test_suite_version=_git_sha(),
            eval_version=task.version,
            harness_version=_harness_version(),
            docker_image_sha=docker_image_sha,
            wall_clock_seconds=container_run.wall_clock_seconds,
            exit_reason=exit_reason,
            model=adapter.model,
            effort=adapter.effort,
            prompt_content_sha=prompt_hash.sha256,
            test_suite_sha=test_hash.sha256,
            agent_last_message=agent_last_message,
        )

        # --- 10. Save artifacts ---
        out_path.parent.mkdir(parents=True, exist_ok=True)
        artifacts = RunArtifacts()

        # Save agent transcript (container stdout/stderr)
        if container_logs:
            artifacts.transcript = save_transcript(out_path, container_logs)

        # Save extracted telemetry files alongside results
        for tpath in adapter.telemetry_paths:
            tfile = extract_dir / PurePosixPath(tpath).name
            if tfile.is_file():
                dest = out_path.parent / tfile.name
                shutil.copy2(tfile, dest)
                log.debug("Saved telemetry file %s", dest)

        # Save agent source code and compute stats
        source_stats = compute_source_stats(submission_dir, task.language)
        if submission_dir.exists() and any(submission_dir.iterdir()):
            artifacts.source_dir = save_source_dir(out_path, submission_dir)

        result = RunResult(
            metadata=metadata,
            token_usage=token_usage,
            build=build_result,
            tests=tests,
            test_summary=test_summary,
            scores=scores,
            artifacts=artifacts,
            source_stats=source_stats,
        )

        # --- 11. Write result ---
        result.write(out_path)
        log.info("Result written to %s", out_path)

        return result
    except (docker.errors.DockerException, requests_exceptions.RequestException) as exc:
        if docker_image_sha == "unknown" and sandbox is not None:
            docker_image_sha = _safe_docker_image_sha(sandbox, adapter.image_tag)

        _write_infrastructure_failure_result(
            out_path=out_path,
            task=task,
            adapter=adapter,
            run_id=run_id,
            run_number=run_number,
            timestamp=timestamp,
            prompt_variant=prompt_variant,
            prompt_content_sha=prompt_hash.sha256,
            test_suite_sha=test_hash.sha256,
            wall_clock_seconds=time.monotonic() - start_time,
            docker_image_sha=docker_image_sha,
            diagnostics=str(exc),
            notes=_docker_failure_note(exc),
        )
        raise

    finally:
        if sandbox is not None:
            try:
                sandbox.cleanup()
            except Exception:
                log.warning("Failed to clean up Docker sandbox after run failure", exc_info=True)
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)
        if extract_dir is not None:
            shutil.rmtree(extract_dir, ignore_errors=True)
