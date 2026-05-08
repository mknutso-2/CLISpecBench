"""Agent adapter for OpenCode CLI using OpenRouter-backed models."""

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
    / "opencode.Dockerfile"
)

EVENT_LOG_PATH = "/tmp/opencode-events.jsonl"
OPENCODE_DATA_DIR = "/root/.local/share/opencode"

_PROMPT_MESSAGE = (
    "Read /workspace/prompt.md and complete the CLISpecBench task exactly as specified. "
    "The prompt file is also attached to this message."
)


class OpenCodeAdapter(AgentAdapter):
    """Adapter for OpenCode CLI (``opencode``) configured for OpenRouter."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "OPENCODE_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        env["OPENCODE_CONFIG_CONTENT"] = json.dumps(
            _opencode_config(self._model),
            separators=(",", ":"),
        )
        env.setdefault("OPENCODE_DISABLE_AUTOUPDATE", "1")
        env.setdefault("OPENCODE_DISABLE_DEFAULT_PLUGINS", "1")
        env.setdefault("OPENCODE_DISABLE_CLAUDE_CODE", "1")
        return env

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        flags = [
            "opencode",
            "run",
            "--pure",
            "--format",
            "json",
            "--dir",
            str(work_dir),
            "--title",
            "clispecbench",
            "--dangerously-skip-permissions",
        ]
        if self._model:
            flags.extend(["--model", self._model])
        if self._effort:
            flags.extend(["--variant", self._effort])
        flags.extend([_PROMPT_MESSAGE, "--file", str(prompt_path)])

        command = " ".join(shlex.quote(part) for part in flags)
        event_log = shlex.quote(EVENT_LOG_PATH)
        script = (
            "set -o pipefail"
            f" && cd {shlex.quote(str(work_dir))}"
            f" && {command} 2>&1 | tee {event_log}"
            '; status="${PIPESTATUS[0]}"'
            f' && if grep -q \'"type":"error"\' {event_log}; then exit 1; fi'
            ' && exit "$status"'
        )
        return ["bash", "-c", script]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        event_log = container_fs / "opencode-events.jsonl"
        if event_log.is_file():
            source = event_log.read_text(encoding="utf-8")
        else:
            source = container_logs

        if not source:
            log.info("No OpenCode event data found")
            return None
        return _parse_step_finish_usage([source], tool_calls=_count_tool_calls(source))

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH, OPENCODE_DATA_DIR]

    @property
    def allowed_hosts(self) -> list[str]:
        return ["openrouter.ai", "models.dev"]

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        texts: list[str] = []
        for event in _iter_dict_events(container_logs):
            text = _event_text(event)
            if text:
                texts.append(text)
        if not texts:
            return None
        return "".join(texts).strip() or None


def _opencode_config(model: str | None) -> dict[str, Any]:
    config: dict[str, Any] = {
        "$schema": "https://opencode.ai/config.json",
        "share": "disabled",
        "autoupdate": False,
        "enabled_providers": ["openrouter"],
        "provider": {
            "openrouter": {
                "options": {
                    "apiKey": "{env:OPENROUTER_API_KEY}",
                },
            },
        },
    }
    if model:
        config["model"] = model
        provider, _, provider_model = model.partition("/")
        if provider == "openrouter" and provider_model:
            openrouter = cast(
                dict[str, Any], cast(dict[str, Any], config["provider"])["openrouter"]
            )
            openrouter["models"] = {provider_model: {}}
    return config


def _parse_step_finish_usage(
    sources: list[str], tool_calls: int | None = None
) -> TokenUsage | None:
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    reported_cost = 0.0
    tokens_found = False
    cost_found = False

    for source in sources:
        for event in _iter_dict_events(source):
            part = _event_part(event)
            if event.get("type") != "step_finish" and part.get("type") != "step-finish":
                continue

            raw_tokens = part.get("tokens", event.get("tokens"))
            if isinstance(raw_tokens, dict):
                tokens = cast(dict[str, Any], raw_tokens)
                tokens_found = True
                cache = tokens.get("cache")
                cache_d = cast(dict[str, Any], cache) if isinstance(cache, dict) else {}
                input_tokens += _coerce_int(tokens.get("input")) or 0
                output_tokens += (_coerce_int(tokens.get("output")) or 0) + (
                    _coerce_int(tokens.get("reasoning")) or 0
                )
                cache_read_tokens += (
                    _coerce_int(cache_d.get("read"))
                    or _coerce_int(tokens.get("cache_read"))
                    or _coerce_int(tokens.get("cacheRead"))
                    or 0
                )
                cache_write_tokens += (
                    _coerce_int(cache_d.get("write"))
                    or _coerce_int(tokens.get("cache_write"))
                    or _coerce_int(tokens.get("cacheWrite"))
                    or 0
                )

            raw_cost = part.get("cost", event.get("cost"))
            cost = _coerce_float(raw_cost)
            if cost is not None:
                reported_cost += cost
                cost_found = True

    total_input = input_tokens + cache_read_tokens + cache_write_tokens
    if not tokens_found or (total_input == 0 and output_tokens == 0):
        return None
    return TokenUsage(
        input_tokens=total_input,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_tokens or None,
        cache_creation_input_tokens=cache_write_tokens or None,
        tool_calls=tool_calls,
        reported_cost_usd=round(reported_cost, 6) if cost_found else None,
        source="opencode_step_finish",
        is_partial=False,
    )


def _count_tool_calls(source: str) -> int | None:
    count_legacy = 0
    call_ids: set[str] = set()
    for event in _iter_dict_events(source):
        part = _event_part(event)
        if event.get("type") != "tool_use" and part.get("type") != "tool":
            continue
        call_id = part.get("callID", event.get("callID"))
        if isinstance(call_id, str) and call_id:
            call_ids.add(call_id)
        else:
            count_legacy += 1
    count = max(count_legacy, len(call_ids))
    return count or None


def _event_text(event: dict[str, Any]) -> str | None:
    part = _event_part(event)
    for value in (part.get("text"), event.get("text"), event.get("content")):
        if isinstance(value, str) and value:
            return value
    return None


def _event_part(event: dict[str, Any]) -> dict[str, Any]:
    raw_part = event.get("part")
    if isinstance(raw_part, dict):
        return cast(dict[str, Any], raw_part)
    return {}


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
