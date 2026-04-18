"""Central registry for supported agent adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from swe_buildbench.agents.base import AgentAdapter
from swe_buildbench.agents.claude_code import ClaudeCodeAdapter
from swe_buildbench.agents.codex_cli import CodexCLIAdapter
from swe_buildbench.agents.copilot_cli import CopilotCLIAdapter
from swe_buildbench.agents.gemini_cli import GeminiCLIAdapter
from swe_buildbench.agents.model_api import ModelAPIAdapter

AgentFactory = Callable[[str | None, str | None], AgentAdapter]


@dataclass(frozen=True)
class AgentSpec:
    """Metadata and construction logic for a supported agent."""

    agent_id: str
    factory: AgentFactory
    docker_image: str | None = None
    version_command: str | None = None

    def create(
        self,
        *,
        model: str | None = None,
        effort: str | None = None,
    ) -> AgentAdapter:
        """Instantiate this agent adapter for a single run."""
        return self.factory(model, effort)


def _build_model_api_adapter(
    model: str | None,
    effort: str | None,
) -> AgentAdapter:
    del effort
    return ModelAPIAdapter(model=model or "claude-opus-4-6")


_AGENT_SPECS: dict[str, AgentSpec] = {
    "claude-code": AgentSpec(
        agent_id="claude-code",
        factory=lambda model, effort: ClaudeCodeAdapter(model=model, effort=effort),
        docker_image="swe-buildbench-claude-code",
        version_command="claude --version",
    ),
    "codex-cli": AgentSpec(
        agent_id="codex-cli",
        factory=lambda model, effort: CodexCLIAdapter(model=model, effort=effort),
        docker_image="swe-buildbench-codex-cli",
        version_command="codex --version",
    ),
    "copilot-cli": AgentSpec(
        agent_id="copilot-cli",
        factory=lambda model, effort: CopilotCLIAdapter(model=model, effort=effort),
        docker_image="swe-buildbench-copilot-cli",
        version_command="copilot --version",
    ),
    "gemini-cli": AgentSpec(
        agent_id="gemini-cli",
        factory=lambda model, effort: GeminiCLIAdapter(model=model, effort=effort),
        docker_image="swe-buildbench-gemini-cli",
        version_command="gemini --version",
    ),
    "model-api": AgentSpec(
        agent_id="model-api",
        factory=_build_model_api_adapter,
    ),
}


def get_agent_spec(agent_id: str) -> AgentSpec:
    """Return the registry entry for a supported agent."""
    spec = _AGENT_SPECS.get(agent_id)
    if spec is None:
        available = ", ".join(sorted(_AGENT_SPECS))
        raise ValueError(f"Unknown agent {agent_id!r}. Available: {available}")
    return spec


def list_agent_ids(*, include_non_container: bool = True) -> list[str]:
    """Return supported agent IDs in stable sorted order."""
    return [spec.agent_id for spec in list_agent_specs(include_non_container=include_non_container)]


def list_agent_specs(*, include_non_container: bool = True) -> list[AgentSpec]:
    """Return supported agent specs in stable sorted order."""
    specs = sorted(_AGENT_SPECS.values(), key=lambda spec: spec.agent_id)
    if include_non_container:
        return specs
    return [spec for spec in specs if spec.docker_image is not None]
