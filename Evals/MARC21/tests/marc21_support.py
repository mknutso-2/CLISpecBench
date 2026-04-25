from __future__ import annotations

import base64
from typing import Any
from xml.etree import ElementTree as ET

FT = b"\x1e"
RT = b"\x1d"
SF = b"\x1f"
NS = "http://www.loc.gov/MARC21/slim"

_SAMPLE_RECORD_B64 = (
    "MDAzMDRuYW0gYTIyMDAxMDkgYSA0NTAwMDAxMDAwNjAwMDAwMDA1MDAxNzAwMDA2MDA4MDA0MTAwMDIzMDQwMDAx"
    "MzAwMDY0MTAwMDAzMTAwMDc3MjQ1MDA1NTAwMTA4NjUwMDAzMTAwMTYzHjEyMzQ1HjIwMjYwNDIxMTIwMDAwLjAe"
    "MjYwNDIxczIwMjYgICAgaWx1ICAgICAgICAgICAwMDAgMCBlbmcgZB4gIB9hRExDH2JlbmceMSAfYUdhcmPDrWEg"
    "TcOhcnF1ZXosIEdhYnJpZWwuHjEwH2FDaWVuIGHDsW9zIGRlIHNvbGVkYWQgOh9jR2FicmllbCBHYXJjw61hIE3D"
    "oXJxdWV6Lh4gMB9hTWFnaWMgcmVhbGlzbSAoTGl0ZXJhdHVyZSkeHQ=="
)

_SAMPLE_RECORD_BYTES = base64.b64decode(_SAMPLE_RECORD_B64.encode("ascii"))
assert _SAMPLE_RECORD_BYTES.endswith(b"\x1d")
assert len(_SAMPLE_RECORD_BYTES) == 304


def sample_record() -> dict[str, Any]:
    return {
        "leader_template": "00000nam a2200000 a 4500",
        "control_fields": [
            {"tag": "001", "value": "12345"},
            {"tag": "005", "value": "20260421120000.0"},
            {"tag": "008", "value": "260421s2026    ilu           000 0 eng d"},
        ],
        "data_fields": [
            {
                "tag": "040",
                "indicators": [" ", " "],
                "subfields": [
                    {"code": "a", "value": "DLC"},
                    {"code": "b", "value": "eng"},
                ],
            },
            {
                "tag": "100",
                "indicators": ["1", " "],
                "subfields": [
                    {"code": "a", "value": "García Márquez, Gabriel."},
                ],
            },
            {
                "tag": "245",
                "indicators": ["1", "0"],
                "subfields": [
                    {"code": "a", "value": "Cien años de soledad :"},
                    {"code": "c", "value": "Gabriel García Márquez."},
                ],
            },
            {
                "tag": "650",
                "indicators": [" ", "0"],
                "subfields": [
                    {"code": "a", "value": "Magic realism (Literature)"},
                ],
            },
        ],
    }


def sample_record_control_only() -> dict[str, Any]:
    record = sample_record()
    record["data_fields"] = []
    return record


def sample_record_cjk() -> dict[str, Any]:
    record = sample_record()
    record["data_fields"][1]["subfields"] = [
        {"code": "a", "value": "李白, Li Bai."},
    ]
    record["data_fields"][2]["subfields"] = [
        {"code": "a", "value": "Cafe\u0301 y te\u0301 :"},
        {"code": "c", "value": "山田太郎."},
    ]
    return record


def encode_iso2709_record(record: dict[str, Any]) -> bytes:
    field_payloads: list[bytes] = []
    directory_entries: list[bytes] = []
    field_start = 0

    for field in record["control_fields"]:
        payload = field["value"].encode("utf-8") + FT
        field_payloads.append(payload)
        directory_entries.append(
            field["tag"].encode("ascii") + f"{len(payload):04d}{field_start:05d}".encode("ascii")
        )
        field_start += len(payload)

    for field in record["data_fields"]:
        body = bytearray()
        body.extend(field["indicators"][0].encode("ascii"))
        body.extend(field["indicators"][1].encode("ascii"))
        for subfield in field["subfields"]:
            body.extend(SF)
            body.extend(subfield["code"].encode("ascii"))
            body.extend(subfield["value"].encode("utf-8"))
        body.extend(FT)
        payload = bytes(body)
        field_payloads.append(payload)
        directory_entries.append(
            field["tag"].encode("ascii") + f"{len(payload):04d}{field_start:05d}".encode("ascii")
        )
        field_start += len(payload)

    directory = b"".join(directory_entries) + FT
    base_address = 24 + len(directory)
    body = directory + b"".join(field_payloads) + RT
    record_length = 24 + len(body)
    leader = _leader_for_transport(record["leader_template"], record_length, base_address)
    return leader.encode("ascii") + body


def encode_iso2709(record: dict[str, Any]) -> bytes:
    if record != sample_record():
        raise ValueError("encode_iso2709 only supports the canonical sample_record fixture")
    return _SAMPLE_RECORD_BYTES


def decode_iso2709_record(data: bytes) -> dict[str, Any]:
    if len(data) < 25:
        raise AssertionError("ISO2709 record is too short")
    if not data.endswith(RT):
        raise AssertionError("ISO2709 record terminator is missing")
    leader = data[:24].decode("ascii")
    base_address = int(leader[12:17])
    if data[base_address - 1 : base_address] != FT:
        raise AssertionError("ISO2709 directory terminator is missing")
    directory = data[24 : base_address - 1]
    if len(directory) % 12 != 0:
        raise AssertionError("ISO2709 directory length is not a multiple of 12")

    control_fields: list[dict[str, str]] = []
    data_fields: list[dict[str, Any]] = []
    for offset in range(0, len(directory), 12):
        entry = directory[offset : offset + 12]
        tag = entry[:3].decode("ascii")
        field_length = int(entry[3:7].decode("ascii"))
        field_start = int(entry[7:12].decode("ascii"))
        field_bytes = data[base_address + field_start : base_address + field_start + field_length]
        if not field_bytes.endswith(FT):
            raise AssertionError(f"ISO2709 field {tag} lacks field terminator")
        payload = field_bytes[:-1]
        if "001" <= tag <= "009":
            control_fields.append({"tag": tag, "value": payload.decode("utf-8")})
            continue
        pieces = payload[2:].split(SF)[1:]
        data_fields.append(
            {
                "tag": tag,
                "indicators": [chr(payload[0]), chr(payload[1])],
                "subfields": [
                    {"code": chr(piece[0]), "value": piece[1:].decode("utf-8")} for piece in pieces
                ],
            }
        )
    return {
        "leader_template": _normalize_leader_template(leader),
        "control_fields": control_fields,
        "data_fields": data_fields,
    }


def sample_marcxml(record: dict[str, Any] | None = None) -> str:
    current = sample_record() if record is None else record
    control_fields = "".join(
        f'<controlfield tag="{field["tag"]}">{_xml_escape(field["value"])}</controlfield>'
        for field in current["control_fields"]
    )
    data_fields = "".join(
        "<datafield "
        f'tag="{field["tag"]}" '
        f'ind1="{_xml_escape(field["indicators"][0])}" '
        f'ind2="{_xml_escape(field["indicators"][1])}">'
        + "".join(
            f'<subfield code="{subfield["code"]}">{_xml_escape(subfield["value"])}</subfield>'
            for subfield in field["subfields"]
        )
        + "</datafield>"
        for field in current["data_fields"]
    )
    return (
        '<record xmlns="http://www.loc.gov/MARC21/slim">'
        f"<leader>{current['leader_template']}</leader>"
        f"{control_fields}{data_fields}"
        "</record>"
    )


def sample_marcxml_collection(record: dict[str, Any] | None = None) -> str:
    return (
        f'<collection xmlns="http://www.loc.gov/MARC21/slim">{sample_marcxml(record)}</collection>'
    )


def decode_marcxml_record(text: str) -> dict[str, Any]:
    root = ET.fromstring(text)
    if root.tag != f"{{{NS}}}record":
        raise AssertionError("MARCXML root is not a record element")
    leader_node = root.find(f"{{{NS}}}leader")
    if leader_node is None or leader_node.text is None:
        raise AssertionError("MARCXML record lacks a leader")

    control_fields = [
        {"tag": node.get("tag"), "value": node.text or ""}
        for node in root.findall(f"{{{NS}}}controlfield")
    ]
    data_fields: list[dict[str, Any]] = []
    for node in root.findall(f"{{{NS}}}datafield"):
        data_fields.append(
            {
                "tag": node.get("tag"),
                "indicators": [node.get("ind1"), node.get("ind2")],
                "subfields": [
                    {"code": subfield.get("code"), "value": subfield.text or ""}
                    for subfield in node.findall(f"{{{NS}}}subfield")
                ],
            }
        )
    return {
        "leader_template": _normalize_leader_template(leader_node.text),
        "control_fields": control_fields,
        "data_fields": data_fields,
    }


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _leader_for_transport(template: str, record_length: int, base_address: int) -> str:
    leader = list(template)
    leader[:5] = list(f"{record_length:05d}")
    leader[12:17] = list(f"{base_address:05d}")
    return "".join(leader)


def _normalize_leader_template(leader: str) -> str:
    chars = list(leader)
    chars[:5] = list("00000")
    chars[12:17] = list("00000")
    return "".join(chars)
