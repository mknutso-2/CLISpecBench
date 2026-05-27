"""Agent adapter for Google Antigravity CLI."""

from __future__ import annotations

import logging
import shlex
from pathlib import Path, PurePosixPath

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

_AUTH_FAILURE_REGEX = "Authentication required|authentication timed out|auth timed out"
_AUTH_NOISE_MARKERS = (
    "authentication required",
    "waiting for authentication",
    "authentication timed out",
    "authentication interrupted",
    "auth timed out",
    "opening browser to authenticate",
    "https://accounts.google.com/",
    "paste the authorization code",
)


class AntigravityCLIAdapter(AgentAdapter):
    """Adapter for Google Antigravity CLI (``agy``).

    Antigravity CLI 1.0.2 does not expose noninteractive model, effort, or
    prompt-file flags. The adapter records the fixed default model label in run
    metadata, ignores unsupported overrides, then sends a short instruction that
    points the agent at CLISpecBench's mounted ``prompt.md``. This avoids shell
    argument limits for large eval docs. The adapter still requires a TTY
    because 1.0.2 can generate a response but emit zero captured stdout when
    ``agy --print`` is run by a non-TTY subprocess.
    """

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        if model and model != DEFAULT_MODEL:
            log.warning(
                "Antigravity CLI does not expose a model flag; ignoring unsupported "
                "model override %r and recording %r",
                model,
                DEFAULT_MODEL,
            )
        if effort:
            log.warning(
                "Antigravity CLI does not expose an effort flag; ignoring unsupported "
                "effort override %r",
                effort,
            )
        self._model = DEFAULT_MODEL

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
        return env

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # host_home may already be a WSL path on Windows, which Windows Python
        # cannot reliably stat. Mount the expected state dirs consistently and
        # let Docker surface missing-source problems if auth has not been set up.
        gemini_dir = host_home / ".gemini"
        return {
            (gemini_dir / "antigravity-cli").as_posix(): {
                "bind": "/root/.gemini/antigravity-cli",
                "mode": "rw",
            },
            (gemini_dir / "config").as_posix(): {
                "bind": "/root/.gemini/config",
                "mode": "rw",
            },
        }

    @property
    def model(self) -> str | None:
        return self._model or DEFAULT_MODEL

    @property
    def effort(self) -> str | None:
        return None

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        flags = [
            "agy",
            "--dangerously-skip-permissions",
            "--print-timeout",
            "24h",
            "--log-file",
            CLI_LOG_PATH,
            "--add-dir",
            str(work_dir),
            "--print",
            _prompt_message(prompt_path, work_dir, self.model),
        ]
        command = " ".join(shlex.quote(part) for part in flags)
        event_log = shlex.quote(EVENT_LOG_PATH)
        cli_log = shlex.quote(CLI_LOG_PATH)
        auth_regex = shlex.quote(_AUTH_FAILURE_REGEX)
        auth_check = f"grep -Eiq {auth_regex} {event_log} {cli_log} 2>/dev/null"
        script = (
            "set -o pipefail"
            f" && cd {shlex.quote(str(work_dir))}"
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
        log.info("Antigravity CLI token usage parsing is not available yet")
        return None

    @property
    def telemetry_paths(self) -> list[str]:
        return [EVENT_LOG_PATH, CLI_LOG_PATH]

    @property
    def allowed_hosts(self) -> list[str]:
        return [
            "accounts.google.com",
            "antigravity.google",
            "cloudcode-pa.googleapis.com",
            "oauth2.googleapis.com",
            "www.googleapis.com",
        ]

    @property
    def requires_tty(self) -> bool:
        return True

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        lines: list[str] = []
        for raw_line in container_logs.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in _AUTH_NOISE_MARKERS):
                continue
            lines.append(line)
        if not lines:
            return None
        return "\n".join(lines[-20:])


def _prompt_message(
    prompt_path: PurePosixPath,
    work_dir: PurePosixPath,
    model: str | None,
) -> str:
    model_note = f"The requested model label is {model}." if model else ""
    return " ".join(
        part
        for part in (
            "You are running inside CLISpecBench.",
            model_note,
            f"The complete task prompt is at {prompt_path}.",
            "Read it completely, including any local docs it references, then implement the task.",
            f"Put every submission file under {work_dir}/output.",
            "Do not ask for clarification.",
        )
        if part
    )
