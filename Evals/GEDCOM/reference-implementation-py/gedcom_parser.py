from __future__ import annotations

import base64
import binascii
import io
import json
import re
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlsplit

from gedcom_model import GedcomDataset, GedcomError, GedcomNode

_DATA_RULES_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "generated" / "gedcom_data_rules.json"
)
_TAG_RE = re.compile(r"^(?:[A-Z][A-Z0-9_]*|_[A-Z0-9_]+)$")
_XREF_RE = re.compile(r"^@[^@\s]+@$")
_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_MEDIA_TYPE_RE = re.compile(
    r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+/[!#$%&'*+\-.^_`|~0-9A-Za-z]+"
    r"(?:\s*;\s*[!#$%&'*+\-.^_`|~0-9A-Za-z]+="
    r'(?:[!#$%&\'*+\-.^_`|~0-9A-Za-z]+|"[^"\r\n]*"))*$'
)
_TIME_RE = re.compile(
    r"^(?P<hour>[0-9]|[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9])"
    r"(?::(?P<second>[0-5][0-9])(?:\.[0-9]+)?)?Z?$"
)
_AGE_RE = re.compile(r"^(?:[<>] )?(?:(?:[0-9]+y)(?: [0-9]+m)?(?: [0-9]+w)?(?: [0-9]+d)?|(?:[0-9]+m)(?: [0-9]+w)?(?: [0-9]+d)?|(?:[0-9]+w)(?: [0-9]+d)?|(?:[0-9]+d))$")
_URL_WHITESPACE_RE = re.compile(r"\s")
_GEDCOM_DATASET_ENTRY = "gedcom.ged"
_SUPPORTED_FILE_SCHEMES = {"", "file", "ftp", "http", "https"}
_MONTHS_BY_CALENDAR = {
    "GREGORIAN": {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"},
    "JULIAN": {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"},
    "FRENCH_R": {"VEND", "BRUM", "FRIM", "NIVO", "PLUV", "VENT", "GERM", "FLOR", "PRAI", "MESS", "THER", "FRUC", "COMP"},
    "HEBREW": {"TSH", "CSH", "KSL", "TVT", "SHV", "ADR", "ADS", "NSN", "IYR", "SVN", "TMZ", "AAV", "ELL"},
}
_DATE_RESTRICT_WORDS = {"FROM", "TO", "BET", "AND", "BEF", "AFT", "ABT", "CAL", "EST"}
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


@lru_cache(maxsize=1)
def _data_rules() -> dict[str, object]:
    try:
        return cast(dict[str, object], json.loads(_DATA_RULES_PATH.read_text(encoding="utf-8")))
    except OSError:
        return {"enumerations": {}}


def _enum_values(name: str, fallback: set[str]) -> set[str]:
    enumerations_obj = _data_rules().get("enumerations")
    if not isinstance(enumerations_obj, dict):
        return fallback
    enumerations = cast(dict[str, object], enumerations_obj)
    values_obj = enumerations.get(name)
    if not isinstance(values_obj, list):
        return fallback
    values = cast(list[object], values_obj)
    return {value for value in values if isinstance(value, str)} or fallback
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


def parse_gedzip_base64(payload: str) -> tuple[GedcomDataset, dict[str, str]]:
    try:
        archive_bytes = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise GedcomError("invalid_document", f"GEDZIP payload is not valid base64: {exc}") from exc

    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except zipfile.BadZipFile as exc:
        raise GedcomError("invalid_document", f"GEDZIP payload is not a ZIP archive: {exc}") from exc

    with archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise GedcomError("invalid_document", "GEDZIP archive contains duplicate entry names")
        if _GEDCOM_DATASET_ENTRY not in names:
            raise GedcomError("invalid_document", "GEDZIP archive must contain gedcom.ged")
        try:
            text = archive.read(_GEDCOM_DATASET_ENTRY).decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise GedcomError("invalid_document", f"gedcom.ged is not valid UTF-8: {exc}") from exc

        dataset = parse_gedcom_text(text)
        attachment_names = {name for name in names if name != _GEDCOM_DATASET_ENTRY and not name.endswith("/")}
        _validate_gedzip_local_file_entries(dataset, attachment_names, request_code="invalid_document")
        attachments = {
            name: base64.b64encode(archive.read(name)).decode("ascii")
            for name in sorted(attachment_names)
        }
    return dataset, attachments


def render_gedcom_text(dataset: GedcomDataset) -> str:
    validate_dataset(dataset, request_code="invalid_request")
    lines: list[str] = []
    for record in dataset.records:
        _render_node(record, 0, lines)
    return "\n".join(lines) + "\n"


def render_gedzip_base64(dataset: GedcomDataset, attachments: dict[str, str]) -> str:
    text = render_gedcom_text(dataset)
    decoded_attachments: dict[str, bytes] = {}
    for name, encoded in attachments.items():
        _validate_zip_entry_name(name, request_code="invalid_request")
        try:
            decoded_attachments[name] = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise GedcomError(
                "invalid_request", f"Attachment {name!r} is not valid base64: {exc}"
            ) from exc

    _validate_gedzip_local_file_entries(
        dataset,
        set(decoded_attachments),
        request_code="invalid_request",
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(_GEDCOM_DATASET_ENTRY, text.encode("utf-8"))
        for name in sorted(decoded_attachments):
            archive.writestr(name, decoded_attachments[name])
    return base64.b64encode(buffer.getvalue()).decode("ascii")


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
    _validate_payload_datatype(node, request_code=request_code, parent=parent)

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


def _validate_payload_datatype(
    node: GedcomNode,
    *,
    request_code: str,
    parent: GedcomNode | None,
) -> None:
    payload = node.payload
    if node.tag == "VERS" and parent is not None and parent.tag == "GEDC":
        if payload not in {"7.0", "7.0.0"}:
            raise GedcomError(request_code, "GEDC/VERS must identify GEDCOM 7.0")
    elif node.tag == "DATE":
        if parent is not None and parent.tag in {"CHAN", "CREA"}:
            if payload is None or not _is_date_exact(payload):
                raise GedcomError(request_code, "CHAN/CREA DATE requires an exact Gregorian date")
        elif payload is not None and not _is_date_value(payload):
            raise GedcomError(request_code, f"Invalid GEDCOM date payload {payload!r}")
    elif node.tag == "TIME":
        if payload is None or _TIME_RE.match(payload) is None:
            raise GedcomError(request_code, f"Invalid GEDCOM time payload {payload!r}")
    elif node.tag == "AGE":
        if payload is not None and _AGE_RE.match(payload) is None:
            raise GedcomError(request_code, f"Invalid GEDCOM age payload {payload!r}")
    elif node.tag == "LANG":
        if payload is None or _LANGUAGE_RE.match(payload) is None:
            raise GedcomError(request_code, f"Invalid GEDCOM language payload {payload!r}")
    elif node.tag in {"MIME"}:
        _validate_media_type_payload(payload, request_code=request_code, tag=node.tag)
    elif node.tag == "FORM" and parent is not None and parent.tag in {"FILE", "TRAN"}:
        _validate_media_type_payload(payload, request_code=request_code, tag=node.tag)
    elif node.tag == "FILE":
        _validate_file_path_payload(payload, request_code=request_code)
    elif node.tag == "WWW":
        _validate_web_payload(payload, request_code=request_code)
    elif node.tag == "TAG":
        _validate_tag_definition_payload(payload, request_code=request_code)
    elif node.tag == "LATI":
        _validate_coordinate_payload(payload, "LATI", request_code=request_code)
    elif node.tag == "LONG":
        _validate_coordinate_payload(payload, "LONG", request_code=request_code)
    elif node.tag == "SEX":
        _validate_enum_payload(payload, "SEX", {"M", "F", "X", "U"}, request_code=request_code)
    elif node.tag == "ADOP" and parent is not None and parent.tag == "FAMC":
        _validate_enum_payload(payload, "ADOP", {"HUSB", "WIFE", "BOTH"}, request_code=request_code)
    elif node.tag == "PEDI":
        _validate_enum_payload(
            payload,
            "PEDI",
            {"ADOPTED", "BIRTH", "FOSTER", "SEALING", "OTHER"},
            request_code=request_code,
        )
    elif node.tag == "MEDI":
        _validate_enum_payload(
            payload,
            "MEDI",
            {
                "AUDIO",
                "BOOK",
                "CARD",
                "ELECTRONIC",
                "FICHE",
                "FILM",
                "MAGAZINE",
                "MANUSCRIPT",
                "MAP",
                "NEWSPAPER",
                "PHOTO",
                "TOMBSTONE",
                "VIDEO",
                "OTHER",
            },
            request_code=request_code,
        )
    elif node.tag == "QUAY":
        _validate_enum_payload(payload, "QUAY", {"0", "1", "2", "3"}, request_code=request_code)
    elif node.tag == "RESN":
        _validate_enum_list_payload(
            payload,
            "RESN",
            {"CONFIDENTIAL", "LOCKED", "PRIVACY"},
            request_code=request_code,
        )
    elif node.tag == "ROLE":
        _validate_enum_payload(
            payload,
            "ROLE",
            {
                "CHIL",
                "CLERGY",
                "FATH",
                "FRIEND",
                "GODP",
                "HUSB",
                "MOTH",
                "MULTIPLE",
                "NGHBR",
                "OFFICIATOR",
                "PARENT",
                "SPOU",
                "WIFE",
                "WITN",
                "OTHER",
            },
            request_code=request_code,
        )
    elif node.tag == "TYPE" and parent is not None and parent.tag == "NAME":
        _validate_enum_payload(
            payload,
            "NAME-TYPE",
            {"AKA", "BIRTH", "IMMIGRANT", "MAIDEN", "MARRIED", "PROFESSIONAL", "OTHER"},
            request_code=request_code,
        )


def _validate_media_type_payload(payload: str | None, *, request_code: str, tag: str) -> None:
    if payload is None or _MEDIA_TYPE_RE.match(payload) is None:
        raise GedcomError(request_code, f"{tag} must contain a valid media type")


def _validate_file_path_payload(payload: str | None, *, request_code: str) -> None:
    if payload is None or payload == "":
        raise GedcomError(request_code, "FILE must contain a file path payload")
    _local_file_zip_name(payload, request_code=request_code)


def _validate_web_payload(payload: str | None, *, request_code: str) -> None:
    if payload is None or _URL_WHITESPACE_RE.search(payload):
        raise GedcomError(request_code, "WWW must contain a valid URL")
    parts = urlsplit(payload)
    if parts.scheme not in {"http", "https", "ftp"} or not parts.netloc:
        raise GedcomError(request_code, "WWW must contain an absolute web URL")


def _validate_tag_definition_payload(payload: str | None, *, request_code: str) -> None:
    if payload is None:
        raise GedcomError(request_code, "TAG requires an extension tag and URI")
    pieces = payload.split(" ", 1)
    if len(pieces) != 2 or not pieces[0].startswith("_") or not _TAG_RE.match(pieces[0]):
        raise GedcomError(request_code, "TAG must begin with an extension tag")
    _validate_uri_reference(pieces[1], request_code=request_code, label="TAG URI")


def _validate_uri_reference(payload: str, *, request_code: str, label: str) -> None:
    if payload == "" or _URL_WHITESPACE_RE.search(payload):
        raise GedcomError(request_code, f"{label} must be a URI reference")
    parts = urlsplit(payload)
    if parts.scheme and not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*$", parts.scheme):
        raise GedcomError(request_code, f"{label} has an invalid URI scheme")


def _validate_coordinate_payload(payload: str | None, tag: str, *, request_code: str) -> None:
    if payload is None or len(payload) < 2:
        raise GedcomError(request_code, f"{tag} requires a coordinate payload")
    hemisphere = payload[0]
    limit = 90 if tag == "LATI" else 180
    if hemisphere not in ({"N", "S"} if tag == "LATI" else {"E", "W"}):
        raise GedcomError(request_code, f"{tag} has an invalid hemisphere")
    number_text = payload[1:]
    if not re.match(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$", number_text):
        raise GedcomError(request_code, f"{tag} has an invalid coordinate value")
    if float(number_text) > limit:
        raise GedcomError(request_code, f"{tag} coordinate is out of range")


def _validate_enum_payload(
    payload: str | None,
    enum_set: str,
    fallback: set[str],
    *,
    request_code: str,
) -> None:
    if payload is None or (payload not in _enum_values(enum_set, fallback) and not _is_ext_tag(payload)):
        raise GedcomError(request_code, f"{enum_set} payload is not a permitted enum value")


def _validate_enum_list_payload(
    payload: str | None,
    enum_set: str,
    fallback: set[str],
    *,
    request_code: str,
) -> None:
    if payload is None:
        raise GedcomError(request_code, f"{enum_set} requires an enum-list payload")
    allowed = _enum_values(enum_set, fallback)
    values = [piece.strip() for piece in payload.split(",")]
    if not values or any(value not in allowed and not _is_ext_tag(value) for value in values):
        raise GedcomError(request_code, f"{enum_set} payload contains an invalid enum value")


def _is_date_value(payload: str) -> bool:
    if payload == "":
        return True
    if "/" in payload:
        return False
    pieces = payload.split()
    if not pieces:
        return True
    if pieces[0] in {"ABT", "CAL", "EST", "AFT", "BEF"}:
        return _is_date_atom(pieces[1:])
    if pieces[0] == "BET":
        if "AND" not in pieces[1:]:
            return False
        index = pieces.index("AND", 1)
        return _is_date_atom(pieces[1:index]) and _is_date_atom(pieces[index + 1 :])
    if pieces[0] == "FROM":
        if "TO" in pieces[1:]:
            index = pieces.index("TO", 1)
            return _is_date_atom(pieces[1:index]) and _is_date_atom(pieces[index + 1 :])
        return _is_date_atom(pieces[1:])
    if pieces[0] == "TO":
        return _is_date_atom(pieces[1:])
    return _is_date_atom(pieces)


def _is_date_exact(payload: str) -> bool:
    return _is_date_atom(payload.split(), allow_calendar=False, require_day=True)


def _is_date_atom(
    pieces: list[str],
    *,
    allow_calendar: bool = True,
    require_day: bool = False,
) -> bool:
    if not pieces:
        return False
    calendar = "GREGORIAN"
    if allow_calendar and pieces[0] in _MONTHS_BY_CALENDAR:
        calendar = pieces.pop(0)
    if pieces and pieces[-1] == "BCE":
        if calendar not in {"GREGORIAN", "JULIAN"}:
            return False
        pieces = pieces[:-1]
    if any(piece in _DATE_RESTRICT_WORDS for piece in pieces):
        return False
    if len(pieces) == 1:
        return not require_day and _is_positive_integer(pieces[0])
    if len(pieces) == 2:
        month, year = pieces
        return (
            not require_day
            and month in _MONTHS_BY_CALENDAR[calendar]
            and _is_positive_integer(year)
        )
    if len(pieces) == 3:
        day, month, year = pieces
        return (
            _is_positive_integer(day)
            and 1 <= int(day) <= 36
            and month in _MONTHS_BY_CALENDAR[calendar]
            and _is_positive_integer(year)
        )
    return False


def _is_positive_integer(value: str) -> bool:
    return bool(re.match(r"^(?:0|[1-9][0-9]*)$", value)) and int(value) > 0


def _is_ext_tag(value: str) -> bool:
    return value.startswith("_") and _TAG_RE.match(value) is not None


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


def _iter_nodes(node: GedcomNode) -> list[GedcomNode]:
    nodes = [node]
    for child in node.children:
        nodes.extend(_iter_nodes(child))
    return nodes


def _validate_gedzip_local_file_entries(
    dataset: GedcomDataset,
    attachment_names: set[str],
    *,
    request_code: str,
) -> None:
    required_names: set[str] = set()
    for record in dataset.records:
        for node in _iter_nodes(record):
            if node.tag != "FILE" or node.payload is None:
                continue
            zip_name = _local_file_zip_name(
                node.payload,
                request_code=request_code,
                inside_gedzip=True,
            )
            if zip_name is None:
                continue
            _validate_zip_entry_name(zip_name, request_code=request_code)
            if zip_name == _GEDCOM_DATASET_ENTRY:
                raise GedcomError(request_code, "GEDZIP local files may not be named gedcom.ged")
            required_names.add(zip_name)
    missing = sorted(required_names - attachment_names)
    if missing:
        raise GedcomError(request_code, f"GEDZIP archive is missing local file {missing[0]!r}")


def _validate_zip_entry_name(name: str, *, request_code: str) -> None:
    if name == "" or name.startswith("/") or "\\" in name:
        raise GedcomError(request_code, f"Invalid GEDZIP entry name {name!r}")
    if any(part in {"", ".", ".."} for part in name.split("/")):
        raise GedcomError(request_code, f"Invalid GEDZIP entry path {name!r}")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in name):
        raise GedcomError(request_code, f"Invalid GEDZIP entry characters in {name!r}")


def _local_file_zip_name(
    file_path: str,
    *,
    request_code: str,
    inside_gedzip: bool = False,
) -> str | None:
    if _URL_WHITESPACE_RE.search(file_path):
        raise GedcomError(request_code, f"FILE path contains whitespace: {file_path!r}")
    if "\\" in file_path or "%5c" in file_path.lower():
        raise GedcomError(request_code, f"FILE path contains a reverse solidus: {file_path!r}")
    parts = urlsplit(file_path)
    if parts.scheme not in _SUPPORTED_FILE_SCHEMES:
        raise GedcomError(request_code, f"Unsupported FILE path scheme {parts.scheme!r}")
    if parts.scheme in {"http", "https", "ftp"}:
        if not parts.netloc:
            raise GedcomError(request_code, f"Absolute FILE URL lacks an authority: {file_path!r}")
        return None
    if parts.scheme == "file":
        if inside_gedzip and parts.netloc in {"", "localhost"}:
            raise GedcomError(request_code, "GEDZIP local FILE paths may not use file: URLs")
        return None
    if parts.netloc or parts.query or parts.fragment or parts.path.startswith("/"):
        raise GedcomError(request_code, f"Unsupported local FILE path {file_path!r}")
    decoded_path = unquote(parts.path)
    decoded_segments = decoded_path.split("/")
    if any(segment in {"", ".", ".."} for segment in decoded_segments):
        raise GedcomError(request_code, f"Unsupported local FILE path {file_path!r}")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in decoded_path):
        raise GedcomError(request_code, f"FILE path contains banned characters: {file_path!r}")
    return decoded_path


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
