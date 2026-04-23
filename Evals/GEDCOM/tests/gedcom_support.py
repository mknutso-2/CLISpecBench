from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict, cast

_RECORD_FRAGMENTS_PATH = Path(__file__).resolve().parent / "generated" / "gedcom_examples.json"
_OFFICIAL_RECORD_FRAGMENT_IDS = {
    "cb5",
    "cb8",
    "cb9",
    "cb12",
    "cb13",
    "cb14",
    "cb16",
    "cb17",
    "cb39",
    "cb43",
    "cb48",
    "cb71",
    "cb79",
    "cb80",
    "cb82",
    "cb83",
    "cb97",
    "cb98",
    "cb102",
    "cb103",
    "cb104",
}
_POINTER_LINE_RE = re.compile(r"^\d+\s+(?:(@[^@\s]+@)\s+)?([A-Z_][A-Z0-9_]+)(?:\s+(@[^@\s]+@))?$")
_DEFINED_XREF_RE = re.compile(r"^\d+\s+(@[^@\s]+@)\s+[A-Z_][A-Z0-9_]+(?:\s+.*)?$")
_DEFAULT_RECORD_TAG_BY_POINTER_TAG = {
    "ALIA": "INDI",
    "ANCI": "SUBM",
    "ASSO": "INDI",
    "CHIL": "INDI",
    "DESI": "SUBM",
    "FAMC": "FAM",
    "FAMS": "FAM",
    "HUSB": "INDI",
    "OBJE": "OBJE",
    "REPO": "REPO",
    "SNOTE": "SNOTE",
    "SOUR": "SOUR",
    "SUBM": "SUBM",
    "WIFE": "INDI",
}


class ExpectedNode(TypedDict):
    tag: str
    xref: str | None
    payload: str | None
    children: list[ExpectedNode]


class ExpectedDataset(TypedDict):
    records: list[ExpectedNode]


class GeneratedExample(TypedDict, total=False):
    section_id: str
    source_block_id: str
    text: str


def node(
    tag: str,
    payload: str | None = None,
    *,
    xref: str | None = None,
    children: list[ExpectedNode] | None = None,
) -> ExpectedNode:
    return {
        "tag": tag,
        "xref": xref,
        "payload": payload,
        "children": [] if children is None else children,
    }


def sample_gedcom_text() -> str:
    return "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "1 SOUR CLISpecBench",
            "1 DATE 21 APR 2026",
            "2 TIME 13:45:00",
            "0 @U1@ SUBM",
            "1 NAME Example Researcher",
            "1 EMAIL researcher@example.com",
            "1 NOTE Lead genealogist",
            "2 CONT Chicago office",
            "0 @N1@ SNOTE Shared note line 1",
            "1 CONT Shared note line 2",
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "2 GIVN John",
            "2 SURN Doe",
            "1 SEX M",
            "1 NOTE @@handle",
            "1 BIRT Y",
            "2 DATE 1 JAN 1900",
            "2 PLAC Boston",
            "2 SNOTE @N1@",
            "1 FAMS @F1@",
            "0 @I2@ INDI",
            "1 NAME Jane /Doe/",
            "1 FAMS @F1@",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 NOTE Household record",
            "2 CONT for downtown apartment",
            "0 TRLR",
            "",
        ]
    )


def sample_dataset() -> ExpectedDataset:
    return {
        "records": [
            node(
                "HEAD",
                children=[
                    node("GEDC", children=[node("VERS", "7.0")]),
                    node("SOUR", "CLISpecBench"),
                    node("DATE", "21 APR 2026", children=[node("TIME", "13:45:00")]),
                ],
            ),
            node(
                "SUBM",
                xref="@U1@",
                children=[
                    node("NAME", "Example Researcher"),
                    node("EMAIL", "researcher@example.com"),
                    node("NOTE", "Lead genealogist\nChicago office"),
                ],
            ),
            node("SNOTE", 'Shared note line 1\nShared note line 2', xref="@N1@"),
            node(
                "INDI",
                xref="@I1@",
                children=[
                    node(
                        "NAME",
                        "John /Doe/",
                        children=[node("GIVN", "John"), node("SURN", "Doe")],
                    ),
                    node("SEX", "M"),
                    node("NOTE", "@handle"),
                    node(
                        "BIRT",
                        "Y",
                        children=[
                            node("DATE", "1 JAN 1900"),
                            node("PLAC", "Boston"),
                            node("SNOTE", "@N1@"),
                        ],
                    ),
                    node("FAMS", "@F1@"),
                ],
            ),
            node(
                "INDI",
                xref="@I2@",
                children=[
                    node("NAME", "Jane /Doe/"),
                    node("FAMS", "@F1@"),
                ],
            ),
            node(
                "FAM",
                xref="@F1@",
                children=[
                    node("HUSB", "@I1@"),
                    node("WIFE", "@I2@"),
                    node("NOTE", "Household record\nfor downtown apartment"),
                ],
            ),
            node("TRLR"),
        ]
    }


def minimal_header_text() -> str:
    return "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
        ]
    )


def wrap_record_fragment(fragment_text: str) -> str:
    lines = fragment_text.strip().splitlines()
    if not lines:
        raise AssertionError("Record fragment may not be empty")

    if lines[0] == "0 HEAD":
        body_lines = _ensure_head_has_gedc_vers(lines)
        return _append_stub_records(body_lines)

    body_lines = [*minimal_header_text().splitlines(), *lines]
    return _append_stub_records(body_lines)


def official_record_fragments() -> list[tuple[str, str]]:
    payload = json.loads(_RECORD_FRAGMENTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise AssertionError("GEDCOM examples artifact must be a list")

    payload_list = cast(list[object], payload)
    entries: list[tuple[str, str]] = []
    for item in payload_list:
        if not isinstance(item, dict):
            continue
        example = cast(GeneratedExample, item)
        source_block_id = example.get("source_block_id")
        section_id = example.get("section_id")
        text = example.get("text")
        if (
            not isinstance(source_block_id, str)
            or source_block_id not in _OFFICIAL_RECORD_FRAGMENT_IDS
        ):
            continue
        if not isinstance(section_id, str) or not isinstance(text, str):
            continue
        entries.append((f"{section_id}::{source_block_id}", text))
    return entries


def _ensure_head_has_gedc_vers(lines: list[str]) -> list[str]:
    if any(line == "1 GEDC" for line in lines):
        return lines
    return [lines[0], "1 GEDC", "2 VERS 7.0", *lines[1:]]


def _append_stub_records(lines: list[str]) -> str:
    defined_xrefs: set[str] = set()
    referenced_xrefs: list[tuple[str, str]] = []

    for line in lines:
        defined_match = _DEFINED_XREF_RE.match(line)
        if defined_match is not None:
            defined_xrefs.add(defined_match.group(1))
        match = _POINTER_LINE_RE.match(line)
        if match is None:
            continue
        tag = match.group(2)
        payload_xref = match.group(3)
        if payload_xref is not None:
            referenced_xrefs.append((tag, payload_xref))

    stub_lines: list[str] = []
    for tag, xref in referenced_xrefs:
        if xref == "@VOID@" or xref in defined_xrefs:
            continue
        record_tag = _DEFAULT_RECORD_TAG_BY_POINTER_TAG.get(tag, "INDI")
        stub_lines.append(f"0 {xref} {record_tag}")
        defined_xrefs.add(xref)

    return "\n".join([*lines, *stub_lines, "0 TRLR"]) + "\n"
