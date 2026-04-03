"""Agent adapter for Claude Code CLI."""

from __future__ import annotations

import json
import logging
from pathlib import Path, PurePosixPath
from typing import Any, cast

from swe_buildbench.agents.base import AgentAdapter, read_dockerfile_arg
from swe_buildbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker" / "agents" / "claude-code.Dockerfile"
)

# OpenTelemetry collector config path inside the container
OTEL_COLLECTOR_DIR = "/tmp/otel"


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code CLI (``claude``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "CLAUDE_CODE_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        # Configure OpenTelemetry file export for token tracking
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
        if self._effort:
            flags += f" --effort {self._effort}"
        setup = (
            f"chown -R agent:agent {work_dir}"
            # Docker creates ~/.claude/ as root when bind-mounting credential
            # files into it.  Fix ownership of the directory (not -R, since
            # the bind-mounted files inside are ro) so Claude Code can create
            # session-env/ (needed by its Bash tool).
            f" && mkdir -p /home/agent/.claude && chown agent:agent /home/agent/.claude"
            f" && su agent -c 'cat {prompt_path}"
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

        otel_dir = container_fs / "tmp" / "otel"
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
        mounts: dict[str, dict[str, str]] = {}
        for filename in (".credentials.json", "settings.json"):
            mounts[(host_home / ".claude" / filename).as_posix()] = {
                "bind": f"{home}/.claude/{filename}", "mode": "ro",
            }
        mounts[(host_home / ".claude.json").as_posix()] = {
            "bind": f"{home}/.claude.json", "mode": "ro",
        }
        return mounts

    @property
    def telemetry_paths(self) -> list[str]:
        return [OTEL_COLLECTOR_DIR]

    @property
    def allowed_hosts(self) -> list[str]:
        return ["api.anthropic.com"]


def _parse_stream_json_usage(container_logs: str) -> TokenUsage | None:
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
        raw_usage = event.get("usage") or event.get("token_usage")
        if not isinstance(raw_usage, dict):
            continue
        usage = cast(dict[str, Any], raw_usage)
        uncached_input = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        cache_read = int(usage.get("cache_read_input_tokens", 0))
        cache_creation = int(usage.get("cache_creation_input_tokens", 0))
        if uncached_input == 0 and output_tokens == 0 and cache_read == 0:
            return None
        raw_cost = event.get("total_cost_usd")
        return TokenUsage(
            input_tokens=uncached_input + cache_read + cache_creation,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read or None,
            cache_creation_input_tokens=cache_creation or None,
            tool_calls=_count_tool_calls(container_logs),
            reported_cost_usd=round(float(raw_cost), 6) if raw_cost is not None else None,
        )
    return None


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
