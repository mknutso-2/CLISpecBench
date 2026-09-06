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

# Codex persists normal session rollout JSONL here. Those files contain
# EventMsg::TokenCount snapshots that survive a later turn.failed event.
SESSION_ROLLOUT_DIR = "/root/.codex/sessions"
TOOL_CALLS_DEFINITION = "underlying_tool_invocations_v2"
_TOOL_ITEMS = frozenset(
    {
        "command_execution",
        "file_change",
        "web_search",
        "mcp_tool_call",
        "collab_tool_call",
        "image_view",
        "image_generation",
    }
)
_NON_TOOL_ITEMS = frozenset({"agent_message", "reasoning", "error"})


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
        # Docker supplies the trust boundary: the whole agent container is on
        # an internal network and can egress only through an allowlisting
        # proxy. Codex therefore runs in its documented external-sandbox mode,
        # while hosted web search is disabled separately.
        flags = (
            f'--json --dangerously-bypass-approvals-and-sandbox --cd "{work_dir}"'
            " --skip-git-repo-check"
            ' -c web_search="disabled"'
            " -c tools.web_search=false"
        )
        if self._model:
            flags += f' --model "{self._model}"'
        if self._effort:
            flags += f' -c model_reasoning_effort="{self._effort}"'
        script = (
            f"set -o pipefail; cat {prompt_path} | codex exec {flags} 2>&1 | tee {EVENT_LOG_PATH}"
        )
        return [
            "bash",
            "-c",
            script,
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from Codex CLI telemetry.

        Primary source: ``codex exec --json`` emits ``turn.completed.usage``.
        Fallback source: Codex's persisted session rollout files contain
        ``token_count`` snapshots after completed model responses. This can
        recover an authoritative lower-bound token count for runs whose final
        event is ``turn.failed``. It still cannot recover tokens for an API
        stream that fails before Codex receives ``response.completed``.

        We deliberately avoid visible-log byte/token estimation. It misses
        hidden prompts, tool schemas, reasoning tokens, and API-call
        multiplication, so a fake count is worse than no count.
        """
        sources: list[str] = []
        if container_logs:
            sources.append(container_logs)
        # copy_out() extracts /tmp/codex-events.jsonl → extract_dir/codex-events.jsonl
        event_log = container_fs / "codex-events.jsonl"
        if event_log.is_file():
            sources.append(event_log.read_text(encoding="utf-8"))

        tool_calls = count_tool_calls(sources)
        if sources:
            usage = _parse_exec_event_usage(sources, tool_calls)
            if usage is not None:
                # Older exec streams omit detail available in the session. Only
                # enrich from a snapshot whose core totals match this turn.
                rollout = _parse_session_rollout_usage(container_fs, tool_calls)
                if rollout is not None and (
                    rollout.input_tokens == usage.input_tokens
                    and rollout.output_tokens == usage.output_tokens
                    and rollout.cache_read_input_tokens == usage.cache_read_input_tokens
                ):
                    for name in ("reasoning_output_tokens", "cache_creation_input_tokens"):
                        if getattr(usage, name) is None:
                            setattr(usage, name, getattr(rollout, name))
                return usage
        else:
            log.info("No Codex event data found")

        return _parse_session_rollout_usage(container_fs, tool_calls)

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH, SESSION_ROLLOUT_DIR]

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

    @property
    def network_policy(self) -> str:
        return "api-only"

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

    def refine_exit_reason(
        self,
        container_fs: Path,
        container_logs: str,
        current_exit_reason: str,
    ) -> str:
        """Mark a final Codex ``turn.failed`` as an error even if the shell exits 0."""
        final_turn = _final_turn_event(_event_sources(container_fs, container_logs))
        if final_turn is not None and final_turn.get("type") == "turn.failed":
            return "error"
        return current_exit_reason


def _parse_exec_event_usage(sources: list[str], tool_calls: int | None = None) -> TokenUsage | None:
    for source in sources:
        for event in _iter_dict_events(source):
            if event.get("type") != "turn.completed":
                continue
            usage = event.get("usage")
            if not isinstance(usage, dict):
                continue
            return _token_usage_from_codex_usage(
                cast(dict[str, Any], usage),
                source="codex_exec_turn_completed",
                is_partial=False,
                tool_calls=tool_calls,
            )
    return None


def _parse_session_rollout_usage(
    container_fs: Path,
    tool_calls: int | None = None,
) -> TokenUsage | None:
    # copy_out() extracts /root/.codex/sessions → extract_dir/sessions
    sessions_dir = container_fs / "sessions"
    if not sessions_dir.is_dir():
        log.info("No Codex session rollout directory found at %s", sessions_dir)
        return None

    latest: TokenUsage | None = None
    # Codex uses ISO-like rollout filenames under YYYY/MM/DD directories, so
    # lexical path order matches chronological order for the current schema.
    for rollout_file in sorted(sessions_dir.rglob("*.jsonl")):
        try:
            text = rollout_file.read_text(encoding="utf-8")
        except OSError:
            log.debug("Could not read Codex rollout file %s", rollout_file, exc_info=True)
            continue
        for event in _iter_dict_events(text):
            total_usage = _token_count_total_usage(event)
            if total_usage is None:
                continue
            latest = _token_usage_from_codex_usage(
                total_usage,
                source="codex_session_rollout_token_count",
                is_partial=True,
                tool_calls=tool_calls,
            )
    return latest


def _token_count_total_usage(event: dict[str, Any]) -> dict[str, Any] | None:
    payload: object
    if event.get("type") == "event_msg":
        payload = event.get("payload")
    else:
        payload = event

    if not isinstance(payload, dict):
        return None
    payload_d = cast(dict[str, Any], payload)
    if payload_d.get("type") != "token_count":
        return None
    info = payload_d.get("info")
    if not isinstance(info, dict):
        return None
    total_usage = cast(dict[str, Any], info).get("total_token_usage")
    if not isinstance(total_usage, dict):
        return None
    return cast(dict[str, Any], total_usage)


def _token_usage_from_codex_usage(
    usage: dict[str, Any],
    *,
    source: str,
    is_partial: bool,
    tool_calls: int | None = None,
) -> TokenUsage | None:
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    if input_tokens == 0 and output_tokens == 0:
        return None
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=_optional_token_count(
            usage, "cached_input_tokens", "cache_read_input_tokens"
        ),
        cache_creation_input_tokens=_optional_token_count(
            usage, "cache_write_input_tokens", "cache_creation_input_tokens"
        ),
        reasoning_output_tokens=_optional_token_count(usage, "reasoning_output_tokens"),
        tool_calls=tool_calls,
        tool_calls_definition=TOOL_CALLS_DEFINITION if tool_calls is not None else None,
        source=source,
        is_partial=is_partial,
    )


def _optional_token_count(usage: dict[str, Any], *names: str) -> int | None:
    for name in names:
        value = usage.get(name)
        if value is not None:
            return int(value)
    return None


def count_tool_calls(sources: list[str]) -> int | None:
    """Count underlying calls once, including failed and unfinished calls.

    Exec's item stream describes the underlying operations, not code-mode
    wrappers. A multi-file patch is one file_change item. stdout and its tee
    are alternative copies: use the most complete, never sum them. Unknown
    item types or unidentifiable unfinished calls make the count unavailable.
    """
    counts: list[int] = []
    for source in sources:
        ids: set[str] = set()
        anonymous = 0
        plan_calls = 0
        plan_seen = False
        seen = False
        unsupported = False
        for event in _iter_dict_events(source):
            event_type = event.get("type", "")
            if event_type in {"thread.started", "turn.started", "turn.completed", "turn.failed"}:
                seen = True
            if event_type not in {"item.started", "item.updated", "item.completed"}:
                continue
            seen = True
            item = event.get("item")
            if not isinstance(item, dict):
                unsupported = True
                continue
            item = cast(dict[str, Any], item)
            kind = item.get("type")
            if kind == "todo_list":
                # The CLI reuses one todo item for the entire turn. Each
                # start/update represents update_plan; completion is emitted
                # automatically at turn end and is not another invocation.
                plan_seen = True
                if event_type in {"item.started", "item.updated"}:
                    plan_calls += 1
                continue
            if kind in _NON_TOOL_ITEMS:
                continue
            if kind not in _TOOL_ITEMS:
                unsupported = True
                continue
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                ids.add(item_id)
            elif event_type == "item.completed":
                anonymous += 1
            else:
                unsupported = True
        if unsupported or (plan_seen and not plan_calls):
            log.warning("Unsupported Codex item telemetry; tool count is unavailable")
            return None
        if seen:
            counts.append(len(ids) + anonymous + plan_calls)
    return max(counts) if counts else None


def _event_sources(container_fs: Path, container_logs: str = "") -> list[str]:
    sources: list[str] = []
    if container_logs:
        sources.append(container_logs)
    event_log = container_fs / "codex-events.jsonl"
    if event_log.is_file():
        sources.append(event_log.read_text(encoding="utf-8"))
    return sources


def _final_turn_event(sources: list[str]) -> dict[str, Any] | None:
    final_turn: dict[str, Any] | None = None
    for source in sources:
        for event in _iter_dict_events(source):
            if event.get("type") in {"turn.completed", "turn.failed"}:
                final_turn = event
    return final_turn


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
