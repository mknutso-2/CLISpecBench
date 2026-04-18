"""Writer-focused tests for PD record construction and packing."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    single_line_document,
    write_iges_from_json,
)
from raw_iges_support import physical_lines_by_section


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
