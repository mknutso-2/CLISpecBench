"""Agent adapter for Google Antigravity CLI."""

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
    / "antigravity-cli.Dockerfile"
)

DEFAULT_MODEL = "gemini-3.5-flash"
EVENT_LOG_PATH = "/tmp/antigravity-cli-events.log"
CLI_LOG_PATH = "/tmp/antigravity-cli.log"
TOKEN_FILE = "antigravity-oauth-token"

# The default agent offers web search, URL fetching, a browser, image
# generation, MCP, scheduled wake-ups and subagents. search_web runs on
# Google's side of the model API, so the egress proxy cannot block it. Runs
# use this project agent instead, which keeps only shell, file and task tools.
AGENT_NAME = "clispecbench"
AGENT_TOOLS = (
    "run_command",
    "manage_task",
    "wait",
    "view_file",
    "list_dir",
    "find_by_name",
    "grep_search",
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
)
AGENT_DEFINITION = (
    "---\n"
    f"name: {AGENT_NAME}\n"
    "description: Benchmark agent with shell and file tools only.\n"
    f"tools: [{', '.join(AGENT_TOOLS)}]\n"
    "---\n"
    "You are a software engineering agent. Complete the user's task using the "
    "available shell and file tools.\n"
)

_AUTH_FAILURE_REGEX = "Authentication required|authentication timed out|auth timed out"


class AntigravityCLIAdapter(AgentAdapter):
    """Adapter for Google Antigravity CLI (``agy``).

    Runs ``agy --print`` headlessly with ``--output-format stream-json``, which
    reports the model, every tool step and token usage. The prompt is a short
    instruction that points the agent at CLISpecBench's mounted ``prompt.md``,
    which avoids shell argument limits for large eval docs.
    """

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model or DEFAULT_MODEL
        self._effort = effort

    @property
    def name(self) -> str:
        return "antigravity-cli"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "ANTIGRAVITY_CLI_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        # Avoid launching an interactive browser if auth is missing in a
        # noninteractive container. The command path still reports auth errors.
        env.setdefault("BROWSER", "/bin/true")
        env.setdefault("NO_COLOR", "1")
        env.setdefault("TERM", "dumb")
        env.setdefault("AGY_CLI_HIDE_ACCOUNT_INFO", "1")
        # Keep the run on the pinned CLI; agy otherwise spawns an updater at start.
        # It accepts "true" only: "1" still starts the updater.
        env["AGY_CLI_DISABLE_AUTO_UPDATE"] = "true"
        return env

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Mount only the OAuth token. The rest of agy's state (conversations,
        # databases, settings) stays inside the container, so runs neither write
        # into the operator's Antigravity history nor share its databases.
        # Read-write so a refreshed token is written back to the host.
        token = host_home / ".gemini" / "antigravity-cli" / TOKEN_FILE
        return {
            token.as_posix(): {
                "bind": f"/root/.gemini/antigravity-cli/{TOKEN_FILE}",
                "mode": "rw",
            },
        }

    @property
    def model(self) -> str | None:
        return self._model or DEFAULT_MODEL

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        flags = [
            "agy",
            "--dangerously-skip-permissions",
            "--agent",
            AGENT_NAME,
            "--print-timeout",
            "0",
            "--log-file",
            CLI_LOG_PATH,
            "--output-format",
            "stream-json",
            "--model",
            self.model or DEFAULT_MODEL,
        ]
        if self.effort:
            flags += ["--effort", self.effort]
        flags += [
            "--add-dir",
            str(work_dir),
            "--print",
            _prompt_message(prompt_path, work_dir),
        ]
        command = " ".join(shlex.quote(part) for part in flags)
        agent_dir = f"{work_dir}/.agents/agents"
        agent_file = shlex.quote(f"{agent_dir}/{AGENT_NAME}.md")
        event_log = shlex.quote(EVENT_LOG_PATH)
        cli_log = shlex.quote(CLI_LOG_PATH)
        auth_regex = shlex.quote(_AUTH_FAILURE_REGEX)
        auth_check = f"grep -Eiq {auth_regex} {event_log} {cli_log} 2>/dev/null"
        script = (
            "set -o pipefail"
            f" && cd {shlex.quote(str(work_dir))}"
            f" && mkdir -p {shlex.quote(agent_dir)}"
            f" && printf '%s' {shlex.quote(AGENT_DEFINITION)} > {agent_file}"
            f" && touch {event_log} {cli_log}"
            " && {"
            f" ( {command} ) > >(tee {event_log}) 2>&1 &"
            ' agy_pid="$!";'
            " for _ in $(seq 1 60); do"
            f" if {auth_check}; then"
            ' kill "$agy_pid" 2>/dev/null || true;'
            ' wait "$agy_pid" 2>/dev/null || true;'
            " exit 1;"
            " fi;"
            ' if ! kill -0 "$agy_pid" 2>/dev/null; then break; fi;'
            " sleep 1;"
            " done;"
            ' wait "$agy_pid";'
            ' status="$?";'
            f" if {auth_check}; then exit 1; fi;"
            ' exit "$status";'
            " }"
        )
        return ["bash", "-c", script]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        events = _events(container_logs)
        result = _result(events)
        usage = _obj((result or {}).get("usage"))
        if not usage:
            log.info("No Antigravity stream-json result usage found")
            return None
        steps = [_obj(event.get("step_update")) for event in events]
        tool_calls = sum(
            1 for step in steps if step.get("step_type") == "tool" and step.get("state") == "DONE"
        )
        cache_read = int(usage.get("cache_read_tokens") or 0)
        return TokenUsage(
            # agy reports uncached input; TokenUsage counts the cached part too.
            input_tokens=int(usage.get("input_tokens") or 0) + cache_read,
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_input_tokens=cache_read,
            reasoning_output_tokens=usage.get("thinking_tokens"),
            tool_calls=tool_calls,
            tool_calls_definition="stream-json tool steps that reached state DONE",
            source="antigravity stream-json result",
        )

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH, CLI_LOG_PATH]

    @property
    def allowed_hosts(self) -> list[str]:
        return [
            "accounts.google.com",
            # CLI configuration and feature flags; without them agy falls back to defaults.
            "aicode.googleapis.com",
            "antigravity-unleash.goog",
            "antigravity.google",
            "cloudcode-pa.googleapis.com",
            "daily-cloudcode-pa.googleapis.com",
            "oauth2.googleapis.com",
            "www.googleapis.com",
        ]

    @property
    def network_policy(self) -> str:
        return "api-only"

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        result = _result(_events(container_logs))
        response = (result or {}).get("response")
        return response.strip() or None if isinstance(response, str) else None

    def detect_served_model(self, container_logs: str) -> str | None:
        for event in _events(container_logs):
            model = _obj(event.get("init")).get("model")
            if isinstance(model, str) and model:
                return model
        return None

    def refine_exit_reason(
        self,
        container_fs: Path,
        container_logs: str,
        current_exit_reason: str,
    ) -> str:
        del container_fs
        result = _result(_events(container_logs))
        if current_exit_reason == "completed" and result and result.get("status") != "SUCCESS":
            return "error"
        return current_exit_reason


def _events(container_logs: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in container_logs.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(cast(dict[str, Any], event))
    return events


def _obj(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _result(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("event") == "result" and (result := _obj(event.get("result"))):
            return result
    return None


def _prompt_message(prompt_path: PurePosixPath, work_dir: PurePosixPath) -> str:
    return " ".join(
        (
            "You are running inside CLISpecBench.",
            f"The complete task prompt is at {prompt_path}.",
            "Read it completely, including any local docs it references, then implement the task.",
            f"Put every submission file under {work_dir}/output.",
            "Do not ask for clarification.",
        )
    )
