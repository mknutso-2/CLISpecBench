"""Tests for result-model reporting helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import clispecbench.harness.results as results
from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
    Scores,
    TestSummary,
    TokenUsage,
    load_result,
    model_effort_slug,
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

    def test_exit_class_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "result.json"
        result = _make_run_result("codex-cli", None)
        result.metadata.exit_class = "completed"

        result.write(path)
        loaded = load_result(path)

        assert loaded.metadata.exit_class == "completed"

    def test_network_policy_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "result.json"
        result = _make_run_result("codex-cli", None)
        result.metadata.network_policy = "api-only"

        result.write(path)
        loaded = load_result(path)

        assert loaded.schema_version == "2.2"
        assert loaded.metadata.network_policy == "api-only"

    def test_network_audit_artifact_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "result.json"
        result = _make_run_result("codex-cli", None)
        result.artifacts.network_audit = "network-audit.jsonl"

        result.write(path)
        loaded = load_result(path)

        assert loaded.artifacts.network_audit == "network-audit.jsonl"

    def test_historical_result_defaults_to_web_enabled(self, tmp_path: Path) -> None:
        path = tmp_path / "result.json"
        result = _make_run_result("codex-cli", None)
        result.write(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["metadata"]["network_policy"]
        path.write_text(json.dumps(data), encoding="utf-8")

        loaded = load_result(path)

        assert loaded.metadata.network_policy == "web-enabled"

    def test_load_result_ignores_historical_score_placeholders(self, tmp_path: Path) -> None:
        path = tmp_path / "result.json"
        result = _make_run_result("codex-cli", None)
        result.write(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["scores"]["self_test_coverage"] = None
        data["scores"]["code_quality"] = None
        path.write_text(json.dumps(data), encoding="utf-8")

        loaded = load_result(path)

        assert loaded.scores.correctness is None
        assert loaded.scores.task_score is None


class TestEvalLock:
    def test_live_lock_exits_without_replacing_lock(self, tmp_path: Path) -> None:
        lock_path = tmp_path / "rs274-cpp" / "codex-cli" / "model_medium" / ".eval.lock"
        lock_path.parent.mkdir(parents=True)
        lock_path.write_text(str(os.getpid()), encoding="utf-8")

        with pytest.raises(SystemExit, match="Another evaluation is already running"):
            results.EvalLock.acquire(tmp_path, "rs274-cpp", "codex-cli", "model", "medium")

        assert lock_path.read_text(encoding="utf-8") == str(os.getpid())

    def test_stale_lock_is_replaced(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        lock_path = tmp_path / "rs274-cpp" / "codex-cli" / "model_medium" / ".eval.lock"
        lock_path.parent.mkdir(parents=True)
        lock_path.write_text("99999999", encoding="utf-8")

        def pid_is_missing(pid: int) -> bool:
            return False

        monkeypatch.setattr(results, "_pid_exists", pid_is_missing)

        lock = results.EvalLock.acquire(tmp_path, "rs274-cpp", "codex-cli", "model", "medium")
        try:
            assert lock_path.read_text(encoding="utf-8") == str(os.getpid())
        finally:
            lock.release()

        assert not lock_path.exists()

    def test_windows_pid_probe_does_not_use_os_kill(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        lock_path = tmp_path / "rs274-cpp" / "codex-cli" / "model_medium" / ".eval.lock"
        lock_path.parent.mkdir(parents=True)
        lock_path.write_text("12345", encoding="utf-8")

        def windows_pid_exists(pid: int) -> bool:
            return True

        def fail_kill(pid: int, sig: int) -> None:
            raise AssertionError("os.kill should not be used on Windows")

        monkeypatch.setattr(results.os, "name", "nt")
        monkeypatch.setattr(results, "_windows_pid_exists", windows_pid_exists)
        monkeypatch.setattr(results.os, "kill", fail_kill)

        with pytest.raises(SystemExit, match="Another evaluation is already running"):
            results.EvalLock.acquire(tmp_path, "rs274-cpp", "codex-cli", "model", "medium")

        assert lock_path.read_text(encoding="utf-8") == "12345"


class TestModelEffortSlug:
    def test_preserves_existing_safe_model_names(self) -> None:
        assert model_effort_slug("gpt-5.4", "xhigh") == "gpt-5.4_xhigh"

    def test_sanitizes_openrouter_model_names_for_paths(self) -> None:
        assert (
            model_effort_slug("openrouter/moonshotai/kimi-k2.6:free", "high")
            == "openrouter_moonshotai_kimi-k2.6_free_high"
        )

    def test_non_base_prompt_variant_gets_distinct_slug(self) -> None:
        # A steered prompt series must not collide with standard base runs.
        assert (
            model_effort_slug("claude-fable-5", "max", "fable-steered")
            == "claude-fable-5_max__fable-steered"
        )

    def test_base_and_none_prompt_variant_leave_slug_unchanged(self) -> None:
        # Both the default (None) and an explicit "base" keep the standard slug,
        # so existing runs are byte-for-byte path-compatible.
        standard = model_effort_slug("claude-fable-5", "max")
        assert model_effort_slug("claude-fable-5", "max", None) == standard
        assert model_effort_slug("claude-fable-5", "max", "base") == standard
        assert standard == "claude-fable-5_max"

    def test_prompt_variant_separates_eval_lock_dirs(self, tmp_path: Path) -> None:
        # Base and steered runs of the same model+effort acquire independent
        # locks (distinct directories), so they can run concurrently.
        base = results.EvalLock.acquire(tmp_path, "rs274-cpp", "claude-code", "m", "max")
        try:
            steered = results.EvalLock.acquire(
                tmp_path, "rs274-cpp", "claude-code", "m", "max", "fable-steered"
            )
            steered.release()
        finally:
            base.release()


def test_models_compatible_exact_and_alias() -> None:
    # Exact match
    assert results.models_compatible("claude-opus-4-7", "claude-opus-4-7")
    # Alias requested, dated snapshot served (and vice versa)
    assert results.models_compatible("claude-opus-4-5", "claude-opus-4-5-20251101")
    assert results.models_compatible("claude-opus-4-5-20251101", "claude-opus-4-5")
    # Missing either side → benefit of the doubt
    assert results.models_compatible(None, "claude-opus-4-7")
    assert results.models_compatible("claude-opus-4-7", None)


def test_models_compatible_detects_silent_fallback() -> None:
    # The real-world bug: requested 4.0 snapshot, served 4.7 default.
    assert not results.models_compatible("claude-opus-4-20250514", "claude-opus-4-7")
    assert not results.models_compatible("claude-sonnet-4-20250514", "claude-opus-4-7")
    # 4.1 falling back to 4.7 would also be caught.
    assert not results.models_compatible("claude-opus-4-1-20250805", "claude-opus-4-7")


def test_detect_served_model_reads_init_event() -> None:
    adapter = ClaudeCodeAdapter(model="claude-opus-4-20250514", effort="max")
    logs = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init", "model": "claude-opus-4-7"}),
            json.dumps(
                {"type": "assistant", "message": {"model": "claude-opus-4-7", "content": []}}
            ),
        ]
    )
    assert adapter.detect_served_model(logs) == "claude-opus-4-7"


def test_detect_served_model_ignores_synthetic_and_returns_none_without_signal() -> None:
    adapter = ClaudeCodeAdapter(model="claude-opus-4-7", effort="max")
    assert adapter.detect_served_model("") is None
    # A synthetic assistant model must not be treated as the served model.
    logs = json.dumps({"type": "assistant", "message": {"model": "<synthetic>", "content": []}})
    assert adapter.detect_served_model(logs) is None
