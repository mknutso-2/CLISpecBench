"""Result schema for SWE-BuildBench evaluation runs."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = "1.0"


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
    reported_cost_usd: float | None = None   # Native cost from agent CLI (e.g. Claude Code)
    estimated_cost_usd: float | None = None  # Calculated from token counts + published pricing

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

    node_id: str
    outcome: str  # "passed" | "failed" | "skipped" | "error"
    duration_seconds: float
    message: str | None = None


@dataclass
class TestSummary:
    """Aggregate counts across all tests."""

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
    self_test_coverage: float | None = None
    code_quality: float | None = None
    task_score: float | None = None
    extension_scores: dict[str, float] = field(default_factory=dict[str, float])


@dataclass
class RunArtifacts:
    """Paths to preserved artifacts from the run, relative to the result file."""

    transcript: str | None = None  # e.g. "run-1-transcript.jsonl"
    source_dir: str | None = None  # e.g. "run-1-source/"


@dataclass
class RunMetadata:
    """Identifying information for a single evaluation run."""

    run_id: str
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
    surgery: str | None = None  # Description of post-hoc fix applied to get code to compile

    @property
    def schema_version(self) -> str:
        return SCHEMA_VERSION

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
        if self.surgery:
            d["surgery"] = self.surgery
        return d

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def make_run_id(task: str, agent: str, run_number: int, model: str | None = None) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%d")
    model_part = f"_{model}" if model else ""
    return f"{task}_{agent}{model_part}_{ts}_run-{run_number}"


def _model_effort_slug(model: str | None, effort: str | None) -> str | None:
    """Build a folder name like 'opus_max' or 'gpt-5.4' from model + effort."""
    if not model:
        return None
    if effort:
        return f"{model}_{effort}"
    return model


def _model_base_dir(
    output_dir: Path,
    task: str,
    agent: str,
    model: str | None = None,
    effort: str | None = None,
) -> Path:
    """Return the base directory for a task/agent/model combination."""
    base = output_dir / task / agent
    slug = _model_effort_slug(model, effort)
    if slug:
        base = base / slug
    return base


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
    meta = data["metadata"]
    meta.setdefault("eval_version", "unknown")
    meta.setdefault("harness_version", "unknown")
    metadata = RunMetadata(**meta)
    token_usage = (
        TokenUsage(
            input_tokens=data["token_usage"]["input_tokens"],
            output_tokens=data["token_usage"]["output_tokens"],
            # Support old field name "cached_input_tokens" for backward compat
            cache_read_input_tokens=(
                data["token_usage"].get("cache_read_input_tokens")
                or data["token_usage"].get("cached_input_tokens")
            ),
            cache_creation_input_tokens=data["token_usage"].get("cache_creation_input_tokens"),
            tool_calls=data["token_usage"].get("tool_calls"),
            reported_cost_usd=data["token_usage"].get("reported_cost_usd"),
            estimated_cost_usd=data["token_usage"].get("estimated_cost_usd"),
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
    scores = Scores(**data["scores"])
    artifacts_data = data.get("artifacts", {})
    artifacts = RunArtifacts(
        transcript=artifacts_data.get("transcript"),
        source_dir=artifacts_data.get("source_dir"),
    )
    return RunResult(
        metadata=metadata,
        token_usage=token_usage,
        build=build,
        tests=tests,
        test_summary=summary,
        scores=scores,
        artifacts=artifacts,
        surgery=data.get("surgery"),
    )
