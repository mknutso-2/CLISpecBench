from __future__ import annotations

from pathlib import Path

from marc21_support import (
    encode_iso2709,
    sample_marcxml,
    sample_marcxml_collection,
    sample_record,
    sample_record_cjk,
    sample_record_control_only,
)

from conftest import b64, run_marc21, unb64


def test_inspect_parses_basic_iso2709_record(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    render_result, render_payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": sample_record()},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None

    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": render_payload["result"]["record_b64"]},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    record = inspect_payload["result"]["record"]
    assert record["control_fields"][0]["tag"] == "001"
    assert record["data_fields"][1]["tag"] == "100"
    assert record["data_fields"][2]["subfields"][0]["value"] == "Cien años de soledad :"


def test_roundtrip_preserves_utf8_iso2709_record(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    render_result, render_payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None

    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": render_payload["result"]["record_b64"]},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    assert inspect_payload["result"]["record"] == record


def test_inspect_parses_hermetic_iso2709_fixture(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709(sample_record()))},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["result"]["record"] == sample_record()


def test_rendered_record_has_record_terminator(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": sample_record_control_only()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    record_bytes = unb64(payload["result"]["record_b64"])
    assert record_bytes.endswith(b"\x1d")


def test_inspect_marcxml_parses_record_root(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["result"]["record"] == sample_record()


def test_inspect_marcxml_parses_collection_wrapper(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml_collection()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["result"]["record"] == sample_record()


def test_render_marcxml_roundtrips_via_inspect_marcxml(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    render_result, render_payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": record},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None

    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": render_payload["result"]["marcxml"]},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    assert inspect_payload["result"]["record"] == record


def test_roundtrip_preserves_utf8_record_with_cjk_and_combining_marks(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record_cjk()
    render_result, render_payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None

    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": render_payload["result"]["record_b64"]},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    assert inspect_payload["result"]["record"] == record


def test_inspect_marcxml_accepts_xml_declaration_and_comment(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<!--bibliographic record-->"
        f"{sample_marcxml()}"
    )
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["result"]["record"] == sample_record()


def test_roundtrip_preserves_data_field_without_subfields(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"].append(
        {
            "tag": "500",
            "indicators": [" ", " "],
            "subfields": [],
        }
    )
    render_result, render_payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None

    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": render_payload["result"]["record_b64"]},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    assert inspect_payload["result"]["record"] == record
