"""Writer-focused tests for PD record construction and packing."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    make_entity,
    parse_iges_to_json,
    single_line_document,
    wrap_entities,
    write_iges_from_json,
)
from raw_iges_support import physical_lines_by_section


def _copious_data_document() -> dict[str, object]:
    data: list[float] = []
    for i in range(20):
        data.extend([float(i), float(i + 1), float(i + 2)])
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=106,
            form=12,
            data={"ip": 2, "n": 20, "zt": 0.0, "data": data},
        ),
    ])


def test_line_parameter_record_has_entity_type_prefix_and_expected_field_count(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = write_iges_from_json(
        submission_command,
        single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)),
        tmp_path,
        name="line-param",
    )

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    assert p_body.startswith("110,")
    assert p_body.endswith(";")
    assert p_body.count(",") == 6


def test_parameter_records_use_selected_custom_delimiters(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    doc["global"]["param_delimiter"] = "|"
    doc["global"]["record_delimiter"] = "#"
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="custom-param")

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    assert p_body.startswith("110|")
    assert p_body.endswith("#")
    assert "," not in p_body
    assert ";" not in p_body


def test_long_parameter_record_splits_across_multiple_p_lines_and_reparses(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _copious_data_document()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="long-param")

    grouped = physical_lines_by_section(iges_path)
    assert len(grouped["P"]) > 1

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="long-param")
    entity = parsed["entities"][0]["entity"]
    assert entity["type"] == 106
    assert entity["data"]["n"] == 20
    assert len(entity["data"]["data"]) == 60
