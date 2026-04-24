from __future__ import annotations

import re

from gedcom_model import GedcomDataset, GedcomError, GedcomNode

_TAG_RE = re.compile(r"^(?:[A-Z][A-Z0-9_]*|_[A-Z0-9_]+)$")
_XREF_RE = re.compile(r"^@[^@\s]+@$")
_TOP_LEVEL_RECORD_TAGS = {
    "HEAD",
    "FAM",
    "INDI",
    "OBJE",
    "REPO",
    "SNOTE",
    "SOUR",
    "SUBM",
    "TRLR",
}
_XREF_REQUIRED_TOP_LEVEL_TAGS = {
    "FAM",
    "INDI",
    "OBJE",
    "REPO",
    "SNOTE",
    "SOUR",
    "SUBM",
}
_POINTER_TARGET_TAGS = {
    "ALIA": {"INDI"},
    "ANCI": {"SUBM"},
    "ASSO": {"INDI"},
    "CHIL": {"INDI"},
    "DESI": {"SUBM"},
    "FAMC": {"FAM"},
    "FAMS": {"FAM"},
    "HUSB": {"INDI"},
    "OBJE": {"OBJE"},
    "REPO": {"REPO"},
    "SNOTE": {"SNOTE"},
    "SOUR": {"SOUR"},
    "SUBM": {"SUBM"},
    "WIFE": {"INDI"},
}
_EVENT_Y_OR_NULL_TAGS = {
    "ADOP",
    "ANUL",
    "BAPM",
    "BARM",
    "BASM",
    "BIRT",
    "BLES",
    "BURI",
    "CENS",
    "CHR",
    "CHRA",
    "CONF",
    "CREM",
    "DEAT",
    "DIV",
    "DIVF",
    "EMIG",
    "ENGA",
    "FCOM",
    "GRAD",
    "IMMI",
    "MARB",
    "MARC",
    "MARL",
    "MARR",
    "MARS",
    "NATU",
    "ORDN",
    "PROB",
    "RETI",
    "WILL",
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

    xref_to_tag: dict[str, str] = {}
    for record in dataset.records:
        _validate_node(record, xref_to_tag, request_code=request_code, parent=None, top_level=True)
    for record in dataset.records:
        _validate_pointer_payloads(
            record,
            xref_to_tag,
            request_code=request_code,
            parent=None,
            top_level=True,
        )


def _parse_records(text: str) -> list[GedcomNode]:
    records: list[GedcomNode] = []
    stack: list[tuple[int, GedcomNode]] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        level, xref, tag, payload = _parse_line(raw_line, line_no)

        if not stack and level != 0:
            raise GedcomError(
                "invalid_document", "Top-level records must use level 0", line=line_no
            )
        if stack and level > stack[-1][0] + 1:
            raise GedcomError("invalid_document", "Illegal level jump", line=line_no)

        while stack and stack[-1][0] >= level:
            stack.pop()

        if tag == "CONT":
            if not stack or stack[-1][0] != level - 1:
                raise GedcomError(
                    "invalid_document", "CONT must continue the previous payload", line=line_no
                )
            parent = stack[-1][1]
            if parent.payload is None:
                raise GedcomError(
                    "invalid_document", "CONT requires a parent payload", line=line_no
                )
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
        raise GedcomError(
            "invalid_document", "GEDCOM delimiters must be single spaces", line=line_no
        )

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
            raise GedcomError(
                "invalid_document", "GEDCOM delimiters must be single spaces", line=line_no
            )
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
        and tag not in _POINTER_TARGET_TAGS
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
    xref_to_tag: dict[str, str],
    *,
    request_code: str,
    parent: GedcomNode | None,
    top_level: bool,
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
        if not top_level:
            raise GedcomError(request_code, "Only level-0 records may define xrefs")
        if node.xref in xref_to_tag:
            raise GedcomError(request_code, f"Duplicate xref {node.xref}")
        xref_to_tag[node.xref] = node.tag
    if node.payload is not None:
        _validate_text_characters(node.payload, request_code=request_code)

    _validate_contextual_rules(
        node,
        request_code=request_code,
        parent=parent,
        top_level=top_level,
    )

    for child in node.children:
        _validate_node(
            child,
            xref_to_tag,
            request_code=request_code,
            parent=node,
            top_level=False,
        )


def _validate_pointer_payloads(
    node: GedcomNode,
    xref_to_tag: dict[str, str],
    *,
    request_code: str,
    parent: GedcomNode | None,
    top_level: bool,
) -> None:
    expected_tags = _expected_pointer_targets(node, parent=parent, top_level=top_level)
    if expected_tags is not None:
        if node.payload is None or not _XREF_RE.match(node.payload):
            raise GedcomError(request_code, f"{node.tag} must use a pointer payload")
        if node.payload != "@VOID@":
            target_tag = xref_to_tag.get(node.payload)
            if target_tag is None:
                raise GedcomError(
                    request_code, f"Dangling pointer {node.payload} for tag {node.tag}"
                )
            if target_tag not in expected_tags:
                allowed = ", ".join(sorted(expected_tags))
                raise GedcomError(
                    request_code,
                    f"{node.tag} must point to one of: {allowed}",
                )
    elif node.payload is not None and _XREF_RE.match(node.payload):
        if node.tag.startswith("_"):
            if node.payload != "@VOID@" and node.payload not in xref_to_tag:
                raise GedcomError(
                    request_code, f"Dangling pointer {node.payload} for tag {node.tag}"
                )
    for child in node.children:
        _validate_pointer_payloads(
            child,
            xref_to_tag,
            request_code=request_code,
            parent=node,
            top_level=False,
        )


def _validate_contextual_rules(
    node: GedcomNode,
    *,
    request_code: str,
    parent: GedcomNode | None,
    top_level: bool,
) -> None:
    if top_level:
        if node.tag not in _TOP_LEVEL_RECORD_TAGS and not node.tag.startswith("_"):
            raise GedcomError(request_code, f"Unsupported top-level record tag {node.tag}")
        if node.tag.startswith("_"):
            return
        if node.tag in _XREF_REQUIRED_TOP_LEVEL_TAGS and node.xref is None:
            raise GedcomError(request_code, f"Top-level {node.tag} record requires an xref")
        if node.tag not in _XREF_REQUIRED_TOP_LEVEL_TAGS and node.xref is not None:
            raise GedcomError(request_code, f"Top-level {node.tag} record may not define an xref")
        if node.tag == "HEAD":
            if node.payload is not None:
                raise GedcomError(request_code, "HEAD may not have a payload")
            _require_child_count(node, "GEDC", 1, 1, request_code=request_code)
            _require_child_count(node, "PLAC", 0, 1, request_code=request_code)
        elif node.tag == "TRLR":
            if node.payload is not None:
                raise GedcomError(request_code, "TRLR may not have a payload")
        elif node.tag == "SUBM":
            if node.payload is not None:
                raise GedcomError(request_code, "SUBM record may not have a payload")
            _require_child_count(node, "NAME", 1, 1, request_code=request_code)
        elif node.tag == "REPO":
            if node.payload is not None:
                raise GedcomError(request_code, "REPO record may not have a payload")
            _require_child_count(node, "NAME", 1, 1, request_code=request_code)
        elif node.tag == "OBJE":
            if node.payload is not None:
                raise GedcomError(request_code, "OBJE record may not have a payload")
            _require_child_count(node, "FILE", 1, None, request_code=request_code)
            _require_child_count(node, "TITL", 0, 0, request_code=request_code)
        elif node.tag == "SOUR":
            if node.payload is not None:
                raise GedcomError(request_code, "SOUR record may not have a payload")
        elif node.tag == "FAM":
            if node.payload is not None:
                raise GedcomError(request_code, "FAM record may not have a payload")
        elif node.tag == "INDI":
            if node.payload is not None:
                raise GedcomError(request_code, "INDI record may not have a payload")
        elif node.tag == "SNOTE":
            if node.payload is None:
                raise GedcomError(request_code, "Shared-note records require a payload")

    if (
        node.tag in _EVENT_Y_OR_NULL_TAGS
        and parent is not None
        and parent.tag in {"INDI", "FAM"}
        and node.payload not in {None, "Y"}
    ):
        raise GedcomError(request_code, f"{node.tag} payload must be Y or empty")

    if node.tag == "GEDC":
        if node.payload is not None:
            raise GedcomError(request_code, "GEDC may not have a payload")
        _require_child_count(node, "VERS", 1, 1, request_code=request_code)
    elif node.tag == "CHAN":
        if node.payload is not None:
            raise GedcomError(request_code, "CHAN may not have a payload")
        _require_child_count(node, "DATE", 1, 1, request_code=request_code)
    elif node.tag == "CREA":
        if node.payload is not None:
            raise GedcomError(request_code, "CREA may not have a payload")
        _require_child_count(node, "DATE", 1, 1, request_code=request_code)
    elif node.tag == "ASSO":
        _require_child_count(node, "ROLE", 1, 1, request_code=request_code)
    elif node.tag == "PLAC":
        _require_child_count(node, "MAP", 0, 1, request_code=request_code)
        if _count_children(node, "MAP"):
            for child in node.children:
                if child.tag == "MAP":
                    _require_child_count(child, "LATI", 1, 1, request_code=request_code)
                    _require_child_count(child, "LONG", 1, 1, request_code=request_code)
    elif node.tag == "FILE":
        _require_child_count(node, "FORM", 1, 1, request_code=request_code)
    elif node.tag == "TRAN" and parent is not None:
        if parent.tag == "NAME":
            _require_child_count(node, "LANG", 1, 1, request_code=request_code)
        elif parent.tag == "PLAC":
            _require_child_count(node, "LANG", 1, 1, request_code=request_code)
        elif parent.tag == "FILE":
            _require_child_count(node, "FORM", 1, 1, request_code=request_code)
    elif node.tag in {"EVEN", "FACT"} and parent is not None and parent.tag in {"INDI", "FAM"}:
        _require_child_count(node, "TYPE", 1, 1, request_code=request_code)

    if parent is not None:
        if parent.tag == "HEAD" and node.tag == "PLAC":
            if node.payload is not None:
                raise GedcomError(request_code, "HEAD/PLAC may not have a payload")
            _require_child_count(node, "FORM", 1, 1, request_code=request_code)
        elif node.tag == "CHIL" and parent.tag != "FAM":
            raise GedcomError(request_code, f"{parent.tag}/CHIL is not permitted")
        elif parent.tag != "FAM" and node.tag in {"HUSB", "WIFE"}:
            if node.payload is not None:
                raise GedcomError(request_code, f"{parent.tag}/{node.tag} may not have a payload")
            _require_child_count(node, "AGE", 1, 1, request_code=request_code)


def _expected_pointer_targets(
    node: GedcomNode,
    *,
    parent: GedcomNode | None,
    top_level: bool,
) -> set[str] | None:
    if top_level:
        return None
    if node.tag in _POINTER_TARGET_TAGS and node.tag not in {"SOUR", "HUSB", "WIFE", "CHIL"}:
        return _POINTER_TARGET_TAGS[node.tag]
    if node.tag == "SOUR":
        if parent is not None and parent.tag == "HEAD":
            return None
        return _POINTER_TARGET_TAGS["SOUR"]
    if node.tag in {"HUSB", "WIFE", "CHIL"}:
        if parent is not None and parent.tag == "FAM":
            return _POINTER_TARGET_TAGS[node.tag]
        return None
    return None


def _count_children(node: GedcomNode, tag: str) -> int:
    return sum(1 for child in node.children if child.tag == tag)


def _require_child_count(
    node: GedcomNode,
    tag: str,
    minimum: int,
    maximum: int | None,
    *,
    request_code: str,
) -> None:
    count = _count_children(node, tag)
    if count < minimum:
        raise GedcomError(request_code, f"{node.tag} requires {tag}")
    if maximum is not None and count > maximum:
        raise GedcomError(request_code, f"{node.tag} permits at most {maximum} {tag}")


def _decode_payload(payload: str | None) -> str | None:
    if payload is None:
        return None
    if payload.startswith("@@"):
        return payload[1:]
    return payload


def _encode_payload(payload: str, tag: str) -> str:
    if payload.startswith("@") and tag not in _POINTER_TARGET_TAGS and not tag.startswith("_"):
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
            raise GedcomError(
                request_code, "GEDCOM text may not contain noncharacters U+FFFE/U+FFFF"
            )
