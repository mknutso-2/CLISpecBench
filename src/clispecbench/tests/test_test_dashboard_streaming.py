"""Per-test dashboard output stays compatible, bounded, and atomic."""

from __future__ import annotations

import importlib.util
import json
import sys
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


@pytest.fixture
def builder(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "test_dashboard_streaming", root / "published_results/web/build_test_results_json.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixed_time = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(module, "datetime", SimpleNamespace(now=lambda: fixed_time))
    return module


@pytest.fixture
def publication(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Explicit expectations from the original aggregate schema and normalization."""
    web = tmp_path / "web"
    web.mkdir()
    first = {
        "task": "las-py",
        "eval": "LAS",
        "language": "py",
        "eval_instance": 3,
        "eval_version": "1.2.0",
        "agent": "codex-cli",
        "model": "modèle",
        "effort": " high ",
        "comparison_cohort": "older 🧪",
        "run_id": "rα",
        "score_count": 1,
        "score_total": 3,
        "score_pct": 100 / 3,
        "result_link": "../first.json",
    }
    second = {
        **first,
        "model": "second",
        "effort": None,
        "comparison_cohort": "",
        "run_id": "r2",
        "score_count": 0,
        "score_total": 2,
        "score_pct": 0.0,
        "result_link": "../second.json",
    }
    node_id = "tests/test_las.py::TestUnicode::test_value[é🧪]"
    message = 'line one\n"quoted" \\ café 🧪'
    (tmp_path / "first.json").write_text(
        json.dumps(
            {
                "tests": [
                    {
                        "node_id": node_id,
                        "outcome": "passed",
                        "duration_seconds": 0.125,
                        "message": message,
                    },
                    None,
                    {
                        "node_id": "tests/test_las.py::test_failure",
                        "outcome": "failed",
                        "duration_seconds": 1.5,
                        "message": {"unstructured": "ignored"},
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "second.json").write_text(
        json.dumps({"tests": [{"node_id": node_id, "outcome": "skipped"}, {}]}),
        encoding="utf-8",
    )
    (tmp_path / "empty.json").write_text("{}", encoding="utf-8")
    runs_file = web / "results-published.json"
    runs_file.write_text(
        json.dumps({"rows": [first, "ignored", second, {"result_link": "../empty.json"}]}),
        encoding="utf-8",
    )
    first_key = "las-py|codex-cli|modèle| high |rα"
    second_key = "las-py|codex-cli|second|None|r2"
    first_run = {
        "run_key": first_key,
        "task": "las-py",
        "eval": "LAS",
        "language": "py",
        "eval_language": "LAS-py",
        "eval_instance": 3,
        "eval_version": "1.2.0",
        "agent": "codex-cli",
        "model": "modèle",
        "effort": " high ",
        "pair": "codex-cli / modèle (high) [older 🧪]",
        "run_id": "rα",
        "score_count": 1,
        "score_total": 3,
        "score_pct": 100 / 3,
        "result_link": "../first.json",
        "test_count": 3,
    }
    second_run = {
        **first_run,
        "run_key": second_key,
        "model": "second",
        "effort": None,
        "pair": "codex-cli / second",
        "run_id": "r2",
        "score_count": 0,
        "score_total": 2,
        "score_pct": 0.0,
        "result_link": "../second.json",
        "test_count": 2,
    }
    first_row = {
        "row_id": f"{first_key}|0",
        "run_key": first_key,
        "run_index": 0,
        "task": "las-py",
        "eval": "LAS",
        "language": "py",
        "eval_language": "LAS-py",
        "eval_version": "1.2.0",
        "agent": "codex-cli",
        "model": "modèle",
        "effort": " high ",
        "pair": "codex-cli / modèle (high) [older 🧪]",
        "run_id": "rα",
        "result_link": "../first.json",
        "test_id": node_id,
        "test_file": "tests/test_las.py",
        "test_name": "test_value[é🧪]",
        "outcome": "passed",
        "duration_seconds": 0.125,
        "message": message,
    }
    skipped_row = {
        **first_row,
        "row_id": f"{second_key}|0",
        "run_key": second_key,
        "run_index": 2,
        "model": "second",
        "effort": None,
        "pair": "codex-cli / second",
        "run_id": "r2",
        "result_link": "../second.json",
        "outcome": "skipped",
        "duration_seconds": None,
        "message": "",
    }
    expected = {
        "schema_version": "1.0",
        "generated_at": datetime(2026, 9, 21, 12, 0, tzinfo=UTC).astimezone().isoformat(),
        "source": (
            "Official completed runs from results-published.json linked curated run JSON files"
        ),
        "completed_run_count": 3,
        "test_result_count": 4,
        "unique_test_count": 3,
        "outcome_counts": {"failed": 1, "passed": 1, "skipped": 1, "unknown": 1},
        "runs": [
            first_run,
            second_run,
            {
                **dict.fromkeys(first_run),
                "run_key": "||||",
                "eval_language": "Unknown-n/a",
                "pair": "unknown / unknown",
                "result_link": "../empty.json",
                "test_count": 0,
            },
        ],
        "rows": [
            first_row,
            {
                **first_row,
                "row_id": f"{first_key}|2",
                "test_id": "tests/test_las.py::test_failure",
                "test_name": "test_failure",
                "outcome": "failed",
                "duration_seconds": 1.5,
                "message": "",
            },
            skipped_row,
            {
                **skipped_row,
                "row_id": f"{second_key}|1",
                "test_id": "",
                "test_file": "",
                "test_name": "",
                "outcome": "unknown",
            },
        ],
    }
    return runs_file, expected


def test_cli_preserves_all_fields_without_building_in_memory(
    builder: ModuleType,
    publication: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs_file, expected = publication
    assert builder.build_payload(runs_file) == expected
    output = runs_file.with_name("test-results-published.json")
    # Invalid prior contents also prove a rebuild never needs the old aggregate.
    output.write_bytes(b"old aggregate is not JSON\n")

    def reject_in_memory_build(*_args: object) -> None:
        pytest.fail("CLI must not build the expanded aggregate in memory")

    monkeypatch.setattr(builder, "build_payload", reject_in_memory_build)
    monkeypatch.setattr(
        sys, "argv", ["build", "--runs-file", str(runs_file), "--output", str(output)]
    )
    builder.main()
    raw = output.read_bytes()
    assert json.loads(raw) == expected
    assert raw.isascii()
    assert raw.endswith(b"\n")
    assert raw.count(b"\n") == 1
    assert capsys.readouterr().out == f"Wrote 4 test results across 3 runs to {output}\n"
    assert sorted(path.name for path in output.parent.iterdir()) == [
        "results-published.json",
        "test-results-published.json",
    ]


@pytest.mark.parametrize("existing_output", [False, True])
@pytest.mark.parametrize("defect", ["score", "json", "tests", "result_object", "missing"])
def test_later_run_failure_preserves_output_and_removes_partial_file(
    builder: ModuleType,
    publication: tuple[Path, dict[str, Any]],
    existing_output: bool,
    defect: str,
) -> None:
    runs_file, _ = publication
    result = runs_file.parent.parent / "second.json"
    if defect == "score":
        result.write_text('{"tests":[{"outcome":"passed"}]}', encoding="utf-8")
    elif defect == "json":
        result.write_text('{"tests": [', encoding="utf-8")
    elif defect == "tests":
        result.write_text('{"tests":{}}', encoding="utf-8")
    elif defect == "result_object":
        result.write_text("[]", encoding="utf-8")
    else:
        result.unlink()
    output = runs_file.with_name("test-results-published.json")
    original = b'{"previous":"caf\xc3\xa9"}\n'
    if existing_output:
        output.write_bytes(original)
    files_before = set(output.parent.iterdir())
    with pytest.raises((ValueError, FileNotFoundError)):
        builder.write_payload(runs_file, output)
    assert set(output.parent.iterdir()) == files_before
    if existing_output:
        assert output.read_bytes() == original
    else:
        assert not output.exists()


def test_replacement_failure_preserves_output_and_removes_temporary_file(
    builder: ModuleType,
    publication: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runs_file, expected = publication
    output = runs_file.with_name("test-results-published.json")
    output.write_bytes(b"previous aggregate\n")
    files_before = set(output.parent.iterdir())

    def reject_replace(source: Path, destination: Path) -> None:
        assert source.parent == destination.parent == output.parent
        assert destination == output
        assert json.loads(source.read_text(encoding="utf-8")) == expected
        assert output.read_bytes() == b"previous aggregate\n"
        raise OSError("replacement failed")

    monkeypatch.setattr(builder.os, "replace", reject_replace)
    with pytest.raises(OSError, match="replacement failed"):
        builder.write_payload(runs_file, output)
    assert output.read_bytes() == b"previous aggregate\n"
    assert set(output.parent.iterdir()) == files_before


def test_streaming_memory_does_not_scale_with_expanded_rows(
    builder: ModuleType, tmp_path: Path
) -> None:
    # Repeated runs expand a small source into >8 MB of output. Retaining all
    # expanded dictionaries/messages or serializing the aggregate exceeds the cap.
    result = tmp_path / "run.json"
    result.write_text(
        json.dumps(
            {
                "tests": [
                    {"node_id": f"test_{index}", "outcome": "passed", "message": "x" * 1024}
                    for index in range(100)
                ]
            }
        ),
        encoding="utf-8",
    )
    runs_file = tmp_path / "runs.json"
    runs_file.write_text(
        json.dumps(
            {
                "rows": [
                    {"run_id": index, "result_link": "run.json", "score_count": 100}
                    for index in range(64)
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "out.json"
    tracemalloc.start()
    try:
        metadata = builder.write_payload(runs_file, output)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert metadata["test_result_count"] == 6400
    assert metadata["unique_test_count"] == 100
    assert output.stat().st_size > 8 * 1024 * 1024
    assert peak < 4 * 1024 * 1024
