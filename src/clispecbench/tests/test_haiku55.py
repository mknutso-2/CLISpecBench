"""API-free variant and privacy regressions for the pinned Claude Haiku 5.5 setup."""

from __future__ import annotations

import json
import shlex
from pathlib import Path, PurePosixPath

import pytest

from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.harness.results import models_compatible

MODEL = "claude-haiku-5-5"


@pytest.mark.parametrize("model", [MODEL, f"{MODEL}-20261007"])
def test_haiku55_routes_to_its_separate_launch_day_pin(model: str) -> None:
    adapter = ClaudeCodeAdapter(model=model, effort="low")

    assert adapter.name == "claude-code"
    assert adapter.model == model
    assert adapter.effort == "low"
    assert adapter.image_tag == "clispecbench-claude-code-haiku55"
    assert adapter.dockerfile.name == "claude-code-haiku55.Dockerfile"
    assert adapter.version == "2.1.293"


@pytest.mark.parametrize("effort", ["low", "high", "max"])
def test_haiku55_invocation_keeps_exact_model_and_adaptive_effort(effort: str) -> None:
    command = ClaudeCodeAdapter(model=MODEL, effort=effort).invoke_command(
        PurePosixPath("/workspace/prompt.md"), PurePosixPath("/workspace")
    )

    assert command[:2] == ["bash", "-c"]
    assert f"--model {MODEL} --effort {effort}" in command[2]
    assert "--output-format stream-json" in command[2]
    assert "--dangerously-skip-permissions" in command[2]
    assert "su agent -c" in command[2]
    assert "MAX_THINKING_TOKENS" not in command[2]
    assert "--fallback-model" not in command[2]


def test_haiku55_invocation_disables_cloud_skill_and_plugin_sync() -> None:
    command = ClaudeCodeAdapter(model=MODEL, effort="low").invoke_command(
        PurePosixPath("/workspace/prompt.md"), PurePosixPath("/workspace")
    )
    # Parse both shell-quoting layers without executing the command.
    agent_script = shlex.split(command[2])[-1]
    arguments = shlex.split(agent_script)
    settings_argument = arguments[arguments.index("--settings") + 1]

    assert json.loads(settings_argument) == {
        "syncClaudeAiSkills": False,
        "syncClaudeAiPlugins": False,
    }


@pytest.mark.parametrize("cli_version", ["haiku55", "2.1.293"])
def test_explicit_haiku55_override_wins_over_model_routing(cli_version: str) -> None:
    adapter = ClaudeCodeAdapter(model="claude-haiku-4-5", cli_version=cli_version)

    assert adapter.image_tag == "clispecbench-claude-code-haiku55"
    assert adapter.version == "2.1.293"
    assert adapter.model == "claude-haiku-4-5"


def test_explicit_older_variant_still_wins_for_haiku55() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL, cli_version="default")

    assert adapter.image_tag == "clispecbench-claude-code"
    assert adapter.version == "2.1.120"
    assert (
        "--settings"
        not in adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"), PurePosixPath("/workspace")
        )[2]
    )


@pytest.mark.parametrize("model", ["claude-haiku-4-5", "claude-haiku-4-5-20251001"])
def test_haiku45_keeps_its_original_pin_and_environment(model: str) -> None:
    adapter = ClaudeCodeAdapter(model=model, effort="low")

    assert adapter.image_tag == "clispecbench-claude-code"
    assert adapter.dockerfile.name == "claude-code.Dockerfile"
    assert adapter.version == "2.1.120"
    haiku55_environment = ClaudeCodeAdapter(model=MODEL).environment({})
    assert haiku55_environment.pop("ENABLE_CLAUDEAI_MCP_SERVERS") == "false"
    assert haiku55_environment.pop("API_TIMEOUT_MS") == "1800000"
    # The helper model follows each adapter's own model.
    assert adapter.environment({}) == {
        **haiku55_environment,
        "ANTHROPIC_SMALL_FAST_MODEL": model,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
    }


def test_haiku55_environment_preserves_telemetry_timeout_and_input() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL)
    provided = {"ANTHROPIC_API_KEY": "synthetic-key"}
    environment = adapter.environment(provided)

    assert provided == {"ANTHROPIC_API_KEY": "synthetic-key"}
    assert environment == {
        "ANTHROPIC_API_KEY": "synthetic-key",
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "1000000",
        "CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK": "1",
        "ANTHROPIC_SMALL_FAST_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": MODEL,
        "API_TIMEOUT_MS": "1800000",
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "file:///tmp/otel",
        "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
    }
    assert "MAX_THINKING_TOKENS" not in environment


def test_haiku55_connector_isolation_overrides_inherited_true() -> None:
    provided = {"ENABLE_CLAUDEAI_MCP_SERVERS": "true"}

    assert ClaudeCodeAdapter(model=MODEL).environment(provided)["ENABLE_CLAUDEAI_MCP_SERVERS"] == (
        "false"
    )
    assert provided == {"ENABLE_CLAUDEAI_MCP_SERVERS": "true"}
    assert (
        ClaudeCodeAdapter(model="claude-haiku-4-5").environment(provided)[
            "ENABLE_CLAUDEAI_MCP_SERVERS"
        ]
        == "true"
    )


def test_haiku55_keeps_canonical_capture_and_excludes_host_connector_cache() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL)
    home = Path("/synthetic-home")

    assert adapter.canonical_transcript_container_dir == "/home/agent/.claude/projects"
    assert adapter.telemetry_paths == ["/tmp/otel"]
    assert adapter.allowed_hosts == ["api.anthropic.com"]
    assert adapter.credential_mounts(home) == {
        (home / ".claude" / filename).as_posix(): {
            "bind": f"/home/agent/.claude/{filename}",
            "mode": "ro",
        }
        for filename in (".credentials.json", "settings.json")
    }
    assert (home / ".claude.json").as_posix() not in adapter.credential_mounts(home)


def test_haiku55_served_model_signal_exposes_a_silent_older_model_fallback() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL)
    events: tuple[dict[str, object], ...] = (
        {"type": "system", "subtype": "init", "model": "claude-haiku-4-5"},
        {"type": "assistant", "message": {"model": MODEL, "content": []}},
    )
    transcript = "\n".join(json.dumps(event) for event in events)

    assert adapter.detect_served_model(transcript) == "claude-haiku-4-5"
    assert not models_compatible(adapter.model, adapter.detect_served_model(transcript))


@pytest.mark.parametrize(
    ("requested", "served", "compatible"),
    [
        (MODEL, "claude-haiku-4-5", False),
        ("claude-haiku-4-5", MODEL, False),
        (MODEL, "claude-haiku-5", False),
        ("claude-haiku-5", MODEL, False),
        (MODEL, f"{MODEL}-20261007", True),
        (f"{MODEL}-20261007", MODEL, True),
        (f"{MODEL}-20261007", f"{MODEL}-20261008", False),
        (MODEL, f"{MODEL}-2026100", False),
        (MODEL, f"{MODEL}-preview", False),
        (MODEL, "claude-sonnet-5-5", False),
        (MODEL, MODEL, True),
    ],
)
def test_served_model_guard_distinguishes_haiku55_from_other_models(
    requested: str | None, served: str | None, compatible: bool
) -> None:
    assert models_compatible(requested, served) is compatible
