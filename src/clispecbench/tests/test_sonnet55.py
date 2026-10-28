"""Focused, API-free regressions for the pinned Claude Sonnet 5.5 setup."""

from __future__ import annotations

import json
import shlex
from pathlib import Path, PurePosixPath

import pytest

from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.harness.pricing import ALL_PRICING, ANTHROPIC_PRICING, estimate_cost
from clispecbench.harness.results import models_compatible

MODEL = "claude-sonnet-5-5"


@pytest.mark.parametrize("model", [MODEL, f"{MODEL}-20261006"])
def test_sonnet55_routes_before_the_older_sonnet5_prefix(model: str) -> None:
    adapter = ClaudeCodeAdapter(model=model, effort="low")

    assert adapter.name == "claude-code"
    assert adapter.model == model
    assert adapter.effort == "low"
    assert adapter.image_tag == "clispecbench-claude-code-sonnet55"
    assert adapter.dockerfile.name == "claude-code-sonnet55.Dockerfile"
    assert adapter.version == "2.1.289"


def test_sonnet55_invocation_keeps_exact_model_and_low_effort() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL, effort="low")
    command = adapter.invoke_command(
        PurePosixPath("/workspace/prompt.md"), PurePosixPath("/workspace")
    )

    assert command[:2] == ["bash", "-c"]
    assert f"--model {MODEL} --effort low" in command[2]
    assert "--output-format stream-json" in command[2]
    assert "--dangerously-skip-permissions" in command[2]
    assert "su agent -c" in command[2]
    assert "MAX_THINKING_TOKENS" not in command[2]


def test_sonnet55_invocation_disables_cloud_skill_and_plugin_sync() -> None:
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


@pytest.mark.parametrize("cli_version", ["sonnet55", "2.1.289"])
def test_explicit_sonnet55_override_wins_over_model_routing(cli_version: str) -> None:
    adapter = ClaudeCodeAdapter(model="claude-sonnet-5", cli_version=cli_version)

    assert adapter.image_tag == "clispecbench-claude-code-sonnet55"
    assert adapter.version == "2.1.289"
    assert adapter.model == "claude-sonnet-5"


def test_explicit_older_variant_still_wins_for_sonnet55() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL, cli_version="sonnet5")

    assert adapter.image_tag == "clispecbench-claude-code-sonnet5"
    assert adapter.version == "2.1.197"
    assert (
        "--settings"
        not in adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"), PurePosixPath("/workspace")
        )[2]
    )


@pytest.mark.parametrize("model", ["claude-sonnet-5", "claude-sonnet-5-20260630"])
def test_sonnet5_keeps_its_original_pin_and_environment(model: str) -> None:
    adapter = ClaudeCodeAdapter(model=model, effort="low")

    assert adapter.image_tag == "clispecbench-claude-code-sonnet5"
    assert adapter.dockerfile.name == "claude-code-sonnet5.Dockerfile"
    assert adapter.version == "2.1.197"
    sonnet55_environment = ClaudeCodeAdapter(model=MODEL).environment({})
    assert sonnet55_environment.pop("ENABLE_CLAUDEAI_MCP_SERVERS") == "false"
    # The helper model follows each adapter's own model.
    assert adapter.environment({}) == {
        **sonnet55_environment,
        "ANTHROPIC_SMALL_FAST_MODEL": model,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
    }
    assert "ENABLE_CLAUDEAI_MCP_SERVERS" not in adapter.environment({})
    assert (
        "--settings"
        not in adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"), PurePosixPath("/workspace")
        )[2]
    )


def test_sonnet55_environment_keeps_telemetry_and_timeout_without_mutating_input() -> None:
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


def test_sonnet55_disables_account_connector_sync_even_when_inherited_true() -> None:
    provided = {"ENABLE_CLAUDEAI_MCP_SERVERS": "true"}
    adapter = ClaudeCodeAdapter(model=MODEL)

    assert adapter.environment(provided)["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert provided == {"ENABLE_CLAUDEAI_MCP_SERVERS": "true"}
    assert (
        ClaudeCodeAdapter(model="claude-sonnet-5").environment(provided)[
            "ENABLE_CLAUDEAI_MCP_SERVERS"
        ]
        == "true"
    )


def test_sonnet55_keeps_canonical_capture_and_excludes_host_connector_cache() -> None:
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


def test_sonnet55_pricing_uses_the_repository_one_hour_cache_write_convention() -> None:
    pricing = ANTHROPIC_PRICING[MODEL]

    assert ALL_PRICING[MODEL] == pricing
    assert pricing.input == 2.00
    assert pricing.output == 10.00
    assert pricing.cached_input == 0.20
    assert pricing.cache_write == 4.00
    assert (
        estimate_cost(
            MODEL,
            input_tokens=1000,
            output_tokens=500,
            cache_read_input_tokens=100,
            cache_creation_input_tokens=200,
        )
        == 0.00722
    )


def test_sonnet55_mixed_model_usage_uses_each_models_prices(tmp_path: Path) -> None:
    adapter = ClaudeCodeAdapter(model=MODEL, effort="low")
    transcript = "\n".join(
        json.dumps(event)
        for event in (
            {"type": "system", "subtype": "init", "model": MODEL},
            {
                "type": "assistant",
                "message": {
                    "model": MODEL,
                    "content": [{"type": "tool_use", "name": "Bash", "id": "main"}],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "model": "claude-haiku-4-5",
                    "content": [{"type": "tool_use", "name": "Read", "id": "helper"}],
                },
            },
            {
                "type": "result",
                "total_cost_usd": 12.34,
                "usage": {"input_tokens": 1, "output_tokens": 2},
                "modelUsage": {
                    MODEL: {
                        "inputTokens": 100,
                        "outputTokens": 200,
                        "cacheReadInputTokens": 300,
                        "cacheCreationInputTokens": 400,
                    },
                    "claude-haiku-4-5": {
                        "inputTokens": 11,
                        "outputTokens": 22,
                        "cacheReadInputTokens": 33,
                        "cacheCreationInputTokens": 44,
                    },
                },
            },
        )
    )
    usage = adapter.parse_token_usage(tmp_path, transcript)

    assert usage is not None
    assert usage.input_tokens == 888
    assert usage.output_tokens == 222
    assert usage.cache_read_input_tokens == 333
    assert usage.cache_creation_input_tokens == 444
    assert usage.tool_calls == 2
    # Sonnet: $0.003860; Haiku: $0.0002123, rounded only after summing.
    assert usage.estimated_cost_usd == 0.004072
    assert adapter.estimate_cost(usage) == 0.004072
    assert usage.reported_cost_usd == 12.34
    assert usage.cost_estimate_blocked_reason is None
    assert adapter.detect_served_model(transcript) == MODEL


def test_sonnet55_unpriced_helper_blocks_single_model_cost_fallback(tmp_path: Path) -> None:
    adapter = ClaudeCodeAdapter(model=MODEL)
    transcript = json.dumps(
        {
            "type": "result",
            "total_cost_usd": 0.123456,
            "modelUsage": {
                MODEL: {"inputTokens": 100, "outputTokens": 200},
                "claude-unknown-synthetic-model": {"inputTokens": 10, "outputTokens": 20},
            },
        }
    )
    usage = adapter.parse_token_usage(tmp_path, transcript)

    assert usage is not None
    assert usage.input_tokens == 110
    assert usage.output_tokens == 220
    assert usage.estimated_cost_usd is None
    assert usage.cost_estimate_blocked_reason == "unpriced_model_usage"
    assert adapter.estimate_cost(usage) is None
    assert usage.reported_cost_usd == 0.123456


def test_sonnet55_served_model_signal_exposes_a_silent_older_model_fallback() -> None:
    adapter = ClaudeCodeAdapter(model=MODEL)
    events: tuple[dict[str, object], ...] = (
        {"type": "system", "subtype": "init", "model": "claude-sonnet-5"},
        {"type": "assistant", "message": {"model": MODEL, "content": []}},
    )
    transcript = "\n".join(json.dumps(event) for event in events)

    assert adapter.detect_served_model(transcript) == "claude-sonnet-5"
    assert adapter.detect_served_model(transcript) != adapter.model
    assert not models_compatible(adapter.model, adapter.detect_served_model(transcript))


@pytest.mark.parametrize(
    ("requested", "served", "compatible"),
    [
        (MODEL, "claude-sonnet-5", False),
        ("claude-sonnet-5", MODEL, False),
        (MODEL, f"{MODEL}-20260928", True),
        (f"{MODEL}-20260928", MODEL, True),
        (f"{MODEL}-20260928", f"{MODEL}-20261006", False),
        (f"{MODEL}-20261006", f"{MODEL}-20260928", False),
        (MODEL, f"{MODEL}-2026092", False),
        (MODEL, f"{MODEL}-preview", False),
        (MODEL, MODEL, True),
        (MODEL, None, True),
        (None, MODEL, True),
        ("gpt-synthetic", "gpt-synthetic-preview", True),
    ],
)
def test_served_model_guard_distinguishes_sonnet55_from_sonnet5(
    requested: str | None, served: str | None, compatible: bool
) -> None:
    assert models_compatible(requested, served) is compatible
