"""Central registry for supported agent adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from clispecbench.agents.base import AgentAdapter
from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.agents.codex_cli import CodexCLIAdapter
from clispecbench.agents.copilot_cli import CopilotCLIAdapter
from clispecbench.agents.gemini_cli import GeminiCLIAdapter

AgentFactory = Callable[[str | None, str | None], AgentAdapter]
BenchmarkCostPreference = Literal["reported", "estimated"]


@dataclass(frozen=True)
class AgentSpec:
    """Metadata and construction logic for a supported agent."""

    agent_id: str
    factory: AgentFactory
    docker_image: str
    version_command: str | None = None
    auth_smoke_script: str | None = None
    benchmark_cost_preference: BenchmarkCostPreference = "reported"

    def create(
        self,
        *,
        model: str | None = None,
        effort: str | None = None,
    ) -> AgentAdapter:
        """Instantiate this agent adapter for a single run."""
        return self.factory(model, effort)


_AGENT_SPECS: dict[str, AgentSpec] = {
    "claude-code": AgentSpec(
        agent_id="claude-code",
        factory=lambda model, effort: ClaudeCodeAdapter(model=model, effort=effort),
        docker_image="clispecbench-claude-code",
        version_command="claude --version",
        auth_smoke_script="scripts/smoke-test-claude.sh",
        benchmark_cost_preference="estimated",
    ),
    "codex-cli": AgentSpec(
        agent_id="codex-cli",
        factory=lambda model, effort: CodexCLIAdapter(model=model, effort=effort),
        docker_image="clispecbench-codex-cli",
        version_command="codex --version",
        auth_smoke_script="scripts/smoke-test-codex.sh",
    ),
    "copilot-cli": AgentSpec(
        agent_id="copilot-cli",
        factory=lambda model, effort: CopilotCLIAdapter(model=model, effort=effort),
        docker_image="clispecbench-copilot-cli",
        version_command="copilot --version",
        auth_smoke_script="scripts/smoke-test-copilot.sh",
    ),
    "gemini-cli": AgentSpec(
        agent_id="gemini-cli",
        factory=lambda model, effort: GeminiCLIAdapter(model=model, effort=effort),
        docker_image="clispecbench-gemini-cli",
        version_command="gemini --version",
        auth_smoke_script="scripts/smoke-test-gemini.sh",
    ),
}


def get_agent_spec(agent_id: str) -> AgentSpec:
    """Return the registry entry for a supported agent."""
    spec = _AGENT_SPECS.get(agent_id)
    if spec is None:
        available = ", ".join(sorted(_AGENT_SPECS))
        raise ValueError(f"Unknown agent {agent_id!r}. Available: {available}")
    return spec


def list_agent_ids() -> list[str]:
    """Return supported agent IDs in stable sorted order."""
    return [spec.agent_id for spec in list_agent_specs()]


def list_agent_specs() -> list[AgentSpec]:
    """Return supported agent specs in stable sorted order."""
    return sorted(_AGENT_SPECS.values(), key=lambda spec: spec.agent_id)


def list_auth_smoke_scripts() -> list[str]:
    """Return repo-relative auth-smoke script paths in stable agent order."""
    return [
        spec.auth_smoke_script for spec in list_agent_specs() if spec.auth_smoke_script is not None
    ]
