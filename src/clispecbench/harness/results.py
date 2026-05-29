"""Result schema for CLISpecBench evaluation runs."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)

SCHEMA_VERSION = "2.1"
_VALID_BENCHMARK_COST_PREFERENCES = frozenset({"reported", "estimated"})
_UNSAFE_MODEL_SLUG_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def _benchmark_cost_preference(agent: str, stored_preference: str | None) -> str:
    if stored_preference in _VALID_BENCHMARK_COST_PREFERENCES:
        return stored_preference
    if stored_preference is not None:
        log.warning(
            "Unknown benchmark_cost_preference %r for agent %s; falling back to registry",
            stored_preference,
            agent,
        )

    from clispecbench.agents.registry import get_agent_spec

    try:
        return get_agent_spec(agent).benchmark_cost_preference
    except ValueError:
        return "reported"


@dataclass
class TokenUsage:
    """Normalized token usage from any agent.

    Token fields are the union of what all supported CLIs report:

    - ``input_tokens``: total input tokens including any cached portion
    - ``output_tokens``: generated / completion tokens
    - ``cache_read_input_tokens``: input tokens served from cache
      (Claude: ``cache_read_input_tokens``, Codex: ``cached_input_tokens``,
      Gemini: ``cached``)
    - ``cache_creation_input_tokens``: input tokens written to cache
      (Claude only — Codex and Gemini don't report this)
    """

    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    tool_calls: int | None = None
    reported_cost_usd: float | None = None  # Raw CLI-reported cost; may itself be a local estimate
    estimated_cost_usd: float | None = None  # Calculated from token counts + published pricing
    # Why a generic model-level estimate should not be attempted even when
    # ``estimated_cost_usd`` is missing. For example, Claude's mixed-model
    # ``modelUsage`` can aggregate token counts from multiple priced models.
    cost_estimate_blocked_reason: str | None = None
    # Machine-readable provenance for adapters that have multiple telemetry
    # paths. Example: Codex can report completed-turn usage via exec JSONL, or
    # recover a lower-bound count from its persisted session rollout.
    source: str | None = None
    is_partial: bool = False

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class BuildResult:
    """Outcome of building the agent's submission."""

    success: bool
    duration_seconds: float
    diagnostics: str = ""


@dataclass
class TestOutcome:
    """Result of a single test case."""

    __test__ = False

    node_id: str
    outcome: str  # "passed" | "failed" | "skipped" | "error"
    duration_seconds: float
    message: str | None = None


@dataclass
class TestSummary:
    """Aggregate counts across all tests."""

    __test__ = False

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped + self.error


@dataclass
class Scores:
    """All scoring dimensions for a run."""

    correctness: float | None = None
    task_score: float | None = None
    extension_scores: dict[str, float] = field(default_factory=dict[str, float])


@dataclass
class SourceStats:
    """Size metrics for the agent's submitted source code."""

    file_count: int = 0
    lines_of_code: int = 0  # non-blank lines


# Source-file extensions counted for SourceStats, keyed by language.
_SOURCE_EXTENSIONS: dict[str, set[str]] = {
    "cpp": {".cpp", ".h", ".c", ".hpp", ".cxx", ".cc", ".hxx"},
    "py": {".py"},
    "js": {".js", ".ts", ".mjs", ".cjs"},
    "rs": {".rs"},
}
# Union of all, used as fallback when language is unknown.
_ALL_SOURCE_EXTENSIONS: set[str] = {ext for exts in _SOURCE_EXTENSIONS.values() for ext in exts}


def compute_source_stats(source_dir: Path, language: str | None = None) -> SourceStats:
    """Count source files and non-blank lines in *source_dir*."""
    if not source_dir.is_dir():
        return SourceStats()
    extensions = _SOURCE_EXTENSIONS.get(language or "", _ALL_SOURCE_EXTENSIONS)
    # CMakeLists.txt is always counted for C++ projects
    file_count = 0
    loc = 0
    for f in source_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix in extensions or (f.name == "CMakeLists.txt" and language in (None, "cpp")):
            file_count += 1
            try:
                loc += sum(1 for line in f.read_text(errors="replace").splitlines() if line.strip())
            except OSError:
                pass
    return SourceStats(file_count=file_count, lines_of_code=loc)


@dataclass
class RunArtifacts:
    """Paths to preserved artifacts from the run, relative to the result file."""

    transcript: str | None = None  # e.g. "transcript.jsonl"
    source_dir: str | None = None  # e.g. "source/"


@dataclass
class RunMetadata:
    """Identifying information for a single evaluation run.

    ``run_uid`` is a UUID4 generated when the result is first written. It is
    the stable cross-reference handle between a transient result and its
    published copy — all other identifying fields (task, agent, model, etc.)
    are already present structurally, so a human-readable composite run_id is
    redundant.
    """

    run_uid: str
    task: str
    agent: str
    agent_version: str
    prompt_variant: str
    run_number: int
    timestamp: str
    test_suite_version: str
    eval_version: str
    harness_version: str
    docker_image_sha: str
    wall_clock_seconds: float
    exit_reason: str  # "completed" | "timeout" | "token_limit" | "error"
    model: str | None = None
    effort: str | None = None
    notes: str | None = None
    benchmark_cost_preference: str | None = None
    # Content hashes — machine-checkable backstop for the manual
    # `eval_version` bump. ``prompt_content_sha`` covers the assembled
    # prompt + docs (what the agent sees); ``test_suite_sha`` covers the
    # hidden tests (what scores it). See ``harness/hashing.py``.
    prompt_content_sha: str = "unknown"
    test_suite_sha: str = "unknown"
    # Last text message from the agent — helps identify whether the agent
    # considered the task complete vs. acknowledged it was incomplete.
    agent_last_message: str | None = None
    # Machine-readable completion classification derived from exit_reason,
    # adapter errors, and transcript signals. Older result files omit it.
    exit_class: str | None = None


@dataclass
class RunResult:
    """Complete result of a single evaluation run."""

    metadata: RunMetadata
    token_usage: TokenUsage | None
    build: BuildResult
    tests: list[TestOutcome]
    test_summary: TestSummary
    scores: Scores
    artifacts: RunArtifacts = field(default_factory=RunArtifacts)
    source_stats: SourceStats = field(default_factory=SourceStats)
    surgery: str | None = None  # Description of post-hoc fix applied to get code to compile

    @property
    def schema_version(self) -> str:
        return SCHEMA_VERSION

    @property
    def benchmark_cost_usd(self) -> float | None:
        """Cost to use for benchmark reporting and cross-agent comparisons.

        Agents can register ``estimated`` as the preferred benchmark-cost
        source when their CLI-reported cost is only a local estimate. If the
        preferred source is unavailable, fall back to the other source so cost
        does not disappear entirely from summaries.
        """
        if self.token_usage is None:
            return None
        preference = _benchmark_cost_preference(
            self.metadata.agent,
            self.metadata.benchmark_cost_preference,
        )
        if preference == "estimated" and self.token_usage.estimated_cost_usd is not None:
            return self.token_usage.estimated_cost_usd
        if self.token_usage.reported_cost_usd is not None:
            return self.token_usage.reported_cost_usd
        return self.token_usage.estimated_cost_usd

    @property
    def benchmark_cost_source(self) -> str | None:
        if self.token_usage is None:
            return None
        preference = _benchmark_cost_preference(
            self.metadata.agent,
            self.metadata.benchmark_cost_preference,
        )
        if preference == "estimated" and self.token_usage.estimated_cost_usd is not None:
            return "estimated"
        if self.token_usage.reported_cost_usd is not None:
            return "reported"
        if self.token_usage.estimated_cost_usd is not None:
            return "estimated"
        return None

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {"schema_version": self.schema_version}
        d["metadata"] = asdict(self.metadata)
        d["token_usage"] = (
            {**asdict(self.token_usage), "total_tokens": self.token_usage.total_tokens}
            if self.token_usage
            else None
        )
        d["build"] = asdict(self.build)
        d["tests"] = [asdict(t) for t in self.tests]
        d["test_summary"] = {**asdict(self.test_summary), "total": self.test_summary.total}
        d["scores"] = asdict(self.scores)
        d["artifacts"] = asdict(self.artifacts)
        d["source_stats"] = asdict(self.source_stats)
        if self.surgery:
            d["surgery"] = self.surgery
        return d

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def make_run_uid() -> str:
    """Return a fresh UUID4 string for a new evaluation run."""
    return str(uuid.uuid4())


def make_run_label(task: str, agent: str, run_number: int, model: str | None = None) -> str:
    """Human-readable label for logs and ~/.claude/projects/ folder naming.

    Not persisted in the result schema — all of its components are already in
    ``RunMetadata`` as structured fields.
    """
    ts = datetime.now(UTC).strftime("%Y-%m-%d")
    model_part = f"_{model}" if model else ""
    return f"{task}_{agent}{model_part}_{ts}_run-{run_number}"


def model_effort_slug(model: str | None, effort: str | None) -> str | None:
    """Build a folder name like 'opus_max' or 'gpt-5.4' from model + effort."""
    if not model:
        return None
    raw = f"{model}_{effort}" if effort else model
    return _UNSAFE_MODEL_SLUG_CHARS.sub("_", raw)


def _model_base_dir(
    output_dir: Path,
    task: str,
    agent: str,
    model: str | None = None,
    effort: str | None = None,
) -> Path:
    """Return the base directory for a task/agent/model combination."""
    base = output_dir / task / agent
    slug = model_effort_slug(model, effort)
    if slug:
        base = base / slug
    return base


def _windows_pid_exists(pid: int) -> bool:
    """Return whether ``pid`` is live on Windows without using ``os.kill(pid, 0)``."""
    import ctypes
    from ctypes import wintypes

    if pid <= 0:
        return False

    error_access_denied = 5
    process_query_limited_information = 0x1000
    still_active = 259
    synchronize = 0x00100000

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.OpenProcess(
        process_query_limited_information | synchronize,
        False,
        pid,
    )
    if not handle:
        return ctypes.get_last_error() == error_access_denied

    exit_code = wintypes.DWORD()
    try:
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            # If Windows let us open the process but not query its status,
            # keep the lock conservative and treat the process as live.
            return True
        return exit_code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def _pid_exists(pid: int) -> bool:
    """Return whether ``pid`` appears to refer to a live process."""
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_exists(pid)

    try:
        os.kill(pid, 0)  # signal 0 = check existence on POSIX
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def result_path(
    output_dir: Path,
    task: str,
    agent: str,
    run_number: int,
    model: str | None = None,
    effort: str | None = None,
    eval_number: int = 1,
) -> Path:
    base = _model_base_dir(output_dir, task, agent, model, effort)
    return base / f"eval{eval_number}" / f"run{run_number}" / "result.json"


def next_eval_number(
    output_dir: Path,
    task: str,
    agent: str,
    model: str | None = None,
    effort: str | None = None,
) -> int:
    """Return the next available eval number (1-based).

    Scans for existing ``evalN/`` directories and returns max(N) + 1.
    """
    base = _model_base_dir(output_dir, task, agent, model, effort)
    if not base.is_dir():
        return 1
    existing = [
        int(d.name[4:])
        for d in base.iterdir()
        if d.is_dir() and d.name.startswith("eval") and d.name[4:].isdigit()
    ]
    return max(existing, default=0) + 1


class EvalLock:
    """Filesystem lock that prevents concurrent runs for the same config.

    Uses ``O_CREAT | O_EXCL`` for atomic creation — if two processes race,
    exactly one wins and the other gets ``FileExistsError``.

    Usage::

        lock = EvalLock.acquire(output_dir, task, agent, model, effort)
        try:
            ...  # run evaluation
        finally:
            lock.release()
    """

    def __init__(self, lock_path: Path, pid: int) -> None:
        self._lock_path = lock_path
        self._pid = pid

    @classmethod
    def acquire(
        cls,
        output_dir: Path,
        task: str,
        agent: str,
        model: str | None = None,
        effort: str | None = None,
    ) -> EvalLock:
        """Acquire a lock, or raise ``SystemExit`` if one is already held."""
        base = _model_base_dir(output_dir, task, agent, model, effort)
        base.mkdir(parents=True, exist_ok=True)
        lock_path = base / ".eval.lock"
        pid = os.getpid()

        # Check for stale lock from a dead process
        if lock_path.exists():
            try:
                old_pid = int(lock_path.read_text().strip())
                if not _pid_exists(old_pid):
                    # Process is dead — stale lock
                    log.warning("Removing stale lock %s (pid %d is dead)", lock_path, old_pid)
                    lock_path.unlink(missing_ok=True)
                else:
                    raise SystemExit(
                        f"Another evaluation is already running for "
                        f"{task}/{agent}/{model or 'default'} "
                        f"(pid {old_pid}, lock: {lock_path}). "
                        f"Wait for it to finish or remove the lock file manually."
                    )
            except (ValueError, OSError):
                # Corrupt lock file — remove it
                log.warning("Removing corrupt lock file %s", lock_path)
                lock_path.unlink(missing_ok=True)

        # Atomic create — races between the stale check and this are still
        # safe because O_EXCL fails if the file already exists.
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(pid).encode())
            os.close(fd)
        except FileExistsError as exc:
            raise SystemExit(
                f"Another evaluation is already running for "
                f"{task}/{agent}/{model or 'default'} "
                f"(lock: {lock_path}). "
                f"Wait for it to finish or remove the lock file manually."
            ) from exc

        log.info("Acquired eval lock: %s (pid %d)", lock_path, pid)
        return cls(lock_path, pid)

    def release(self) -> None:
        """Release the lock if we still own it."""
        try:
            if self._lock_path.exists():
                current_pid = int(self._lock_path.read_text().strip())
                if current_pid == self._pid:
                    self._lock_path.unlink(missing_ok=True)
                    log.info("Released eval lock: %s", self._lock_path)
        except (ValueError, OSError) as exc:
            log.warning("Failed to release lock %s: %s", self._lock_path, exc)


def save_transcript(result_json_path: Path, transcript_data: str) -> str:
    """Save agent transcript alongside the result JSON. Returns the relative filename."""
    dest = result_json_path.parent / "transcript.jsonl"
    dest.write_text(transcript_data, encoding="utf-8")
    return "transcript.jsonl"


def save_source_dir(result_json_path: Path, source_dir: Path) -> str:
    """Copy agent source output alongside the result JSON. Returns the relative dir name."""
    dest = result_json_path.parent / "source"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source_dir, dest)
    return "source"


def load_result(path: Path) -> RunResult:
    """Load a RunResult from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    metadata = RunMetadata(**data["metadata"])
    token_usage = (
        TokenUsage(
            input_tokens=data["token_usage"]["input_tokens"],
            output_tokens=data["token_usage"]["output_tokens"],
            cache_read_input_tokens=data["token_usage"].get("cache_read_input_tokens"),
            cache_creation_input_tokens=data["token_usage"].get("cache_creation_input_tokens"),
            tool_calls=data["token_usage"].get("tool_calls"),
            reported_cost_usd=data["token_usage"].get("reported_cost_usd"),
            estimated_cost_usd=data["token_usage"].get("estimated_cost_usd"),
            cost_estimate_blocked_reason=data["token_usage"].get("cost_estimate_blocked_reason"),
            source=data["token_usage"].get("source"),
            is_partial=data["token_usage"].get("is_partial", False),
        )
        if data.get("token_usage")
        else None
    )
    build = BuildResult(**data["build"])
    tests = [TestOutcome(**t) for t in data["tests"]]
    summary = TestSummary(
        passed=data["test_summary"]["passed"],
        failed=data["test_summary"]["failed"],
        skipped=data["test_summary"]["skipped"],
        error=data["test_summary"]["error"],
    )
    scores_data = dict(data["scores"])
    # Historical 2.0 results emitted these fields as null placeholders, but
    # the harness never implemented either dimension. Drop them on load so
    # published results remain readable after the schema cleanup.
    scores_data.pop("self_test_coverage", None)
    scores_data.pop("code_quality", None)
    scores = Scores(**scores_data)
    artifacts_data = data.get("artifacts", {})
    artifacts = RunArtifacts(
        transcript=artifacts_data.get("transcript"),
        source_dir=artifacts_data.get("source_dir"),
    )
    ss_data = data.get("source_stats", {})
    source_stats = SourceStats(
        file_count=ss_data.get("file_count", 0),
        lines_of_code=ss_data.get("lines_of_code", 0),
    )
    return RunResult(
        metadata=metadata,
        token_usage=token_usage,
        build=build,
        tests=tests,
        test_summary=summary,
        scores=scores,
        artifacts=artifacts,
        source_stats=source_stats,
        surgery=data.get("surgery"),
    )
