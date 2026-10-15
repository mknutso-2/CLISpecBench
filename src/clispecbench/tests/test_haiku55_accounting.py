"""API-free request-tier accounting and fail-closed coverage for Haiku 5.5."""

from __future__ import annotations

import copy
import json
from math import isclose
from pathlib import Path
from typing import Any

import pytest

from clispecbench.agents.claude_code import ClaudeCodeAdapter
from clispecbench.harness.pricing import (
    estimate_cost,
    estimate_haiku55_request_cost,
    is_haiku55_model,
)

MODEL = "claude-haiku-5-5"


def assistant(
    message_id: str,
    uncached: int = 10,
    output: int = 20,
    read: int = 30,
    write: int = 40,
    model: str = MODEL,
    ttl: tuple[int, int] | None = None,
) -> dict[str, Any]:
    usage: dict[str, Any] = {
        "input_tokens": uncached,
        "output_tokens": output,
        "cache_read_input_tokens": read,
        "cache_creation_input_tokens": write,
    }
    if ttl is not None:
        usage["cache_creation"] = {
            "ephemeral_5m_input_tokens": ttl[0],
            "ephemeral_1h_input_tokens": ttl[1],
        }
    return {"type": "assistant", "message": {"id": message_id, "model": model, "usage": usage}}


def result(requests: list[dict[str, Any]]) -> dict[str, Any]:
    models: dict[str, dict[str, int]] = {}
    unique = {(r["message"]["model"], r["message"]["id"]): r for r in requests}
    for request in unique.values():
        message = request["message"]
        totals = models.setdefault(
            message["model"],
            {
                "inputTokens": 0,
                "outputTokens": 0,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
            },
        )
        for target, source in (
            ("inputTokens", "input_tokens"),
            ("outputTokens", "output_tokens"),
            ("cacheReadInputTokens", "cache_read_input_tokens"),
            ("cacheCreationInputTokens", "cache_creation_input_tokens"),
        ):
            totals[target] += message["usage"][source]
    return {"type": "result", "modelUsage": models, "total_cost_usd": 123.456}


def logs(stream: list[dict[str, Any]], billed: list[dict[str, Any]] | None = None) -> str:
    return "\n".join(
        json.dumps(r) for r in [*stream, result(billed if billed is not None else stream)]
    )


def canonical(root: Path, requests: list[dict[str, Any]]) -> None:
    folder = root / "projects" / "isolated-fixture"
    folder.mkdir(parents=True)
    (folder / "session.jsonl").write_text(
        "\n".join(json.dumps(r) for r in requests), encoding="utf-8"
    )


@pytest.mark.parametrize("context", [100_000, 100_001])
def test_context_boundary_prices_entire_request_output(context: int) -> None:
    input_rate, output_rate = (0.1, 0.5) if context == 100_000 else (0.5, 2.5)
    assert isclose(
        estimate_haiku55_request_cost(context, 1000, 0, 0),
        (context * input_rate + 1000 * output_rate) / 1_000_000,
    )


@pytest.mark.parametrize("cache_kind", ["read", "write"])
def test_context_boundary_includes_all_cached_input(cache_kind: str) -> None:
    read, write = (100_000, 0) if cache_kind == "read" else (0, 100_000)
    cache_rate = 0.05 if cache_kind == "read" else 1.0
    assert isclose(
        estimate_haiku55_request_cost(1, 1000, read, write),
        (0.5 + 1000 * 2.5 + 100_000 * cache_rate) / 1_000_000,
    )


@pytest.mark.parametrize("context", [100_000, 100_001])
def test_explicit_five_minute_and_one_hour_cache_rates(context: int) -> None:
    input_rate, output_rate, five_rate, hour_rate = (
        (0.1, 0.5, 0.125, 0.2) if context == 100_000 else (0.5, 2.5, 0.625, 1.0)
    )
    uncached = context - 100
    assert isclose(
        estimate_haiku55_request_cost(uncached, 1000, 0, 100, 40, 60),
        (uncached * input_rate + 1000 * output_rate + 40 * five_rate + 60 * hour_rate) / 1_000_000,
    )


def test_absent_cache_tiers_use_existing_documented_one_hour_estimate() -> None:
    assert isclose(estimate_haiku55_request_cost(0, 0, 0, 100), 0.00002)


def test_all_missing_cache_tiers_keep_documented_one_hour_estimate_and_source(
    tmp_path: Path,
) -> None:
    request = assistant("main", uncached=1000, output=500, read=100, write=200)
    assert "cache_creation" not in request["message"]["usage"]
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([request]))
    assert usage is not None
    # No TTL information was supplied: $0.20/MTok is the documented one-hour
    # convention, not a claim about actual billing or an inferred cache TTL.
    assert usage.estimated_cost_usd == 0.000391
    assert usage.source == "claude_haiku55_request_usage_reconciled"
    assert usage.cost_estimate_blocked_reason is None
    assert usage.reported_cost_usd == 123.456


@pytest.mark.parametrize("model", [MODEL, f"{MODEL}-20261007"])
def test_aggregate_estimates_are_never_used_for_haiku55(model: str) -> None:
    assert is_haiku55_model(model)
    assert estimate_cost(model, 10_000, 100) is None
    assert estimate_cost(model, 1_000_000, 100) is None


@pytest.mark.parametrize(
    "model", ["claude-haiku-5-50", "claude-haiku-5-5-preview", "claude-haiku-4-5"]
)
def test_haiku55_family_recognition_is_narrow(model: str) -> None:
    assert not is_haiku55_model(model)


def test_identical_message_ids_are_deduplicated_across_stream_and_canonical(tmp_path: Path) -> None:
    request = assistant("main", ttl=(15, 25))
    canonical(tmp_path, [request, request])
    adapter = ClaudeCodeAdapter(model=MODEL)
    usage = adapter.parse_token_usage(tmp_path, logs([request, request]))
    assert usage is not None
    expected = round(estimate_haiku55_request_cost(10, 20, 30, 40, 15, 25), 6)
    assert usage.estimated_cost_usd == expected
    assert adapter.estimate_cost(usage) == expected
    assert usage.input_tokens == 80
    assert usage.output_tokens == 20
    assert usage.reported_cost_usd == 123.456
    assert usage.cost_estimate_blocked_reason is None
    assert usage.source == "claude_haiku55_request_usage_reconciled"


def test_canonical_final_output_completes_stream_without_adding_calls(tmp_path: Path) -> None:
    provisional = assistant("main", output=2)
    complete = assistant("main", output=2000)
    canonical(tmp_path, [complete, complete])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([provisional, provisional], [complete])
    )
    assert usage is not None
    assert usage.output_tokens == 2000
    assert usage.estimated_cost_usd == round(estimate_haiku55_request_cost(10, 2000, 30, 40), 6)
    assert usage.cost_estimate_blocked_reason is None


def test_canonical_explicit_cache_tiers_complete_absent_stream_tiers(tmp_path: Path) -> None:
    provisional = assistant("main", output=2)
    complete = assistant("main", output=2000, ttl=(40, 0))
    canonical(tmp_path, [complete])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([provisional], [complete])
    )
    assert usage is not None
    assert usage.estimated_cost_usd == round(
        estimate_haiku55_request_cost(10, 2000, 30, 40, 40, 0), 6
    )


def test_mixed_context_tiers_are_priced_per_request_not_session_total(tmp_path: Path) -> None:
    small = assistant("small", uncached=100_000, output=1000, read=0, write=0)
    large = assistant("large", uncached=1, output=1000, read=100_000, write=0)
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([small, large]))
    assert usage is not None
    expected = estimate_haiku55_request_cost(100_000, 1000, 0, 0)
    expected += estimate_haiku55_request_cost(1, 1000, 100_000, 0)
    assert usage.estimated_cost_usd == round(expected, 6)
    assert usage.input_tokens == 200_001


def test_mixed_helper_models_require_and_receive_complete_coverage(tmp_path: Path) -> None:
    main = assistant("shared-id")
    helper = assistant("shared-id", model="claude-haiku-4-5")
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([main, helper]))
    assert usage is not None
    expected = estimate_haiku55_request_cost(10, 20, 30, 40)
    expected += (10 * 1 + 20 * 5 + 30 * 0.1 + 40 * 2) / 1_000_000
    assert usage.estimated_cost_usd == round(expected, 6)
    assert usage.input_tokens == 160
    assert usage.output_tokens == 40


def test_unknown_helper_blocks_all_estimation_without_losing_reported_cost(tmp_path: Path) -> None:
    main = assistant("main")
    helper = assistant("helper", model="claude-unknown-synthetic-model")
    adapter = ClaudeCodeAdapter(model=MODEL)
    usage = adapter.parse_token_usage(tmp_path, logs([main, helper]))
    assert usage is not None
    assert usage.estimated_cost_usd is None
    assert usage.cost_estimate_blocked_reason == "haiku55_unpriced_model_usage"
    assert adapter.estimate_cost(usage) is None
    assert usage.reported_cost_usd == 123.456


@pytest.mark.parametrize("category", ["uncached", "output", "read", "write"])
def test_every_aggregate_category_must_be_covered(tmp_path: Path, category: str) -> None:
    request = assistant("main")
    billed = copy.deepcopy(request)
    field = {
        "uncached": "input_tokens",
        "output": "output_tokens",
        "read": "cache_read_input_tokens",
        "write": "cache_creation_input_tokens",
    }[category]
    billed["message"]["usage"][field] = 999
    adapter = ClaudeCodeAdapter(model=MODEL)
    usage = adapter.parse_token_usage(tmp_path, logs([request], [billed]))
    assert usage is not None
    assert usage.estimated_cost_usd is None
    assert usage.cost_estimate_blocked_reason == "haiku55_request_usage_coverage_mismatch"
    assert adapter.estimate_cost(usage) is None


def test_missing_assistant_coverage_blocks_aggregate_fallback(tmp_path: Path) -> None:
    request = assistant("main")
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([], [request]))
    assert usage is not None
    assert usage.estimated_cost_usd is None
    assert usage.cost_estimate_blocked_reason == "haiku55_request_usage_coverage_mismatch"


def test_top_level_only_usage_cannot_prove_per_model_coverage(tmp_path: Path) -> None:
    event = {"type": "result", "usage": assistant("main")["message"]["usage"]}
    adapter = ClaudeCodeAdapter(model=MODEL)
    usage = adapter.parse_token_usage(tmp_path, json.dumps(event))
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_missing_model_usage"
    assert adapter.estimate_cost(usage) is None


@pytest.mark.parametrize("bad", [-1, True, 1.5, "100", None])
def test_invalid_request_counts_fail_closed(tmp_path: Path, bad: Any) -> None:
    complete = assistant("main")
    malformed = copy.deepcopy(complete)
    malformed["message"]["usage"]["input_tokens"] = bad
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([malformed], [complete])
    )
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_invalid_request_usage"
    assert usage.estimated_cost_usd is None


@pytest.mark.parametrize("missing", ["id", "model", "usage"])
def test_missing_request_identity_or_usage_fails_closed(tmp_path: Path, missing: str) -> None:
    complete = assistant("main")
    malformed = copy.deepcopy(complete)
    malformed["message"].pop(missing)
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([malformed], [complete])
    )
    assert usage is not None
    assert usage.cost_estimate_blocked_reason is not None
    assert usage.estimated_cost_usd is None


def test_inconsistent_duplicate_input_is_not_resolved_by_canonical(tmp_path: Path) -> None:
    request = assistant("main")
    changed = assistant("main", uncached=100)
    canonical(tmp_path, [request])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([request, changed], [request])
    )
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_conflicting_request_usage"


def test_ambiguous_duplicate_output_requires_consistent_canonical_completion(
    tmp_path: Path,
) -> None:
    first, second = assistant("main", output=1), assistant("main", output=2)
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([first, second], [second])
    )
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_conflicting_request_usage"
    canonical(tmp_path, [assistant("main", output=20)])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([first, second], [assistant("main", output=20)])
    )
    assert usage is not None
    assert usage.cost_estimate_blocked_reason is None


def test_conflicting_canonical_records_block_estimation(tmp_path: Path) -> None:
    request, changed = assistant("main"), assistant("main", output=21)
    canonical(tmp_path, [request, changed])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([request]))
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_conflicting_request_usage"


def test_canonical_output_cannot_be_lower_than_any_stream_counter(tmp_path: Path) -> None:
    first, second = assistant("main", output=20), assistant("main", output=1)
    complete = assistant("main", output=10)
    canonical(tmp_path, [complete])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(
        tmp_path, logs([first, second], [complete])
    )
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_conflicting_request_usage"


def test_canonical_request_identity_must_match_model_and_message_id(tmp_path: Path) -> None:
    stream = assistant("stream-id", output=1)
    complete = assistant("different-id", output=20)
    canonical(tmp_path, [complete])
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([stream], [complete]))
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_request_usage_coverage_mismatch"


def test_uncovered_helper_tokens_block_even_when_main_requests_match(tmp_path: Path) -> None:
    main = assistant("main")
    helper = assistant("hidden-helper", model="claude-haiku-4-5")
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([main], [main, helper]))
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_request_usage_coverage_mismatch"


def test_haiku55_in_a_helper_bucket_also_blocks_flat_accounting(tmp_path: Path) -> None:
    main = assistant("main", model="claude-sonnet-5-5")
    helper = assistant("helper")
    adapter = ClaudeCodeAdapter(model="claude-sonnet-5-5")
    usage = adapter.parse_token_usage(tmp_path, logs([main], [main, helper]))
    assert usage is not None
    assert usage.cost_estimate_blocked_reason == "haiku55_request_usage_coverage_mismatch"
    assert adapter.estimate_cost(usage) is None


def test_otel_only_usage_preserves_counts_but_blocks_haiku_aggregate_estimate(
    tmp_path: Path,
) -> None:
    otel = tmp_path / "otel"
    otel.mkdir()
    points = [
        {"asInt": count, "attributes": [{"key": "type", "value": {"stringValue": kind}}]}
        for kind, count in (("input", 10), ("output", 20))
    ]
    payload = {
        "resourceMetrics": [
            {
                "scopeMetrics": [
                    {"metrics": [{"name": "claude_code.token.usage", "dataPoints": points}]}
                ]
            }
        ]
    }
    (otel / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")
    adapter = ClaudeCodeAdapter(model=MODEL)
    usage = adapter.parse_token_usage(tmp_path, "")
    assert usage is not None
    assert usage.input_tokens == 10
    assert usage.output_tokens == 20
    assert usage.cost_estimate_blocked_reason == "haiku55_request_usage_unavailable"
    assert adapter.estimate_cost(usage) is None


@pytest.mark.parametrize("bad", [-1, True, False, 1.5])
def test_per_request_pricing_rejects_invalid_cache_tier_counters(bad: Any) -> None:
    with pytest.raises(ValueError):
        estimate_haiku55_request_cost(0, 0, 0, 0, bad, 0)


@pytest.mark.parametrize("ttl", [(40, 1), (-1, 41), (True, 39)])
def test_invalid_cache_tier_coverage_blocks_estimation(
    tmp_path: Path, ttl: tuple[int, int]
) -> None:
    malformed = assistant("main", ttl=ttl)
    usage = ClaudeCodeAdapter(model=MODEL).parse_token_usage(tmp_path, logs([malformed]))
    assert usage is not None
    assert usage.estimated_cost_usd is None
    assert usage.cost_estimate_blocked_reason is not None


def test_old_model_accounting_remains_unchanged_without_request_messages(tmp_path: Path) -> None:
    event = result([assistant("main", model="claude-sonnet-5-5")])
    adapter = ClaudeCodeAdapter(model="claude-sonnet-5-5")
    usage = adapter.parse_token_usage(tmp_path, json.dumps(event))
    assert usage is not None
    assert usage.estimated_cost_usd == round((10 * 2 + 20 * 10 + 30 * 0.2 + 40 * 4) / 1_000_000, 6)
    assert usage.cost_estimate_blocked_reason is None
    assert usage.source is None
