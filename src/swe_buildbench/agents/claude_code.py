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
            f" && su agent -c 'cat {prompt_path}"
            f" | claude {flags}'"
        )
        return ["bash", "-c", setup]

    def parse_token_usage(self, container_fs: Path) -> TokenUsage | None:
        """Parse token usage from OpenTelemetry export files."""
        otel_dir = container_fs / "tmp" / "otel"
        if not otel_dir.is_dir():
            log.info("No OpenTelemetry directory found at %s", otel_dir)
            return None
        return _parse_otel_token_usage(otel_dir)

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        home = "/home/agent"
        return {
            (host_home / ".claude").as_posix(): {
                "bind": f"{home}/.claude", "mode": "ro",
            },
            (host_home / ".claude.json").as_posix(): {
                "bind": f"{home}/.claude.json", "mode": "ro",
            },
        }

    @property
    def telemetry_paths(self) -> list[str]:
        return [OTEL_COLLECTOR_DIR]

    @property
    def allowed_hosts(self) -> list[str]:
        return ["api.anthropic.com"]


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
        cached_input_tokens=cache_read_tokens or None,
    )
