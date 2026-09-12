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
    assert_semantic_equal,
    is_input_rejection,
    make_entity,
    parse_iges_to_json,
    semantic_roundtrip_json,
)
from raw_iges_support import build_global_payload, hollerith, make_empty_iges
from topology_support import open_triangle_document


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
    assert_semantic_equal(global_section["model_space_scale"], 0.125)
    assert global_section["units"] == "millimeters"
    assert_semantic_equal(global_section["max_line_weight_width"], 0.01)
    assert_semantic_equal(global_section["min_resolution"], 0.0001)
    assert_semantic_equal(global_section["max_coordinate"], 1459876.3)
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


def test_control_character_in_start_section_is_rejected(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§2.2.4.2: Start lines 'shall not contain any ASCII control characters.'"""
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
    iges_path = tmp_path / "bad-start.iges"
    out_path = tmp_path / "bad-start.json"
    iges_path.write_bytes(
        make_empty_iges(
            build_global_payload(fields),
            start_lines=[f"A{chr(1)}B"],
        ).encode("latin-1")
    )

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
    assert completed.returncode == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert is_input_rejection(payload)


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
    assert is_input_rejection(payload)
    assert "error" in payload


def test_spec_version_below_range_is_clamped_to_default(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§2.2.4.3.23: 'Postprocessors finding an unrecognized value less than 1
    shall assign 3' (version 3 = spec v2_0)."""
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
        "0",  # field 23: unrecognized spec version (< 1)
        "0",
        "",
        "",
    ]
    parsed = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(build_global_payload(fields)),
        name="spec-version-below",
    )
    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["spec_version"] == "v2_0"


def test_spec_version_above_range_is_clamped_to_v5_3(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§2.2.4.3.23: 'Postprocessors finding an unrecognized value greater
    than 11 shall assign 11' (code 11 = v5_3)."""
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
        "20",  # field 23: unrecognized spec version (> 11)
        "0",
        "",
        "",
    ]
    parsed = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(build_global_payload(fields)),
        name="spec-version-above",
    )
    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["spec_version"] == "v5_3"


def test_pointer_and_logical_values_roundtrip_through_entity_json(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # §§2.2.4.4.13/4.76 and 4.146: a negative Color Definition pointer
    # and the Face boolean must occur in a complete legal geometric context.
    doc, ids = open_triangle_document()
    line = next(record for record in doc["entities"] if record["entity"]["type"] == 110)
    line_de = line["de_index"]
    color_de = max(record["de_index"] for record in doc["entities"]) + 2
    line["directory_entry"]["color"] = -color_de
    doc["entities"].append(
        make_entity(
            de_index=color_de,
            entity_type=314,
            data={"red": 20.0, "green": 40.0, "blue": 60.0, "name": "CUSTOM"},
            directory_entry_overrides={
                "color": 8,
                "status": {
                    "blank": "visible",
                    "subordinate": "independent",
                    "entity_use": "definition",
                    "hierarchy": "global_top_down",
                },
            },
        )
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    records = {record["de_index"]: record for record in reparsed["entities"]}
    assert records[line_de]["directory_entry"]["color"] == -color_de
    face_record = records[ids["face"]]
    assert face_record["entity"]["type"] == 510
    assert face_record["entity"]["data"]["outer_loop_flag"] is True


def test_zero_count_hollerith_is_rejected_after_defaulted_string_control(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # §§2.2.2.3/2.2.3 distinguish a legal defaulted NULL from illegal 0H.
    # Use a standalone raw Global fixture, so neither submitted writing nor
    # any geometry feature is a prerequisite for observing this string rule.
    fields = [
        hollerith("product"),
        hollerith("test.igs"),
        hollerith("native"),
        hollerith("v1"),
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
        hollerith("John"),
        hollerith("Org"),
        "11",
        "0",
        "",
        "",
    ]
    valid = _parse_raw_document(
        submission_command,
        tmp_path,
        make_empty_iges(build_global_payload(fields)),
        name="hollerith-default-control",
    )
    global_section = valid["global"]
    assert isinstance(global_section, dict)
    assert global_section["app_protocol"] == ""
    fields[-1] = "0H"
    path = tmp_path / "zero-count.iges"
    output = tmp_path / "zero-count.json"
    path.write_bytes(make_empty_iges(build_global_payload(fields)).encode("latin-1"))
    completed = subprocess.run(
        [*submission_command, "parse", "--input", str(path), "--output", str(output)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert is_input_rejection(payload)
