"""Structural-validation tests for ``iges parse``.

These port the CLI-observable behavior from the SDK's
``tests/spec/test_validate.cpp``. The CLI surface does not expose a
separate ``validate`` subcommand; instead, ``iges parse`` must reject
files that fail the shipped structural validation checks.
"""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from iges_support import make_entity, wrap_entities, write_iges_from_json
from raw_iges_support import build_global_payload, hollerith, make_empty_iges


def _run_parse(
    submission_command: Sequence[str], iges_path: Path, out_path: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            *submission_command,
            "parse",
            "--input", str(iges_path),
            "--output", str(out_path),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def _write_lines(path: Path, lines: Sequence[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="latin-1")


def _replace_field(line: str, start_col: int, width: int, value: str) -> str:
    field = f"{value:>{width}}"
    return f"{line[:start_col]}{field}{line[start_col + width:]}"


def _directory_line_indexes(lines: Sequence[str]) -> tuple[int, int]:
    indexes = [i for i, line in enumerate(lines) if len(line) >= 73 and line[72] == "D"]
    assert len(indexes) == 2
    return indexes[0], indexes[1]


def _make_valid_line_file(submission_command: Sequence[str], tmp_path: Path) -> Path:
    return write_iges_from_json(
        submission_command,
        wrap_entities([
            make_entity(
                de_index=1,
                entity_type=110,
                data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 1.0, 1.0]},
            ),
        ]),
        tmp_path,
        name="valid-line",
    )


def _make_valid_empty_iges(*, model_space_scale: str = "1.0") -> str:
    return make_empty_iges(build_global_payload([
        hollerith("test"),
        hollerith("test.igs"),
        hollerith("SDK"),
        hollerith("1.0"),
        "32",
        "38",
        "6",
        "308",
        "15",
        hollerith("test"),
        model_space_scale,
        "2",
        hollerith("MM"),
        "1",
        "0.01",
        hollerith("20260416.120000"),
        "1.0E-6",
        "1.0",
        hollerith("usr"),
        hollerith("site"),
        "11",
        "3",
        "",
        "",
    ]))


def test_parse_accepts_valid_file_with_no_validation_diagnostics(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    out_path = tmp_path / "valid-line.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 1


def test_parse_rejects_invalid_xform_matrix_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    lines = iges_path.read_text(encoding="latin-1").splitlines()
    d1, _ = _directory_line_indexes(lines)
    lines[d1] = _replace_field(lines[d1], 48, 8, "999")
    _write_lines(iges_path, lines)

    out_path = tmp_path / "invalid-xform.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "xform_matrix" in payload["error"]


def test_parse_rejects_invalid_view_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    lines = iges_path.read_text(encoding="latin-1").splitlines()
    d1, _ = _directory_line_indexes(lines)
    lines[d1] = _replace_field(lines[d1], 40, 8, "999")
    _write_lines(iges_path, lines)

    out_path = tmp_path / "invalid-view.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "view" in payload["error"]


def test_parse_rejects_invalid_label_display_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """TR §1.2: label_display must be validated alongside view / xform_matrix."""
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    lines = iges_path.read_text(encoding="latin-1").splitlines()
    d1, _ = _directory_line_indexes(lines)
    # Field 8 (Label Display) occupies cols 57-64 (0-indexed offset 56, width 8).
    lines[d1] = _replace_field(lines[d1], 56, 8, "999")
    _write_lines(iges_path, lines)

    out_path = tmp_path / "invalid-label-display.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "label_display" in payload["error"]


def test_parse_rejects_negative_entity_type(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    lines = iges_path.read_text(encoding="latin-1").splitlines()
    d1, d2 = _directory_line_indexes(lines)
    lines[d1] = _replace_field(lines[d1], 0, 8, "-1")
    lines[d2] = _replace_field(lines[d2], 0, 8, "-1")
    _write_lines(iges_path, lines)

    out_path = tmp_path / "negative-entity-type.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "negative entity type" in payload["error"]


def test_parse_rejects_zero_param_line_count_for_non_null_entity(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    lines = iges_path.read_text(encoding="latin-1").splitlines()
    _, d2 = _directory_line_indexes(lines)
    lines[d2] = _replace_field(lines[d2], 24, 8, "0")
    _write_lines(iges_path, lines)

    out_path = tmp_path / "zero-param-line-count.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "param_line_count" in payload["error"]


def test_parse_rejects_non_positive_model_space_scale(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = tmp_path / "bad-scale.iges"
    iges_path.write_text(_make_valid_empty_iges(model_space_scale="0.0"), encoding="latin-1")

    out_path = tmp_path / "bad-scale.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "model_space_scale" in payload["error"]


def test_parse_accepts_valid_empty_file_with_no_entities(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    iges_path = tmp_path / "empty-but-valid.iges"
    iges_path.write_text(_make_valid_empty_iges(), encoding="latin-1")

    out_path = tmp_path / "empty-but-valid.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["entities"] == []
