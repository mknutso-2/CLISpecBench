"""Agent adapter for Claude Code CLI."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

from clispecbench.agents.base import AgentAdapter, read_dockerfile_arg
from clispecbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

_AGENTS_DOCKER_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docker" / "agents"
DOCKERFILE = _AGENTS_DOCKER_DIR / "claude-code.Dockerfile"
LEGACY_DOCKERFILE = _AGENTS_DOCKER_DIR / "claude-code-legacy.Dockerfile"

# OpenTelemetry export directory inside the container
OTEL_COLLECTOR_DIR = "/tmp/otel"

# Per-message output-token ceiling for the CLI. The CLI default is 32000, which
# truncates the most verbose models mid-task (Opus 4.8 at --effort max hit it on
# every run, dying with stub submissions). We set a virtually-unlimited value;
# the CLI clamps it down to each model's true max output (verified: 1e6 succeeds
# on both 128k- and 64k-max models, with no API max_tokens rejection), so this
# is safe across all models and simply removes the artificial 32k truncation.
# Kept well under int32 max to avoid any downstream overflow. Models that don't
# exceed 32k (4.5/4.6/4.7 historically did so only twice ever) are unaffected.
MAX_OUTPUT_TOKENS = "1000000"


@dataclass(frozen=True)
class _CliVariant:
    """A pinned Claude Code CLI generation behind the single ``claude-code`` agent.

    The agent identity is always ``claude-code``; the *variant* selects which
    container image / CLI version runs and how it is driven. The CLI version is
    recorded per-run in ``metadata.agent_version`` (read from the variant's
    Dockerfile), so the dashboard can distinguish e.g. 2.1.120 from 2.0.2
    without inventing separate agent names.
    """

    key: str
    image_tag: str
    dockerfile: Path
    supports_effort: bool  # 2.1+ has --effort; 2.0.x controls reasoning via a budget
    telemetry: bool  # 2.0.x's OTLP exporter crashes on file:// — disable there
    max_thinking_tokens: str | None  # fixed reasoning budget when --effort is absent


# Default: the current pinned CLI (2.1.x), adaptive thinking via --effort, OTEL on.
_DEFAULT_VARIANT = _CliVariant(
    key="default",
    image_tag="clispecbench-claude-code",
    dockerfile=DOCKERFILE,
    supports_effort=True,
    telemetry=True,
    max_thinking_tokens=None,
)
# Legacy: a 2.0.x CLI that still recognizes the deprecated 4.0-generation
# snapshot IDs. No --effort flag; reasoning set via MAX_THINKING_TOKENS; OTEL off.
_LEGACY_VARIANT = _CliVariant(
    key="legacy",
    image_tag="clispecbench-claude-code-legacy",
    dockerfile=LEGACY_DOCKERFILE,
    supports_effort=False,
    telemetry=False,
    max_thinking_tokens="31999",
)
_VARIANTS: dict[str, _CliVariant] = {v.key: v for v in (_DEFAULT_VARIANT, _LEGACY_VARIANT)}

# Models the current pinned CLI no longer serves faithfully — it silently falls
# back to its default model (verified: claude-opus-4-7). These must run on the
# legacy CLI variant. The served-vs-requested model guard backstops this map:
# if a model routes to the wrong CLI, the run fails rather than mislabels.
_LEGACY_MODELS: frozenset[str] = frozenset(
    {
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-opus-4-1-20250805",
    }
)


def _resolve_cli_variant(model: str | None, cli_version: str | None) -> _CliVariant:
    """Pick the CLI variant for a run: explicit override, else model-driven default.

    ``cli_version`` accepts a variant key (``"default"``/``"legacy"``) or the
    resolved CLI version string (e.g. ``"2.0.2"``). When unset, models in
    :data:`_LEGACY_MODELS` route to the legacy variant and everything else to
    the default.
    """
    if cli_version:
        if cli_version in _VARIANTS:
            return _VARIANTS[cli_version]
        for variant in _VARIANTS.values():
            if read_dockerfile_arg(variant.dockerfile, "CLAUDE_CODE_VERSION") == cli_version:
                return variant
        versions = {
            read_dockerfile_arg(v.dockerfile, "CLAUDE_CODE_VERSION") for v in _VARIANTS.values()
        }
        valid = ", ".join(sorted({*_VARIANTS} | versions))
        raise ValueError(f"Unknown --cli-version {cli_version!r}. Valid: {valid}")
    if model in _LEGACY_MODELS:
        return _LEGACY_VARIANT
    return _DEFAULT_VARIANT


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code CLI (``claude``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
        cli_version: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort
        # One agent identity ("claude-code") spanning multiple pinned CLI
        # generations. The variant (default vs legacy) is chosen by an explicit
        # --cli-version or, by default, by the model. The CLI version is
        # surfaced per-run via the `version` property → metadata.agent_version.
        self._variant = _resolve_cli_variant(model, cli_version)

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(self._variant.dockerfile, "CLAUDE_CODE_VERSION")

    @property
    def dockerfile(self) -> Path:
        return self._variant.dockerfile

    @property
    def image_tag(self) -> str:
        return self._variant.image_tag

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        # Lift the 32k per-message output cap (CLI clamps to each model's max).
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = MAX_OUTPUT_TOKENS
        if self._variant.telemetry:
            # Configure OpenTelemetry file export for token tracking. Disabled
            # on the legacy variant — the 2.0.x OTLP exporter crashes on the
            # file:// endpoint; token/cost there come from the stream-json
            # result event instead (the preferred parse path).
            env["CLAUDE_CODE_ENABLE_TELEMETRY"] = "1"
            env["OTEL_METRICS_EXPORTER"] = "otlp"
            env["OTEL_LOGS_EXPORTER"] = "otlp"
            env["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"file://{OTEL_COLLECTOR_DIR}"
        return env

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        # Container starts as root (so copy_in can write files), then we fix
        # ownership and drop to the non-root 'agent' user before running claude.
        # Claude Code refuses --dangerously-skip-permissions as root.
        flags = "--print --dangerously-skip-permissions --verbose --output-format stream-json"
        if self._model:
            flags += f" --model {self._model}"
        # --effort only exists on 2.1+. On the legacy variant we instead set a
        # fixed reasoning budget via MAX_THINKING_TOKENS inside the agent shell.
        if self._variant.supports_effort and self._effort:
            flags += f" --effort {self._effort}"
        thinking_prefix = ""
        if self._variant.max_thinking_tokens:
            thinking_prefix = f"export MAX_THINKING_TOKENS={self._variant.max_thinking_tokens}; "
        setup = (
            f"chown -R agent:agent {work_dir}"
            # Docker creates ~/.claude/ as root when bind-mounting credential
            # files into it.  Fix ownership of the directory (not -R, since
            # the bind-mounted files inside are ro) so Claude Code can create
            # session-env/ (needed by its Bash tool).
            f" && mkdir -p /home/agent/.claude && chown agent:agent /home/agent/.claude"
            f" && su agent -c '{thinking_prefix}cat {prompt_path}"
            f" | claude {flags}'"
        )
        return ["bash", "-c", setup]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from the stream-json transcript.

        The ``result`` event emitted at the end of the stream-json output
        contains aggregated token counts.  Falls back to OTEL if the
        transcript doesn't contain usage data.
        """
        usage = _parse_stream_json_usage(container_logs)
        if usage is not None:
            return usage

        # copy_out() extracts /tmp/otel → extract_dir/otel
        otel_dir = container_fs / "otel"
        if not otel_dir.is_dir():
            log.info("No OpenTelemetry directory found at %s", otel_dir)
            return None
        return _parse_otel_token_usage(otel_dir)

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        home = "/home/agent"
        # Mount individual credential files — NOT the whole ~/.claude/ dir.
        # Claude Code needs to create ~/.claude/session-env/ at runtime, so
        # the directory itself must be writable.  Mounting the dir as ro
        # causes every Bash tool invocation to fail with ENOENT.
        #
        # Deliberately do NOT mount ~/.claude.json. That host file caches the
        # user's claude.ai connector list (Gmail / GCal / Drive MCP servers)
        # under `claudeAiMcpEverConnected`; mounting it leaks those connector
        # names into the in-container session's `tools` and `mcp_servers`
        # advertisements, contaminating the eval. Empirically (verified at
        # claude-code 2.1.120) the CLI runs cleanly without the file — no
        # warnings on stdout/stderr, `mcp_servers:[]`, no `mcp__*` tools.
        mounts: dict[str, dict[str, str]] = {}
        for filename in (".credentials.json", "settings.json"):
            mounts[(host_home / ".claude" / filename).as_posix()] = {
                "bind": f"{home}/.claude/{filename}",
                "mode": "ro",
            }
        return mounts

    @property
    def telemetry_paths(self) -> list[str]:
        return [OTEL_COLLECTOR_DIR]

    @property
    def canonical_transcript_container_dir(self) -> str | None:
        # Claude Code persists each session as a JSONL under
        # ~/.claude/projects/<munged-cwd>/<session-id>.jsonl even in
        # --print headless mode.  Capturing it gives us the on-disk
        # canonical-format transcript (with the initial prompt as a
        # replayable user message and isCompactSummary flags) in addition
        # to the stream-json we already collect from stdout.
        return "/home/agent/.claude/projects"

    @property
    def allowed_hosts(self) -> list[str]:
        return ["api.anthropic.com"]

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        """Extract last assistant text from Claude Code stream-json output."""
        for line in reversed(container_logs.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if event.get("type") != "assistant":
                continue
            content = event.get("message", {}).get("content", [])
            texts = [b.get("text", "") for b in content if b.get("type") == "text"]
            if texts:
                return texts[-1]
        return None

    def detect_served_model(self, container_logs: str) -> str | None:
        """Return the model claude-code actually ran, per its transcript.

        The CLI emits a ``{"type":"system","subtype":"init",...}`` event at
        startup whose ``model`` field is the resolved main-session model — the
        ground truth for what was served, recorded before any API call. We
        prefer it over per-turn ``model`` fields because the latter also
        include subagent models (e.g. a haiku quota/title helper), which would
        be false mismatches. Falls back to the first non-subagent assistant
        turn's ``model`` if no init event is present.
        """
        first_assistant_model: str | None = None
        for line in container_logs.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                model = event.get("model")
                if isinstance(model, str) and model:
                    return model
            if first_assistant_model is None and event.get("type") == "assistant":
                model = event.get("message", {}).get("model")
                if isinstance(model, str) and model and "<synthetic>" not in model:
                    first_assistant_model = model
        return first_assistant_model


def _parse_stream_json_usage(
    container_logs: str,
) -> TokenUsage | None:
    """Parse token usage from the stream-json ``result`` event."""
    for line in reversed(container_logs.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if event.get("type") != "result":
            continue
        usage = _extract_stream_json_usage(event)
        if usage is None:
            continue
        if (
            usage.uncached_input_tokens == 0
            and usage.output_tokens == 0
            and usage.cache_read_input_tokens == 0
        ):
            return None
        raw_cost = event.get("total_cost_usd")
        return TokenUsage(
            input_tokens=usage.total_input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_input_tokens=usage.cache_read_input_tokens or None,
            cache_creation_input_tokens=usage.cache_creation_input_tokens or None,
            tool_calls=_count_tool_calls(container_logs),
            estimated_cost_usd=usage.estimated_cost_usd,
            cost_estimate_blocked_reason=usage.cost_estimate_blocked_reason,
            reported_cost_usd=round(float(raw_cost), 6) if raw_cost is not None else None,
        )
    return None


@dataclass(frozen=True)
class _ClaudeModelUsage:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int

    @property
    def total_input_tokens(self) -> int:
        return self.input_tokens + self.cache_read_input_tokens + self.cache_creation_input_tokens


@dataclass(frozen=True)
class _StreamJsonUsage:
    uncached_input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    estimated_cost_usd: float | None = None
    cost_estimate_blocked_reason: str | None = None

    @property
    def total_input_tokens(self) -> int:
        return (
            self.uncached_input_tokens
            + self.cache_read_input_tokens
            + self.cache_creation_input_tokens
        )


def _extract_stream_json_usage(
    event: dict[str, Any],
) -> _StreamJsonUsage | None:
    """Extract the most complete usage tuple from a Claude Code result event.

    Prefer aggregated ``modelUsage`` totals whenever they are present. Claude
    Code's top-level ``usage`` block can undercount billed categories compared
    to per-model entries, and mixed-model sessions need the sum across all
    models rather than a single selected bucket.
    """
    raw_model_usage = event.get("modelUsage") or event.get("model_usage")
    if isinstance(raw_model_usage, dict):
        model_usage = _parse_model_usage_entries(cast(dict[str, Any], raw_model_usage))
        if model_usage:
            return _aggregate_model_usage(model_usage)

    raw_usage = event.get("usage") or event.get("token_usage")
    if not isinstance(raw_usage, dict):
        return None
    usage = cast(dict[str, Any], raw_usage)
    return _StreamJsonUsage(
        uncached_input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        cache_read_input_tokens=int(usage.get("cache_read_input_tokens", 0)),
        cache_creation_input_tokens=int(usage.get("cache_creation_input_tokens", 0)),
    )


def _parse_model_usage_entries(raw_model_usage: dict[str, Any]) -> list[_ClaudeModelUsage]:
    entries: list[_ClaudeModelUsage] = []
    for model_name, raw_usage in raw_model_usage.items():
        if not isinstance(raw_usage, dict):
            continue
        usage = cast(dict[str, Any], raw_usage)
        entries.append(
            _ClaudeModelUsage(
                model=model_name,
                input_tokens=int(usage.get("inputTokens", 0)),
                output_tokens=int(usage.get("outputTokens", 0)),
                cache_read_input_tokens=int(usage.get("cacheReadInputTokens", 0)),
                cache_creation_input_tokens=int(usage.get("cacheCreationInputTokens", 0)),
            )
        )
    return entries


def _aggregate_model_usage(entries: list[_ClaudeModelUsage]) -> _StreamJsonUsage:
    estimated_cost = _estimate_model_usage_cost(entries)
    return _StreamJsonUsage(
        uncached_input_tokens=sum(entry.input_tokens for entry in entries),
        output_tokens=sum(entry.output_tokens for entry in entries),
        cache_read_input_tokens=sum(entry.cache_read_input_tokens for entry in entries),
        cache_creation_input_tokens=sum(entry.cache_creation_input_tokens for entry in entries),
        estimated_cost_usd=estimated_cost,
        cost_estimate_blocked_reason=("unpriced_model_usage" if estimated_cost is None else None),
    )


def _estimate_model_usage_cost(entries: list[_ClaudeModelUsage]) -> float | None:
    from clispecbench.harness.pricing import ALL_PRICING

    total_cost = 0.0
    for entry in entries:
        pricing = ALL_PRICING.get(entry.model)
        if pricing is None:
            return None
        total_cost += (
            entry.input_tokens * pricing.input / 1_000_000
            + entry.cache_read_input_tokens * pricing.cached_input / 1_000_000
            + entry.cache_creation_input_tokens * (pricing.cache_write or pricing.input) / 1_000_000
            + entry.output_tokens * pricing.output / 1_000_000
        )
    return round(total_cost, 6)


def _count_tool_calls(container_logs: str) -> int:
    """Count tool_use blocks in Claude Code stream-json assistant events."""
    count = 0
    for line in container_logs.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                count += 1
    return count


def _parse_otel_attrs(raw_attrs: Any) -> dict[str, str]:
    """Extract key-value string pairs from OTLP attribute arrays."""
    attrs: dict[str, str] = {}
    if not isinstance(raw_attrs, list):
        return attrs
    typed_attrs = cast(list[dict[str, Any]], raw_attrs)
    for a in typed_attrs:
        k = str(a.get("key", ""))
        v = cast(dict[str, Any] | None, a.get("value"))
        if isinstance(v, dict):
            attrs[k] = str(v.get("stringValue", ""))
        else:
            attrs[k] = ""
    return attrs


def _parse_otel_token_usage(otel_dir: Path) -> TokenUsage | None:
    """Parse OTLP JSON exports for Claude Code token usage.

    The OTLP JSON structure is deeply nested and untyped, so this function
    uses ``Any`` throughout to keep the parsing readable.
    """
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0

    for metrics_file in otel_dir.rglob("*.json"):
        try:
            data: Any = json.loads(metrics_file.read_text(encoding="utf-8"))
            for rm in data.get("resourceMetrics", []):
                for sm in rm.get("scopeMetrics", []):
                    for metric in sm.get("metrics", []):
                        if metric.get("name") != "claude_code.token.usage":
                            continue
                        for dp in metric.get("dataPoints", []):
                            attrs = _parse_otel_attrs(dp.get("attributes", []))
                            value = int(dp.get("asInt", dp.get("asDouble", 0)))
                            token_type = attrs.get("type", "")
                            if token_type == "input":
                                input_tokens += value
                            elif token_type == "output":
                                output_tokens += value
                            elif token_type == "cacheRead":
                                cache_read_tokens += value
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            log.warning("Failed to parse metrics file %s", metrics_file, exc_info=True)

    if input_tokens == 0 and output_tokens == 0:
        return None

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_tokens or None,
    )
