"""Tests for API pricing estimation."""

from __future__ import annotations

import pytest

from clispecbench.harness.pricing import ALL_PRICING, estimate_cost


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
        assert cost == pytest.approx(6.0)  # type: ignore[reportUnknownMemberType]

    def test_haiku_with_cache_read(self) -> None:
        # 500k uncached @ $1 + 500k cache read @ $0.10 + 100k output @ $5
        cost = estimate_cost(
            "claude-haiku-4-5-20251001",
            input_tokens=1_000_000,
            output_tokens=100_000,
            cache_read_input_tokens=500_000,
        )
        assert cost is not None
        expected = 500_000 * 1.0 / 1e6 + 500_000 * 0.10 / 1e6 + 100_000 * 5.0 / 1e6
        assert cost == pytest.approx(expected)  # type: ignore[reportUnknownMemberType]

    def test_haiku_with_cache_write(self) -> None:
        # 100k uncached @ $1 + 200k cache write @ $2 + 700k cache read @ $0.10 + 50k output @ $5
        cost = estimate_cost(
            "claude-haiku-4-5-20251001",
            input_tokens=1_000_000,
            output_tokens=50_000,
            cache_read_input_tokens=700_000,
            cache_creation_input_tokens=200_000,
        )
        assert cost is not None
        expected = (
            100_000 * 1.0 / 1e6 + 700_000 * 0.10 / 1e6 + 200_000 * 2.0 / 1e6 + 50_000 * 5.0 / 1e6
        )
        assert cost == pytest.approx(expected)  # type: ignore[reportUnknownMemberType]

    def test_haiku_real_run(self) -> None:
        """Verify estimate against the actual haiku RS274 run token breakdown."""
        # From transcript: input=360, cache_creation=109733, cache_read=3542369, output=63559
        cost = estimate_cost(
            "claude-haiku-4-5-20251001",
            input_tokens=360 + 109733 + 3542369,  # 3652462
            output_tokens=63559,
            cache_read_input_tokens=3542369,
            cache_creation_input_tokens=109733,
        )
        assert cost is not None
        expected = (
            360 * 1.0 / 1e6  # uncached input
            + 3542369 * 0.10 / 1e6  # cache read
            + 109733 * 2.0 / 1e6  # cache write (1h ephemeral)
            + 63559 * 5.0 / 1e6  # output
        )
        assert cost == pytest.approx(expected)  # type: ignore[reportUnknownMemberType]

    def test_opus_4_7_real_run_model_usage(self) -> None:
        """Verify estimate against the Opus 4.7 modelUsage breakdown."""
        cost = estimate_cost(
            "claude-opus-4-7",
            input_tokens=1859 + 322004 + 4606340,  # uncached + cache write + cache read
            output_tokens=107653,
            cache_read_input_tokens=4606340,
            cache_creation_input_tokens=322004,
        )
        assert cost is not None
        expected = (
            1859 * 5.0 / 1e6 + 4606340 * 0.50 / 1e6 + 322004 * 10.0 / 1e6 + 107653 * 25.0 / 1e6
        )
        assert cost == pytest.approx(expected)  # type: ignore[reportUnknownMemberType]

    def test_openai_model(self) -> None:
        cost = estimate_cost(
            "gpt-5.4",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        assert cost is not None
        assert cost == pytest.approx(2.50 + 15.00)  # type: ignore[reportUnknownMemberType]

    def test_gpt_5_5_model(self) -> None:
        cost = estimate_cost(
            "gpt-5.5",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cache_read_input_tokens=500_000,
        )
        assert cost is not None
        assert cost == pytest.approx(0.5 * 5.00 + 0.5 * 0.50 + 30.00)  # type: ignore[reportUnknownMemberType]

    def test_gemini_model(self) -> None:
        cost = estimate_cost(
            "gemini-2.5-flash-lite",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        assert cost is not None
        assert cost == pytest.approx(0.10 + 0.40)  # type: ignore[reportUnknownMemberType]

    def test_zero_tokens(self) -> None:
        cost = estimate_cost("claude-haiku-4-5-20251001", 0, 0)
        assert cost == pytest.approx(0.0)  # type: ignore[reportUnknownMemberType]


class TestPricingTableCompleteness:
    def test_all_claude_models_present(self) -> None:
        for model in (
            "claude-opus-4-7",
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
        ):
            assert model in ALL_PRICING, f"Missing pricing for {model}"

    def test_all_openai_models_present(self) -> None:
        for model in (
            "gpt-5.5",
            "gpt-5.4",
            "gpt-5.4-mini",
            "gpt-5.3-codex",
            "gpt-5.2-codex",
            "gpt-5.2",
            "gpt-5.1-codex-max",
            "gpt-5.1-codex-mini",
        ):
            assert model in ALL_PRICING, f"Missing pricing for {model}"

    def test_all_gemini_models_present(self) -> None:
        for model in (
            "gemini-3.1-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ):
            assert model in ALL_PRICING, f"Missing pricing for {model}"
