"""API pricing tables and cost estimation from token counts.

Prices are per million tokens (MTok).  Update this file when providers
change their pricing or new models are added.

Known discrepancy (Claude Code)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Claude Code's ``total_cost_usd`` (captured as ``reported_cost_usd``) is
not authoritative billing data. Anthropic documents it as a client-side
estimate computed from a bundled price table, and we have seen it diverge
from published API pricing in more than one way.

Historically we observed runs where Claude Code reported roughly 10%
higher cost than what we calculated from token counts and published
per-MTok rates. For example, a Haiku 4.5 run reported $0.9803 vs our
estimate of $0.8919. Possible causes investigated:

- **Data residency / regional routing premium (most likely).**
  Anthropic applies a 1.1x multiplier for region-locked inference.
  $0.8919 × 1.1 = $0.9811, which matches the reported cost within
  $0.001. The transcript shows ``inference_geo: ""`` (empty, meaning
  no explicit preference), but default routing may still incur the
  premium. See https://platform.claude.com/docs/en/about-claude/pricing.
- **5-min vs 1-hr cache write tiers.** Anthropic charges 1.25x for
  5-min and 2x for 1-hr ephemeral cache writes. We assume 1-hr when
  transcript fields confirm it, but a mix of tiers could widen or
  narrow the gap.
- **Extended thinking tokens** are billed but only a summary is
  surfaced in the usage object. Not applicable to Haiku 4.5 (no
  thinking support), but it affects Opus/Sonnet estimates.
- **Tool-use system prompt overhead** is billed but may not appear in
  the session-level token summary.

We have also seen much larger divergences when Claude Code appears to
use stale bundled model pricing. For example, an Opus 4.7 run's
``modelUsage`` token counts priced at Anthropic's published Opus 4.7
rates come out to about $8.22, while Claude Code reported $21.05,
which is within about a tenth of a cent of applying older Claude 3
Opus-style rates ($15 / MTok input, $75 / MTok output, $1.50 / MTok
cache read, and $18.75 / MTok 5-minute cache writes).

For benchmark reporting, prefer ``estimated_cost_usd`` from transcript
token counts + this file's pricing table. Even that value remains an
approximation when transcripts omit billed categories or cache-tier
details.

See also: https://github.com/anthropics/claude-code/issues/26762
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """Per-million-token prices for a single model."""

    input: float  # $/MTok for uncached input
    output: float  # $/MTok for output
    cached_input: float  # $/MTok for cache-hit (read) input
    cache_write: float  # $/MTok for cache creation/write (0 if same as input)


# ---------------------------------------------------------------------------
# Pricing tables
# Anthropic rows last verified 2026-04-19
# OpenAI rows last verified 2026-04-26
# Google rows last verified 2026-04-02
# OpenRouter rows last verified 2026-05-08
# ---------------------------------------------------------------------------

# Anthropic Claude
# https://platform.claude.com/docs/en/about-claude/pricing
# cache_write = 1h ephemeral cache creation rate (2x base input)
ANTHROPIC_PRICING: dict[str, ModelPricing] = {
    "claude-opus-4-7": ModelPricing(input=5.00, output=25.00, cached_input=0.50, cache_write=10.00),  # noqa: E501
    "claude-opus-4-6": ModelPricing(input=5.00, output=25.00, cached_input=0.50, cache_write=10.00),  # noqa: E501
    "claude-sonnet-4-6": ModelPricing(
        input=3.00, output=15.00, cached_input=0.30, cache_write=6.00
    ),  # noqa: E501
    "claude-opus-4-5-20251101": ModelPricing(
        input=5.00, output=25.00, cached_input=0.50, cache_write=10.00
    ),  # noqa: E501
    "claude-sonnet-4-5-20250929": ModelPricing(
        input=3.00, output=15.00, cached_input=0.30, cache_write=6.00
    ),  # noqa: E501
    "claude-haiku-4-5-20251001": ModelPricing(
        input=1.00, output=5.00, cached_input=0.10, cache_write=2.00
    ),  # noqa: E501
    # Claude Code's modelUsage block reports Haiku 4.5 under both the
    # timestamped ID and the bare alias (the alias gets the bulk of the
    # tokens). Without this entry _estimate_model_usage_cost short-circuits
    # to None and estimated_cost_usd is left blank on every Haiku 4.5 run.
    "claude-haiku-4-5": ModelPricing(input=1.00, output=5.00, cached_input=0.10, cache_write=2.00),  # noqa: E501
}

# OpenAI GPT / Codex
# https://openai.com/api/pricing/
# cache_write = 0 (Codex CLI doesn't report cache creation tokens)
OPENAI_PRICING: dict[str, ModelPricing] = {
    "gpt-5.5": ModelPricing(input=5.00, output=30.00, cached_input=0.50, cache_write=0),  # noqa: E501
    "gpt-5.4": ModelPricing(input=2.50, output=15.00, cached_input=0.25, cache_write=0),  # noqa: E501
    "gpt-5.4-mini": ModelPricing(input=0.75, output=4.50, cached_input=0.075, cache_write=0),  # noqa: E501
    "gpt-5-mini": ModelPricing(input=0.25, output=2.00, cached_input=0.025, cache_write=0),  # noqa: E501
    "gpt-5.3-codex": ModelPricing(input=1.75, output=14.00, cached_input=0.175, cache_write=0),  # noqa: E501
    "gpt-5.2-codex": ModelPricing(input=1.75, output=14.00, cached_input=0.175, cache_write=0),  # noqa: E501
    "gpt-5.2": ModelPricing(input=1.75, output=14.00, cached_input=0.175, cache_write=0),  # noqa: E501
    "gpt-5.1-codex-max": ModelPricing(input=1.25, output=10.00, cached_input=0.125, cache_write=0),  # noqa: E501
    "gpt-5.1-codex-mini": ModelPricing(input=0.25, output=2.00, cached_input=0.025, cache_write=0),  # noqa: E501
    "gpt-5.1": ModelPricing(input=1.25, output=10.00, cached_input=0.125, cache_write=0),  # noqa: E501
    "gpt-5": ModelPricing(input=1.25, output=10.00, cached_input=0.125, cache_write=0),  # noqa: E501
}

# Google Gemini (text input, <=200k context)
# https://ai.google.dev/gemini-api/docs/pricing
# cache_write = 0 (Gemini CLI doesn't report cache creation tokens)
GOOGLE_PRICING: dict[str, ModelPricing] = {
    "gemini-3.1-pro-preview": ModelPricing(
        input=2.00, output=12.00, cached_input=0.20, cache_write=0
    ),  # noqa: E501
    "gemini-3-flash-preview": ModelPricing(
        input=0.50, output=3.00, cached_input=0.05, cache_write=0
    ),  # noqa: E501
    "gemini-2.5-pro": ModelPricing(input=1.25, output=10.00, cached_input=0.125, cache_write=0),  # noqa: E501
    "gemini-2.5-flash": ModelPricing(input=0.30, output=2.50, cached_input=0.03, cache_write=0),  # noqa: E501
    "gemini-2.5-flash-lite": ModelPricing(
        input=0.10, output=0.40, cached_input=0.01, cache_write=0
    ),  # noqa: E501
}

# OpenRouter
# https://openrouter.ai/deepseek/deepseek-v4-pro/pricing
# https://openrouter.ai/xiaomi/mimo-v2.5-pro/pricing
OPENROUTER_PRICING: dict[str, ModelPricing] = {
    "openrouter/deepseek/deepseek-v4-pro": ModelPricing(
        input=0.435, output=0.87, cached_input=0.435, cache_write=0.435
    ),
    "deepseek/deepseek-v4-pro": ModelPricing(
        input=0.435, output=0.87, cached_input=0.435, cache_write=0.435
    ),
    "openrouter/xiaomi/mimo-v2.5-pro": ModelPricing(
        input=1.00, output=3.00, cached_input=1.00, cache_write=1.00
    ),
    "xiaomi/mimo-v2.5-pro": ModelPricing(
        input=1.00, output=3.00, cached_input=1.00, cache_write=1.00
    ),
}

# Combined lookup
ALL_PRICING: dict[str, ModelPricing] = {
    **ANTHROPIC_PRICING,
    **OPENAI_PRICING,
    **GOOGLE_PRICING,
    **OPENROUTER_PRICING,
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
