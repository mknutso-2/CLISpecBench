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

from clispecbench.agents.base import AgentAdapter
from clispecbench.agents.registry import get_agent_spec
from clispecbench.harness.docker import (
    CONTAINER_OUTPUT,
    CONTAINER_PROMPT,
    CONTAINER_WORKSPACE,
    ContainerConfig,
    DockerSandbox,
)
from clispecbench.harness.hashing import hash_prompt_content, hash_test_suite
from clispecbench.harness.platform import resolve_host_home
from clispecbench.harness.results import (
    BuildResult,
    RunArtifacts,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
    TokenUsage,
    compute_source_stats,
    make_run_label,
    make_run_uid,
    models_compatible,
    result_path,
    save_network_audit,
    save_source_dir,
    save_transcript,
)
from clispecbench.harness.scoring import (
    compute_correctness,
    compute_subscores,
    compute_task_score,
    run_hidden_tests,
)
from clispecbench.harness.task import TaskDefinition
from clispecbench.harness.workspace import prepare_workspace

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
    """Return the installed clispecbench package version."""
    try:
        return importlib.metadata.version("clispecbench")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _write_infrastructure_failure_result(
    *,
    out_path: Path,
    task: TaskDefinition,
    adapter: AgentAdapter,
    run_uid: str,
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
        run_uid=run_uid,
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
        network_policy=adapter.network_policy,
        model=adapter.model,
        effort=adapter.effort,
        notes=notes,
        benchmark_cost_preference=_benchmark_cost_preference(adapter.name),
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


def _benchmark_cost_preference(agent_id: str) -> str | None:
    try:
        return get_agent_spec(agent_id).benchmark_cost_preference
    except ValueError:
        return None


def run_evaluation(
    task: TaskDefinition,
    adapter: AgentAdapter,
    *,
    run_number: int = 1,
    eval_number: int = 1,
    prompt_variant: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT,
    output_dir: Path = Path("transient_results"),
    api_key_env: dict[str, str] | None = None,
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

    run_uid = make_run_uid()
    run_label = make_run_label(task.task_id, adapter.name, run_number, adapter.model)
    timestamp = datetime.now(UTC).isoformat()
    log.info("Starting run %s (uid=%s)", run_label, run_uid)

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
        prompt_variant,
    )

    sandbox: DockerSandbox | None = None
    workspace: Path | None = None
    extract_dir: Path | None = None
    container_logs: str = ""
    network_audit_logs: str = ""
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
            egress_allowlist=(
                adapter.allowed_hosts if adapter.network_policy == "api-only" else []
            ),
            tty=adapter.requires_tty,
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
        try:
            network_audit_logs = sandbox.get_network_audit_logs()
        except Exception:
            log.debug("Could not retrieve restricted-egress audit logs", exc_info=True)

        # --- 4. Extract agent output ---
        extract_dir = Path(tempfile.mkdtemp(prefix="clispecbench-extract-"))
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

        # Also pull the agent CLI's on-disk canonical session transcript, if
        # the adapter exposes one.  Best-effort; never fails the run.
        canonical_src_dir = adapter.canonical_transcript_container_dir
        if canonical_src_dir is not None:
            try:
                sandbox.copy_out(PurePosixPath(canonical_src_dir), extract_dir)
            except Exception:
                log.debug(
                    "Canonical transcript path %s not found in container",
                    canonical_src_dir,
                )

        token_usage: TokenUsage | None = None
        try:
            token_usage = adapter.parse_token_usage(extract_dir, container_logs)
        except Exception:
            log.warning("Failed to parse token usage", exc_info=True)

        if token_usage is not None:
            token_usage.estimated_cost_usd = adapter.estimate_cost(token_usage)

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
        scores = compute_task_score(correctness)
        # Per-capability breakdown — passed/total per test file, stored in
        # extension_scores so it rides along without changing the Scores
        # schema. Surface with `clispecbench results --breakdown`.
        scores.extension_scores.update(compute_subscores(tests))

        # --- 9. Assemble result ---
        # Extract last agent message for completeness assessment. Pulled up
        # from later in this block so it can feed into the no_output heuristic.
        agent_last_message: str | None = None
        try:
            raw_msg = adapter.extract_last_agent_message(container_logs)
            if raw_msg:
                agent_last_message = raw_msg[:2000]
        except Exception:
            log.debug("Failed to extract last agent message", exc_info=True)

        exit_reason = "timeout" if container_run.timed_out else "completed"
        if container_run.exit_code and container_run.exit_code != 0:
            exit_reason = "error"

        # Detect runs where the agent never actually started doing work
        # (e.g. auth failure, container startup crash, CLI binary missing).
        # A real agent run takes minutes. If the container exited cleanly in
        # under a minute with no output files AND no agent chat message, the
        # agent never ran in any meaningful sense — reclassify as no_output.
        #
        # NOTE: token_usage is NOT a reliable signal here. Some CLI adapters
        # only emit usage on successful turns (codex-cli, for example, only
        # records tokens on `turn.completed` — a `turn.failed` from context
        # exhaustion leaves token_usage=None even after a 30-minute run).
        # Using wall_clock_seconds + agent_last_message avoids conflating
        # "agent ran and hit an API error" with "agent never started".
        if (
            exit_reason == "completed"
            and container_run.wall_clock_seconds < 60
            and not any(submission_dir.iterdir())
            and not agent_last_message
        ):
            exit_reason = "no_output"
            log.warning(
                "Agent produced no output files in %.1fs — likely startup failure",
                container_run.wall_clock_seconds,
            )

        try:
            exit_reason = adapter.refine_exit_reason(
                extract_dir,
                container_logs,
                exit_reason,
            )
        except Exception:
            log.debug("Failed to refine exit reason from adapter telemetry", exc_info=True)

        # --- Served-vs-requested model guard ---
        # The agent CLI can silently fall back to a default model when it
        # doesn't recognize the requested --model snapshot ID (e.g. the pinned
        # claude-code CLI serving Opus 4.7 for an unrecognized
        # claude-opus-4-20250514). Such a run is mislabeled: its score belongs
        # to whatever model actually ran, not the one we asked for. Detect the
        # served model from the transcript and, on a positive mismatch, force
        # exit_reason="error" so it is never mistaken for a clean run. The
        # publish gate hard-refuses these (see publish.py), but failing here
        # also surfaces it immediately in the transient result.
        run_notes: str | None = None
        served_model: str | None = None
        try:
            served_model = adapter.detect_served_model(container_logs)
        except Exception:
            log.debug("Failed to detect served model from transcript", exc_info=True)
        model_mismatch = bool(
            adapter.model and served_model and not models_compatible(adapter.model, served_model)
        )
        if model_mismatch:
            exit_reason = "error"
            mismatch_note = (
                f"MODEL MISMATCH: requested {adapter.model!r} but the CLI served "
                f"{served_model!r} (silent fallback). Score reflects {served_model!r}, "
                f"not the requested model — scrap and do not publish."
            )
            run_notes = f"{mismatch_note}\n{run_notes}" if run_notes else mismatch_note
            log.error(
                "Served model %r != requested model %r — marking run as error",
                served_model,
                adapter.model,
            )

        metadata = RunMetadata(
            run_uid=run_uid,
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
            network_policy=adapter.network_policy,
            model=adapter.model,
            served_model=served_model,
            effort=adapter.effort,
            notes=run_notes,
            benchmark_cost_preference=_benchmark_cost_preference(adapter.name),
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
        if network_audit_logs:
            artifacts.network_audit = save_network_audit(out_path, network_audit_logs)

        # Save extracted telemetry files alongside results
        for tpath in adapter.telemetry_paths:
            tfile = extract_dir / PurePosixPath(tpath).name
            if tfile.is_file():
                dest = out_path.parent / tfile.name
                shutil.copy2(tfile, dest)
                log.debug("Saved telemetry file %s", dest)

        # Save the agent CLI's on-disk canonical session transcript (if we
        # extracted one).  Two destinations:
        #   1. <run-dir>/transcript.canonical.jsonl — alongside the
        #      stream-json transcript.jsonl, for reviewers and third-party
        #      viewers that expect canonical shape.
        #   2. ~/.claude/projects/<run-id>/<original-session-filename>.jsonl —
        #      sits under the same root claude-code uses for its own sessions,
        #      so any tool that scans ~/.claude/projects/ (e.g.
        #      claude-code-transcripts) discovers our runs automatically.
        #      The agent CLI's own session filename is preserved
        #      (e.g. <session-uuid>.jsonl).
        if canonical_src_dir is not None:
            canonical_root = extract_dir / PurePosixPath(canonical_src_dir).name
            session_files = sorted(canonical_root.rglob("*.jsonl"))
            if session_files:
                # Pick the largest file in case the dir contains multiple
                # session shards (only one is expected per run).
                src = max(session_files, key=lambda p: p.stat().st_size)
                run_dest = out_path.parent / "transcript.canonical.jsonl"
                try:
                    shutil.copy2(src, run_dest)
                    log.debug("Saved canonical transcript %s", run_dest)
                except Exception:
                    log.warning(
                        "Failed to write canonical transcript to run dir",
                        exc_info=True,
                    )
                # Include the eval directory in the folder name.  ``run_label``
                # alone collides across re-runs because it omits the
                # auto-incremented eval number — two ``--runs 1`` invocations
                # of the same task/agent/model on the same day produce
                # identical labels but distinct ``eval<N>/`` paths.
                eval_dir_name = out_path.parent.parent.name  # e.g. "eval2"
                home_dest_dir = (
                    Path.home() / ".claude" / "projects" / f"{run_label}_{eval_dir_name}"
                )
                home_dest = home_dest_dir / src.name
                try:
                    home_dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, home_dest)
                    log.debug("Saved canonical transcript copy %s", home_dest)
                except Exception:
                    log.warning(
                        "Failed to write canonical transcript to ~/.claude/projects/%s_%s/",
                        run_label,
                        eval_dir_name,
                        exc_info=True,
                    )
            else:
                log.debug(
                    "No canonical session JSONL found under extracted %s",
                    canonical_root,
                )

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
            run_uid=run_uid,
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
