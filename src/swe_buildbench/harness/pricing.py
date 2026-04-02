"""API pricing tables and cost estimation from token counts.

Prices are per million tokens (MTok).  Update this file when providers
change their pricing or new models are added.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """Per-million-token prices for a single model."""

    input: float          # $/MTok for uncached input
    output: float         # $/MTok for output
    cached_input: float   # $/MTok for cache-hit (read) input
    cache_write: float    # $/MTok for cache creation/write (0 if same as input)


# ---------------------------------------------------------------------------
# Pricing tables — last verified 2026-04-02
# ---------------------------------------------------------------------------

# Anthropic Claude
# https://docs.anthropic.com/en/docs/about-claude/pricing
# cache_write = 1h ephemeral cache creation rate (2x base input)
ANTHROPIC_PRICING: dict[str, ModelPricing] = {
    "claude-opus-4-6":             ModelPricing(input=5.00,  output=25.00, cached_input=0.50,  cache_write=10.00),
    "claude-sonnet-4-6":           ModelPricing(input=3.00,  output=15.00, cached_input=0.30,  cache_write=6.00),
    "claude-opus-4-5-20251101":    ModelPricing(input=5.00,  output=25.00, cached_input=0.50,  cache_write=10.00),
    "claude-sonnet-4-5-20250929":  ModelPricing(input=3.00,  output=15.00, cached_input=0.30,  cache_write=6.00),
    "claude-haiku-4-5-20251001":   ModelPricing(input=1.00,  output=5.00,  cached_input=0.10,  cache_write=2.00),
}

# OpenAI GPT / Codex
# https://openai.com/api/pricing/
# cache_write = 0 (Codex CLI doesn't report cache creation tokens)
OPENAI_PRICING: dict[str, ModelPricing] = {
    "gpt-5.4":             ModelPricing(input=2.50,  output=15.00, cached_input=0.25,  cache_write=0),
    "gpt-5.4-mini":        ModelPricing(input=0.75,  output=4.50,  cached_input=0.075, cache_write=0),
    "gpt-5.3-codex":       ModelPricing(input=1.75,  output=14.00, cached_input=0.175, cache_write=0),
    "gpt-5.2-codex":       ModelPricing(input=1.75,  output=14.00, cached_input=0.175, cache_write=0),
    "gpt-5.2":             ModelPricing(input=1.75,  output=14.00, cached_input=0.175, cache_write=0),
    "gpt-5.1-codex-max":   ModelPricing(input=1.25,  output=10.00, cached_input=0.125, cache_write=0),
    "gpt-5.1-codex-mini":  ModelPricing(input=0.25,  output=2.00,  cached_input=0.025, cache_write=0),
}

# Google Gemini (text input, <=200k context)
# https://ai.google.dev/gemini-api/docs/pricing
# cache_write = 0 (Gemini CLI doesn't report cache creation tokens)
GOOGLE_PRICING: dict[str, ModelPricing] = {
    "gemini-3.1-pro-preview":  ModelPricing(input=2.00,  output=12.00, cached_input=0.20,  cache_write=0),
    "gemini-3-flash-preview":  ModelPricing(input=0.50,  output=3.00,  cached_input=0.05,  cache_write=0),
    "gemini-2.5-pro":          ModelPricing(input=1.25,  output=10.00, cached_input=0.125, cache_write=0),
    "gemini-2.5-flash":        ModelPricing(input=0.30,  output=2.50,  cached_input=0.03,  cache_write=0),
    "gemini-2.5-flash-lite":   ModelPricing(input=0.10,  output=0.40,  cached_input=0.01,  cache_write=0),
}

# Combined lookup
ALL_PRICING: dict[str, ModelPricing] = {
    **ANTHROPIC_PRICING,
    **OPENAI_PRICING,
    **GOOGLE_PRICING,
}


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_input_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
) -> float | None:
    """Estimate API cost in USD from token counts.

    Returns None if the model is not in the pricing table.
    Uncached input = input_tokens - cache_read - cache_creation.
    """
    pricing = ALL_PRICING.get(model)
    if pricing is None:
        return None

    uncached = max(0, input_tokens - cache_read_input_tokens - cache_creation_input_tokens)
    cost = (
        uncached * pricing.input / 1_000_000
        + cache_read_input_tokens * pricing.cached_input / 1_000_000
        + cache_creation_input_tokens * (pricing.cache_write or pricing.input) / 1_000_000
        + output_tokens * pricing.output / 1_000_000
    )
    return round(cost, 6)
