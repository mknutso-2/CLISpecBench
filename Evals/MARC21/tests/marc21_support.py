from __future__ import annotations

import base64
from typing import Any

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


def encode_iso2709(record: dict[str, Any]) -> bytes:
    if record != sample_record():
        raise ValueError("encode_iso2709 only supports the canonical sample_record fixture")
    return _SAMPLE_RECORD_BYTES


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
        '<collection xmlns="http://www.loc.gov/MARC21/slim">'
        f"{sample_marcxml(record)}"
        "</collection>"
    )


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
