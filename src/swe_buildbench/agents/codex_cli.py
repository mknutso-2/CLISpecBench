"""Agent adapter for OpenAI Codex CLI."""

from __future__ import annotations

import json
import logging
from pathlib import Path, PurePosixPath

from swe_buildbench.agents.base import AgentAdapter
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

    @property
    def name(self) -> str:
        return "codex-cli"

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        return {**api_key_env}

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        # Use `codex exec --json` and tee the event stream for token parsing.
        # The shell pipeline captures events while letting codex write to the
        # workspace normally.
        return [
            "bash", "-c",
            f'codex exec --json --cwd "{work_dir}" '
            f'"$(cat {prompt_path})" '
            f'2>/dev/null | tee {EVENT_LOG_PATH}',
        ]

    def parse_token_usage(self, container_fs: Path) -> TokenUsage | None:
        """Parse token usage from the JSONL event stream."""
        event_log = container_fs / "tmp" / "codex-events.jsonl"
        if not event_log.is_file():
            log.info("No Codex event log found at %s", event_log)
            return None

        input_tokens = 0
        output_tokens = 0
        cached_input_tokens = 0

        for line in event_log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Codex emits turn.completed events with usage data
            if event.get("type") == "turn.completed":
                usage = event.get("usage", {})
                input_tokens += usage.get("input_tokens", 0)
                output_tokens += usage.get("output_tokens", 0)
                cached_input_tokens += usage.get("cached_input_tokens", 0)

        if input_tokens == 0 and output_tokens == 0:
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens or None,
        )

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
