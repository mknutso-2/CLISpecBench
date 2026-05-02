"""Tests for agent adapters: credentials, version, model/effort."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import pytest

from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.agents.codex_cli import CodexCLIAdapter
from clispecbench.agents.copilot_cli import CopilotCLIAdapter
from clispecbench.agents.gemini_cli import GeminiCLIAdapter
from clispecbench.agents.registry import (
    AgentSpec,
    get_agent_spec,
    list_agent_specs,
    list_auth_smoke_scripts,
)

CONTAINER_AGENT_SPECS = list_agent_specs()
REPO_ROOT = Path(__file__).resolve().parents[3]


def _agent_spec_id(spec: AgentSpec) -> str:
    return spec.agent_id


class TestAgentRegistry:
    def test_auth_smoke_scripts_exist(self) -> None:
        smoke_scripts = list_auth_smoke_scripts()
        assert smoke_scripts
        for script_path in smoke_scripts:
            assert script_path.endswith(".sh")
            assert (REPO_ROOT / script_path).is_file()

    def test_benchmark_cost_preference_is_registered(self) -> None:
        assert get_agent_spec("claude-code").benchmark_cost_preference == "estimated"
        assert get_agent_spec("codex-cli").benchmark_cost_preference == "reported"


class TestClaudeCodeCredentialMounts:
    def test_mounts_individual_credential_files(self) -> None:
        adapter = ClaudeCodeAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        # Should mount individual files, not the whole ~/.claude/ dir
        assert "/home/user/.claude" not in mounts, (
            "Must not mount ~/.claude as a directory — breaks session-env creation"
        )
        # Credential files
        assert "/home/user/.claude/.credentials.json" in mounts
        assert (
            mounts["/home/user/.claude/.credentials.json"]["bind"]
            == "/home/agent/.claude/.credentials.json"
        )
        assert mounts["/home/user/.claude/.credentials.json"]["mode"] == "ro"
        # Settings
        assert "/home/user/.claude/settings.json" in mounts
        assert mounts["/home/user/.claude/settings.json"]["mode"] == "ro"
        # ~/.claude.json must NOT be mounted — it caches the host's claude.ai
        # connector list (Gmail / GCal / Drive) which would leak as advertised
        # `mcp__*` tools into the in-container session.
        assert "/home/user/.claude.json" not in mounts


class TestCodexCLICredentialMounts:
    def test_mounts_auth_json_only(self) -> None:
        adapter = CodexCLIAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        assert len(mounts) == 1
        key = "/home/user/.codex/auth.json"
        assert key in mounts
        assert mounts[key]["bind"] == "/root/.codex/auth.json"
        assert mounts[key]["mode"] == "rw"


class TestGeminiCLICredentialMounts:
    def test_mounts_three_files_to_staging(self) -> None:
        adapter = GeminiCLIAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        assert len(mounts) == 3
        for filename in ("oauth_creds.json", "google_accounts.json", "settings.json"):
            key = f"/home/user/.gemini/{filename}"
            assert key in mounts, f"Missing mount for {filename}"
            assert mounts[key]["bind"].startswith("/tmp/gemini-auth/")
            assert mounts[key]["mode"] == "ro"

    def test_invoke_command_copies_credentials(self) -> None:
        adapter = GeminiCLIAdapter()
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        # The bash command should copy from staging and seed projects.json
        bash_script = cmd[2]
        assert "cp /tmp/gemini-auth/*" in bash_script
        assert "projects.json" in bash_script
        assert "--yolo" in bash_script
        assert "--skip-trust" in bash_script
        assert "--output-format stream-json" in bash_script


class TestCopilotCLICredentialMounts:
    def test_returns_empty_when_no_hosts_file(self, tmp_path: Path) -> None:
        adapter = CopilotCLIAdapter()
        mounts = adapter.credential_mounts(tmp_path)
        assert len(mounts) == 0

    def test_mounts_xdg_hosts_yml(self, tmp_path: Path) -> None:
        gh_dir = tmp_path / ".config" / "gh"
        gh_dir.mkdir(parents=True)
        (gh_dir / "hosts.yml").write_text("github.com:\n  oauth_token: test\n")
        adapter = CopilotCLIAdapter()
        mounts = adapter.credential_mounts(tmp_path)
        assert len(mounts) == 1
        key = (gh_dir / "hosts.yml").as_posix()
        assert key in mounts
        assert mounts[key]["bind"] == "/root/.config/gh/hosts.yml"
        assert mounts[key]["mode"] == "ro"

    def test_mounts_appdata_hosts_yml(self, tmp_path: Path) -> None:
        appdata_dir = tmp_path / "AppData" / "Roaming" / "GitHub CLI"
        appdata_dir.mkdir(parents=True)
        (appdata_dir / "hosts.yml").write_text("github.com:\n  oauth_token: test\n")
        adapter = CopilotCLIAdapter()
        mounts = adapter.credential_mounts(tmp_path)
        assert len(mounts) == 1
        key = (appdata_dir / "hosts.yml").as_posix()
        assert key in mounts
        assert mounts[key]["bind"] == "/root/.config/gh/hosts.yml"
        assert mounts[key]["mode"] == "ro"


class TestAgentVersions:
    @pytest.mark.parametrize(
        "spec",
        CONTAINER_AGENT_SPECS,
        ids=_agent_spec_id,
    )
    def test_container_agent_version_from_dockerfile(self, spec: AgentSpec) -> None:
        adapter = spec.create()
        assert adapter.version != "unknown"
        assert "." in adapter.version


class TestModelAndEffort:
    def test_claude_code_model_in_command(self) -> None:
        adapter = ClaudeCodeAdapter(model="sonnet", effort="high")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert "--model sonnet" in bash_script
        assert "--effort high" in bash_script

    def test_claude_code_no_model_flags_by_default(self) -> None:
        adapter = ClaudeCodeAdapter()
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert "--model" not in bash_script
        assert "--effort" not in bash_script

    def test_codex_model_in_command(self) -> None:
        adapter = CodexCLIAdapter(model="o3", effort="high")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert '--model "o3"' in bash_script
        assert 'model_reasoning_effort="high"' in bash_script

    def test_gemini_model_in_command(self) -> None:
        adapter = GeminiCLIAdapter(model="gemini-2.5-pro")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert '--model "gemini-2.5-pro"' in bash_script
        assert "--yolo" in bash_script
        assert "--skip-trust" in bash_script

    def test_copilot_model_in_command(self) -> None:
        adapter = CopilotCLIAdapter(model="gpt-5.2", effort="high")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert '--model "gpt-5.2"' in bash_script
        assert '--effort "high"' in bash_script
        assert "--yolo" in bash_script

    def test_copilot_no_model_flags_by_default(self) -> None:
        adapter = CopilotCLIAdapter()
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert "--model" not in bash_script
        assert "--effort" not in bash_script

    def test_adapter_model_property(self) -> None:
        adapter = ClaudeCodeAdapter(model="opus")
        assert adapter.model == "opus"
        assert adapter.effort is None

    def test_adapter_effort_property(self) -> None:
        adapter = ClaudeCodeAdapter(effort="max")
        assert adapter.effort == "max"
        assert adapter.model is None


class TestTelemetryPaths:
    def test_claude_code_has_otel_path(self) -> None:
        adapter = ClaudeCodeAdapter()
        assert any("otel" in p for p in adapter.telemetry_paths)

    def test_codex_has_event_log_path(self) -> None:
        adapter = CodexCLIAdapter()
        assert any("codex-events" in p for p in adapter.telemetry_paths)
        assert any("/root/.codex/sessions" == p for p in adapter.telemetry_paths)

    def test_gemini_has_no_telemetry_paths(self) -> None:
        adapter = GeminiCLIAdapter()
        assert adapter.telemetry_paths == []

    def test_copilot_has_otel_path(self) -> None:
        adapter = CopilotCLIAdapter()
        assert any("copilot-otel" in p for p in adapter.telemetry_paths)


class TestClaudeCodeTokenUsage:
    def test_parse_token_usage_prefers_model_usage(self, tmp_path: Path) -> None:
        adapter = ClaudeCodeAdapter(model="claude-opus-4-7")
        result_event = {
            "type": "result",
            "total_cost_usd": 21.04894500000001,
            "usage": {
                "input_tokens": 76,
                "cache_creation_input_tokens": 306436,
                "cache_read_input_tokens": 4461375,
                "output_tokens": 101769,
            },
            "modelUsage": {
                "claude-opus-4-7": {
                    "inputTokens": 1859,
                    "outputTokens": 107653,
                    "cacheReadInputTokens": 4606340,
                    "cacheCreationInputTokens": 322004,
                    "costUSD": 21.04894500000001,
                }
            },
        }

        usage = adapter.parse_token_usage(tmp_path, json.dumps(result_event))

        assert usage is not None
        assert usage.input_tokens == 1859 + 4606340 + 322004
        assert usage.output_tokens == 107653
        assert usage.cache_read_input_tokens == 4606340
        assert usage.cache_creation_input_tokens == 322004
        assert usage.estimated_cost_usd == pytest.approx(8.22383)
        assert usage.cost_estimate_blocked_reason is None
        assert usage.reported_cost_usd == pytest.approx(21.048945)

    def test_parse_token_usage_aggregates_multi_model_usage(self, tmp_path: Path) -> None:
        adapter = ClaudeCodeAdapter(model="claude-opus-4-7")
        result_event = {
            "type": "result",
            "total_cost_usd": 12.34,
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": 30,
                "output_tokens": 40,
            },
            "modelUsage": {
                "claude-opus-4-7": {
                    "inputTokens": 100,
                    "outputTokens": 200,
                    "cacheReadInputTokens": 300,
                    "cacheCreationInputTokens": 400,
                },
                "claude-sonnet-4-6": {
                    "inputTokens": 11,
                    "outputTokens": 22,
                    "cacheReadInputTokens": 33,
                    "cacheCreationInputTokens": 44,
                },
            },
        }

        usage = adapter.parse_token_usage(tmp_path, json.dumps(result_event))

        assert usage is not None
        assert usage.input_tokens == 888
        assert usage.output_tokens == 222
        assert usage.cache_read_input_tokens == 333
        assert usage.cache_creation_input_tokens == 444
        assert usage.estimated_cost_usd == pytest.approx(0.010287)
        assert usage.cost_estimate_blocked_reason is None
        assert usage.reported_cost_usd == pytest.approx(12.34)

    def test_estimate_cost_skips_generic_fallback_for_unpriced_model_usage(
        self, tmp_path: Path
    ) -> None:
        adapter = ClaudeCodeAdapter(model="claude-opus-4-7")
        result_event = {
            "type": "result",
            "total_cost_usd": 9.87,
            "modelUsage": {
                "claude-opus-4-7": {
                    "inputTokens": 100,
                    "outputTokens": 200,
                    "cacheReadInputTokens": 300,
                    "cacheCreationInputTokens": 400,
                },
                "claude-unknown-future-model": {
                    "inputTokens": 10,
                    "outputTokens": 20,
                    "cacheReadInputTokens": 30,
                    "cacheCreationInputTokens": 40,
                },
            },
        }

        usage = adapter.parse_token_usage(tmp_path, json.dumps(result_event))

        assert usage is not None
        assert usage.estimated_cost_usd is None
        assert usage.cost_estimate_blocked_reason == "unpriced_model_usage"
        assert adapter.estimate_cost(usage) is None

    def test_estimate_cost_is_not_order_dependent_across_parse_calls(self, tmp_path: Path) -> None:
        adapter = ClaudeCodeAdapter(model="claude-opus-4-7")
        model_usage_event = {
            "type": "result",
            "total_cost_usd": 9.87,
            "modelUsage": {
                "claude-opus-4-7": {
                    "inputTokens": 100,
                    "outputTokens": 200,
                    "cacheReadInputTokens": 300,
                    "cacheCreationInputTokens": 400,
                },
                "claude-unknown-future-model": {
                    "inputTokens": 10,
                    "outputTokens": 20,
                    "cacheReadInputTokens": 30,
                    "cacheCreationInputTokens": 40,
                },
            },
        }
        top_level_usage_event = {
            "type": "result",
            "total_cost_usd": 1.23,
            "usage": {
                "input_tokens": 100,
                "cache_creation_input_tokens": 200,
                "cache_read_input_tokens": 300,
                "output_tokens": 400,
            },
        }

        blocked_usage = adapter.parse_token_usage(tmp_path, json.dumps(model_usage_event))
        estimated_usage = adapter.parse_token_usage(tmp_path, json.dumps(top_level_usage_event))

        assert blocked_usage is not None
        assert blocked_usage.cost_estimate_blocked_reason == "unpriced_model_usage"
        assert adapter.estimate_cost(blocked_usage) is None
        assert estimated_usage is not None
        assert estimated_usage.cost_estimate_blocked_reason is None
        assert adapter.estimate_cost(estimated_usage) == pytest.approx(0.01265)

    def test_parse_token_usage_falls_back_to_top_level_usage(self, tmp_path: Path) -> None:
        adapter = ClaudeCodeAdapter(model="claude-opus-4-7")
        result_event = {
            "type": "result",
            "total_cost_usd": 1.23,
            "usage": {
                "input_tokens": 100,
                "cache_creation_input_tokens": 200,
                "cache_read_input_tokens": 300,
                "output_tokens": 400,
            },
        }

        usage = adapter.parse_token_usage(tmp_path, json.dumps(result_event))

        assert usage is not None
        assert usage.input_tokens == 600
        assert usage.output_tokens == 400
        assert usage.cache_read_input_tokens == 300
        assert usage.cache_creation_input_tokens == 200
        assert usage.estimated_cost_usd is None
        assert usage.cost_estimate_blocked_reason is None
        assert usage.reported_cost_usd == pytest.approx(1.23)


class TestCodexCLITokenUsage:
    def test_parse_token_usage_prefers_completed_turn_usage(self, tmp_path: Path) -> None:
        adapter = CodexCLIAdapter()
        logs = "\n".join(
            [
                json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 1000,
                            "cached_input_tokens": 250,
                            "output_tokens": 125,
                        },
                    }
                ),
            ]
        )

        usage = adapter.parse_token_usage(tmp_path, logs)

        assert usage is not None
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 125
        assert usage.cache_read_input_tokens == 250
        assert usage.tool_calls == 1
        assert usage.source == "codex_exec_turn_completed"
        assert usage.is_partial is False

    def test_parse_token_usage_reads_completed_turn_from_event_log(self, tmp_path: Path) -> None:
        adapter = CodexCLIAdapter()
        (tmp_path / "codex-events.jsonl").write_text(
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 2000,
                        "cached_input_tokens": 500,
                        "output_tokens": 250,
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

        usage = adapter.parse_token_usage(tmp_path)

        assert usage is not None
        assert usage.input_tokens == 2000
        assert usage.output_tokens == 250
        assert usage.cache_read_input_tokens == 500
        assert usage.source == "codex_exec_turn_completed"
        assert usage.is_partial is False

    def test_parse_token_usage_falls_back_to_session_rollout_token_count(
        self, tmp_path: Path
    ) -> None:
        adapter = CodexCLIAdapter()
        rollout = tmp_path / "sessions" / "2026" / "04" / "29"
        rollout.mkdir(parents=True)
        (rollout / "rollout-2026-04-29T01-02-03-thread.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "timestamp": "2026-04-29T01:02:03Z",
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {
                                    "total_token_usage": {
                                        "input_tokens": 1000,
                                        "cached_input_tokens": 200,
                                        "output_tokens": 100,
                                        "reasoning_output_tokens": 50,
                                        "total_tokens": 1100,
                                    },
                                    "last_token_usage": {
                                        "input_tokens": 1000,
                                        "cached_input_tokens": 200,
                                        "output_tokens": 100,
                                        "reasoning_output_tokens": 50,
                                        "total_tokens": 1100,
                                    },
                                    "model_context_window": 400000,
                                },
                                "rate_limits": None,
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "timestamp": "2026-04-29T01:03:03Z",
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {
                                    "total_token_usage": {
                                        "input_tokens": 3000,
                                        "cached_input_tokens": 900,
                                        "output_tokens": 450,
                                        "reasoning_output_tokens": 200,
                                        "total_tokens": 3450,
                                    },
                                    "last_token_usage": {
                                        "input_tokens": 2000,
                                        "cached_input_tokens": 700,
                                        "output_tokens": 350,
                                        "reasoning_output_tokens": 150,
                                        "total_tokens": 2350,
                                    },
                                    "model_context_window": 400000,
                                },
                                "rate_limits": None,
                            },
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        logs = "\n".join(
            [
                json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}),
                json.dumps({"type": "turn.failed", "error": {"message": "context exhausted"}}),
            ]
        )

        usage = adapter.parse_token_usage(tmp_path, logs)

        assert usage is not None
        assert usage.input_tokens == 3000
        assert usage.output_tokens == 450
        assert usage.cache_read_input_tokens == 900
        assert usage.tool_calls == 1
        assert usage.source == "codex_session_rollout_token_count"
        assert usage.is_partial is True

    def test_parse_token_usage_prefers_exec_usage_over_rollout_fallback(
        self, tmp_path: Path
    ) -> None:
        adapter = CodexCLIAdapter()
        rollout = tmp_path / "sessions" / "2026" / "04" / "29"
        rollout.mkdir(parents=True)
        (rollout / "rollout-2026-04-29T01-02-03-thread.jsonl").write_text(
            json.dumps(
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 9999,
                                "cached_input_tokens": 1111,
                                "output_tokens": 888,
                            }
                        },
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        logs = json.dumps(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 123,
                    "cached_input_tokens": 45,
                    "output_tokens": 67,
                },
            }
        )

        usage = adapter.parse_token_usage(tmp_path, logs)

        assert usage is not None
        assert usage.input_tokens == 123
        assert usage.output_tokens == 67
        assert usage.cache_read_input_tokens == 45
        assert usage.source == "codex_exec_turn_completed"
        assert usage.is_partial is False

    def test_parse_token_usage_returns_none_without_completed_usage_or_rollout(
        self, tmp_path: Path
    ) -> None:
        adapter = CodexCLIAdapter()
        logs = json.dumps({"type": "turn.failed", "error": {"message": "rate limited"}})

        usage = adapter.parse_token_usage(tmp_path, logs)

        assert usage is None
