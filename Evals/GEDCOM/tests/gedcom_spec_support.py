from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

_STRUCTURES_PATH = Path(__file__).resolve().parent / "generated" / "gedcom_structure_grammar.json"
_CARDINALITY_RE = re.compile(
    r"^(?P<depth>n|\+\d+|0)\s+(?P<body>.+?)\s+\{(?P<min>\d+):(?P<max>\d+|M)\}(?:\s+.*)?$"
)
_RECORD_PRODUCTIONS = (
    "FAMILY_RECORD",
    "INDIVIDUAL_RECORD",
    "MULTIMEDIA_RECORD",
    "REPOSITORY_RECORD",
    "SHARED_NOTE_RECORD",
    "SOURCE_RECORD",
    "SUBMITTER_RECORD",
)
_EVENT_PRODUCTIONS = {
    "INDIVIDUAL_EVENT_STRUCTURE": "INDI",
    "FAMILY_EVENT_STRUCTURE": "FAM",
}


@dataclass(frozen=True, slots=True)
class StructureEntry:
    depth: int
    tag: str
    min_occurs: int
    max_occurs: int | None
    xref_token: str | None
    payload_token: str | None
    is_ref: bool


def _load_structures() -> dict[str, str]:
    payload = json.loads(_STRUCTURES_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("GEDCOM structure artifact must be a JSON object")
    payload_dict = cast(dict[object, object], payload)
    return {str(key): str(value) for key, value in payload_dict.items()}


def _parse_entry(line: str) -> StructureEntry:
    match = _CARDINALITY_RE.match(line.strip())
    if match is None:
        raise ValueError(f"Unrecognized GEDCOM structure line: {line!r}")

    depth_token = match.group("depth")
    depth = 0 if depth_token in {"n", "0"} else int(depth_token[1:])
    max_token = match.group("max")
    max_occurs = None if max_token == "M" else int(max_token)

    tokens = match.group("body").split()
    xref_token: str | None = None
    if tokens[0].startswith("@"):
        xref_token = tokens.pop(0)

    tag = tokens.pop(0)
    payload_token = tokens[0] if tokens else None
    return StructureEntry(
        depth=depth,
        tag=tag,
        min_occurs=int(match.group("min")),
        max_occurs=max_occurs,
        xref_token=xref_token,
        payload_token=payload_token,
        is_ref=tag.startswith("<<") and tag.endswith(">>"),
    )


def _entries_for_production(production_name: str) -> list[StructureEntry]:
    raw = _load_structures()[production_name]
    entries: list[StructureEntry] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped in {"[", "]", "|"}:
            continue
        entries.append(_parse_entry(stripped))
    return entries


def record_root_specs() -> list[StructureEntry]:
    return [_entries_for_production(name)[0] for name in _RECORD_PRODUCTIONS]


def y_or_null_event_cases() -> list[tuple[str, str]]:
    cases: set[tuple[str, str]] = set()
    for production_name, parent_tag in _EVENT_PRODUCTIONS.items():
        for entry in _entries_for_production(production_name):
            if entry.depth != 0:
                continue
            if entry.payload_token == "[Y|<NULL>]":
                cases.add((parent_tag, entry.tag))
    return sorted(cases)
