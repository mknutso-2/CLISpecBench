"""Writer-format tests for Hollerith, real, and logical output."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import make_entity, single_line_document, wrap_entities, write_iges_from_json
from raw_iges_support import physical_lines_by_section


def test_global_strings_use_hollerith_encoding_in_g_section(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([])
    doc["global"]["author"] = "Jane Doe"
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="global-hollerith")

    g_body = "".join(line[:72] for line in physical_lines_by_section(iges_path)["G"])
    assert "8HJane Doe" in g_body


def test_real_values_in_parameter_records_include_decimal_points(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = write_iges_from_json(
        submission_command,
        single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)),
        tmp_path,
        name="real-format",
    )

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    assert "1.0" in p_body
    assert "2.0" in p_body
    assert "6.0" in p_body


def test_string_values_in_parameter_records_use_hollerith_encoding(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=308,
            data={"depth": 1, "name": "NETLIST", "n": 0, "entities": []},
        ),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="pd-hollerith")

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    assert "7HNETLIST" in p_body


def test_logical_values_in_parameter_records_use_zero_and_one(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=510,
            form=1,
            data={"surf": 0, "n": 0, "outer_loop_flag": True, "loops": []},
        ),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="logical-format")

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    assert p_body.startswith("510,0,0,1")
    assert "TRUE" not in p_body
    assert "FALSE" not in p_body
