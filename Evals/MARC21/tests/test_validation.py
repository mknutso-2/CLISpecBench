from __future__ import annotations

from pathlib import Path

from marc21_support import encode_iso2709, sample_marcxml, sample_record, sample_record_control_only

from conftest import b64, run_marc21


def test_inspect_rejects_missing_record_terminator(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bad_record = encode_iso2709(sample_record())[:-1]
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bad_record)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_leader_record_length_mismatch(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[:5] = b"99999"
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_leader_base_address_outside_record(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[12:17] = b"99999"
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_render_accepts_leader_position_09_blank_marc8_indicator(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record_control_only()
    leader = list(record["leader_template"])
    leader[9] = " "
    record["leader_template"] = "".join(leader)
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["error"] is None


def test_render_rejects_leader_positions_10_and_11_not_equal_22(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["leader_template"] = "00000nam a1200000 a 4500"
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_inspect_rejects_leader_positions_20_to_23_not_equal_4500(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[20:24] = b"9999"
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_missing_directory_terminator(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    base_address = int(raw[12:17].decode("ascii"))
    raw[base_address - 1] = 0x20
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_directory_length_not_divisible_by_12(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = b"00039nam a2200036 a 4500" + b"00100010000" + b"\x1e" + b"A\x1e" + b"\x1d"
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(raw)},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_field_range_outside_record(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[31:36] = b"99999"
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_data_field_without_subfield_delimiter(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    location = raw.index(b"\x1f", 24)
    raw[location] = ord("X")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_render_rejects_control_field_tag_outside_00x(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["control_fields"] = [{"tag": "245", "value": "bad"}]
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_control_field_value_with_marc_control_character(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["control_fields"][0]["value"] = "abc\x1e"
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_data_field_with_bad_indicator(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"][0]["indicators"] = ["AB", " "]
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_data_field_subfield_code_not_lowercase_or_digit(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"][0]["subfields"] = [{"code": "A", "value": "bad"}]
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_data_field_subfield_code_punctuation(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"][0]["subfields"] = [{"code": "-", "value": "bad"}]
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_subfield_value_with_marc_control_character(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"][0]["subfields"][0]["value"] = "bad\x1f"
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_data_field_subfield_code_with_multiple_characters(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"][0]["subfields"] = [{"code": "ab", "value": "bad"}]
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_inspect_rejects_directory_entry_with_non_digit_field_length(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[27] = ord("A")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_directory_entry_with_non_digit_field_start(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[31] = ord("A")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_directory_entry_with_non_digit_tag(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    raw[24] = ord("A")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_subfield_code_punctuation(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    location = raw.index(b"\x1f", 24)
    raw[location + 1] = ord("-")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_non_utf8_control_field_payload(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    first_field_start = int(raw[31:36].decode("ascii"))
    base_address = int(raw[12:17].decode("ascii"))
    raw[base_address + first_field_start] = 0xFF
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_rejects_non_utf8_subfield_value(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    raw = bytearray(encode_iso2709(sample_record()))
    location = raw.index("Cien años de soledad :".encode())
    raw[location] = 0xFF
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(bytes(raw))},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_render_rejects_field_length_overflow(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["control_fields"] = [{"tag": "001", "value": "A" * 10000}]
    record["data_fields"] = []
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_record_length_overflow(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["control_fields"] = [{"tag": "001", "value": "12345"}]
    record["data_fields"] = [
        {
            "tag": "245",
            "indicators": ["1", "0"],
            "subfields": [{"code": "a", "value": "X" * 20}],
        }
        for _ in range(3500)
    ]
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_inspect_marcxml_rejects_wrong_namespace(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = sample_marcxml().replace("http://www.loc.gov/MARC21/slim", "http://example.com")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_missing_leader(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = sample_marcxml().replace("<leader>00000nam a2200000 a 4500</leader>", "")
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_collection_with_multiple_records(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = (
        '<collection xmlns="http://www.loc.gov/MARC21/slim">'
        f"{sample_marcxml()}{sample_marcxml()}"
        "</collection>"
    )
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_datafield_missing_indicator_attribute(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = sample_marcxml().replace(' ind2="0"', "", 1)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_controlfield_tag_outside_001_to_009(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = sample_marcxml().replace('<controlfield tag="001">', '<controlfield tag="245">', 1)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_datafield_tag_inside_control_range(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = sample_marcxml().replace('<datafield tag="245"', '<datafield tag="008"', 1)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_non_subfield_child(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = sample_marcxml().replace("</datafield>", "<junk/></datafield>", 1)
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"


def test_inspect_marcxml_rejects_controlfield_after_datafield(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    marcxml = (
        '<record xmlns="http://www.loc.gov/MARC21/slim">'
        "<leader>00000nam a2200000 a 4500</leader>"
        '<datafield tag="245" ind1="1" ind2="0"><subfield code="a">Title</subfield></datafield>'
        '<controlfield tag="001">123</controlfield>'
        "</record>"
    )
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": marcxml},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_record"
