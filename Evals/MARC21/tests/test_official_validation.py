from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from marc21_spec_support import (
    duplicate_nonrepeatable_field_record,
    fields_with_indicator_constraints,
    fields_with_nonrepeatable_subfields,
    fields_with_subfield_constraints,
    first_nonrepeatable_subfield_code,
    invalid_indicator_for,
    invalid_subfield_code_for,
    nonrepeatable_control_field_cases,
    nonrepeatable_data_field_cases,
    record_for_official_example,
    rule_compatible_example_text,
)
from marc21_support import encode_iso2709_record, sample_marcxml

from conftest import b64, run_marc21

_INDICATOR_CASES = fields_with_indicator_constraints()
_INDICATOR_IDS = [tag for tag, _ in _INDICATOR_CASES]
_NONREPEATABLE_CONTROL_CASES = nonrepeatable_control_field_cases()
_NONREPEATABLE_CONTROL_IDS = [tag for tag, _ in _NONREPEATABLE_CONTROL_CASES]
_NONREPEATABLE_DATA_CASES = nonrepeatable_data_field_cases()
_NONREPEATABLE_DATA_IDS = [tag for tag, _ in _NONREPEATABLE_DATA_CASES]
_SUBFIELD_CASES = fields_with_subfield_constraints()
_SUBFIELD_IDS = [tag for tag, _ in _SUBFIELD_CASES]
_NONREPEATABLE_CASES = fields_with_nonrepeatable_subfields()
_NONREPEATABLE_IDS = [tag for tag, _ in _NONREPEATABLE_CASES]


def _record_with_invalid_indicator(tag: str, rule: dict[str, Any]) -> dict[str, Any]:
    record = record_for_official_example(tag, rule_compatible_example_text(tag))
    field = deepcopy(record["data_fields"][0])
    indicators = list(field["indicators"])
    if rule.get("indicator1"):
        indicators[0] = invalid_indicator_for(tag, cast(list[str] | None, rule["indicator1"]))
    else:
        indicators[1] = invalid_indicator_for(tag, cast(list[str] | None, rule["indicator2"]))
    field["indicators"] = indicators
    record["data_fields"] = [field]
    return record


def _record_with_invalid_subfield_code(tag: str, rule: dict[str, Any]) -> dict[str, Any]:
    record = record_for_official_example(tag, rule_compatible_example_text(tag))
    field = deepcopy(record["data_fields"][0])
    field["subfields"].append({"code": invalid_subfield_code_for(rule), "value": "invalid"})
    record["data_fields"] = [field]
    return record


def _record_with_duplicate_nonrepeatable_subfield(tag: str, rule: dict[str, Any]) -> dict[str, Any]:
    record = record_for_official_example(tag, rule_compatible_example_text(tag))
    field = deepcopy(record["data_fields"][0])
    code = first_nonrepeatable_subfield_code(rule)
    existing = next((subfield for subfield in field["subfields"] if subfield["code"] == code), None)
    duplicate_value = "duplicate" if existing is None else str(existing["value"])
    field["subfields"].append({"code": code, "value": duplicate_value})
    if existing is None:
        field["subfields"].append({"code": code, "value": duplicate_value})
    record["data_fields"] = [field]
    return record


@pytest.mark.parametrize(("tag", "rule"), _INDICATOR_CASES, ids=_INDICATOR_IDS)
def test_render_rejects_indicator_values_outside_official_field_definition(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_invalid_indicator(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(("tag", "rule"), _SUBFIELD_CASES, ids=_SUBFIELD_IDS)
def test_render_rejects_subfield_codes_outside_official_field_definition(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_invalid_subfield_code(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_CASES,
    ids=_NONREPEATABLE_IDS,
)
def test_render_rejects_duplicate_nonrepeatable_subfields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_duplicate_nonrepeatable_subfield(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_CONTROL_CASES,
    ids=_NONREPEATABLE_CONTROL_IDS,
)
def test_render_rejects_duplicate_nonrepeatable_control_fields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del rule
    record = duplicate_nonrepeatable_field_record(tag)
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_DATA_CASES,
    ids=_NONREPEATABLE_DATA_IDS,
)
def test_render_rejects_duplicate_nonrepeatable_data_fields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del rule
    record = duplicate_nonrepeatable_field_record(tag)
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_CONTROL_CASES,
    ids=_NONREPEATABLE_CONTROL_IDS,
)
def test_inspect_marcxml_rejects_duplicate_nonrepeatable_control_fields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del rule
    record = duplicate_nonrepeatable_field_record(tag)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_DATA_CASES,
    ids=_NONREPEATABLE_DATA_IDS,
)
def test_inspect_marcxml_rejects_duplicate_nonrepeatable_data_fields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del rule
    record = duplicate_nonrepeatable_field_record(tag)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_CONTROL_CASES,
    ids=_NONREPEATABLE_CONTROL_IDS,
)
def test_inspect_rejects_duplicate_nonrepeatable_control_fields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del rule
    record = duplicate_nonrepeatable_field_record(tag)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(
    ("tag", "rule"),
    _NONREPEATABLE_DATA_CASES,
    ids=_NONREPEATABLE_DATA_IDS,
)
def test_inspect_rejects_duplicate_nonrepeatable_data_fields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del rule
    record = duplicate_nonrepeatable_field_record(tag)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(("tag", "rule"), _INDICATOR_CASES, ids=_INDICATOR_IDS)
def test_inspect_rejects_indicator_values_outside_official_field_definition(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_invalid_indicator(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(("tag", "rule"), _INDICATOR_CASES, ids=_INDICATOR_IDS)
def test_inspect_marcxml_rejects_indicator_values_outside_official_field_definition(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_invalid_indicator(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(("tag", "rule"), _SUBFIELD_CASES, ids=_SUBFIELD_IDS)
def test_inspect_rejects_subfield_codes_outside_official_field_definition(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_invalid_subfield_code(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(("tag", "rule"), _SUBFIELD_CASES, ids=_SUBFIELD_IDS)
def test_inspect_marcxml_rejects_subfield_codes_outside_official_field_definition(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_invalid_subfield_code(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(("tag", "rule"), _NONREPEATABLE_CASES, ids=_NONREPEATABLE_IDS)
def test_inspect_rejects_duplicate_nonrepeatable_subfields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_duplicate_nonrepeatable_subfield(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


@pytest.mark.parametrize(("tag", "rule"), _NONREPEATABLE_CASES, ids=_NONREPEATABLE_IDS)
def test_inspect_marcxml_rejects_duplicate_nonrepeatable_subfields_from_official_rules(
    tag: str,
    rule: dict[str, Any],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    record = _record_with_duplicate_nonrepeatable_subfield(tag, rule)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"
