from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import b64, run_marc21, unb64
from marc21_spec_support import (
    data_field_example_records,
    representative_example_records,
)
from marc21_support import (
    decode_iso2709_record,
    decode_marcxml_record,
    encode_iso2709_record,
    sample_marcxml,
)

_REPRESENTATIVE_CASES = representative_example_records()
_REPRESENTATIVE_IDS = [tag for tag, _ in _REPRESENTATIVE_CASES]
_DATA_FIELD_CASES = data_field_example_records()
_DATA_FIELD_IDS = [tag for tag, _ in _DATA_FIELD_CASES]


def _field_content(record: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    # These cases measure the named LOC field. Leader normalization, unrelated
    # 001 preservation, envelope fields and full-record integration have their
    # own tests; one such error must not fail every field in the corpus.
    key = "control_fields" if tag <= "009" else "data_fields"
    fields = [field for field in record[key] if field.get("tag") == tag]
    if tag <= "009":
        return [{"tag": field["tag"], "value": field["value"]} for field in fields]
    return [
        {
            "tag": field["tag"],
            "indicators": field["indicators"],
            "subfields": [
                {"code": subfield["code"], "value": subfield["value"]}
                for subfield in field["subfields"]
            ],
        }
        for field in fields
    ]


@pytest.mark.parametrize(("tag", "record"), _REPRESENTATIVE_CASES, ids=_REPRESENTATIVE_IDS)
def test_render_iso2709_roundtrips_representative_official_field_examples(
    tag: str,
    record: dict[str, object],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, render_payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert render_payload is not None

    assert _field_content(
        decode_iso2709_record(unb64(render_payload["result"]["record_b64"])), tag
    ) == _field_content(record, tag)


@pytest.mark.parametrize(("tag", "record"), _REPRESENTATIVE_CASES, ids=_REPRESENTATIVE_IDS)
def test_inspect_accepts_representative_official_field_examples_without_render_dependency(
    tag: str,
    record: dict[str, object],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(record))},
        tmp_path,
    )
    assert inspect_payload is not None
    assert _field_content(inspect_payload["result"]["record"], tag) == _field_content(record, tag)


@pytest.mark.parametrize(("tag", "record"), _REPRESENTATIVE_CASES, ids=_REPRESENTATIVE_IDS)
def test_inspect_marcxml_accepts_representative_official_field_examples_without_render_dependency(
    tag: str,
    record: dict[str, object],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml(record)},
        tmp_path,
    )
    assert inspect_payload is not None
    assert _field_content(inspect_payload["result"]["record"], tag) == _field_content(record, tag)


@pytest.mark.parametrize(("tag", "record"), _DATA_FIELD_CASES, ids=_DATA_FIELD_IDS)
def test_render_marcxml_roundtrips_representative_official_data_field_examples(
    tag: str,
    record: dict[str, object],
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, render_payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": record},
        tmp_path,
    )
    assert render_payload is not None

    assert _field_content(
        decode_marcxml_record(render_payload["result"]["marcxml"]), tag
    ) == _field_content(record, tag)
