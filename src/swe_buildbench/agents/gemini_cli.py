"""Agent adapter for Google Gemini CLI."""

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
    / "docker" / "agents" / "gemini-cli.Dockerfile"
)



class GeminiCLIAdapter(AgentAdapter):
    """Adapter for Google Gemini CLI (``gemini``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "gemini-cli"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "GEMINI_CLI_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        return {**api_key_env}

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Gemini CLI needs a writable ~/.gemini/ (writes projects.json at
        # startup), so we mount auth files to a read-only staging dir and
        # copy them in the invoke_command startup script.
        gemini_dir = host_home / ".gemini"
        staging = "/tmp/gemini-auth"
        return {
            (gemini_dir / "oauth_creds.json").as_posix(): {
                "bind": f"{staging}/oauth_creds.json",
                "mode": "ro",
            },
            (gemini_dir / "google_accounts.json").as_posix(): {
                "bind": f"{staging}/google_accounts.json",
                "mode": "ro",
            },
            (gemini_dir / "settings.json").as_posix(): {
                "bind": f"{staging}/settings.json",
                "mode": "ro",
            },
        }

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        # Copy staged auth files into a writable ~/.gemini/ and seed
        # projects.json before running gemini.
        setup = (
            'mkdir -p /root/.gemini'
            ' && cp /tmp/gemini-auth/* /root/.gemini/'
            ' && echo \'{"projects":{}}\' > /root/.gemini/projects.json'
        )
        flags = "--yolo --output-format stream-json"
        if self._model:
            flags += f' --model "{self._model}"'
        return [
            "bash", "-c",
            f'{setup} && cd "{work_dir}" && cat "{prompt_path}" '
            f"| gemini {flags}",
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from stream-json ``result`` event."""
        usage = _parse_stream_json_stats(container_logs)
        if usage is not None:
            return usage
        log.info("No token usage found in Gemini stream-json output")
        return None

    @property
    def allowed_hosts(self) -> list[str]:
        return ["generativelanguage.googleapis.com", "oauth2.googleapis.com"]


def _parse_stream_json_stats(container_logs: str) -> TokenUsage | None:
    """Parse token usage from the Gemini stream-json ``result`` event."""
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
        raw_stats = event.get("stats")
        if not isinstance(raw_stats, dict):
            continue
        stats = cast(dict[str, Any], raw_stats)
        input_tokens = int(stats.get("input_tokens", 0))
        output_tokens = int(stats.get("output_tokens", 0))
        if input_tokens == 0 and output_tokens == 0:
            return None
        cached = int(stats.get("cached", 0))
        tool_calls = int(stats.get("tool_calls", 0))
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cached or None,
            tool_calls=tool_calls or None,
        )
    return None
