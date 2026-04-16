"""CLI-level ports of the SDK's §2.2.2 data-type tests.

The original Catch2 cases exercise tokenizer helpers directly. The hidden
eval only observes the CLI, so these tests drive the same semantics through
``iges parse`` / ``iges write`` and the canonical IGES-JSON envelope.
"""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    make_entity,
    parse_iges_to_json,
    semantic_roundtrip_json,
    wrap_entities,
)
from raw_iges_support import build_global_payload, hollerith, make_empty_iges


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


def test_integer_real_and_timestamp_fields_accept_spec_forms(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    fields = [
        hollerith("product"),
        hollerith("test.igs"),
        hollerith("TestSystem"),
        hollerith("v1.0"),
        "+32",
        " 38",
        "6",
        "308",
        "15",
        "",
        ".125",
        "2",
        hollerith("MM"),
        "1",
        "1.E-2",
        hollerith("900411.120000"),
        "0.1E-3",
        "145.98763D4",
        hollerith("John"),
        hollerith("Company"),
        "11",
        "0",
        "",
        "",
    ]
    parsed = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(build_global_payload(fields)),
        name="numeric-forms",
    )

    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["integer_bits"] == 32
    assert global_section["sp_magnitude"] == 38
    assert global_section["product_id_receiver"] == "product"
    assert global_section["model_space_scale"] == 0.125
    assert global_section["units"] == "millimeters"
    assert global_section["max_line_weight_width"] == 0.01
    assert global_section["min_resolution"] == 0.0001
    assert global_section["max_coordinate"] == 1459876.3
    timestamp = global_section["file_timestamp"]
    assert isinstance(timestamp, dict)
    assert timestamp["year"] == 1990
    assert timestamp["month"] == 4
    assert timestamp["day"] == 11


def test_hollerith_strings_preserve_delimiters_spaces_and_empty_defaults(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    fields = [
        hollerith("he,lo"),
        hollerith("a; b,c"),
        hollerith("native"),
        hollerith("v1.0"),
        "32",
        "38",
        "6",
        "308",
        "15",
        "",
        "1.0",
        "1",
        hollerith("IN"),
        "1",
        "0.01",
        hollerith("20260416.120000"),
        "1.0E-6",
        "1000.0",
        hollerith(" HELLO THERE"),
        hollerith("Org"),
        "11",
        "0",
        "",
        "",
    ]
    parsed = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(build_global_payload(fields)),
        name="hollerith",
    )

    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["product_id_sender"] == "he,lo"
    assert global_section["file_name"] == "a; b,c"
    assert global_section["product_id_receiver"] == "he,lo"
    assert global_section["author"] == " HELLO THERE"
    assert global_section["app_protocol"] == ""


def test_control_character_in_hollerith_string_is_rejected(
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
        hollerith(f"A{chr(1)}B"),
        hollerith("Org"),
        "11",
        "0",
        "",
        "",
    ]
    iges_path = tmp_path / "bad-string.iges"
    out_path = tmp_path / "bad-string.json"
    iges_path.write_bytes(make_empty_iges(build_global_payload(fields)).encode("latin-1"))

    completed = subprocess.run(
        [
            *submission_command,
            "parse",
            "--input",
            str(iges_path),
            "--output",
            str(out_path),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert completed.returncode != 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "error" in payload


def test_pointer_and_logical_values_roundtrip_through_entity_json(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={"color": -7},
        ),
        make_entity(
            de_index=3,
            entity_type=510,
            form=1,
            data={"surf": 0, "n": 0, "outer_loop_flag": True, "loops": []},
        ),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)

    line_record = reparsed["entities"][0]
    assert line_record["directory_entry"]["color"] == -7

    face_record = reparsed["entities"][1]
    assert face_record["entity"]["type"] == 510
    assert face_record["entity"]["data"]["outer_loop_flag"] is True
