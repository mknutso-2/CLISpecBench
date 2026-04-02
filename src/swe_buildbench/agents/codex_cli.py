"""Agent adapter for OpenAI Codex CLI."""

from __future__ import annotations

import json
import logging
from pathlib import Path, PurePosixPath

from swe_buildbench.agents.base import AgentAdapter, read_dockerfile_arg
from swe_buildbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker" / "agents" / "codex-cli.Dockerfile"
)

# Path inside the container where we tee the JSONL event stream
EVENT_LOG_PATH = "/tmp/codex-events.jsonl"


class CodexCLIAdapter(AgentAdapter):
    """Adapter for OpenAI Codex CLI (``codex``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "codex-cli"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "CODEX_CLI_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        return {**api_key_env}

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        # Use `codex exec --json` and tee the event stream for token parsing.
        flags = (
            f"--json --dangerously-bypass-approvals-and-sandbox"
            f' --cd "{work_dir}"'
        )
        if self._model:
            flags += f' --model "{self._model}"'
        return [
            "bash", "-c",
            f'cat {prompt_path} | codex exec {flags}'
            f' 2>&1 | tee {EVENT_LOG_PATH}',
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from the JSONL event stream.

        Checks container logs first (the --json output is tee'd to stdout),
        then falls back to the event log file.
        """
        sources: list[str] = []
        if container_logs:
            sources.append(container_logs)
        event_log = container_fs / "tmp" / "codex-events.jsonl"
        if event_log.is_file():
            sources.append(event_log.read_text(encoding="utf-8"))

        if not sources:
            log.info("No Codex event data found")
            return None

        input_tokens = 0
        output_tokens = 0
        cached_input_tokens = 0

        for source in sources:
            for line in source.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "turn.completed":
                    usage = event.get("usage", {})
                    input_tokens += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)
                    cached_input_tokens += usage.get(
                        "cached_input_tokens", 0,
                    )
                    break  # Only one turn in exec mode
            if input_tokens > 0:
                break  # Found usage, don't double-count from second source

        if input_tokens == 0 and output_tokens == 0:
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens or None,
        )

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH]

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Mount only the auth file, not the whole .codex/ dir, to avoid
        # read-only filesystem errors from Codex writing state files.
        return {
            (host_home / ".codex" / "auth.json").as_posix(): {
                "bind": "/root/.codex/auth.json",
                "mode": "ro",
            },
        }

    @property
    def allowed_hosts(self) -> list[str]:
        return ["chatgpt.com"]
