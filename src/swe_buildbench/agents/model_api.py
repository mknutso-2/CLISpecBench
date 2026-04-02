"""Agent adapter for direct Model API mode (single-shot, no Docker)."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from swe_buildbench.agents.base import AgentAdapter
from swe_buildbench.harness.results import TokenUsage

log = logging.getLogger(__name__)


class ModelAPIAdapter(AgentAdapter):
    """Adapter for Model API mode.

    Unlike the agentic CLI adapters, this adapter does not use Docker.
    It calls the model API directly from the host, parses the structured
    JSON file envelope from the response, and writes files to disk.
    The rest of the scoring pipeline proceeds identically.
    """

    def __init__(self, model: str = "claude-opus-4-6") -> None:
        self._model = model

    @property
    def name(self) -> str:
        return "model-api"

    @property
    def dockerfile(self) -> Path:
        # Model API mode does not use Docker
        raise NotImplementedError("Model API adapter does not use Docker containers")

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        return {**api_key_env}

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        raise NotImplementedError(
            "Model API adapter calls the API directly, not via a container command"
        )

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        # Token usage is returned inline from the API response,
        # not parsed from container filesystem.
        return None

    @property
    def model(self) -> str:
        return self._model
