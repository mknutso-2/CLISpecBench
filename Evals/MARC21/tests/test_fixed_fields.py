from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from conftest import assert_rejected, b64, run_marc21, unb64
from marc21_support import (
    decode_iso2709_record,
    decode_marcxml_record,
    encode_iso2709_record,
    sample_marcxml,
    sample_record,
)

FIXED_RULES = json.loads(
    (Path(__file__).resolve().parent / "generated" / "marc21_fixed_field_rules.json").read_text(
        encoding="utf-8"
    )
)


def _code(value: str) -> str:
    return " " if value == "#" else value


def _invalid_code(allowed_values: list[str]) -> str:
    allowed = {_code(value) for value in allowed_values}
    for candidate in ["x", "?", "~", "0", "z", "|", "a", " "]:
        if candidate not in allowed:
            return candidate
    raise AssertionError(f"Could not find an invalid code outside {allowed_values!r}")


LEADER_ALLOWED_CASES = [
    (int(position), _code(value))
    for position, values in FIXED_RULES["leader"]["positions"].items()
    for value in values
]
LEADER_INVALID_CASES = [
    (int(position), _invalid_code(values))
    for position, values in FIXED_RULES["leader"]["positions"].items()
]
CONTROL_006_ALLOWED = [_code(value) for value in FIXED_RULES["006"]["position_00"]]
CONTROL_007_CATEGORIES = [_code(value) for value in FIXED_RULES["007"]["position_00"]]
CONTROL_007_LENGTH_CASES = [
    (category, bounds["minimum"], bounds["maximum"])
    for category, bounds in FIXED_RULES["007"]["category_lengths"].items()
]
# bd007c/bd007m Input Conventions recommend six/eight initial positions.
# Whether shorter forms must be accepted is not unequivocal ("should always").
# Test positive lengths inside both readings. For c/m, only over-maximum
# negatives are unequivocal; undersized acceptance/rejection is left unscored.
CONTROL_007_ACCEPTED_LENGTH_CASES = [
    (category, {"c": 6, "m": 8}.get(category, minimum), maximum)
    for category, minimum, maximum in CONTROL_007_LENGTH_CASES
]
CONTROL_008_DATE_TYPES = [_code(value) for value in FIXED_RULES["008"]["date_type_position_06"]]
CONTROL_008_POSITION_CASES = [
    (int(position), _code(value))
    for position, values in FIXED_RULES["008"]["position_code_tables"].items()
    for value in values
]
CONTROL_008_INVALID_POSITION_CASES = [
    (int(position), _invalid_code(values))
    for position, values in FIXED_RULES["008"]["position_code_tables"].items()
]


def _minimal_record() -> dict[str, Any]:
    # Changing Leader/06 changes the interpretation of 008/18-34. A book's 008
    # is not a valid independent precondition for every material-type case.
    record = sample_record()
    record["control_fields"] = [{"tag": "001", "value": "fixed-field-example"}]
    record["data_fields"] = []
    return record


def _with_control_field(tag: str, value: str) -> dict[str, Any]:
    record = _minimal_record()
    record["control_fields"] = [field for field in record["control_fields"] if field["tag"] != tag]
    record["control_fields"].append({"tag": tag, "value": value})
    record["control_fields"].sort(key=lambda field: field["tag"])
    return record


def _with_leader_char(position: int, value: str) -> dict[str, Any]:
    record = _minimal_record()
    leader = list(record["leader_template"])
    leader[position] = value
    record["leader_template"] = "".join(leader)
    return record


def _with_control_field_char(tag: str, position: int, value: str) -> dict[str, Any]:
    record = deepcopy(sample_record())
    for field in record["control_fields"]:
        if field["tag"] == tag:
            characters = list(field["value"])
            characters[position] = value
            field["value"] = "".join(characters)
            return record
    raise AssertionError(f"sample fixture has no control field {tag}")


def _assert_render_ok(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    record: dict[str, Any],
    *,
    action: str = "render_iso2709",
    leader_position: int | None = None,
) -> None:
    _, payload = run_marc21(
        submission_command,
        {"action": action, "record": record},
        tmp_path,
    )
    assert payload is not None
    # Successful validation must produce the requested material, not merely an
    # exit-zero envelope. Scope the observation to the fixed field under test.
    rendered = (
        decode_iso2709_record(unb64(payload["result"]["record_b64"]))
        if action == "render_iso2709"
        else decode_marcxml_record(payload["result"]["marcxml"])
    )
    fixed_fields = [field for field in record["control_fields"] if field["tag"] != "001"]
    if fixed_fields:
        tag = fixed_fields[0]["tag"]
        assert [
            field for field in rendered["control_fields"] if field["tag"] == tag
        ] == fixed_fields
    else:
        # This case names one Leader position. The remaining positions and
        # success envelope have their own schema/integration checks.
        assert leader_position is not None
        assert (
            rendered["leader_template"][leader_position]
            == record["leader_template"][leader_position]
        )


def _assert_render_error(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    record: dict[str, Any],
    *,
    action: str = "render_iso2709",
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": action, "record": record},
        tmp_path,
    )
    assert_rejected(result, payload)


def _assert_inspect_error(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    record: dict[str, Any],
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert_rejected(result, payload)


def _control_008_with(position: int, value: str) -> str:
    characters = list("260421s2026    ilu           000 0 eng d")
    characters[position] = value
    return "".join(characters)


@pytest.mark.parametrize(("position", "value"), LEADER_ALLOWED_CASES)
def test_render_accepts_all_leader_codes_from_official_tables(
    position: int,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _assert_render_ok(
        submission_command,
        tmp_path,
        _with_leader_char(position, value),
        leader_position=position,
    )


@pytest.mark.parametrize(("position", "value"), LEADER_INVALID_CASES)
def test_render_rejects_each_leader_position_outside_official_tables(
    position: int,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _assert_render_error(submission_command, tmp_path, _with_leader_char(position, value))


def test_render_rejects_leader_entry_map_outside_official_value(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _assert_render_error(submission_command, tmp_path, _with_leader_char(20, "9"))


@pytest.mark.parametrize("category", CONTROL_006_ALLOWED)
def test_render_accepts_all_006_position_00_codes_from_official_table(
    category: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # bd006.html permits fill in every position after 00; blanks are not legal
    # defaults in every material-specific table.
    _assert_render_ok(submission_command, tmp_path, _with_control_field("006", category + "|" * 17))


@pytest.mark.parametrize("length", [17, 19])
def test_render_rejects_006_lengths_other_than_18(
    length: int,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("006", "a".ljust(length))
    _assert_render_error(submission_command, tmp_path, record)


@pytest.mark.parametrize("category", CONTROL_007_CATEGORIES)
def test_render_accepts_all_007_position_00_categories_from_official_table(
    category: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    minimum = {"c": 6, "m": 8}.get(
        category, int(FIXED_RULES["007"]["category_lengths"][category]["minimum"])
    )
    record = _with_control_field("007", category + "|" * (minimum - 1))
    _assert_render_ok(submission_command, tmp_path, record)


@pytest.mark.parametrize(("category", "minimum", "maximum"), CONTROL_007_ACCEPTED_LENGTH_CASES)
def test_render_accepts_007_recommended_base_and_maximum_lengths(
    category: str,
    minimum: int,
    maximum: int,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    minimum_record = _with_control_field("007", category + "|" * (minimum - 1))
    maximum_record = _with_control_field("007", category + "|" * (maximum - 1))
    _assert_render_ok(submission_command, tmp_path, minimum_record)
    _assert_render_ok(submission_command, tmp_path, maximum_record)


@pytest.mark.parametrize(("category", "minimum", "maximum"), CONTROL_007_LENGTH_CASES)
def test_inspect_rejects_007_category_lengths_outside_official_range(
    category: str,
    minimum: int,
    maximum: int,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    too_short = _with_control_field("007", category + "|" * (minimum - 2))
    too_long = _with_control_field("007", category + "|" * maximum)
    # The variable-length c/m pages do not make a precise short-form cutoff
    # mandatory. Defined positions alone do not establish the old inferred
    # two-character minimum; leave that public ambiguity unscored.
    if category not in {"c", "m"}:
        _assert_inspect_error(submission_command, tmp_path, too_short)
    _assert_inspect_error(submission_command, tmp_path, too_long)


@pytest.mark.parametrize("date_type", CONTROL_008_DATE_TYPES)
def test_render_accepts_all_008_date_type_codes_from_official_table(
    date_type: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # bd008a.html defines Date 1/Date 2 jointly with the date-type code. Give
    # each type compatible dates, not the old single-date 2026/blank pair.
    dates = {
        "b": "        ",
        "c": "20209999",
        "d": "20202026",
        "e": "20260101",
        "i": "20202026",
        "k": "20202026",
        "m": "20202026",
        "n": "uuuuuuuu",
        "p": "20262020",
        "q": "20202026",
        "r": "20262020",
        "s": "2026    ",
        "t": "20262025",
        "u": "2020uuuu",
        "|": "||||||||",
    }
    value = list(_control_008_with(6, date_type))
    value[7:15] = dates[date_type]
    # c/d/u describe continuing resources. Use the serial bibliographic level
    # and permitted fill for unrelated material-specific 008 positions.
    if date_type in {"c", "d", "u"}:
        value[18:35] = "|" * 17
    record = _with_control_field("008", "".join(value))
    if date_type in {"c", "d", "u"}:
        leader = list(record["leader_template"])
        leader[7] = "s"
        record["leader_template"] = "".join(leader)
    _assert_render_ok(submission_command, tmp_path, record)


@pytest.mark.parametrize("position", [0, 1, 2, 3, 4, 5])
def test_render_rejects_008_fill_character_in_each_date_entered_position(
    position: int,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("008", _control_008_with(position, "|"))
    _assert_render_error(submission_command, tmp_path, record)


@pytest.mark.parametrize("position", [0, 1, 2, 3, 4, 5])
def test_inspect_rejects_008_non_digit_in_each_date_entered_position(
    position: int,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("008", _control_008_with(position, "A"))
    _assert_inspect_error(submission_command, tmp_path, record)


@pytest.mark.parametrize(("position", "value"), CONTROL_008_POSITION_CASES)
def test_render_accepts_all_008_position_code_table_values(
    position: int,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("008", _control_008_with(position, value))
    _assert_render_ok(submission_command, tmp_path, record)


@pytest.mark.parametrize(("position", "value"), CONTROL_008_INVALID_POSITION_CASES)
def test_inspect_rejects_each_008_position_code_outside_official_tables(
    position: int,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("008", _control_008_with(position, value))
    _assert_inspect_error(submission_command, tmp_path, record)


@pytest.mark.parametrize(
    ("tag", "value"),
    [
        ("006", "a" + " " * 16),
        ("007", "a"),
        ("008", "260421s2026    ilu           000 0 eng "),
    ],
)
def test_render_rejects_fixed_control_fields_with_wrong_official_length(
    tag: str,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": _with_control_field(tag, value)},
        tmp_path,
    )
    assert_rejected(result, payload)


@pytest.mark.parametrize(
    ("tag", "value"),
    [
        ("006", "|" + " " * 17),
        ("007", "|a"),
        ("008", "|60421s2026    ilu           000 0 eng d"),
    ],
)
def test_render_rejects_fixed_control_fields_with_disallowed_fill_positions(
    tag: str,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": _with_control_field(tag, value)},
        tmp_path,
    )
    assert_rejected(result, payload)


@pytest.mark.parametrize(
    ("tag", "value"),
    [
        ("006", "x" + " " * 17),
        ("007", "x "),
        ("008", "260421x2026    ilu           000 0 eng d"),
    ],
)
def test_inspect_rejects_fixed_control_field_codes_outside_official_tables(
    tag: str,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field(tag, value)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert_rejected(result, payload)


def test_inspect_rejects_short_007_map_category(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("007", "a ")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert_rejected(result, payload)


def test_render_accepts_complete_007_map_category(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field("007", "aj canzn")
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload.get("error") is None


def test_inspect_rejects_008_cataloging_source_outside_official_table(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field_char("008", 39, "x")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert_rejected(result, payload)


def test_render_accepts_008_modified_record_x_with_valid_cataloging_source(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _with_control_field_char("008", 38, "x")
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload.get("error") is None


def test_inspect_marcxml_rejects_non_digit_008_date_entered(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = _with_control_field("008", "26A421s2026    ilu           000 0 eng d")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert_rejected(result, payload)


@pytest.mark.parametrize(
    ("position", "value"),
    [
        (5, "x"),
        (6, "x"),
        (7, "x"),
        (8, "x"),
        (17, "x"),
        (18, "x"),
        (19, "x"),
    ],
)
def test_render_rejects_leader_codes_outside_official_tables(
    position: int,
    value: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": _with_leader_char(position, value)},
        tmp_path,
    )
    assert_rejected(result, payload)
