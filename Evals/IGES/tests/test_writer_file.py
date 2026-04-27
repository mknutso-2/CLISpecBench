"""Writer tests for full-file section layout and terminate counts."""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    parse_iges_to_json,
    single_line_document,
    wrap_entities,
    write_iges_from_json,
)
from raw_iges_support import physical_lines_by_section, read_physical_lines


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


def test_empty_start_lines_produce_one_or_more_blank_start_records(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([])
    doc["start_lines"] = []
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="blank-start")

    grouped = physical_lines_by_section(iges_path)
    assert len(grouped["S"]) >= 1
    assert all(line[:72].strip() == "" for line in grouped["S"])

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="blank-start")
    assert len(parsed["start_lines"]) >= 1
    assert all(line == "" for line in parsed["start_lines"])
