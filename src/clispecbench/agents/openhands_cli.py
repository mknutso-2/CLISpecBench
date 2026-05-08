"""Agent adapter for OpenHands CLI using OpenRouter-backed models."""

from __future__ import annotations

import json
import logging
import shlex
from pathlib import Path, PurePosixPath
from typing import Any, cast

from clispecbench.agents.base import AgentAdapter, read_dockerfile_arg
from clispecbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker"
    / "agents"
    / "openhands.Dockerfile"
)

EVENT_LOG_PATH = "/tmp/openhands-events.jsonl"
BASE_STATE_PATH = "/tmp/openhands-base-state.json"
OPENHANDS_PERSISTENCE_DIR = "/tmp/openhands"
OPENHANDS_CONVERSATIONS_DIR = f"{OPENHANDS_PERSISTENCE_DIR}/conversations"


class OpenHandsCLIAdapter(AgentAdapter):
    """Adapter for OpenHands CLI (``openhands``) configured through LiteLLM."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "openhands"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "OPENHANDS_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        if "OPENROUTER_API_KEY" in env:
            env.setdefault("LLM_API_KEY", env["OPENROUTER_API_KEY"])
        if self._model:
            env["LLM_MODEL"] = self._model
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("NO_COLOR", "1")
        env.setdefault("TERM", "dumb")
        env.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
        return env

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        flags = [
            "openhands",
            "--headless",
            "--json",
            "--always-approve",
            "--override-with-envs",
            "--file",
            str(prompt_path),
        ]

        command = " ".join(shlex.quote(part) for part in flags)
        event_log = shlex.quote(EVENT_LOG_PATH)
        base_state = shlex.quote(BASE_STATE_PATH)
        persistence_dir = shlex.quote(OPENHANDS_PERSISTENCE_DIR)
        conversations_dir = shlex.quote(OPENHANDS_CONVERSATIONS_DIR)
        work_dir_q = shlex.quote(str(work_dir))
        script = (
            "set -o pipefail"
            f" && mkdir -p {persistence_dir} {conversations_dir}"
            f" && export OPENHANDS_PERSISTENCE_DIR={persistence_dir}"
            f" OPENHANDS_CONVERSATIONS_DIR={conversations_dir}"
            f" OPENHANDS_WORK_DIR={work_dir_q}"
            " PYTHONIOENCODING=utf-8 PYTHONUTF8=1 NO_COLOR=1 TERM=dumb"
            " OPENHANDS_SUPPRESS_BANNER=1"
            f" && cd {work_dir_q}"
            f" && {command} 2>&1 | tee {event_log}"
            '; status="${PIPESTATUS[0]}"'
            f"; latest_state=$(find {conversations_dir} -name base_state.json -type f "
            "-printf '%T@ %p\\n' 2>/dev/null | sort -nr | awk 'NR==1 {print $2}')"
            f'; if [ -n "$latest_state" ]; then cp "$latest_state" {base_state}; fi'
            f'; if grep -q \'"kind": "ConversationErrorEvent"\\|'
            f'"kind":"ConversationErrorEvent"\' {event_log}; then exit 1; fi'
            ' && exit "$status"'
        )
        return ["bash", "-c", script]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        base_state = container_fs / PurePosixPath(BASE_STATE_PATH).name
        if not base_state.is_file():
            base_state = _find_latest_base_state(container_fs)

        if base_state is None or not base_state.is_file():
            log.info("No OpenHands base_state.json found")
            return None

        try:
            state = json.loads(base_state.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            log.info("Could not read OpenHands base_state.json")
            return None

        usage = _parse_base_state_usage(state)
        if usage is None:
            return None

        event_source = _read_event_source(container_fs, container_logs)
        usage.tool_calls = _count_tool_calls(event_source)
        return usage

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH, BASE_STATE_PATH, OPENHANDS_PERSISTENCE_DIR]

    @property
    def allowed_hosts(self) -> list[str]:
        return ["openrouter.ai", "github.com", "objects.githubusercontent.com"]

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        messages: list[str] = []
        for event in _iter_dict_events(container_logs):
            text = _agent_event_text(event)
            if text:
                messages.append(text)
        if not messages:
            return None
        return messages[-1].strip() or None


def _find_latest_base_state(container_fs: Path) -> Path | None:
    candidates = list((container_fs / "openhands").rglob("base_state.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _parse_base_state_usage(state: dict[str, Any]) -> TokenUsage | None:
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return None
    stats_dict = cast(dict[str, object], stats)
    raw_usage_to_metrics = stats_dict.get("usage_to_metrics")
    if not isinstance(raw_usage_to_metrics, dict):
        return None

    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    reported_cost = 0.0
    cost_found = False
    usage_found = False

    usage_to_metrics = cast(dict[str, object], raw_usage_to_metrics)
    for raw_metrics in usage_to_metrics.values():
        if not isinstance(raw_metrics, dict):
            continue
        metrics = cast(dict[str, object], raw_metrics)
        cost = _coerce_float(metrics.get("accumulated_cost"))
        if cost is not None:
            reported_cost += cost
            cost_found = True

        raw_usage = metrics.get("accumulated_token_usage")
        if not isinstance(raw_usage, dict):
            continue
        usage = cast(dict[str, object], raw_usage)
        prompt_tokens = _coerce_int(usage.get("prompt_tokens")) or 0
        completion_tokens = _coerce_int(usage.get("completion_tokens")) or 0
        cache_read = _coerce_int(usage.get("cache_read_tokens")) or 0
        cache_write = _coerce_int(usage.get("cache_write_tokens")) or 0

        input_tokens += prompt_tokens
        output_tokens += completion_tokens
        cache_read_tokens += cache_read
        cache_write_tokens += cache_write
        usage_found = True

    if not usage_found or (input_tokens == 0 and output_tokens == 0):
        return None

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_tokens or None,
        cache_creation_input_tokens=cache_write_tokens or None,
        tool_calls=None,
        reported_cost_usd=round(reported_cost, 6) if cost_found else None,
        source="openhands_base_state",
        is_partial=False,
    )


def _read_event_source(container_fs: Path, container_logs: str) -> str:
    event_log = container_fs / PurePosixPath(EVENT_LOG_PATH).name
    if event_log.is_file():
        return event_log.read_text(encoding="utf-8")
    return container_logs


def _count_tool_calls(source: str) -> int | None:
    action_ids: set[str] = set()
    count_without_id = 0
    for event in _iter_dict_events(source):
        if event.get("kind") != "ActionEvent":
            continue
        if event.get("source") != "agent":
            continue
        event_id = event.get("id")
        if isinstance(event_id, str) and event_id:
            action_ids.add(event_id)
        else:
            count_without_id += 1
    count = len(action_ids) + count_without_id
    return count or None


def _agent_event_text(event: dict[str, Any]) -> str | None:
    if event.get("source") != "agent":
        return None

    if event.get("kind") == "MessageEvent":
        raw_message = event.get("llm_message")
        if not isinstance(raw_message, dict):
            return None
        message = cast(dict[str, Any], raw_message)
        if message.get("role") != "assistant":
            return None
        return _content_text(message.get("content"))

    if event.get("kind") == "ActionEvent" and event.get("tool_name") == "finish":
        raw_action = event.get("action")
        if isinstance(raw_action, dict):
            action = cast(dict[str, Any], raw_action)
            message = action.get("message")
            if isinstance(message, str) and message:
                return message
    return None


def _content_text(raw_content: Any) -> str | None:
    if isinstance(raw_content, str):
        return raw_content
    if not isinstance(raw_content, list):
        return None

    parts: list[str] = []
    content_parts = cast(list[object], raw_content)
    for raw_part in content_parts:
        if not isinstance(raw_part, dict):
            continue
        part = cast(dict[str, object], raw_part)
        text = part.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts) if parts else None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iter_dict_events(source: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in source.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(event, dict):
            events.append(cast(dict[str, Any], event))
    return events
