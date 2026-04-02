"""Abstract base class for agent adapters."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from swe_buildbench.harness.results import TokenUsage


def read_dockerfile_arg(dockerfile: Path, arg_name: str) -> str:
    """Read an ARG default value from a Dockerfile."""
    pattern = re.compile(rf"^ARG\s+{re.escape(arg_name)}=(.+)$", re.MULTILINE)
    match = pattern.search(dockerfile.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else "unknown"


@dataclass
class AgentRunResult:
    """What an adapter returns after an agent run completes."""

    exit_reason: str  # "completed" | "timeout" | "token_limit" | "error"
    wall_clock_seconds: float
    token_usage: TokenUsage | None = None
    raw_log_path: Path | None = None
    error_message: str | None = None


class AgentAdapter(ABC):
    """Abstract base for all agent adapters.

    Each supported agent CLI implements this interface.  The harness interacts
    with agents only through this abstraction.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier used in results and CLI (e.g. ``"claude-code"``)."""

    @property
    def version(self) -> str:
        """Agent CLI version string (e.g. ``"2.1.90"``)."""
        return "unknown"

    @property
    @abstractmethod
    def dockerfile(self) -> Path:
        """Path to the Dockerfile that builds this agent's container image."""

    @abstractmethod
    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        """Environment variables to inject into the container.

        *api_key_env* contains user-provided secrets (e.g. ``ANTHROPIC_API_KEY``).
        The adapter merges any agent-specific variables and returns the full dict.
        """

    @abstractmethod
    def invoke_command(
        self,
        prompt_path: PurePosixPath,
        work_dir: PurePosixPath,
    ) -> list[str]:
        """Shell command to start the agent inside the container.

        *prompt_path*: path (inside the container) to the assembled prompt file.
        *work_dir*: path (inside the container) to the clean working directory.
        Returns the command and arguments as a list of strings.
        """

    @abstractmethod
    def parse_token_usage(self, container_fs: Path) -> TokenUsage | None:
        """Extract token usage from agent-specific logs or telemetry.

        *container_fs*: root of the extracted container filesystem on the host.
        Returns normalized :class:`TokenUsage`, or ``None`` if unavailable.
        """

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        """Return Docker volume mounts for agent credentials.

        *host_home*: user's home directory (WSL-mapped on Windows).
        Returns dict in Docker SDK format:
        ``{host_path: {"bind": container_path, "mode": "ro"}}``
        """
        return {}

    @property
    def telemetry_paths(self) -> list[str]:
        """Container paths to extract for token usage and telemetry parsing.

        Each path is extracted into the host extract directory before
        :meth:`parse_token_usage` is called.  Paths that don't exist in
        the container are silently skipped.
        """
        return []

    @property
    def allowed_hosts(self) -> list[str]:
        """Network hosts the container is allowed to reach.

        Override this to return the agent's API endpoint(s).  All other
        outbound traffic is blocked by the sandbox network policy.
        """
        return []

    @property
    def model(self) -> str | None:
        """Model identifier for this run (e.g. ``"opus"``).

        Override in subclass or set via adapter constructor.
        """
        return None

    @property
    def effort(self) -> str | None:
        """Effort / reasoning level (e.g. ``"high"``, ``"max"``)."""
        return None

    @property
    def image_tag(self) -> str:
        """Docker image tag for this agent (e.g. ``swe-buildbench-claude-code``)."""
        return f"swe-buildbench-{self.name}"
