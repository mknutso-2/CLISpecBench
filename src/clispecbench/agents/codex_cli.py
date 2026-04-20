"""Agent adapter for OpenAI Codex CLI."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any, cast

from clispecbench.agents.base import AgentAdapter, read_dockerfile_arg
from clispecbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker"
    / "agents"
    / "codex-cli.Dockerfile"
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
        flags = f'--json --dangerously-bypass-approvals-and-sandbox --cd "{work_dir}"'
        if self._model:
            flags += f' --model "{self._model}"'
        if self._effort:
            flags += f' -c model_reasoning_effort="{self._effort}"'
        return [
            "bash",
            "-c",
            f"cat {prompt_path} | codex exec {flags} 2>&1 | tee {EVENT_LOG_PATH}",
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from the JSONL event stream.

        Codex CLI only attaches ``usage`` to ``turn.completed`` events.
        ``turn.failed`` (e.g. on context_exhausted / max_output_tokens
        / remote-compact failure) carries no usage record, so runs that
        die mid-turn return None here.

        Do not try to recover token counts after a turn failure. The
        signals that look promising are not actually comparable to the
        ``reported`` cumulative-input metric:

        - ``last_api_response_total_tokens=N`` in Codex's compact_remote
          ERROR log is the size of the *most recent single API request*,
          not the cumulative sum across all calls in the turn. For a
          run with N tool-calls these differ by a factor of ~N/2 (each
          call's input re-sends prior context).
        - Byte-summing the visible event stream (prompt + tool outputs +
          agent messages) misses the prompt itself, Codex's internal
          system prompts and tool schemas, reasoning tokens, and the
          API-call multiplication just mentioned. Measured against a
          completed run this undercounts by 16-95x — useless as a proxy.

        The qualitative signal (``metadata.notes = "context_exhausted"``)
        is the meaningful information for failed runs; a fake token
        count is worse than no token count.
        """
        sources: list[str] = []
        if container_logs:
            sources.append(container_logs)
        # copy_out() extracts /tmp/codex-events.jsonl → extract_dir/codex-events.jsonl
        event_log = container_fs / "codex-events.jsonl"
        if event_log.is_file():
            sources.append(event_log.read_text(encoding="utf-8"))

        if not sources:
            log.info("No Codex event data found")
            return None

        input_tokens = 0
        output_tokens = 0
        cached_input_tokens = 0

        for source in sources:
            for event in _iter_dict_events(source):
                if event.get("type") == "turn.completed":
                    usage = event.get("usage")
                    if not isinstance(usage, dict):
                        continue
                    usage_d = cast(dict[str, Any], usage)
                    input_tokens += int(usage_d.get("input_tokens", 0) or 0)
                    output_tokens += int(usage_d.get("output_tokens", 0) or 0)
                    cached_input_tokens += int(usage_d.get("cached_input_tokens", 0) or 0)
                    break  # Only one turn in exec mode
            if input_tokens > 0:
                break  # Found usage, don't double-count from second source

        if input_tokens == 0 and output_tokens == 0:
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cached_input_tokens or None,
            tool_calls=_count_tool_calls(container_logs),
        )

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH]

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Mount only the auth file, not the whole .codex/ dir, to avoid
        # read-only filesystem errors from Codex writing state files.
        #
        # Mode is "rw" because Codex uses single-use refresh tokens: each
        # API call may rotate the refresh token and write the replacement
        # back to auth.json.  With "ro" the write fails silently, and
        # the *next* container run finds a stale (already-consumed) token
        # and gets 401 Unauthorized on every request.  With "rw" the
        # refreshed token is written through the bind mount to the host
        # file, so sequential runs each see the latest credentials.
        return {
            (host_home / ".codex" / "auth.json").as_posix(): {
                "bind": "/root/.codex/auth.json",
                "mode": "rw",
            },
        }

    @property
    def allowed_hosts(self) -> list[str]:
        return ["chatgpt.com"]

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        """Extract last agent_message text from Codex CLI JSONL output."""
        for event in _iter_dict_events(container_logs, reverse=True):
            if event.get("type") != "item.completed":
                continue
            item = event.get("item")
            if not isinstance(item, dict):
                continue
            item_d = cast(dict[str, Any], item)
            if item_d.get("type") != "agent_message":
                continue
            text = item_d.get("text", "")
            if isinstance(text, str) and text.strip():
                return text
        return None


def _count_tool_calls(container_logs: str) -> int:
    """Count command_execution items in Codex JSONL event stream."""
    count = 0
    for event in _iter_dict_events(container_logs):
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if isinstance(item, dict):
            item_d = cast(dict[str, Any], item)
            if item_d.get("type") == "command_execution":
                count += 1
    return count


def _iter_dict_events(
    text: str,
    *,
    reverse: bool = False,
) -> Iterator[dict[str, Any]]:
    """Yield dict events from a Codex JSONL stream, skipping noise.

    The codex-cli adapter tees stdout+stderr to the event log, so any bare
    JSON literal the agent emits (``true`` / ``false`` / a quoted string of
    source code / a bare number) ends up interleaved with the real event
    dicts. Downstream parsers only care about dict-shaped events — skip
    everything else here so callers don't need to repeat the guard.
    """
    lines = text.splitlines()
    if reverse:
        lines = list(reversed(lines))
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(event, dict):
            yield event
