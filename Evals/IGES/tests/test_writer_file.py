"""Writer tests for full-file section layout and terminate counts."""
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
from raw_iges_support import parse_terminate_counts, physical_lines_by_section, read_physical_lines


def _two_entity_document() -> dict[str, object]:
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 1.0, 1.0]},
        ),
        make_entity(
            de_index=3,
            entity_type=116,
            data={"coords": [5.0, 5.0, 5.0], "display_symbol": 0},
        ),
    ])


def test_written_file_has_all_five_sections_and_80_column_records(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = write_iges_from_json(
        submission_command,
        single_line_document((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
        tmp_path,
        name="file-shape",
    )

    lines = read_physical_lines(iges_path)
    grouped = physical_lines_by_section(iges_path)

    assert all(len(line) == 80 for line in lines)
    assert len(grouped["S"]) >= 1
    assert len(grouped["G"]) >= 1
    assert len(grouped["D"]) == 2
    assert len(grouped["P"]) >= 1
    assert len(grouped["T"]) == 1


def test_terminate_counts_match_written_sections(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = write_iges_from_json(
        submission_command, _two_entity_document(), tmp_path, name="file-counts"
    )
    grouped = physical_lines_by_section(iges_path)
    counts = parse_terminate_counts(grouped["T"][0])

    assert counts["S"] == len(grouped["S"])
    assert counts["G"] == len(grouped["G"])
    assert counts["D"] == len(grouped["D"])
    assert counts["P"] == len(grouped["P"])


def test_empty_start_lines_produce_single_blank_start_record(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([])
    doc["start_lines"] = []
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="blank-start")

    grouped = physical_lines_by_section(iges_path)
    assert len(grouped["S"]) == 1
    assert grouped["S"][0][:72].strip() == ""

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="blank-start")
    assert parsed["start_lines"] == [""]
