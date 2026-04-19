"""CLI-level ports of the SDK's §2.2.3 free-formatted-data tests."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    parse_iges_to_json,
    single_line_document,
    write_iges_from_json,
)
from raw_iges_support import (
    build_global_payload,
    hollerith,
    make_empty_iges,
    physical_lines_by_section,
    read_physical_lines,
)


def _parse_raw_document(
    submission_command: Sequence[str],
    tmp_path: Path,
    contents: str,
    *,
    name: str,
) -> dict[str, object]:
    iges_path = tmp_path / f"{name}.iges"
    iges_path.write_bytes(contents.encode("latin-1"))
    return parse_iges_to_json(submission_command, iges_path, tmp_path, name=name)


def test_custom_parameter_delimiter_is_honored_in_written_and_parsed_files(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    doc["global"]["param_delimiter"] = "|"
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="pipe")

    grouped = physical_lines_by_section(iges_path)
    assert any("1H|" in line[:72] for line in grouped["G"])
    assert any("|" in line[:64] for line in grouped["P"])

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="pipe")
    data = parsed["entities"][0]["entity"]["data"]
    assert data["start"] == [0.0, 0.0, 0.0]
    assert data["terminate"] == [1.0, 1.0, 1.0]


def test_custom_record_delimiter_is_honored_in_written_and_parsed_files(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    doc["global"]["record_delimiter"] = "#"
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="hash")

    grouped = physical_lines_by_section(iges_path)
    assert any("1H,,1H#" in line[:72] for line in grouped["G"])
    assert any("#" in line[:64] for line in grouped["P"])

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="hash")
    data = parsed["entities"][0]["entity"]["data"]
    assert data["terminate"] == [1.0, 1.0, 1.0]


def test_consecutive_delimiters_default_global_fields(
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
        "",
        "",
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
        "",
        "",
        "",
    ]
    parsed = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(build_global_payload(fields)),
        name="defaults",
    )

    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["product_id_receiver"] == "product"
    assert global_section["model_space_scale"] == 1.0
    assert global_section["drafting_std"] == "none"
    assert global_section["model_timestamp"] is None
    assert global_section["app_protocol"] == ""


def test_custom_delimiters_do_not_split_hollerith_text(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    fields = [
        hollerith("a|b#c"),
        hollerith("file|#"),
        hollerith("native"),
        hollerith("v1.0"),
        "32",
        "38",
        "6",
        "308",
        "15",
        "",
        "1.0",
        "2",
        hollerith("MM"),
        "1",
        "0.01",
        hollerith("20260416.120000"),
        "1.0E-6",
        "1000.0",
        hollerith("Author"),
        hollerith("Org"),
        "11",
        "0",
        "",
        "",
    ]
    parsed = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(
            build_global_payload(
                fields, param_delimiter="|", record_delimiter="#"
            )
        ),
        name="custom-hollerith",
    )

    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["param_delimiter"] == "|"
    assert global_section["record_delimiter"] == "#"
    assert global_section["product_id_sender"] == "a|b#c"
    assert global_section["file_name"] == "file|#"


def test_prohibited_parameter_delimiter_is_rejected(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§2.2.3.1: digits, '+', '-', '.', 'D', 'E', 'H', space, and control
    chars are prohibited as parameter / record delimiters. A Global section
    declaring a digit as parameter delimiter must be rejected."""
    # Hand-craft a Global payload using '9' as the parameter delimiter.
    # build_global_payload() would encode fields using the custom delimiter,
    # but the illegal-choice probe only needs field 1 to advertise it.
    payload = (
        "1H9,1H;,3Hfoo,3Hbar,3HSDK,3H1.0,32,38,6,308,15,,"
        "1.0,1,2HIN,1,0.01,15H20260416.120000,1.0E-6,1.0,"
        "3Husr,4Hsite,11,0,,;"
    )
    iges = tmp_path / "bad-delim.iges"
    iges.write_bytes(make_empty_iges(payload).encode("latin-1"))
    out = tmp_path / "bad-delim.json"

    completed = subprocess.run(
        [
            *submission_command, "parse",
            "--input", str(iges),
            "--output", str(out),
        ],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1
    payload_out = json.loads(out.read_text(encoding="utf-8"))
    assert payload_out["ok"] is False


def test_comment_after_parameter_record_delimiter_is_ignored(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = write_iges_from_json(
        submission_command,
        single_line_document((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
        tmp_path,
        name="commented",
    )
    lines = read_physical_lines(iges_path)
    param_index = next(i for i, line in enumerate(lines) if line[72] == "P")
    suffix = lines[param_index][64:]
    body = "110,0.,0.,0.,1.,1.,1.;this is a comment"
    lines[param_index] = body.ljust(64)[:64] + suffix
    iges_path.write_text("\n".join(lines) + "\n", encoding="latin-1")

    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="commented")
    data = parsed["entities"][0]["entity"]["data"]
    assert data["start"] == [0.0, 0.0, 0.0]
    assert data["terminate"] == [1.0, 1.0, 1.0]
