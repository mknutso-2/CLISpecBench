from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from marc21_support import sample_record

from conftest import run_marc21, unb64

NS = "http://www.loc.gov/MARC21/slim"


def test_render_marcxml_uses_marc21_namespace(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": sample_record()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    root = ET.fromstring(payload["result"]["marcxml"])
    assert root.tag == f"{{{NS}}}record"


def test_render_marcxml_contains_control_and_data_fields(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": sample_record()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    root = ET.fromstring(payload["result"]["marcxml"])
    controlfield = root.find(f"{{{NS}}}controlfield[@tag='001']")
    assert controlfield is not None
    assert controlfield.text == "12345"
    datafield = root.find(f"{{{NS}}}datafield[@tag='245']")
    assert datafield is not None
    assert datafield.get("ind1") == "1"
    assert datafield.get("ind2") == "0"
    subfield = datafield.find(f"{{{NS}}}subfield[@code='a']")
    assert subfield is not None
    assert subfield.text == "Cien años de soledad :"


def test_render_iso2709_recomputes_leader_length_and_base_address(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["leader_template"] = "99999nam a2299999 a 4500"
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": record},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    record_bytes = unb64(payload["result"]["record_b64"])
    leader = record_bytes[:24].decode("ascii")
    assert leader[:5] == f"{len(record_bytes):05d}"
    assert leader[12:17].isdigit()
    assert leader[12:17] != "99999"


def test_render_marcxml_emits_normalized_leader_template(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["leader_template"] = "99999nam a2299999 a 4500"
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": record},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    root = ET.fromstring(payload["result"]["marcxml"])
    leader = root.find(f"{{{NS}}}leader")
    assert leader is not None
    assert leader.text == "00000nam a2200000 a 4500"


def test_render_marcxml_escapes_special_characters(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    record["data_fields"][2]["subfields"][0]["value"] = 'Fish & Chips <Vol. 1> "Special"'
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": record},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    marcxml = payload["result"]["marcxml"]
    assert "&amp;" in marcxml
    assert "&lt;Vol. 1&gt;" in marcxml
