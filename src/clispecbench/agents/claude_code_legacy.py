"""Agent adapter for the legacy Claude Code CLI (4.0-generation models).

This is the current :class:`ClaudeCodeAdapter` with three differences, all
forced by the older 2.0.x CLI that still recognizes the Claude 4.0-generation
snapshot IDs:

  * a distinct agent id (``claude-code-legacy``) and Docker image, so its
    results never blend into the newer-CLI ``claude-code`` rows;
  * its version/Dockerfile point at ``claude-code-legacy.Dockerfile``; and
  * it never emits ``--effort`` (the flag does not exist in the 2.0.x CLI) and
    instead sets ``MAX_THINKING_TOKENS`` to the generation's maximum thinking
    budget, which is how that CLI generation controls reasoning.

Everything else — token-usage parsing, last-message extraction, served-model
detection, credential mounts — is inherited unchanged.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from clispecbench.agents.base import read_dockerfile_arg
from clispecbench.agents.claude_code import ClaudeCodeAdapter

LEGACY_DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker"
    / "agents"
    / "claude-code-legacy.Dockerfile"
)

# The 4.0-generation "max reasoning" setting. The 2.0.x CLI has no --effort
# flag; reasoning is a fixed thinking-token budget. 31999 is the conventional
# "ultrathink" ceiling, just under Opus 4's 32k output cap — the honest
# maximum-capability point for this model generation.
MAX_THINKING_TOKENS = "31999"


class ClaudeCodeLegacyAdapter(ClaudeCodeAdapter):
    """Claude Code on the legacy 2.0.x CLI, for the deprecated 4.0-gen models."""

    @property
    def name(self) -> str:
        return "claude-code-legacy"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(LEGACY_DOCKERFILE, "CLAUDE_CODE_VERSION")

    @property
    def dockerfile(self) -> Path:
        return LEGACY_DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        # Deliberately do NOT inherit the parent's OpenTelemetry env vars. The
        # 2.0.x CLI's OTLP exporter does not support the file:// endpoint the
        # parent configures and crashes at startup ("Unknown protocol ...")
        # before doing any work. Token usage is parsed from the stream-json
        # `result` event instead (the parser prefers it; OTEL is only a
        # fallback), so dropping telemetry costs us nothing here.
        return {**api_key_env}

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        # Same shape as the parent, with two deliberate changes:
        #   1. never add --effort (unsupported on the 2.0.x CLI), and
        #   2. export MAX_THINKING_TOKENS inside the `su agent` shell so it
        #      reaches the claude process regardless of su env propagation.
        flags = "--print --dangerously-skip-permissions --verbose --output-format stream-json"
        if self._model:
            flags += f" --model {self._model}"
        setup = (
            f"chown -R agent:agent {work_dir}"
            f" && mkdir -p /home/agent/.claude && chown agent:agent /home/agent/.claude"
            f" && su agent -c 'export MAX_THINKING_TOKENS={MAX_THINKING_TOKENS};"
            f" cat {prompt_path}"
            f" | claude {flags}'"
        )
        return ["bash", "-c", setup]
