"""Agent adapter for Google Gemini CLI."""

from __future__ import annotations

import json
import logging
from pathlib import Path, PurePosixPath

from swe_buildbench.agents.base import AgentAdapter, read_dockerfile_arg
from swe_buildbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker" / "agents" / "gemini-cli.Dockerfile"
)

# OpenTelemetry export directory inside the container
OTEL_EXPORT_DIR = "/tmp/gemini-otel"


class GeminiCLIAdapter(AgentAdapter):
    """Adapter for Google Gemini CLI (``gemini``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "gemini-cli"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "GEMINI_CLI_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        # Configure OpenTelemetry file export for token tracking
        env["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"file://{OTEL_EXPORT_DIR}"
        return env

    @property
    def telemetry_paths(self) -> list[str]:
        return [OTEL_EXPORT_DIR]

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Gemini CLI needs a writable ~/.gemini/ (writes projects.json at
        # startup), so we mount auth files to a read-only staging dir and
        # copy them in the invoke_command startup script.
        gemini_dir = host_home / ".gemini"
        staging = "/tmp/gemini-auth"
        return {
            (gemini_dir / "oauth_creds.json").as_posix(): {
                "bind": f"{staging}/oauth_creds.json",
                "mode": "ro",
            },
            (gemini_dir / "google_accounts.json").as_posix(): {
                "bind": f"{staging}/google_accounts.json",
                "mode": "ro",
            },
            (gemini_dir / "settings.json").as_posix(): {
                "bind": f"{staging}/settings.json",
                "mode": "ro",
            },
        }

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(self, prompt_path: PurePosixPath, work_dir: PurePosixPath) -> list[str]:
        # Copy staged auth files into a writable ~/.gemini/ and seed
        # projects.json before running gemini.
        setup = (
            'mkdir -p /root/.gemini'
            ' && cp /tmp/gemini-auth/* /root/.gemini/'
            ' && echo \'{"projects":{}}\' > /root/.gemini/projects.json'
        )
        model_flag = f' --model "{self._model}"' if self._model else ""
        return [
            "bash", "-c",
            f'{setup} && cd "{work_dir}" && cat "{prompt_path}" '
            f'| gemini{model_flag}',
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from OpenTelemetry export."""
        otel_dir = container_fs / "tmp" / "gemini-otel"
        if not otel_dir.is_dir():
            log.info("No Gemini OTEL directory found at %s", otel_dir)
            return None

        input_tokens = 0
        output_tokens = 0

        for metrics_file in otel_dir.rglob("*.json"):
            try:
                data = json.loads(metrics_file.read_text(encoding="utf-8"))
                # Gemini CLI OTLP export structure — extract token metrics
                for resource_metric in data.get("resourceMetrics", []):
                    for scope_metric in resource_metric.get("scopeMetrics", []):
                        for metric in scope_metric.get("metrics", []):
                            name = metric.get("name", "")
                            if "token" not in name.lower():
                                continue
                            for dp in metric.get("dataPoints", []):
                                value = dp.get("asInt", dp.get("asDouble", 0))
                                if "input" in name.lower() or "prompt" in name.lower():
                                    input_tokens += int(value)
                                elif "output" in name.lower() or "candidate" in name.lower():
                                    output_tokens += int(value)
            except (json.JSONDecodeError, KeyError):
                log.warning("Failed to parse metrics file %s", metrics_file, exc_info=True)

        if input_tokens == 0 and output_tokens == 0:
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    @property
    def allowed_hosts(self) -> list[str]:
        return ["generativelanguage.googleapis.com", "oauth2.googleapis.com"]
