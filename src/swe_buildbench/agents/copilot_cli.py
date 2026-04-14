"""Agent adapter for GitHub Copilot CLI."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, cast

from swe_buildbench.agents.base import AgentAdapter, read_dockerfile_arg
from swe_buildbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker" / "agents" / "copilot-cli.Dockerfile"
)

# Path inside the container where OTel data is written as JSON-lines
OTEL_FILE_PATH = "/tmp/copilot-otel.jsonl"


class CopilotCLIAdapter(AgentAdapter):
    """Adapter for GitHub Copilot CLI (``copilot``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "copilot-cli"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "COPILOT_CLI_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        # Auto-discover GitHub token if not explicitly provided.
        # Copilot CLI checks COPILOT_GITHUB_TOKEN, GH_TOKEN, GITHUB_TOKEN
        # (in that order).  We try `gh auth token` and common env vars.
        token_vars = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
        if not any(v in env for v in token_vars):
            token = _discover_gh_token()
            if token:
                env["COPILOT_GITHUB_TOKEN"] = token
            else:
                log.warning(
                    "No GitHub token found. Set COPILOT_GITHUB_TOKEN, "
                    "GH_TOKEN, or run 'gh auth login'."
                )
        # Enable OTel file export for token tracking.
        # COPILOT_OTEL_ENABLED activates instrumentation (available since
        # v1.0.4).  COPILOT_OTEL_FILE_EXPORTER_PATH tells the CLI to write
        # metrics/traces as JSON-lines to a local file instead of requiring
        # an OTLP endpoint.
        env["COPILOT_OTEL_ENABLED"] = "true"
        env["COPILOT_OTEL_FILE_EXPORTER_PATH"] = OTEL_FILE_PATH
        return env

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(
        self, prompt_path: PurePosixPath, work_dir: PurePosixPath,
    ) -> list[str]:
        # Copilot CLI's -p flag takes a literal text argument (not stdin),
        # so we use command substitution to read the prompt file.
        flags = "--yolo --output-format json --no-auto-update"
        if self._model:
            flags += f' --model "{self._model}"'
        if self._effort:
            flags += f' --effort "{self._effort}"'
        return [
            "bash", "-c",
            f'cd "{work_dir}" && copilot -p "$(cat {prompt_path})" {flags}',
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from OTel file export or JSONL output.

        OTel is preferred because it reports both input and output tokens,
        while the JSONL event stream only has output tokens.
        """
        # copy_out() extracts /tmp/copilot-otel.jsonl to extract_dir/copilot-otel.jsonl
        otel_file = container_fs / "copilot-otel.jsonl"
        log.debug("Looking for OTel file at %s (exists=%s)", otel_file, otel_file.is_file())
        if otel_file.is_file():
            otel_usage = _parse_otel_file(otel_file)
            if otel_usage is not None:
                # Supplement with tool call count from JSONL
                otel_usage.tool_calls = _count_tool_calls(container_logs)
                return otel_usage

        # Fall back to JSONL output (only has output tokens)
        usage = _parse_jsonl_usage(container_logs)
        if usage is not None:
            return usage

        log.info("No token usage found in Copilot CLI output")
        return None

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Copilot CLI authenticates via COPILOT_GITHUB_TOKEN / GH_TOKEN env
        # var, so credential file mounts are not strictly needed.  However,
        # we mount the gh hosts.yml so the CLI can discover the token if the
        # caller sets up the env var via the harness's api_key_env dict.
        gh_hosts = host_home / ".config" / "gh" / "hosts.yml"
        appdata_hosts = host_home / "AppData" / "Roaming" / "GitHub CLI" / "hosts.yml"
        mounts: dict[str, dict[str, str]] = {}
        # Try AppData location first (Windows), then XDG (Linux/WSL)
        for src in (appdata_hosts, gh_hosts):
            if src.exists():
                mounts[src.as_posix()] = {
                    "bind": "/root/.config/gh/hosts.yml",
                    "mode": "ro",
                }
                break
        return mounts

    @property
    def telemetry_paths(self) -> list[str]:
        return [OTEL_FILE_PATH]

    @property
    def allowed_hosts(self) -> list[str]:
        return [
            "api.github.com",
            "api.individual.githubcopilot.com",
            "copilot-proxy.githubusercontent.com",
        ]

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        """Extract last assistant.message text from Copilot CLI JSONL output."""
        for line in reversed(container_logs.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if event.get("type") != "assistant.message":
                continue
            data = event.get("data", event)
            text = data.get("text", data.get("content", ""))
            if isinstance(text, str) and text.strip():
                return text
        return None


def _parse_jsonl_usage(container_logs: str) -> TokenUsage | None:
    """Parse token usage from the Copilot CLI JSON output.

    The ``--output-format json`` flag emits JSONL events.  Token counts
    come from two places:

    - ``assistant.message`` events carry an ``outputTokens`` field.
    - The final ``result`` event carries ``usage`` with session-level
      stats (``premiumRequests``, ``totalApiDurationMs``, etc.) but may
      also contain ``input_tokens`` / ``output_tokens`` in future versions.

    We sum ``outputTokens`` from assistant messages and check the result
    event for any token-level data.
    """
    output_tokens = 0
    input_tokens = 0
    result_found = False

    for line in container_logs.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        event_type = event.get("type", "")

        if event_type == "assistant.message":
            data = event.get("data", event)
            output_tokens += int(data.get("outputTokens", 0))

        elif event_type == "result":
            result_found = True
            raw_usage = event.get("usage", {})
            if isinstance(raw_usage, dict):
                usage = cast(dict[str, Any], raw_usage)
                input_tokens += int(usage.get("input_tokens", 0))
                output_tokens += int(usage.get("output_tokens", 0))

    if not result_found:
        return None

    if input_tokens == 0 and output_tokens == 0:
        return None

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        tool_calls=_count_tool_calls(container_logs),
    )


def _count_tool_calls(container_logs: str) -> int:
    """Count tool invocations in Copilot CLI JSONL event stream."""
    count = 0
    for line in container_logs.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if event.get("type") == "tool_call":
            count += 1
    return count


def _parse_otel_file(otel_file: Path) -> TokenUsage | None:
    """Parse token usage from the Copilot CLI OTel JSON-lines file.

    The CLI writes flat JSONL records (not OTLP-wrapped ``resourceMetrics``).
    Token data comes from ``gen_ai.client.token.usage`` metric entries whose
    ``dataPoints`` carry cumulative histogram values.  The file may contain
    multiple snapshots; we take the last one (highest cumulative totals).
    """
    input_tokens = 0
    output_tokens = 0

    try:
        for line in otel_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record: Any = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue

            if record.get("type") != "metric":
                continue
            if record.get("name") != "gen_ai.client.token.usage":
                continue

            for dp in record.get("dataPoints", []):
                attrs = dp.get("attributes", {})
                if not isinstance(attrs, dict):
                    continue
                typed_attrs = cast(dict[str, Any], attrs)
                token_type = str(typed_attrs.get("gen_ai.token.type", ""))
                # Value may be a histogram dict ({"sum": N, ...}) or a scalar
                raw_value = dp.get("value", 0)
                if isinstance(raw_value, dict):
                    typed_value = cast(dict[str, Any], raw_value)
                    value = int(typed_value.get("sum", 0))
                else:
                    value = int(raw_value)
                # Cumulative — last entry wins
                if token_type == "input":
                    input_tokens = value
                elif token_type == "output":
                    output_tokens = value
    except (OSError, TypeError, AttributeError):
        log.warning("Failed to parse OTel file %s", otel_file, exc_info=True)

    if input_tokens == 0 and output_tokens == 0:
        return None
    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)


def _discover_gh_token() -> str | None:
    """Try to discover a GitHub token from the environment or ``gh`` CLI."""
    for var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(var)
        if value:
            return value
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
        )
        token = result.stdout.strip()
        if result.returncode == 0 and token:
            return token
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None
