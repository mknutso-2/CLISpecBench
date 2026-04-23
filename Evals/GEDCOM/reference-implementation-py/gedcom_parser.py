from __future__ import annotations

import re

from gedcom_model import GedcomDataset, GedcomError, GedcomNode

_TAG_RE = re.compile(r"^(?:[A-Z][A-Z0-9_]*|_[A-Z0-9_]+)$")
_XREF_RE = re.compile(r"^@[^@\s]+@$")
_POINTER_TAGS = {
    "ALIA",
    "ANCI",
    "ASSO",
    "CHIL",
    "DESI",
    "FAMC",
    "FAMS",
    "HUSB",
    "OBJE",
    "REPO",
    "SNOTE",
    "SOUR",
    "SUBM",
    "WIFE",
}


def parse_gedcom_text(text: str) -> GedcomDataset:
    _validate_text_characters(text, request_code="invalid_document")
    records = _parse_records(text)
    dataset = GedcomDataset(records=records)
    validate_dataset(dataset)
    return dataset


def render_gedcom_text(dataset: GedcomDataset) -> str:
    validate_dataset(dataset, request_code="invalid_request")
    lines: list[str] = []
    for record in dataset.records:
        _render_node(record, 0, lines)
    return "\n".join(lines) + "\n"


def validate_dataset(dataset: GedcomDataset, *, request_code: str = "invalid_document") -> None:
    if not dataset.records:
        raise GedcomError(request_code, "Dataset must contain at least one record")
    if dataset.records[0].tag != "HEAD":
        raise GedcomError(request_code, "Dataset must begin with HEAD")
    if dataset.records[-1].tag != "TRLR":
        raise GedcomError(request_code, "Dataset must end with TRLR")
    if sum(1 for record in dataset.records if record.tag == "HEAD") != 1:
        raise GedcomError(request_code, "Dataset must contain exactly one HEAD")
    if sum(1 for record in dataset.records if record.tag == "TRLR") != 1:
        raise GedcomError(request_code, "Dataset must contain exactly one TRLR")
    if dataset.records[-1].children:
        raise GedcomError(request_code, "TRLR may not contain child structures")

    _validate_head_has_gedc_vers(dataset.records[0], request_code=request_code)

    seen_xrefs: set[str] = set()
    for record in dataset.records:
        _validate_node(record, seen_xrefs, request_code=request_code)
    for record in dataset.records:
        _validate_pointer_payloads(record, seen_xrefs, request_code=request_code)


def _parse_records(text: str) -> list[GedcomNode]:
    records: list[GedcomNode] = []
    stack: list[tuple[int, GedcomNode]] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        level, xref, tag, payload = _parse_line(raw_line, line_no)

        if not stack and level != 0:
            raise GedcomError("invalid_document", "Top-level records must use level 0", line=line_no)
        if stack and level > stack[-1][0] + 1:
            raise GedcomError("invalid_document", "Illegal level jump", line=line_no)

        while stack and stack[-1][0] >= level:
            stack.pop()

        if tag == "CONT":
            if not stack or stack[-1][0] != level - 1:
                raise GedcomError("invalid_document", "CONT must continue the previous payload", line=line_no)
            parent = stack[-1][1]
            if parent.payload is None:
                raise GedcomError("invalid_document", "CONT requires a parent payload", line=line_no)
            addition = "" if payload is None else payload
            parent.payload = f"{parent.payload}\n{addition}"
            continue
        if tag == "CONC":
            raise GedcomError("invalid_document", "GEDCOM 7 does not permit CONC", line=line_no)

        node = GedcomNode(tag=tag, xref=xref, payload=payload)
        if stack:
            stack[-1][1].children.append(node)
        else:
            records.append(node)
        stack.append((level, node))

    return records


def _parse_line(raw_line: str, line_no: int) -> tuple[int, str | None, str, str | None]:
    first_space = raw_line.find(" ")
    if first_space <= 0:
        raise GedcomError("invalid_document", f"Invalid GEDCOM line: {raw_line}", line=line_no)
    if first_space + 1 < len(raw_line) and raw_line[first_space + 1] == " ":
        raise GedcomError("invalid_document", "GEDCOM delimiters must be single spaces", line=line_no)

    level_text = raw_line[:first_space]
    if not level_text.isdigit():
        raise GedcomError("invalid_document", f"Invalid GEDCOM level: {raw_line}", line=line_no)
    level = int(level_text)

    rest = raw_line[first_space + 1 :]
    xref: str | None = None
    if rest.startswith("@"):
        second_space = rest.find(" ")
        if second_space <= 0:
            raise GedcomError("invalid_document", f"Invalid GEDCOM line: {raw_line}", line=line_no)
        xref = rest[:second_space]
        if not _XREF_RE.match(xref):
            raise GedcomError("invalid_document", f"Invalid xref syntax {xref!r}", line=line_no)
        if second_space + 1 < len(rest) and rest[second_space + 1] == " ":
            raise GedcomError("invalid_document", "GEDCOM delimiters must be single spaces", line=line_no)
        rest = rest[second_space + 1 :]

    tag_end = rest.find(" ")
    if tag_end == -1:
        tag = rest
        payload = None
    else:
        tag = rest[:tag_end]
        payload = rest[tag_end + 1 :]

    if not _TAG_RE.match(tag):
        raise GedcomError("invalid_document", f"Invalid GEDCOM tag {tag!r}", line=line_no)
    if (
        payload is not None
        and payload.startswith("@")
        and not payload.startswith("@@")
        and tag not in _POINTER_TAGS
        and not tag.startswith("_")
    ):
        raise GedcomError(
            "invalid_document",
            f"Payload for {tag} must escape a leading @ if it is not a pointer",
            line=line_no,
        )
    return level, xref, tag, _decode_payload(payload)


def _render_node(node: GedcomNode, level: int, lines: list[str]) -> None:
    line = f"{level} "
    if node.xref is not None:
        line += f"{node.xref} "
    line += node.tag

    if node.payload is not None:
        payload_lines = node.payload.split("\n")
        line += f" {_encode_payload(payload_lines[0], node.tag)}"
        lines.append(line)
        for continuation in payload_lines[1:]:
            cont_line = f"{level + 1} CONT"
            if continuation:
                cont_line += f" {_encode_payload(continuation, node.tag)}"
            lines.append(cont_line)
    else:
        lines.append(line)

    for child in node.children:
        _render_node(child, level + 1, lines)


def _validate_head_has_gedc_vers(head: GedcomNode, *, request_code: str) -> None:
    gedc_children = [child for child in head.children if child.tag == "GEDC"]
    if len(gedc_children) != 1:
        raise GedcomError(request_code, "HEAD must contain exactly one GEDC structure")
    vers_children = [child for child in gedc_children[0].children if child.tag == "VERS"]
    if len(vers_children) != 1 or vers_children[0].payload is None:
        raise GedcomError(request_code, "HEAD/GEDC must contain exactly one VERS payload")


def _validate_node(
    node: GedcomNode,
    seen_xrefs: set[str],
    *,
    request_code: str,
) -> None:
    if not _TAG_RE.match(node.tag):
        raise GedcomError(request_code, f"Invalid GEDCOM tag {node.tag!r}")
    if node.tag in {"CONT", "CONC"}:
        raise GedcomError(request_code, f"{node.tag} may not appear as a normal structure node")
    _validate_text_characters(node.tag, request_code=request_code)

    if node.xref is not None:
        _validate_text_characters(node.xref, request_code=request_code)
        if not _XREF_RE.match(node.xref):
            raise GedcomError(request_code, f"Invalid xref syntax {node.xref!r}")
        if node.xref in seen_xrefs:
            raise GedcomError(request_code, f"Duplicate xref {node.xref}")
        seen_xrefs.add(node.xref)
    if node.payload is not None:
        _validate_text_characters(node.payload, request_code=request_code)

    for child in node.children:
        _validate_node(child, seen_xrefs, request_code=request_code)


def _validate_pointer_payloads(
    node: GedcomNode,
    known_xrefs: set[str],
    *,
    request_code: str,
) -> None:
    if node.payload is not None and _XREF_RE.match(node.payload):
        if node.tag in _POINTER_TAGS or node.tag.startswith("_"):
            if node.payload != "@VOID@" and node.payload not in known_xrefs:
                raise GedcomError(request_code, f"Dangling pointer {node.payload} for tag {node.tag}")
    for child in node.children:
        _validate_pointer_payloads(child, known_xrefs, request_code=request_code)


def _decode_payload(payload: str | None) -> str | None:
    if payload is None:
        return None
    if payload.startswith("@@"):
        return payload[1:]
    return payload


def _encode_payload(payload: str, tag: str) -> str:
    if payload.startswith("@") and tag not in _POINTER_TAGS and not tag.startswith("_"):
        return f"@{payload}"
    return payload


def _validate_text_characters(text: str, *, request_code: str) -> None:
    for character in text:
        codepoint = ord(character)
        if character in {"\t", "\n", "\r"}:
            continue
        if codepoint < 0x20 or codepoint == 0x7F:
            raise GedcomError(request_code, "GEDCOM text may not contain C0 controls or DEL")
        if 0xD800 <= codepoint <= 0xDFFF:
            raise GedcomError(request_code, "GEDCOM text may not contain surrogate code points")
        if codepoint in {0xFFFE, 0xFFFF}:
            raise GedcomError(request_code, "GEDCOM text may not contain noncharacters U+FFFE/U+FFFF")
