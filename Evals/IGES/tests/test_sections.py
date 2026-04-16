"""CLI-level ports of the SDK's §2.2.4 section-structure tests."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    make_entity,
    parse_iges_to_json,
    query_entity,
    wrap_entities,
    write_iges_from_json,
)
from raw_iges_support import (
    build_global_payload,
    hollerith,
    make_empty_iges,
    parse_terminate_counts,
    physical_lines_by_section,
)


def _copious_data_document() -> dict[str, object]:
    data: list[float] = []
    for i in range(18):
        data.extend([float(i), float(i + 1), float(i + 2)])
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=106,
            form=12,
            data={"ip": 2, "n": 18, "zt": 0.0, "data": data},
        ),
    ])
    doc["start_lines"] = ["first start line", "second start line"]
    return doc


def test_start_section_preserves_multiple_comment_lines(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    fields = [
        hollerith("product"),
        hollerith("test.igs"),
        hollerith("native"),
        hollerith("v1.0"),
        "32",
        "38",
        "6",
        "308",
        "15",
        hollerith("product"),
        "1.0",
        "1",
        hollerith("IN"),
        "1",
        "0.01",
        hollerith("20260416.120000"),
        "1.0E-6",
        "1000.0",
        hollerith("John"),
        hollerith("Org"),
        "11",
        "0",
        "",
        "",
    ]
    iges_path = tmp_path / "start-lines.iges"
    iges_path.write_bytes(
        make_empty_iges(
            build_global_payload(fields),
            start_lines=["first start line", "second start line"],
        ).encode("latin-1")
    )

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="start-lines")
    assert parsed["start_lines"] == ["first start line", "second start line"]


def test_directory_section_uses_two_lines_per_entity_and_odd_de_indices(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
        ),
        make_entity(
            de_index=3,
            entity_type=110,
            data={"start": [1.0, 0.0, 0.0], "terminate": [2.0, 0.0, 0.0]},
        ),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="two-lines")

    grouped = physical_lines_by_section(iges_path)
    assert len(grouped["D"]) == 4

    first = query_entity(submission_command, iges_path, 1, tmp_path, name="de1")
    second = query_entity(submission_command, iges_path, 3, tmp_path, name="de3")
    assert first["de_index"] == 1
    assert second["de_index"] == 3
    assert second["entity"]["data"]["start"] == [1.0, 0.0, 0.0]


def test_parameter_line_uses_column_65_space_and_de_back_pointer(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
        ),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="param-line")

    param_line = physical_lines_by_section(iges_path)["P"][0]
    assert param_line[64] == " "
    assert int(param_line[65:72]) == 1
    assert param_line[72] == "P"
    assert int(param_line[73:80]) == 1


def test_terminate_section_counts_match_actual_physical_sections(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = write_iges_from_json(
        submission_command, _copious_data_document(), tmp_path, name="counts"
    )
    grouped = physical_lines_by_section(iges_path)
    counts = parse_terminate_counts(grouped["T"][0])

    assert counts["S"] == len(grouped["S"])
    assert counts["G"] == len(grouped["G"])
    assert counts["D"] == len(grouped["D"])
    assert counts["P"] == len(grouped["P"])


def test_parameter_data_spanning_multiple_physical_lines_is_concatenated(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _copious_data_document()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="multiline")

    grouped = physical_lines_by_section(iges_path)
    assert len(grouped["P"]) > 1

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="multiline")
    entity = parsed["entities"][0]["entity"]
    assert entity["type"] == 106
    assert entity["data"]["ip"] == 2
    assert entity["data"]["n"] == 18
    assert len(entity["data"]["data"]) == 54
