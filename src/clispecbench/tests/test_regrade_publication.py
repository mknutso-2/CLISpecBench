"""Publication replaces grading, not generation or dashboard data sources."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]


def module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("publication_test_module", ROOT / path)
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    original: dict[str, Any] = {
        "metadata": {
            "run_uid": "uid",
            "task": "rs274-cpp",
            "eval_version": "3.2.0",
            "exit_reason": "completed",
            "prompt_content_sha": "generation-prompt",
            "docker_image_sha": "generation-image",
            "model": "test",
            "agent": "codex-cli",
        },
        "token_usage": {"input_tokens": 10, "output_tokens": 2, "reported_cost_usd": 1.25},
        "tests": [],
        "test_summary": {"passed": 0, "total": 546},
        "scores": {"correctness": 0.0},
        "build": {"success": True},
        "editorial": {"last_message": "Claims complete; original score 0/546."},
    }
    record: dict[str, Any] = {
        "original": {
            "run_uid": "uid",
            "published_result_sha256": "original-hash",
            "source_content_sha": "source-hash",
        },
        "grading": {
            "status": "completed",
            "eval_version": "3.2.2",
            "test_suite_sha": module("scripts/promote_rs274_regrades.py").TEST_SHA,
            "environment": {"docker_image_sha": "grading-image"},
        },
        "regrade_uid": "regrade-uid",
        "tests": [{"node_id": f"test_{n}", "outcome": "passed"} for n in range(555)],
        "test_summary": {"passed": 555, "failed": 0, "error": 0, "skipped": 0, "total": 555},
        "scores": {"correctness": 1.0, "task_score": 1.0},
        "comparison": {
            "additional_model_calls": 0,
            "additional_model_cost_usd": 0,
            "model_input_unchanged": True,
        },
    }
    return original, record


def promote(
    original: dict[str, Any], record: dict[str, Any], cohort: str = "gpt-6-astra"
) -> dict[str, Any]:
    return module("scripts/promote_rs274_regrades.py").promote(
        original,
        record,
        record_path="audit.json",
        record_sha="audit-hash",
        revision="git-revision",
        cohort=cohort,
    )


def test_preserves_generation_and_does_not_mutate_inputs() -> None:
    original, record = fixture()
    snapshot = copy.deepcopy(original)
    result = promote(original, record)
    assert original == snapshot
    for field in ("metadata", "token_usage", "build"):
        assert result[field] == original[field]
    assert result["tests"] == record["tests"]
    assert result["regrade"]["original_scores"] == original["scores"]
    assert result["regrade"]["original_editorial"] == original["editorial"]
    assert "Original 3.2.0 assessment (historical)" in result["editorial"]["last_message"]
    with pytest.raises(ValueError, match="Already promoted"):
        promote(result, record)


@pytest.mark.parametrize("defect", ["uid", "failed", "duplicate", "count", "score", "prompt"])
def test_rejects_invalid_promotion(defect: str) -> None:
    original, record = fixture()
    if defect == "uid":
        record["original"]["run_uid"] = "wrong"
    elif defect == "failed":
        record["grading"]["status"] = "failed"
    elif defect == "duplicate":
        record["tests"][1]["node_id"] = "test_0"
    elif defect == "count":
        record["test_summary"]["passed"] = 554
    elif defect == "score":
        record["scores"]["correctness"] = 0.5
    else:
        record["comparison"]["model_input_unchanged"] = False
    with pytest.raises(ValueError):
        promote(original, record)


def test_dashboard_uses_published_grading_and_separates_old_prompt(tmp_path: Path) -> None:
    original, record = fixture()
    record["comparison"]["model_input_unchanged"] = False
    result = promote(original, record, "historical-rs-older-prompt")
    web = tmp_path / "web"
    web.mkdir()
    path = tmp_path / "rs274-cpp/codex-cli/test/run1.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(result), encoding="utf-8")
    builder = module("published_results/web/build_results_json.py")
    row = builder.build_row(path, web)
    assert row["eval_version"] == "3.2.2"
    assert row["generation_eval_version"] == "3.2.0"
    assert row["score_pct"] == 100
    assert row["cost_usd"] == 1.25
    assert row["grading_image_sha"] == "grading-image"
    assert row["comparison_cohort"] == "older Rust prompt 35713dbfd826"
    per_test = module("published_results/web/build_test_results_json.py")
    assert "[older Rust prompt 35713dbfd826]" in per_test.pair_id(row)
    # No audit archive is present under tmp_path: the normal published reader suffices.


def test_unregraded_row_keeps_historical_version(tmp_path: Path) -> None:
    original, _ = fixture()
    original["editorial"]["comparison_cohort"] = "historical grading; no saved source"
    path = tmp_path / "rs274-cpp/codex-cli/test/run1.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(original), encoding="utf-8")
    row = module("published_results/web/build_results_json.py").build_row(path, tmp_path / "web")
    assert row["eval_version"] == "3.2.0"
    assert row["comparison_cohort"] == "historical grading; no saved source"
