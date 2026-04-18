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
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

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


_GLOBAL_FIELD_DEFAULTS: dict[int, str] = {
    3: hollerith("test"),
    4: hollerith("test.igs"),
    5: hollerith("SDK"),
    6: hollerith("1.0"),
    7: "32",        # integer_bits
    8: "38",        # sp_magnitude
    9: "6",         # sp_significance
    10: "308",      # dp_magnitude
    11: "15",       # dp_significance
    12: hollerith("test"),
    13: "1.0",      # model_space_scale
    14: "2",
    15: hollerith("MM"),
    16: "1",        # max_line_weight_grads
    17: "0.01",
    18: hollerith("20260416.120000"),
    19: "1.0E-6",   # min_resolution
    20: "1.0",
    21: hollerith("usr"),
    22: hollerith("site"),
    23: "11",
    24: "3",
    25: "",
    26: "",
}


def _make_valid_empty_iges(
    *,
    model_space_scale: str = "1.0",
    integer_bits: str = "32",
    overrides: Mapping[int, str] | None = None,
) -> str:
    fields_by_num = dict(_GLOBAL_FIELD_DEFAULTS)
    fields_by_num[7] = integer_bits
    fields_by_num[13] = model_space_scale
    if overrides:
        fields_by_num.update(overrides)
    fields = [fields_by_num[n] for n in range(3, 27)]
    return make_empty_iges(build_global_payload(fields))


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


def test_parse_rejects_non_positive_integer_bits(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """TR §1.2 + spec §2.2.4.3.7: integer_bits must be positive."""
    iges_path = tmp_path / "bad-integer-bits.iges"
    iges_path.write_text(
        _make_valid_empty_iges(integer_bits="0"), encoding="latin-1"
    )

    out_path = tmp_path / "bad-integer-bits.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "integer_bits" in payload["error"]


@pytest.mark.parametrize(
    ("field_num", "field_name"),
    [
        (8, "sp_magnitude"),
        (9, "sp_significance"),
        (10, "dp_magnitude"),
        (11, "dp_significance"),
        (16, "max_line_weight_grads"),
        (19, "min_resolution"),
    ],
)
def test_parse_rejects_non_positive_required_global_field(
    submission_command: Sequence[str], tmp_path: Path,
    field_num: int, field_name: str,
) -> None:
    """TR §1.2: 'any non-positive required Global numeric field such as
    model_space_scale' must exit 1. Parameterized across the remaining
    required positive fields per spec §2.2.4.3 (fields 8, 9, 10, 11, 16,
    19). Field 7 (integer_bits) and 13 (model_space_scale) have their own
    dedicated tests above."""
    bad_value = "0" if field_num != 19 else "0.0"
    iges_path = tmp_path / f"bad-{field_name}.iges"
    iges_path.write_text(
        _make_valid_empty_iges(overrides={field_num: bad_value}),
        encoding="latin-1",
    )

    out_path = tmp_path / f"bad-{field_name}.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert field_name in payload["error"]


def test_write_rejects_non_positive_global_field(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """TR §1.2: `iges write` must reject canonical JSON that encodes an
    invalid Global section — specifically non-positive required numeric
    fields (§2.2.4.3). This mirrors the parse-side check and ensures
    `iges write` cannot produce a file `iges parse` would reject.

    Error output for write/roundtrip goes to stderr (see TR §1.4 and the
    ref-impl behavior), so we assert on exit code only.
    """
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
        ),
    ])
    doc["global"]["min_resolution"] = 0.0
    json_path = tmp_path / "bad-global.json"
    iges_path = tmp_path / "bad-global.iges"
    json_path.write_text(json.dumps(doc), encoding="utf-8")

    completed = subprocess.run(
        [
            *submission_command, "write",
            "--input", str(json_path),
            "--output", str(iges_path),
        ],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_write_rejects_invalid_xform_matrix_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """TR §1.2: the write path must reject DE cross-references that
    point to non-existent entities, symmetric with the parse-side check.

    A file emitted with a dangling xform_matrix pointer would be
    rejected by `iges parse`, so `iges write` must refuse to produce it.
    """
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={"xform_matrix": 999},
        ),
    ])
    json_path = tmp_path / "bad-xform.json"
    iges_path = tmp_path / "bad-xform.iges"
    json_path.write_text(json.dumps(doc), encoding="utf-8")

    completed = subprocess.run(
        [
            *submission_command, "write",
            "--input", str(json_path),
            "--output", str(iges_path),
        ],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_write_rejects_invalid_view_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """TR §1.2: mirror of `test_write_rejects_invalid_xform_matrix_pointer`
    for the view cross-reference."""
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={"view": 999},
        ),
    ])
    json_path = tmp_path / "bad-view.json"
    iges_path = tmp_path / "bad-view.iges"
    json_path.write_text(json.dumps(doc), encoding="utf-8")

    completed = subprocess.run(
        [
            *submission_command, "write",
            "--input", str(json_path),
            "--output", str(iges_path),
        ],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_write_rejects_invalid_label_display_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """TR §1.2: mirror of the other write-side cross-reference tests for
    label_display."""
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={"label_display": 999},
        ),
    ])
    json_path = tmp_path / "bad-label-display.json"
    iges_path = tmp_path / "bad-label-display.iges"
    json_path.write_text(json.dumps(doc), encoding="utf-8")

    completed = subprocess.run(
        [
            *submission_command, "write",
            "--input", str(json_path),
            "--output", str(iges_path),
        ],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_write_rejects_zero_length_line(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§3.2.5 symmetric enforcement: the write path must also reject
    degenerate (zero-length) Line entities. Without this check, `iges
    write` would produce an .iges file that `iges parse` rejects — a
    contract violation per TR §1.2."""
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={
                "start": [1.0, 2.0, 3.0],
                "terminate": [1.0, 2.0, 3.0],
            },
        ),
    ])
    json_path = tmp_path / "bad-line.json"
    iges_path = tmp_path / "bad-line.iges"
    json_path.write_text(json.dumps(doc), encoding="utf-8")

    completed = subprocess.run(
        [
            *submission_command, "write",
            "--input", str(json_path),
            "--output", str(iges_path),
        ],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_parse_rejects_zero_length_line(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """Spec §3.2.5: 'All curves shall have non-zero arc length.' A Line
    with coincident start and terminate points is degenerate and must be
    rejected.

    The fixture is built by rewriting the PD record of a valid Line file
    in raw bytes; we cannot round-trip a degenerate Line through
    `iges write` because the writer also rejects zero-length Lines
    (symmetric enforcement of the same §3.2.5 rule).
    """
    iges_path = _make_valid_line_file(submission_command, tmp_path)
    lines = iges_path.read_text(encoding="latin-1").splitlines()
    p_idx = next(
        i for i, line in enumerate(lines)
        if len(line) >= 73 and line[72] == "P"
    )
    # Preserve columns 65-80 (DE back-pointer + P-section sequence
    # number) and rewrite the free-format PD body so start == terminate.
    suffix = lines[p_idx][64:]
    body = "110,0.,0.,0.,0.,0.,0.;"
    lines[p_idx] = body.ljust(64)[:64] + suffix
    _write_lines(iges_path, lines)

    out_path = tmp_path / "zero-length-line.json"
    completed = _run_parse(submission_command, iges_path, out_path)
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False


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


