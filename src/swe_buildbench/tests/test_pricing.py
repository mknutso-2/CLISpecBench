"""Tests for API pricing estimation."""

from __future__ import annotations

import pytest

from swe_buildbench.harness.pricing import ALL_PRICING, estimate_cost


class TestEstimateCost:
    def test_unknown_model_returns_none(self) -> None:
        assert estimate_cost("unknown-model", 1000, 1000) is None

    def test_haiku_no_cache(self) -> None:
        # haiku: $1/MTok input, $5/MTok output
        cost = estimate_cost(
            "claude-haiku-4-5-20251001",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        assert cost == pytest.approx(6.0)

    def test_haiku_with_cache(self) -> None:
        # 500k uncached input @ $1/MTok + 500k cached @ $0.10/MTok + 100k output @ $5/MTok
        cost = estimate_cost(
            "claude-haiku-4-5-20251001",
            input_tokens=1_000_000,
            output_tokens=100_000,
            cached_input_tokens=500_000,
        )
        assert cost is not None
        expected = 500_000 * 1.0 / 1e6 + 500_000 * 0.10 / 1e6 + 100_000 * 5.0 / 1e6
        assert cost == pytest.approx(expected)

    def test_openai_model(self) -> None:
        cost = estimate_cost(
            "gpt-5.4",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        assert cost is not None
        assert cost == pytest.approx(2.50 + 15.00)

    def test_gemini_model(self) -> None:
        cost = estimate_cost(
            "gemini-2.5-flash-lite",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        assert cost is not None
        assert cost == pytest.approx(0.10 + 0.40)

    def test_zero_tokens(self) -> None:
        cost = estimate_cost("claude-haiku-4-5-20251001", 0, 0)
        assert cost == pytest.approx(0.0)


class TestPricingTableCompleteness:
    def test_all_claude_models_present(self) -> None:
        for model in (
            "claude-opus-4-6", "claude-sonnet-4-6",
            "claude-opus-4-5-20251101", "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
        ):
            assert model in ALL_PRICING, f"Missing pricing for {model}"

    def test_all_openai_models_present(self) -> None:
        for model in (
            "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex",
            "gpt-5.2-codex", "gpt-5.2",
            "gpt-5.1-codex-max", "gpt-5.1-codex-mini",
        ):
            assert model in ALL_PRICING, f"Missing pricing for {model}"

    def test_all_gemini_models_present(self) -> None:
        for model in (
            "gemini-3.1-pro-preview", "gemini-3-flash-preview",
            "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
        ):
            assert model in ALL_PRICING, f"Missing pricing for {model}"
