"""Tests for result-model reporting helpers."""

from __future__ import annotations

import json
from pathlib import Path

from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
    TokenUsage,
    load_result,
)


def _make_run_result(agent: str, token_usage: TokenUsage | None) -> RunResult:
    return RunResult(
        metadata=RunMetadata(
            run_uid="00000000-0000-0000-0000-000000000001",
            task="rs274-cpp",
            agent=agent,
            agent_version="1.0.0",
            prompt_variant="base",
            run_number=1,
            timestamp="2026-04-19T00:00:00+00:00",
            test_suite_version="abc1234",
            eval_version="2.1.1",
            harness_version="0.1.0",
            docker_image_sha="sha256:test",
            wall_clock_seconds=1.0,
            exit_reason="completed",
            model="model-x",
            effort=None,
            benchmark_cost_preference=None,
        ),
        token_usage=token_usage,
        build=BuildResult(success=True, duration_seconds=0.0),
        tests=[],
        test_summary=TestSummary(),
        scores=Scores(),
    )


class TestBenchmarkCostPolicy:
    def test_claude_code_prefers_estimated_cost_via_registry_fallback(self) -> None:
        result = _make_run_result(
            "claude-code",
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                reported_cost_usd=21.048945,
                estimated_cost_usd=8.22383,
            ),
        )

        assert result.benchmark_cost_usd == 8.22383
        assert result.benchmark_cost_source == "estimated"

    def test_claude_code_falls_back_to_reported_cost_when_estimate_missing(self) -> None:
        result = _make_run_result(
            "claude-code",
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                reported_cost_usd=21.048945,
                estimated_cost_usd=None,
            ),
        )

        assert result.benchmark_cost_usd == 21.048945
        assert result.benchmark_cost_source == "reported"

    def test_claude_code_unpriced_model_usage_falls_back_to_reported_cost(
        self, tmp_path: Path
    ) -> None:
        adapter = ClaudeCodeAdapter(model="claude-opus-4-7")
        usage = adapter.parse_token_usage(
            tmp_path,
            json.dumps(
                {
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
            ),
        )

        assert usage is not None
        usage.estimated_cost_usd = adapter.estimate_cost(usage)
        result = _make_run_result("claude-code", usage)

        assert usage.cost_estimate_blocked_reason == "unpriced_model_usage"
        assert result.benchmark_cost_usd == 9.87
        assert result.benchmark_cost_source == "reported"

    def test_metadata_preference_can_override_registry(self) -> None:
        result = _make_run_result(
            "some-agent",
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                reported_cost_usd=1.5,
                estimated_cost_usd=1.2,
            ),
        )
        result.metadata.benchmark_cost_preference = "estimated"

        assert result.benchmark_cost_usd == 1.2
        assert result.benchmark_cost_source == "estimated"

    def test_other_agents_prefer_reported_cost_when_present(self) -> None:
        result = _make_run_result(
            "some-agent",
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                reported_cost_usd=1.5,
                estimated_cost_usd=1.2,
            ),
        )

        assert result.benchmark_cost_usd == 1.5
        assert result.benchmark_cost_source == "reported"

    def test_falls_back_to_estimated_cost_when_reported_missing(self) -> None:
        result = _make_run_result(
            "gemini-cli",
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                reported_cost_usd=None,
                estimated_cost_usd=0.75,
            ),
        )

        assert result.benchmark_cost_usd == 0.75
        assert result.benchmark_cost_source == "estimated"

    def test_token_usage_source_and_partial_flag_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "result.json"
        result = _make_run_result(
            "codex-cli",
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                cache_read_input_tokens=25,
                estimated_cost_usd=0.001,
                source="codex_session_rollout_token_count",
                is_partial=True,
            ),
        )

        result.write(path)
        loaded = load_result(path)

        assert loaded.token_usage is not None
        assert loaded.token_usage.source == "codex_session_rollout_token_count"
        assert loaded.token_usage.is_partial is True
