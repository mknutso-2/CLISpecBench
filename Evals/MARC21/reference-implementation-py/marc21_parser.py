from __future__ import annotations

from base64 import b64decode, b64encode
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

from marc21_model import ControlField, DataField, MarcError, Record, Subfield

FT = b"\x1e"
RT = b"\x1d"
SF = b"\x1f"
NS = "http://www.loc.gov/MARC21/slim"
# Regenerated from prompt/docs by Evals/MARC21/scripts/generate_official_artifacts.py.
_RULES_PATH = Path(__file__).resolve().parent / "generated" / "marc21_field_rules.json"


def inspect_record_bytes(data: bytes) -> Record:
    if len(data) < 25:
        raise MarcError("invalid_record", "Record is too short")
    if not data.endswith(RT):
        raise MarcError("invalid_record", "Record terminator is missing")

    leader = data[:24]
    try:
        leader_text = leader.decode("ascii")
    except UnicodeDecodeError as exc:
        raise MarcError("invalid_record", f"Leader must be ASCII: {exc}") from exc

    _validate_iso2709_leader(leader_text, expected_length=len(data))

    base_address = int(leader_text[12:17])
    if data[base_address - 1 : base_address] != FT:
        raise MarcError("invalid_record", "Directory terminator is missing")
    directory = data[24 : base_address - 1]
    if len(directory) % 12 != 0:
        raise MarcError("invalid_record", "Directory length must be divisible by 12")

    control_fields: list[ControlField] = []
    data_fields: list[DataField] = []
    seen_data_field = False
    for offset in range(0, len(directory), 12):
        entry = directory[offset : offset + 12]
        tag = _parse_tag(entry[:3], "directory tag", error_code="invalid_record")
        field_length = _parse_ascii_int(entry[3:7], "directory field length")
        field_start = _parse_ascii_int(entry[7:12], "directory field start")
        field_start_abs = base_address + field_start
        field_end_abs = field_start_abs + field_length
        if field_end_abs > len(data):
            raise MarcError("invalid_record", f"Field {tag} points outside the record")
        field_bytes = data[field_start_abs:field_end_abs]
        if not field_bytes.endswith(FT):
            raise MarcError("invalid_record", f"Field {tag} is missing a field terminator")
        payload = field_bytes[:-1]
        if "001" <= tag <= "009":
            if seen_data_field:
                raise MarcError("invalid_record", "Control fields must precede data fields")
            control_fields.append(ControlField(tag=tag, value=_decode_utf8(payload, f"field {tag}")))
            continue
        seen_data_field = True
        if len(payload) < 2:
            raise MarcError("invalid_record", f"Data field {tag} must contain two indicators")
        indicators = (_parse_indicator(payload[0], tag), _parse_indicator(payload[1], tag))
        subfield_payload = payload[2:]
        subfields = _parse_subfields(tag, subfield_payload)
        data_fields.append(DataField(tag=tag, indicators=indicators, subfields=subfields))

    record = Record(
        leader_template=_normalize_leader_template(leader_text),
        control_fields=control_fields,
        data_fields=data_fields,
    )
    _validate_record_fields(record, error_code="invalid_record")
    return record


def inspect_marcxml(text: str) -> Record:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise MarcError("invalid_record", f"Invalid MARCXML: {exc}") from exc

    record = _resolve_marcxml_record(root)
    leader_node = record.find(f"{{{NS}}}leader")
    if leader_node is None or leader_node.text is None:
        raise MarcError("invalid_record", "MARCXML record must contain exactly one leader")
    leader_text = leader_node.text
    _validate_marcxml_leader(leader_text)

    control_fields: list[ControlField] = []
    data_fields: list[DataField] = []
    seen_data_field = False
    for child in list(record):
        if child.tag == f"{{{NS}}}leader":
            continue
        if child.tag == f"{{{NS}}}controlfield":
            if seen_data_field:
                raise MarcError("invalid_record", "MARCXML controlfield elements must precede datafield elements")
            tag = _parse_tag(
                _required_attr(child, "tag", "controlfield"),
                "controlfield tag",
                error_code="invalid_record",
            )
            if not ("001" <= tag <= "009"):
                raise MarcError("invalid_record", f"Control field tag {tag} must be in 001-009")
            control_fields.append(ControlField(tag=tag, value=child.text or ""))
            continue
        if child.tag == f"{{{NS}}}datafield":
            seen_data_field = True
            tag = _parse_tag(
                _required_attr(child, "tag", "datafield"),
                "datafield tag",
                error_code="invalid_record",
            )
            if not ("010" <= tag <= "999"):
                raise MarcError("invalid_record", f"Data field tag {tag} must be in 010-999")
            ind1 = _parse_xml_indicator(_required_attr(child, "ind1", "datafield"), tag)
            ind2 = _parse_xml_indicator(_required_attr(child, "ind2", "datafield"), tag)
            subfields: list[Subfield] = []
            for subfield in list(child):
                if subfield.tag != f"{{{NS}}}subfield":
                    raise MarcError("invalid_record", f"Unexpected MARCXML element inside field {tag}")
                code = _required_attr(subfield, "code", "subfield")
                _validate_subfield_code(code, tag, error_code="invalid_record")
                subfields.append(Subfield(code=code, value=subfield.text or ""))
            data_fields.append(DataField(tag=tag, indicators=(ind1, ind2), subfields=subfields))
            continue
        raise MarcError("invalid_record", "Unexpected MARCXML child element")

    record = Record(
        leader_template=_normalize_leader_template(leader_text),
        control_fields=control_fields,
        data_fields=data_fields,
    )
    _validate_record_fields(record, error_code="invalid_record")
    return record


def render_iso2709(record: Record) -> bytes:
    _validate_render_record(record)
    field_chunks: list[bytes] = []
    directory_entries: list[bytes] = []
    field_start = 0

    for field in record.control_fields:
        payload = field.value.encode("utf-8") + FT
        field_chunks.append(payload)
        directory_entries.append(_encode_directory_entry(field.tag, len(payload), field_start))
        field_start += len(payload)

    for field in record.data_fields:
        body = bytearray()
        body.extend(field.indicators[0].encode("ascii"))
        body.extend(field.indicators[1].encode("ascii"))
        for subfield in field.subfields:
            body.extend(SF)
            body.extend(subfield.code.encode("ascii"))
            body.extend(subfield.value.encode("utf-8"))
        body.extend(FT)
        payload = bytes(body)
        field_chunks.append(payload)
        directory_entries.append(_encode_directory_entry(field.tag, len(payload), field_start))
        field_start += len(payload)

    directory = b"".join(directory_entries) + FT
    base_address = 24 + len(directory)
    body = directory + b"".join(field_chunks) + RT
    record_length = 24 + len(body)
    leader = _build_leader(record.leader_template, record_length, base_address)
    return leader.encode("ascii") + body


def render_marcxml(record: Record) -> str:
    _validate_render_record(record)
    ET.register_namespace("", NS)
    root = ET.Element(f"{{{NS}}}record")
    leader = ET.SubElement(root, f"{{{NS}}}leader")
    leader.text = _build_leader(record.leader_template, 0, 0)
    for field in record.control_fields:
        node = ET.SubElement(root, f"{{{NS}}}controlfield", {"tag": field.tag})
        node.text = field.value
    for field in record.data_fields:
        node = ET.SubElement(
            root,
            f"{{{NS}}}datafield",
            {
                "tag": field.tag,
                "ind1": field.indicators[0],
                "ind2": field.indicators[1],
            },
        )
        for subfield in field.subfields:
            sub = ET.SubElement(node, f"{{{NS}}}subfield", {"code": subfield.code})
            sub.text = subfield.value
    return ET.tostring(root, encoding="unicode")


def _resolve_marcxml_record(root: ET.Element) -> ET.Element:
    if root.tag == f"{{{NS}}}record":
        return root
    if root.tag == f"{{{NS}}}collection":
        records = [child for child in list(root) if child.tag == f"{{{NS}}}record"]
        if len(records) != 1:
            raise MarcError("invalid_record", "MARCXML collection must contain exactly one record")
        return records[0]
    raise MarcError("invalid_record", "MARCXML root must be record or collection in the MARC21 slim namespace")


def _parse_subfields(tag: str, data: bytes) -> list[Subfield]:
    if not data:
        return []
    if not data.startswith(SF):
        raise MarcError("invalid_record", f"Data field {tag} must start subfields with 0x1F")
    pieces = data.split(SF)[1:]
    subfields: list[Subfield] = []
    for piece in pieces:
        if len(piece) < 1:
            raise MarcError("invalid_record", f"Malformed subfield in field {tag}")
        code = chr(piece[0])
        _validate_subfield_code(code, tag, error_code="invalid_record")
        subfields.append(Subfield(code=code, value=_decode_utf8(piece[1:], f"subfield {tag}${code}")))
    return subfields


def _validate_iso2709_leader(leader: str, *, expected_length: int) -> None:
    _validate_leader_template_core(leader, error_code="invalid_record")
    if not leader[:5].isdigit():
        raise MarcError("invalid_record", "Leader record length must be numeric")
    if int(leader[:5]) != expected_length:
        raise MarcError("invalid_record", "Leader record length does not match actual length")
    if not leader[12:17].isdigit():
        raise MarcError("invalid_record", "Leader base address must be numeric")


def _validate_marcxml_leader(leader: str) -> None:
    _validate_leader_template_core(leader, error_code="invalid_record")
    if not leader[:5].isdigit():
        raise MarcError("invalid_record", "MARCXML leader positions 00-04 must be digits")
    if not leader[12:17].isdigit():
        raise MarcError("invalid_record", "MARCXML leader positions 12-16 must be digits")


def _validate_leader_template_core(leader: str, *, error_code: str) -> None:
    if len(leader) != 24:
        raise MarcError(error_code, "Leader must be 24 bytes")
    if leader[9] != "a":
        raise MarcError(error_code, "Leader position 09 must be 'a'")
    if leader[10] != "2" or leader[11] != "2":
        raise MarcError(error_code, "Leader positions 10 and 11 must both be '2'")
    if leader[20:24] != "4500":
        raise MarcError(error_code, "Leader positions 20-23 must be 4500")


def _build_leader(template: str, record_length: int, base_address: int) -> str:
    _validate_leader_template_core(template, error_code="invalid_request")
    if record_length and record_length > 99999:
        raise MarcError("invalid_request", "Rendered record length exceeds the five-digit leader field")
    if base_address and base_address > 99999:
        raise MarcError("invalid_request", "Rendered base address exceeds the five-digit leader field")
    leader = list(template)
    if record_length:
        leader[:5] = list(f"{record_length:05d}")
    if base_address:
        leader[12:17] = list(f"{base_address:05d}")
    return "".join(leader)


def _normalize_leader_template(leader: str) -> str:
    chars = list(leader)
    chars[:5] = list("00000")
    chars[12:17] = list("00000")
    return "".join(chars)


def _validate_render_record(record: Record) -> None:
    _build_leader(record.leader_template, 24, 24)
    _validate_record_fields(record, error_code="invalid_request")


def _validate_record_fields(record: Record, *, error_code: str) -> None:
    control_counts: dict[str, int] = {}
    for field in record.control_fields:
        tag = _parse_tag(field.tag, "control field tag", error_code=error_code)
        if not ("001" <= tag <= "009"):
            raise MarcError(error_code, f"Control field tag {tag} must be in 001-009")
        _validate_field_text(field.value, f"control field {tag}", error_code=error_code)
        control_counts[tag] = control_counts.get(tag, 0) + 1
    for field in record.data_fields:
        tag = _parse_tag(field.tag, "data field tag", error_code=error_code)
        if not ("010" <= tag <= "999"):
            raise MarcError(error_code, f"Data field tag {tag} must be in 010-999")
        if len(field.indicators) != 2:
            raise MarcError(error_code, f"Data field {tag} must contain exactly two indicators")
        for indicator in field.indicators:
            _validate_indicator_text(indicator, tag, error_code=error_code)
        for subfield in field.subfields:
            _validate_subfield_code(subfield.code, tag, error_code=error_code)
            _validate_field_text(subfield.value, f"subfield {tag}${subfield.code}", error_code=error_code)
    _validate_against_official_field_rules(record, control_counts, error_code=error_code)


def _validate_against_official_field_rules(
    record: Record,
    control_counts: dict[str, int],
    *,
    error_code: str,
) -> None:
    rules = _field_rules()
    for tag, count in control_counts.items():
        rule = rules.get(tag)
        if rule is None:
            raise MarcError(error_code, f"Control field tag {tag} is not recognized by the bundled MARC21 rule table")
        if rule.get("repeatable") is False and count > 1:
            raise MarcError(error_code, f"Control field {tag} is not repeatable in the bundled MARC21 rule table")

    data_counts: dict[str, int] = {}
    for field in record.data_fields:
        tag = field.tag
        data_counts[tag] = data_counts.get(tag, 0) + 1
        rule = rules.get(tag)
        if rule is None:
            raise MarcError(error_code, f"Data field tag {tag} is not recognized by the bundled MARC21 rule table")
        _validate_official_indicators(field, rule, error_code=error_code)
        _validate_official_subfields(field, rule, error_code=error_code)

    for tag, count in data_counts.items():
        rule = rules.get(tag)
        if rule is not None and rule.get("repeatable") is False and count > 1:
            raise MarcError(error_code, f"Data field {tag} is not repeatable in the bundled MARC21 rule table")


def _validate_official_indicators(field: DataField, rule: dict[str, object], *, error_code: str) -> None:
    allowed_1 = _allowed_indicator_values(rule.get("indicator1"))
    allowed_2 = _allowed_indicator_values(rule.get("indicator2"))
    if allowed_1 is not None and field.indicators[0] not in allowed_1:
        raise MarcError(error_code, f"Indicator 1 value {field.indicators[0]!r} is not allowed in field {field.tag}")
    if allowed_2 is not None and field.indicators[1] not in allowed_2:
        raise MarcError(error_code, f"Indicator 2 value {field.indicators[1]!r} is not allowed in field {field.tag}")


def _validate_official_subfields(field: DataField, rule: dict[str, object], *, error_code: str) -> None:
    raw_entries = rule.get("subfields")
    if not isinstance(raw_entries, list) or not raw_entries:
        return
    allowed: dict[str, bool | None] = {}
    entries = cast(list[dict[str, Any]], raw_entries)
    for entry in entries:
        code = entry.get("code")
        if not isinstance(code, str):
            continue
        repeatable = entry.get("repeatable")
        allowed[code] = repeatable if repeatable in {True, False} else None
    counts: dict[str, int] = {}
    for subfield in field.subfields:
        if subfield.code not in allowed:
            raise MarcError(error_code, f"Subfield ${subfield.code} is not defined for field {field.tag} in the bundled MARC21 rule table")
        counts[subfield.code] = counts.get(subfield.code, 0) + 1
        if allowed[subfield.code] is False and counts[subfield.code] > 1:
            raise MarcError(error_code, f"Subfield ${subfield.code} is not repeatable in field {field.tag}")


def _allowed_indicator_values(value: object) -> set[str] | None:
    if not isinstance(value, list) or not value:
        return None
    result: set[str] = set()
    for entry in cast(list[Any], value):
        if isinstance(entry, str):
            result.add(" " if entry == "#" else entry)
    return result if result else None


@lru_cache(maxsize=1)
def _field_rules() -> dict[str, dict[str, object]]:
    return json.loads(_RULES_PATH.read_text(encoding="utf-8"))


def _encode_directory_entry(tag: str, field_length: int, field_start: int) -> bytes:
    if field_length > 9999:
        raise MarcError("invalid_request", f"Field {tag} is too long for the ISO 2709 directory length field")
    if field_start > 99999:
        raise MarcError("invalid_request", f"Field {tag} starts beyond the ISO 2709 directory start field")
    return tag.encode("ascii") + f"{field_length:04d}{field_start:05d}".encode("ascii")


def _parse_ascii_int(data: bytes, label: str) -> int:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise MarcError("invalid_record", f"{label} must be ASCII digits") from exc
    if not text.isdigit():
        raise MarcError("invalid_record", f"{label} must contain only digits")
    return int(text)


def _parse_tag(data: bytes | str, label: str, *, error_code: str) -> str:
    text = data.decode("ascii") if isinstance(data, bytes) else data
    if len(text) != 3 or not text.isdigit():
        raise MarcError(error_code, f"{label} must be a three-digit tag")
    return text


def _parse_indicator(value: int, tag: str) -> str:
    char = chr(value)
    _validate_indicator_text(char, tag, error_code="invalid_record")
    return char


def _parse_xml_indicator(value: str, tag: str) -> str:
    _validate_indicator_text(value, tag, error_code="invalid_record")
    return value


def _validate_indicator_text(indicator: str, tag: str, *, error_code: str = "invalid_request") -> None:
    if len(indicator) != 1 or not indicator.isascii():
        raise MarcError(error_code, f"Indicators in field {tag} must be one ASCII character")


def _validate_subfield_code(code: str, tag: str, *, error_code: str) -> None:
    if len(code) != 1 or not (code.isdigit() or ("a" <= code <= "z")):
        raise MarcError(
            error_code,
            f"Subfield code {code!r} in field {tag} must be one lowercase letter or digit",
        )


def _validate_field_text(text: str, label: str, *, error_code: str = "invalid_request") -> None:
    if any(char in text for char in ("\x1d", "\x1e", "\x1f")):
        raise MarcError(error_code, f"{label} may not contain MARC control characters")


def _decode_utf8(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MarcError("invalid_record", f"{label} must be valid UTF-8") from exc


def _required_attr(node: ET.Element, key: str, label: str) -> str:
    value = node.get(key)
    if value is None:
        raise MarcError("invalid_record", f"{label} is missing required attribute {key!r}")
    return value


def b64encode_bytes(data: bytes) -> str:
    return b64encode(data).decode("ascii")


def b64decode_bytes(text: str) -> bytes:
    try:
        return b64decode(text.encode("ascii"))
    except Exception as exc:  # pragma: no cover - stdlib exact exception varies
        raise MarcError("invalid_request", f"Invalid base64 input: {exc}") from exc
