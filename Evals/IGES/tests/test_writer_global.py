"""Writer-focused tests for Global-section serialization."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import parse_iges_to_json, wrap_entities, write_iges_from_json


def test_write_and_parse_preserve_all_26_global_fields(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([])
    global_section = doc["global"]
    global_section.update({
        "param_delimiter": "|",
        "record_delimiter": "#",
        "product_id_sender": "WriterProduct",
        "file_name": "writer-full.igs",
        "native_system_id": "WRITER-SDK",
        "preprocessor_version": "v9.9",
        "integer_bits": 64,
        "sp_magnitude": 37,
        "sp_significance": 6,
        "dp_magnitude": 307,
        "dp_significance": 15,
        "product_id_receiver": "Receiver",
        "model_space_scale": 0.125,
        "units": "millimeters",
        "units_name": "MM",
        "max_line_weight_grads": 4,
        "max_line_weight_width": 0.02,
        "file_timestamp": {
            "year": 2026,
            "month": 4,
            "day": 16,
            "hour": 13,
            "minute": 45,
            "second": 30,
        },
        "min_resolution": 1.0e-6,
        "max_coordinate": 2500.0,
        "author": "Jane Doe",
        "organization": "ACME CAD",
        "spec_version": "v5_3",
        "drafting_std": "ansi",
        "model_timestamp": {
            "year": 2026,
            "month": 4,
            "day": 15,
            "hour": 8,
            "minute": 0,
            "second": 5,
        },
        "app_protocol": "AP242",
    })

    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="global-full")
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="global-full")

    assert parsed["entities"] == []
    assert parsed["global"] == global_section


def test_write_empty_document_roundtrips_default_global_values(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="global-defaults")
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path, name="global-defaults")

    global_section = parsed["global"]
    assert isinstance(global_section, dict)
    assert global_section["product_id_sender"] == "TEST"
    assert global_section["product_id_receiver"] == "TEST"
    assert global_section["units"] == "inches"
    assert global_section["model_space_scale"] == 1.0
    assert global_section["model_timestamp"] is None
    assert global_section["app_protocol"] == ""
