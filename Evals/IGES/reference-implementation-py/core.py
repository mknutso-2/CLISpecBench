from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any


UNITS_BY_CODE = {
    1: "inches",
    2: "millimeters",
    3: "see_field_15",
    4: "feet",
    5: "miles",
    6: "meters",
    7: "kilometers",
    8: "mils",
    9: "microns",
    10: "centimeters",
    11: "microinches",
}
UNITS_TO_CODE = {value: key for key, value in UNITS_BY_CODE.items()}

SPEC_VERSION_BY_CODE = {
    1: "v1_0",
    2: "ansi_1981",
    3: "v2_0",
    4: "v3_0",
    5: "asme_1987",
    6: "v4_0",
    7: "asme_1989",
    8: "v5_0",
    9: "v5_2",
    10: "v5_1",
    11: "v5_3",
}
SPEC_VERSION_TO_CODE = {value: key for key, value in SPEC_VERSION_BY_CODE.items()}

DRAFTING_STD_BY_CODE = {
    0: "none",
    1: "iso",
    2: "afnor",
    3: "ansi",
    4: "bsi",
    5: "csa",
    6: "din",
    7: "jis",
}
DRAFTING_STD_TO_CODE = {value: key for key, value in DRAFTING_STD_BY_CODE.items()}

BLANK_BY_CODE = {0: "visible", 1: "blanked"}
BLANK_TO_CODE = {"visible": 0, "blanked": 1}

SUBORDINATE_BY_CODE = {
    0: "independent",
    1: "physically_dependent",
    2: "logically_dependent",
    3: "both",
}
SUBORDINATE_TO_CODE = {value: key for key, value in SUBORDINATE_BY_CODE.items()}

ENTITY_USE_BY_CODE = {
    0: "geometry",
    1: "annotation",
    2: "definition",
    3: "other",
    4: "logical_positional",
    5: "parametric_2d",
    6: "construction_geometry",
}
ENTITY_USE_TO_CODE = {value: key for key, value in ENTITY_USE_BY_CODE.items()}

HIERARCHY_BY_CODE = {
    0: "global_top_down",
    1: "global_defer",
    2: "use_property",
}
HIERARCHY_TO_CODE = {value: key for key, value in HIERARCHY_BY_CODE.items()}


class _Section:
    FLAG = "flag"
    START = "start"
    GLOBAL = "global"
    DIRECTORY = "directory"
    PARAMETER = "parameter"
    TERMINATE = "terminate"
    UNKNOWN = "unknown"


SECTION = _Section()
_MISSING = object()


class Obj(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def copy(self) -> Obj:
        return Obj(self)


def obj(value: Any) -> Any:
    if isinstance(value, Obj):
        return value
    if isinstance(value, dict):
        return Obj({key: obj(inner) for key, inner in value.items()})
    if isinstance(value, list):
        return [obj(inner) for inner in value]
    return value


def parse_args(argv: list[str]) -> Obj | None:
    if not argv:
        return None
    args = obj(
        {
            "subcommand": argv[0],
            "input": None,
            "output": None,
            "de": None,
            "t": None,
            "s": None,
        }
    )
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--input" and index + 1 < len(argv):
            args.input = argv[index + 1]
            index += 2
        elif token == "--output" and index + 1 < len(argv):
            args.output = argv[index + 1]
            index += 2
        elif token == "--de" and index + 1 < len(argv):
            args.de = argv[index + 1]
            index += 2
        elif token == "--t" and index + 1 < len(argv):
            args.t = argv[index + 1]
            index += 2
        elif token == "--s" and index + 1 < len(argv):
            args.s = argv[index + 1]
            index += 2
        else:
            return None
    return args


def make_error(
    message: str,
    spec_ref: str | None,
    line: int = 0,
    section: str = "unknown",
    diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": message,
        "spec_ref": spec_ref,
        "line": line,
        "section": section,
        "diagnostics": diagnostics or [],
    }


def write_json(output_path: str | Path, payload: Any) -> None:
    Path(output_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_file(input_path: str | Path) -> str:
    return Path(input_path).read_text(encoding="latin-1")


def write_file(output_path: str | Path, content: str) -> None:
    Path(output_path).write_text(content, encoding="latin-1")


def make_diag(
    severity: str,
    line: int,
    section: str,
    message: str,
    spec_ref: str | None,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "line": line,
        "section": section,
        "message": message,
        "spec_ref": spec_ref,
    }


def error_from_diagnostics(diags: list[dict[str, Any]]) -> dict[str, Any]:
    if not diags:
        return make_error("Unknown parse error", "§3")
    primary = diags[0]
    return {
        "ok": False,
        "error": primary["message"],
        "spec_ref": primary["spec_ref"],
        "line": primary["line"],
        "section": primary["section"],
        "diagnostics": list(diags),
    }


class IgesError(RuntimeError):
    def __init__(self, diag: dict[str, Any]) -> None:
        super().__init__(diag["message"])
        self.diag = diag


def read_physical_lines(text: str) -> list[str]:
    lines = re.split(r"\r?\n", text)
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def section_letter(line: str) -> str | None:
    if len(line) < 73:
        return None
    return line[72]


def group_by_section(lines: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"S": [], "G": [], "D": [], "P": [], "T": [], "F": []}
    for line in lines:
        letter = section_letter(line)
        if letter is not None and letter in grouped:
            grouped[letter].append(line)
    return grouped


def pad_section_line(data: str, section: str, seq: int) -> str:
    body = data.ljust(72)[:72]
    return f"{body}{section}{str(seq).rjust(7)}"


def pad_param_line(data: str, de_seq: int, p_seq: int) -> str:
    body = data.ljust(64)[:64]
    return f"{body} {str(de_seq).rjust(7)}P{str(p_seq).rjust(7)}"


class ParamTokenizer:
    def __init__(self, data: str, pd: str = ",", rd: str = ";") -> None:
        self.data = data
        self.pd = pd
        self.rd = rd
        self.pos = 0
        self.terminated = False

    def _next_field(self) -> Obj:
        if self.terminated:
            return obj({"kind": "raw", "raw": ""})

        start = self.pos
        index = start
        while index < len(self.data) and self.data[index] == " ":
            index += 1
        digit_start = index
        while index < len(self.data) and self.data[index].isdigit():
            index += 1

        if index > digit_start and index < len(self.data) and self.data[index] == "H":
            count = int(self.data[digit_start:index])
            text_start = index + 1
            text_end = text_start + count
            if text_end > len(self.data):
                raise IgesError(
                    make_diag(
                        "error",
                        0,
                        SECTION.UNKNOWN,
                        f"Hollerith length {count} exceeds remaining data",
                        "§2.2.2.3",
                    )
                )
            self.pos = text_end
            while self.pos < len(self.data) and self.data[self.pos] == " ":
                self.pos += 1
            if self.pos < len(self.data):
                current = self.data[self.pos]
                if current == self.rd:
                    self.terminated = True
                    self.pos += 1
                elif current == self.pd:
                    self.pos += 1
            return obj({"kind": "hollerith", "raw": self.data[text_start:text_end]})

        end = start
        while end < len(self.data):
            current = self.data[end]
            if current == self.pd or current == self.rd:
                break
            end += 1
        raw = self.data[start:end]
        if end < len(self.data):
            delim = self.data[end]
            if delim == self.rd:
                self.terminated = True
            self.pos = end + 1
        else:
            self.pos = end
        return obj({"kind": "raw", "raw": raw})

    def nextInteger(self, default_value: Any = _MISSING) -> int:
        field = self._next_field()
        raw = field.raw.strip() if field.kind == "raw" else ""
        if raw == "":
            if default_value is not _MISSING:
                return default_value
            raise IgesError(make_diag("error", 0, SECTION.UNKNOWN, "required integer field is empty", "§2.2.2.1"))
        if not re.fullmatch(r"[+-]?\d+", raw):
            raise IgesError(
                make_diag("error", 0, SECTION.UNKNOWN, f"invalid integer literal: '{raw}'", "§2.2.2.1")
            )
        value = int(raw, 10)
        return value

    def nextReal(self, default_value: Any = _MISSING) -> float:
        field = self._next_field()
        raw = field.raw.strip() if field.kind == "raw" else ""
        if raw == "":
            if default_value is not _MISSING:
                return default_value
            raise IgesError(make_diag("error", 0, SECTION.UNKNOWN, "required real field is empty", "§2.2.2.2"))
        normalized = re.sub(r"[dD]", "e", raw)
        try:
            value = float(normalized)
        except ValueError as exc:
            raise IgesError(
                make_diag("error", 0, SECTION.UNKNOWN, f"invalid real literal: '{raw}'", "§2.2.2.2")
            ) from exc
        if not math.isfinite(value):
            raise IgesError(
                make_diag("error", 0, SECTION.UNKNOWN, f"invalid real literal: '{raw}'", "§2.2.2.2")
            )
        return value

    def nextString(self, default_value: Any = _MISSING) -> str:
        field = self._next_field()
        if field.kind == "hollerith":
            for char in field.raw:
                code = ord(char)
                if 0x00 <= code <= 0x1F or code == 0x7F:
                    raise IgesError(
                        make_diag(
                            "error",
                            0,
                            SECTION.UNKNOWN,
                            "Hollerith string contains ASCII control character",
                            "§2.2.2.3",
                        )
                    )
            return field.raw

        raw = field.raw.strip()
        if raw == "":
            if default_value is not _MISSING:
                return default_value
            raise IgesError(make_diag("error", 0, SECTION.UNKNOWN, "required string field is empty", "§2.2.2.3"))
        raise IgesError(
            make_diag("error", 0, SECTION.UNKNOWN, f"expected Hollerith string, got '{raw}'", "§2.2.2.3")
        )

    def nextPointer(self, default_value: Any = _MISSING) -> int:
        return self.nextInteger(0 if default_value is _MISSING else default_value)

    def nextLogical(self, default_value: Any = _MISSING) -> bool:
        field = self._next_field()
        raw = field.raw.strip() if field.kind == "raw" else ""
        if raw == "":
            if default_value is not _MISSING:
                return default_value
            return False
        if raw == "0":
            return False
        if raw == "1":
            return True
        raise IgesError(
            make_diag(
                "error",
                0,
                SECTION.UNKNOWN,
                f"invalid logical literal '{raw}'; must be 0 or 1",
                "§2.2.2.6",
            )
        )

    def atEnd(self) -> bool:
        return self.terminated or self.pos >= len(self.data)


def format_real(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError(f"cannot format non-finite real: {value}")
    if value == 0:
        value = 0.0
    text = format(value, ".15g")
    if "e" in text or "E" in text:
        mantissa, exponent = re.split(r"([eE].*)", text, maxsplit=1)[:2]
        if "." not in mantissa:
            mantissa += ".0"
        return mantissa + exponent
    if "." not in text:
        text += ".0"
    return text


def format_integer(value: int) -> str:
    if int(value) != value:
        raise ValueError(f"cannot format non-integer: {value}")
    return str(int(value))


def format_hollerith(value: str) -> str:
    return f"{len(value.encode('latin-1'))}H{value}"


class ParamWriter:
    def __init__(self, pd: str = ",", rd: str = ";") -> None:
        self.pd = pd
        self.rd = rd
        self.parts: list[str] = []

    def _push(self, value: str) -> ParamWriter:
        self.parts.append(value)
        return self

    def writeInteger(self, value: int) -> ParamWriter:
        return self._push(format_integer(value))

    def writeReal(self, value: float) -> ParamWriter:
        return self._push(format_real(value))

    def writeString(self, value: str) -> ParamWriter:
        return self._push(format_hollerith(value))

    def writePointer(self, value: int) -> ParamWriter:
        return self._push(format_integer(value))

    def writeLogical(self, value: bool) -> ParamWriter:
        return self._push("1" if value else "0")

    def build(self) -> str:
        return self.pd.join(self.parts) + self.rd

    @staticmethod
    def forEntity(entity_type: int, pd: str = ",", rd: str = ";") -> ParamWriter:
        writer = ParamWriter(pd, rd)
        writer._push(format_integer(entity_type))
        return writer


def parse_timestamp(value: str | None) -> Obj | None:
    if not value:
        return None
    match_15 = re.fullmatch(r"(\d{4})(\d{2})(\d{2})\.(\d{2})(\d{2})(\d{2})", value)
    match_13 = re.fullmatch(r"(\d{2})(\d{2})(\d{2})\.(\d{2})(\d{2})(\d{2})", value)
    if match_15:
        return obj(
            {
                "year": int(match_15.group(1)),
                "month": int(match_15.group(2)),
                "day": int(match_15.group(3)),
                "hour": int(match_15.group(4)),
                "minute": int(match_15.group(5)),
                "second": int(match_15.group(6)),
            }
        )
    if match_13:
        return obj(
            {
                "year": 1900 + int(match_13.group(1)),
                "month": int(match_13.group(2)),
                "day": int(match_13.group(3)),
                "hour": int(match_13.group(4)),
                "minute": int(match_13.group(5)),
                "second": int(match_13.group(6)),
            }
        )
    raise IgesError(make_diag("error", 0, SECTION.GLOBAL, f"invalid timestamp '{value}'", "§2.2.4.3.18"))


def format_timestamp(ts: Obj | dict[str, Any] | None) -> str:
    if not ts:
        return ""
    ts = obj(ts)
    return (
        f"{ts.year:04d}{ts.month:02d}{ts.day:02d}."
        f"{ts.hour:02d}{ts.minute:02d}{ts.second:02d}"
    )


def detect_delimiters(data: str) -> Obj:
    pd = ","
    rd = ";"
    pos = 0
    if len(data) > 2 and data[0] == "1" and data[1] == "H":
        pd = data[2]
        pos = 3
        if pos < len(data) and (data[pos] == "," or data[pos] == pd):
            pos += 1
    elif data.startswith(","):
        pos = 1

    if pos + 2 < len(data) and data[pos] == "1" and data[pos + 1] == "H":
        rd = data[pos + 2]
        pos += 3
        if pos < len(data) and (data[pos] == pd or data[pos] == ","):
            pos += 1
    elif pos < len(data) and (data[pos] == pd or data[pos] == ","):
        pos += 1
    return obj({"pd": pd, "rd": rd, "pos": pos})


def parse_global_section(data: str) -> Obj:
    detected = detect_delimiters(data)
    tok = ParamTokenizer(data[detected.pos :], detected.pd, detected.rd)
    global_section = obj(
        {
            "param_delimiter": detected.pd,
            "record_delimiter": detected.rd,
        }
    )
    diags: list[dict[str, Any]] = []

    def push(exc: Exception) -> None:
        if isinstance(exc, IgesError):
            exc.diag["section"] = SECTION.GLOBAL
            diags.append(exc.diag)
        else:
            diags.append(make_diag("error", 0, SECTION.GLOBAL, str(exc), "§2.2.4.3"))

    def try_call(fn: Any) -> Any:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            push(exc)
            return None

    global_section.product_id_sender = try_call(lambda: tok.nextString())
    global_section.file_name = try_call(lambda: tok.nextString())
    global_section.native_system_id = try_call(lambda: tok.nextString())
    global_section.preprocessor_version = try_call(lambda: tok.nextString())
    global_section.integer_bits = try_call(lambda: tok.nextInteger())
    global_section.sp_magnitude = try_call(lambda: tok.nextInteger())
    global_section.sp_significance = try_call(lambda: tok.nextInteger())
    global_section.dp_magnitude = try_call(lambda: tok.nextInteger())
    global_section.dp_significance = try_call(lambda: tok.nextInteger())
    global_section.product_id_receiver = try_call(lambda: tok.nextString(global_section.product_id_sender or ""))
    global_section.model_space_scale = try_call(lambda: tok.nextReal(1.0))
    units_code = try_call(lambda: tok.nextInteger(1))
    global_section.units = UNITS_BY_CODE.get(units_code, "inches")
    global_section.units_name = try_call(lambda: tok.nextString("IN"))
    global_section.max_line_weight_grads = try_call(lambda: tok.nextInteger(1))
    global_section.max_line_weight_width = try_call(lambda: tok.nextReal(0.0))
    timestamp18 = try_call(lambda: tok.nextString())
    global_section.file_timestamp = try_call(lambda: parse_timestamp(timestamp18)) if timestamp18 is not None else None
    global_section.min_resolution = try_call(lambda: tok.nextReal(0.0))
    global_section.max_coordinate = try_call(lambda: tok.nextReal(0.0))
    global_section.author = try_call(lambda: tok.nextString(""))
    global_section.organization = try_call(lambda: tok.nextString(""))
    version_code = try_call(lambda: tok.nextInteger(3))
    if version_code is not None:
        if version_code < 1:
            version_code = 3
        elif version_code > 11:
            version_code = 11
    global_section.spec_version = SPEC_VERSION_BY_CODE.get(version_code, "v2_0")
    drafting_code = try_call(lambda: tok.nextInteger(0))
    global_section.drafting_std = DRAFTING_STD_BY_CODE.get(drafting_code, "none")
    timestamp25 = try_call(lambda: tok.nextString(""))
    global_section.model_timestamp = try_call(lambda: parse_timestamp(timestamp25)) if timestamp25 else None
    global_section.app_protocol = try_call(lambda: tok.nextString(""))
    return obj({"global": global_section, "diagnostics": diags})


def write_global_section(global_section: Obj | dict[str, Any]) -> str:
    global_section = obj(global_section)
    pd = global_section.param_delimiter or ","
    rd = global_section.record_delimiter or ";"
    pw = ParamWriter(pd, rd)
    pw.writeString(pd)
    pw.writeString(rd)
    pw.writeString(global_section.product_id_sender or "")
    pw.writeString(global_section.file_name or "")
    pw.writeString(global_section.native_system_id or "")
    pw.writeString(global_section.preprocessor_version or "")
    pw.writeInteger(global_section.integer_bits if global_section.integer_bits is not None else 32)
    pw.writeInteger(global_section.sp_magnitude if global_section.sp_magnitude is not None else 38)
    pw.writeInteger(global_section.sp_significance if global_section.sp_significance is not None else 6)
    pw.writeInteger(global_section.dp_magnitude if global_section.dp_magnitude is not None else 308)
    pw.writeInteger(global_section.dp_significance if global_section.dp_significance is not None else 15)
    pw.writeString(global_section.product_id_receiver or global_section.product_id_sender or "")
    pw.writeReal(global_section.model_space_scale if global_section.model_space_scale is not None else 1.0)
    pw.writeInteger(UNITS_TO_CODE.get(global_section.units, 1))
    pw.writeString(global_section.units_name or "IN")
    pw.writeInteger(global_section.max_line_weight_grads if global_section.max_line_weight_grads is not None else 1)
    pw.writeReal(global_section.max_line_weight_width if global_section.max_line_weight_width is not None else 0.0)
    pw.writeString(format_timestamp(global_section.file_timestamp))
    pw.writeReal(global_section.min_resolution if global_section.min_resolution is not None else 0.0)
    pw.writeReal(global_section.max_coordinate if global_section.max_coordinate is not None else 0.0)
    pw.writeString(global_section.author or "")
    pw.writeString(global_section.organization or "")
    pw.writeInteger(SPEC_VERSION_TO_CODE.get(global_section.spec_version, 3))
    pw.writeInteger(DRAFTING_STD_TO_CODE.get(global_section.drafting_std, 0))
    if global_section.model_timestamp:
        pw.writeString(format_timestamp(global_section.model_timestamp))
    else:
        pw.parts.append("")
    pw.writeString(global_section.app_protocol or "")
    return pw.build()


def parse_status_number(raw: str) -> Obj:
    padded = raw.strip().rjust(8, "0")
    if len(padded) != 8:
        raise IgesError(make_diag("error", 0, SECTION.DIRECTORY, f"invalid status number '{raw}'", "§2.2.4.4.9"))
    blank = int(padded[0:2], 10)
    subordinate = int(padded[2:4], 10)
    entity_use = int(padded[4:6], 10)
    hierarchy = int(padded[6:8], 10)
    return obj(
        {
            "blank": BLANK_BY_CODE.get(blank, "visible"),
            "subordinate": SUBORDINATE_BY_CODE.get(subordinate, "independent"),
            "entity_use": ENTITY_USE_BY_CODE.get(entity_use, "geometry"),
            "hierarchy": HIERARCHY_BY_CODE.get(hierarchy, "global_top_down"),
        }
    )


def format_status_number(status: Obj | dict[str, Any] | None) -> str:
    status = obj(status or {})
    return (
        f"{BLANK_TO_CODE.get(status.get('blank', 'visible'), 0):02d}"
        f"{SUBORDINATE_TO_CODE.get(status.get('subordinate', 'independent'), 0):02d}"
        f"{ENTITY_USE_TO_CODE.get(status.get('entity_use', 'geometry'), 0):02d}"
        f"{HIERARCHY_TO_CODE.get(status.get('hierarchy', 'global_top_down'), 0):02d}"
    )


def read_field(line: str, start_col: int, width: int) -> str:
    return line[start_col : start_col + width]


def parse_int_field(raw: str, default_value: int = 0) -> int:
    text = raw.strip()
    if text == "":
        return default_value
    try:
        return int(text, 10)
    except ValueError as exc:
        raise IgesError(make_diag("error", 0, SECTION.DIRECTORY, f"invalid integer field '{raw}'", "§2.2.4.4")) from exc


def parse_directory_entry(line1: str, line2: str) -> Obj:
    if len(line1) < 72 or len(line2) < 72:
        raise IgesError(make_diag("error", 0, SECTION.DIRECTORY, "directory entry lines too short", "§2.2.4.4"))
    return obj(
        {
            "entity_type": parse_int_field(read_field(line1, 0, 8)),
            "param_data_ptr": parse_int_field(read_field(line1, 8, 8)),
            "structure": parse_int_field(read_field(line1, 16, 8)),
            "line_font": parse_int_field(read_field(line1, 24, 8)),
            "level": parse_int_field(read_field(line1, 32, 8)),
            "view": parse_int_field(read_field(line1, 40, 8)),
            "xform_matrix": parse_int_field(read_field(line1, 48, 8)),
            "label_display": parse_int_field(read_field(line1, 56, 8)),
            "status": parse_status_number(read_field(line1, 64, 8)),
            "line_weight": parse_int_field(read_field(line2, 8, 8)),
            "color": parse_int_field(read_field(line2, 16, 8)),
            "param_line_count": parse_int_field(read_field(line2, 24, 8)),
            "form": parse_int_field(read_field(line2, 32, 8)),
            "entity_label": read_field(line2, 56, 8).strip(),
            "entity_subscript": parse_int_field(read_field(line2, 64, 8)),
        }
    )


def format_directory_entry(de: Obj | dict[str, Any], de_seq: int) -> list[str]:
    de = obj(de)

    def f(value: Any, width: int = 8) -> str:
        return str(value).rjust(width)

    def fs(value: str, width: int = 8) -> str:
        return value.rjust(width)[:width]

    line1 = (
        f(de.entity_type)
        + f(de.param_data_ptr or 0)
        + f(de.structure or 0)
        + f(de.line_font or 0)
        + f(de.level or 0)
        + f(de.view or 0)
        + f(de.xform_matrix or 0)
        + f(de.label_display or 0)
        + fs(format_status_number(de.status or {}))
        + "D"
        + str(de_seq).rjust(7)
    )
    line2 = (
        f(de.entity_type)
        + f(de.line_weight or 0)
        + f(de.color or 0)
        + f(de.param_line_count or 0)
        + f(de.form or 0)
        + "        "
        + "        "
        + fs(de.entity_label or "")
        + f(de.entity_subscript or 0)
        + "D"
        + str(de_seq + 1).rjust(7)
    )
    return [line1, line2]


def read_iges_file(text: str) -> Obj:
    lines = read_physical_lines(text)
    grouped = group_by_section(lines)
    diags: list[dict[str, Any]] = []

    if not grouped["S"]:
        diags.append(make_diag("error", 0, SECTION.START, "no Start section lines found", "§2.2.4.2"))
    if not grouped["G"]:
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "no Global section lines found", "§2.2.4.3"))
    if not grouped["T"]:
        diags.append(make_diag("error", 0, SECTION.TERMINATE, "no Terminate section line found", "§2.2.4.6"))
    if diags:
        return obj({"ok": False, "diagnostics": diags})

    start_lines: list[str] = []
    for line in grouped["S"]:
        body = line[:72]
        for char in body:
            code = ord(char)
            if code < 0x20 or code == 0x7F:
                diags.append(
                    make_diag(
                        "error",
                        0,
                        SECTION.START,
                        "Start section contains ASCII control character",
                        "§2.2.4.2",
                    )
                )
                return obj({"ok": False, "diagnostics": diags})
        start_lines.append(body.rstrip())

    global_data = "".join(line[:72] for line in grouped["G"]).rstrip()
    parsed_global = parse_global_section(global_data)
    if parsed_global.diagnostics:
        return obj({"ok": False, "diagnostics": parsed_global.diagnostics})

    if len(grouped["D"]) % 2 != 0:
        diags.append(make_diag("error", 0, SECTION.DIRECTORY, "odd number of DE lines", "§2.2.4.4"))
        return obj({"ok": False, "diagnostics": diags})

    directory_entries: list[Obj] = []
    for index in range(0, len(grouped["D"]), 2):
        try:
            directory_entries.append(parse_directory_entry(grouped["D"][index], grouped["D"][index + 1]))
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, IgesError):
                diags.append(exc.diag)
            else:
                diags.append(make_diag("error", 0, SECTION.DIRECTORY, str(exc), "§2.2.4.4"))
            return obj({"ok": False, "diagnostics": diags})

    pd_by_de: dict[int, str] = {}
    for line in grouped["P"]:
        body = line[:64]
        back_raw = line[65:72].strip()
        back = int(back_raw, 10) if back_raw else 0
        pd_by_de[back] = pd_by_de.get(back, "") + body

    entities: list[Obj] = []
    for index, de in enumerate(directory_entries):
        de_seq = 2 * index + 1
        pd_string = pd_by_de.get(de_seq, "").rstrip()
        entities.append(obj({"de": de, "pd_string": pd_string}))

    return obj(
        {
            "ok": True,
            "start_lines": start_lines,
            "global": parsed_global["global"],
            "entities": entities,
        }
    )


def split_pd_into_lines(pd_string: str, entity_type: int, de_seq: int, start_p_seq: int, pd: str) -> Obj:
    del entity_type, pd
    lines: list[str] = []
    p_seq = start_p_seq
    for pos in range(0, len(pd_string), 64):
        lines.append(pad_param_line(pd_string[pos : pos + 64], de_seq, p_seq))
        p_seq += 1
    if not lines:
        lines.append(pad_param_line("", de_seq, p_seq))
        p_seq += 1
    return obj({"lines": lines, "nextPSeq": p_seq, "lineCount": len(lines)})


def write_iges_file(start_lines: list[str], global_section: Obj | dict[str, Any], entities: list[Obj]) -> str:
    global_section = obj(global_section)
    output_parts: list[str] = []
    s_lines = start_lines if start_lines else [""]
    s_count = 0
    for line in s_lines:
        s_count += 1
        output_parts.append(pad_section_line(line, "S", s_count) + "\n")

    g_payload = write_global_section(global_section)
    g_count = 0
    if not g_payload:
        g_count += 1
        output_parts.append(pad_section_line("", "G", g_count) + "\n")
    else:
        for pos in range(0, len(g_payload), 72):
            g_count += 1
            output_parts.append(pad_section_line(g_payload[pos : pos + 72], "G", g_count) + "\n")

    pd_infos: list[Obj] = []
    p_seq = 1
    for index, ent in enumerate(entities):
        de_seq = 2 * index + 1
        result = split_pd_into_lines(ent.pd_string, ent.de.entity_type, de_seq, p_seq, global_section.param_delimiter or ",")
        pd_infos.append(obj({"start": p_seq, "count": result.lineCount, "lines": result.lines}))
        p_seq = result.nextPSeq
    p_count = p_seq - 1

    d_count = 0
    for index, ent in enumerate(entities):
        de_copy = obj(dict(ent.de))
        de_copy.param_data_ptr = pd_infos[index].start
        de_copy.param_line_count = pd_infos[index].count
        pair = format_directory_entry(de_copy, 2 * index + 1)
        output_parts.append(pair[0] + "\n")
        output_parts.append(pair[1] + "\n")
        d_count += 2

    for info in pd_infos:
        for line in info.lines:
            output_parts.append(line + "\n")

    t_body = (
        "S"
        + str(s_count).rjust(7)
        + "G"
        + str(g_count).rjust(7)
        + "D"
        + str(d_count).rjust(7)
        + "P"
        + str(p_count).rjust(7)
    )
    output_parts.append(pad_section_line(t_body, "T", 1) + "\n")
    return "".join(output_parts)


ENTITIES: dict[int, Obj] = {}


def registerEntity(entity_type: int, parser: Any, writer: Any) -> None:
    ENTITIES[entity_type] = obj({"parse": parser, "write": writer})


def readAttrValue(tok: ParamTokenizer, avdt: int) -> Obj:
    if avdt in {1, 6}:
        return obj({"kind": "int", "value": tok.nextInteger(0)})
    if avdt == 2:
        return obj({"kind": "real", "value": tok.nextReal(0)})
    if avdt == 3:
        return obj({"kind": "string", "value": tok.nextString("")})
    if avdt == 4:
        return obj({"kind": "pointer", "value": tok.nextPointer(0)})
    raise IgesError(make_diag("error", 0, SECTION.PARAMETER, f"unsupported AVDT {avdt}", "§4.79"))


def writeAttrValue(pw: ParamWriter, avdt: int, value: Any) -> None:
    value = obj(value)
    if isinstance(value, dict) and "kind" in value:
        raw = value["value"]
        if value["kind"] in {"int", "pointer"}:
            pw.writeInteger(raw)
        elif value["kind"] == "real":
            pw.writeReal(raw)
        elif value["kind"] == "string":
            pw.writeString(raw or "")
        else:
            raise ValueError(f"unknown FieldValue kind: {value['kind']}")
        return

    if avdt in {1, 4, 6}:
        pw.writeInteger(int(value or 0))
    elif avdt == 2:
        pw.writeReal(float(value) if value is not None else 0.0)
    elif avdt == 3:
        pw.writeString(str(value or ""))
    else:
        raise ValueError(f"unknown AVDT {avdt}")


def readFieldValue(tok: ParamTokenizer) -> Obj:
    field = tok._next_field()
    raw = field.raw.strip() if field.kind == "raw" else ""
    if field.kind == "hollerith":
        return obj({"kind": "string", "value": field.raw})
    if raw == "":
        return obj({"kind": "defaulted", "value": None})
    if re.fullmatch(r"[+-]?\d+", raw):
        return obj({"kind": "int", "value": int(raw, 10)})
    try:
        number = float(re.sub(r"[dD]", "e", raw))
    except ValueError:
        return obj({"kind": "string", "value": raw})
    if math.isfinite(number):
        return obj({"kind": "real", "value": number})
    return obj({"kind": "string", "value": raw})


def writeFieldValue(pw: ParamWriter, value: Any) -> None:
    value = obj(value)
    if not isinstance(value, dict) or "kind" not in value:
        raise ValueError(f"Property value must be a tagged FieldValue: {json.dumps(value)}")
    if value["kind"] == "int":
        pw.writeInteger(int(value["value"]))
    elif value["kind"] == "real":
        pw.writeReal(float(value["value"]) if value["value"] is not None else 0.0)
    elif value["kind"] == "string":
        pw.writeString(str(value["value"] or ""))
    elif value["kind"] == "bool":
        pw.writeLogical(bool(value["value"]))
    elif value["kind"] == "defaulted":
        pw.parts.append("")
    else:
        raise ValueError(f"unknown FieldValue kind: {value['kind']}")


from entities_generated import install_entities  # noqa: E402


install_entities(registerEntity, obj, IgesError, make_diag, SECTION, readAttrValue, writeAttrValue, readFieldValue, writeFieldValue)


def parse_entity(entity_type: int, form: int, pd_string: str, pd: str, rd: str) -> Any:
    reg = ENTITIES.get(entity_type)
    if reg is None:
        raise IgesError(
            make_diag("error", 0, SECTION.PARAMETER, f"Unsupported entity type: {entity_type}", "§3.2")
        )
    tok = ParamTokenizer(pd_string, pd, rd)
    first_type = tok.nextInteger(entity_type)
    if first_type != entity_type:
        pass
    return reg.parse(tok, form)


def write_entity(entity_type: int, form: int, data: Any, pd: str, rd: str) -> str:
    reg = ENTITIES.get(entity_type)
    if reg is None:
        raise IgesError(
            make_diag("error", 0, SECTION.PARAMETER, f"Unsupported entity type: {entity_type}", "§3.2")
        )
    pw = ParamWriter.forEntity(entity_type, pd, rd)
    reg.write(obj(data), pw, form)
    return pw.build()


def de_to_json(de: Obj | dict[str, Any]) -> dict[str, Any]:
    de = obj(de)
    return {
        "entity_type": de.entity_type,
        "param_data_ptr": de.param_data_ptr or 0,
        "structure": de.structure or 0,
        "line_font": de.line_font or 0,
        "level": de.level or 0,
        "view": de.view or 0,
        "xform_matrix": de.xform_matrix or 0,
        "label_display": de.label_display or 0,
        "status": de.status,
        "line_weight": de.line_weight or 0,
        "color": de.color or 0,
        "param_line_count": de.param_line_count or 0,
        "form": de.form or 0,
        "entity_label": de.entity_label or "",
        "entity_subscript": de.entity_subscript or 0,
    }


def de_from_json(data: Any) -> Obj:
    data = obj(data or {})
    return obj(
        {
            "entity_type": int(data.get("entity_type", 0)),
            "param_data_ptr": int(data.get("param_data_ptr", 0)),
            "structure": int(data.get("structure", 0)),
            "line_font": int(data.get("line_font", 0)),
            "level": int(data.get("level", 0)),
            "view": int(data.get("view", 0)),
            "xform_matrix": int(data.get("xform_matrix", 0)),
            "label_display": int(data.get("label_display", 0)),
            "status": obj(
                data.get(
                    "status",
                    {
                        "blank": "visible",
                        "subordinate": "independent",
                        "entity_use": "geometry",
                        "hierarchy": "global_top_down",
                    },
                )
            ),
            "line_weight": int(data.get("line_weight", 0)),
            "color": int(data.get("color", 0)),
            "param_line_count": int(data.get("param_line_count", 0)),
            "form": int(data.get("form", 0)),
            "entity_label": data.get("entity_label", "") or "",
            "entity_subscript": int(data.get("entity_subscript", 0)),
        }
    )


def build_canonical_json(iges_file: Obj) -> dict[str, Any]:
    entities: list[dict[str, Any]] = []
    pd = iges_file["global"].param_delimiter or ","
    rd = iges_file["global"].record_delimiter or ";"
    for index, raw in enumerate(iges_file.entities):
        entity_type = raw.de.entity_type
        form = raw.de.form
        data = parse_entity(entity_type, form, raw.pd_string, pd, rd)
        entities.append(
            {
                "de_index": 2 * index + 1,
                "directory_entry": de_to_json(raw.de),
                "entity": {"type": entity_type, "form": form, "data": data},
            }
        )
    return {
        "start_lines": iges_file.start_lines,
        "global": iges_file["global"],
        "entities": entities,
    }


def build_iges_from_canonical_json(payload: Any) -> Obj:
    payload = obj(payload)
    start_lines = payload.get("start_lines", [])
    global_section = obj(payload["global"])
    entities_json = payload.get("entities", [])
    if not isinstance(entities_json, list):
        raise IgesError(make_diag("error", 0, SECTION.UNKNOWN, "'entities' must be an array", "§2.1"))

    entities: list[Obj] = []
    pd = global_section.param_delimiter or ","
    rd = global_section.record_delimiter or ";"
    for record in entities_json:
        record = obj(record)
        de = de_from_json(record.get("directory_entry", {}))
        entity = obj(record.entity)
        entity_type = int(entity.type)
        form = int(entity.form)
        de.entity_type = entity_type
        de.form = form
        pd_string = write_entity(entity_type, form, entity.data, pd, rd)
        entities.append(obj({"de": de, "pd_string": pd_string}))

    return obj({"start_lines": start_lines, "global": global_section, "entities": entities})


def validateSharedDe(iges_file: Obj, valid_de_seqs: set[int]) -> list[dict[str, Any]]:
    diags: list[dict[str, Any]] = []
    for index, ent in enumerate(iges_file.entities):
        de_seq = 2 * index + 1
        entity_type = ent.de.entity_type
        if entity_type < 0:
            diags.append(
                make_diag("error", 0, SECTION.DIRECTORY, f"DE {de_seq} has negative entity type {entity_type}", "§2.2.4.4")
            )
        if ent.de.xform_matrix and ent.de.xform_matrix not in valid_de_seqs:
            diags.append(
                make_diag(
                    "error",
                    0,
                    SECTION.DIRECTORY,
                    f"DE {de_seq} xform_matrix points to non-existent DE {ent.de.xform_matrix}",
                    "§2.2.4.4",
                )
            )
        if ent.de.view and ent.de.view not in valid_de_seqs:
            diags.append(
                make_diag(
                    "error",
                    0,
                    SECTION.DIRECTORY,
                    f"DE {de_seq} view points to non-existent DE {ent.de.view}",
                    "§2.2.4.4",
                )
            )
        if ent.de.label_display and ent.de.label_display not in valid_de_seqs:
            diags.append(
                make_diag(
                    "error",
                    0,
                    SECTION.DIRECTORY,
                    f"DE {de_seq} label_display points to non-existent DE {ent.de.label_display}",
                    "§2.2.4.4",
                )
            )
    return diags


def validateGlobal(global_section: Obj | dict[str, Any]) -> list[dict[str, Any]]:
    global_section = obj(global_section)
    diags: list[dict[str, Any]] = []
    if int(global_section.integer_bits) <= 0:
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 7 (integer_bits) is not positive", "§2.2.4.3"))
    if int(global_section.sp_magnitude) <= 0:
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 8 (sp_magnitude) is not positive", "§2.2.4.3"))
    if int(global_section.sp_significance) <= 0:
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 9 (sp_significance) is not positive", "§2.2.4.3"))
    if int(global_section.dp_magnitude) <= 0:
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 10 (dp_magnitude) is not positive", "§2.2.4.3"))
    if int(global_section.dp_significance) <= 0:
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 11 (dp_significance) is not positive", "§2.2.4.3"))
    if not (global_section.model_space_scale > 0):
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 13 (model_space_scale) is not positive", "§2.2.4.3"))
    if int(global_section.max_line_weight_grads) <= 0:
        diags.append(
            make_diag("error", 0, SECTION.GLOBAL, "Global field 16 (max_line_weight_grads) is not positive", "§2.2.4.3")
        )
    if not (global_section.min_resolution > 0):
        diags.append(make_diag("error", 0, SECTION.GLOBAL, "Global field 19 (min_resolution) is not positive", "§2.2.4.3"))
    return diags


def validate(iges_file: Obj) -> list[dict[str, Any]]:
    diags: list[dict[str, Any]] = []
    valid_de_seqs = {2 * index + 1 for index in range(len(iges_file.entities))}
    diags.extend(validateSharedDe(iges_file, valid_de_seqs))
    for index, ent in enumerate(iges_file.entities):
        de_seq = 2 * index + 1
        if ent.de.param_line_count <= 0 and ent.de.entity_type != 0:
            diags.append(
                make_diag(
                    "error",
                    0,
                    SECTION.DIRECTORY,
                    f"DE {de_seq} param_line_count is {ent.de.param_line_count} for non-null entity type {ent.de.entity_type}",
                    "§2.2.4.4",
                )
            )
        if (not ent.pd_string) and ent.de.entity_type != 0:
            diags.append(
                make_diag(
                    "error",
                    0,
                    SECTION.PARAMETER,
                    f"DE {de_seq} has empty parameter data for entity type {ent.de.entity_type}",
                    "§2.2.4.5",
                )
            )
    diags.extend(validateGlobal(iges_file["global"]))
    return diags


def validateWriteInput(iges_file: Obj) -> list[dict[str, Any]]:
    valid_de_seqs = {2 * index + 1 for index in range(len(iges_file.entities))}
    diags = validateSharedDe(iges_file, valid_de_seqs)
    diags.extend(validateGlobal(iges_file["global"]))
    return diags


CURVE_TYPES = {100, 102, 104, 106, 110, 112, 126, 130}
SURFACE_TYPES = {114, 118, 120, 122, 128, 140, 190, 192, 194, 196, 198}


def isCurveForEval(entity_type: int, form: int) -> bool:
    if entity_type in CURVE_TYPES:
        if entity_type == 106:
            return form in {11, 12, 63}
        return True
    return False


def isSurfaceForEval(entity_type: int) -> bool:
    return entity_type in SURFACE_TYPES


def vec_add(a: list[float], b: list[float]) -> list[float]:
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def vec_sub(a: list[float], b: list[float]) -> list[float]:
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def vec_scale(a: list[float], scale: float) -> list[float]:
    return [a[0] * scale, a[1] * scale, a[2] * scale]


def vec_dot(a: list[float], b: list[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def vec_norm(a: list[float]) -> list[float]:
    magnitude = math.sqrt(vec_dot(a, a))
    if magnitude == 0:
        return [0.0, 0.0, 0.0]
    return [a[0] / magnitude, a[1] / magnitude, a[2] / magnitude]


def mat_vec(rotation: list[list[float]], vector: list[float]) -> list[float]:
    return [
        rotation[0][0] * vector[0] + rotation[0][1] * vector[1] + rotation[0][2] * vector[2],
        rotation[1][0] * vector[0] + rotation[1][1] * vector[1] + rotation[1][2] * vector[2],
        rotation[2][0] * vector[0] + rotation[2][1] * vector[1] + rotation[2][2] * vector[2],
    ]


def makeResolver(canonical: Obj | dict[str, Any]) -> Any:
    canonical = obj(canonical)
    by_de: dict[int, Obj] = {}
    for record in canonical.entities:
        by_de[record.de_index] = obj(
            {
                "type": record.entity.type,
                "form": record.entity.form,
                "xform_de": record.directory_entry.xform_matrix or 0,
                "data": record.entity.data,
            }
        )
    return lambda de: by_de.get(de)


def sampleCurvePoint(ent: Obj, t: float, resolver: Any) -> list[float]:
    return evaluateEntity(ent.type, ent.form, ent.xform_de, ent.data, t, None, resolver, True)["point"]


def curveNativeSpan(entity_type: int, form: int, data: Obj | dict[str, Any]) -> list[float]:
    data = obj(data)
    if entity_type == 100:
        sa = math.atan2(data.y2 - data.y1, data.x2 - data.x1)
        ta = math.atan2(data.y3 - data.y1, data.x3 - data.x1)
        if ta <= sa:
            ta += 2 * math.pi
        return [sa, ta]
    if entity_type == 104:
        return [data.x1, data.x2]
    if entity_type == 106:
        return [0, data.n - 1]
    if entity_type == 110:
        return [0, 1]
    if entity_type == 112:
        return [data.breakpoints[0], data.breakpoints[-1]]
    if entity_type == 126:
        return [data.v0, data.v1]
    if entity_type == 130:
        return [data.tt1, data.tt2]
    if entity_type == 102:
        return [0, 1]
    return [0, 1]


def applyXform(point: list[float], xform_de: int, resolver: Any) -> list[float]:
    if not xform_de:
        return point
    matrix = resolver(xform_de)
    if not matrix or matrix.type != 124:
        return point
    return vec_add(mat_vec(matrix.data.rotation, point), matrix.data.translation)


def sampleCopiousTuple(data: Obj, index: int) -> list[float]:
    if data.ip == 1:
        return [data.data[index * 2], data.data[index * 2 + 1], data.zt]
    if data.ip == 2:
        return [data.data[index * 3], data.data[index * 3 + 1], data.data[index * 3 + 2]]
    return [data.data[index * 6], data.data[index * 6 + 1], data.data[index * 6 + 2]]


def bsplineBasis(t: float, knots: list[float], degree: int, start_index: int) -> float:
    knot_count = len(knots) - 1
    values = [0.0] * (degree + 1)
    for offset in range(degree + 1):
        idx = start_index + offset
        values[offset] = 1.0 if knots[idx] <= t < knots[idx + 1] else 0.0
        if idx == knot_count - 1 and t == knots[knot_count]:
            values[offset] = 1.0
    for level in range(1, degree + 1):
        for offset in range(degree - level + 1):
            idx = start_index + offset
            denom1 = knots[idx + level] - knots[idx]
            denom2 = knots[idx + level + 1] - knots[idx + 1]
            left = (t - knots[idx]) / denom1 * values[offset] if denom1 != 0 else 0.0
            right = (knots[idx + level + 1] - t) / denom2 * values[offset + 1] if denom2 != 0 else 0.0
            values[offset] = left + right
    return values[0]


def bsplineCurvePoint(data: Obj | dict[str, Any], t: float) -> list[float]:
    data = obj(data)
    if t < data.v0:
        t = data.v0
    if t > data.v1:
        t = data.v1
    num = [0.0, 0.0, 0.0]
    den = 0.0
    for index in range(data.K + 1):
        basis = bsplineBasis(t, data.knots, data.M, index)
        weight = data.weights[index] * basis
        num = vec_add(num, vec_scale(data.control_points[index], weight))
        den += weight
    if den == 0:
        return [0.0, 0.0, 0.0]
    return [num[0] / den, num[1] / den, num[2] / den]


def bsplineSurfacePoint(data: Obj | dict[str, Any], u: float, v: float) -> list[float]:
    data = obj(data)
    u = min(max(u, data.u0), data.u1)
    v = min(max(v, data.v0), data.v1)
    num = [0.0, 0.0, 0.0]
    den = 0.0
    for i in range(data.K1 + 1):
        bi = bsplineBasis(u, data.knots_u, data.M1, i)
        for j in range(data.K2 + 1):
            bj = bsplineBasis(v, data.knots_v, data.M2, j)
            idx = i * (data.K2 + 1) + j
            weight = data.weights[idx] * bi * bj
            num = vec_add(num, vec_scale(data.control_points[idx], weight))
            den += weight
    if den == 0:
        return [0.0, 0.0, 0.0]
    return [num[0] / den, num[1] / den, num[2] / den]


def splineSurfacePoint(data: Obj | dict[str, Any], u: float, v: float) -> list[float]:
    data = obj(data)
    pi = 0
    pj = 0
    for index in range(data.M):
        if u >= data.tu[index] and (index == data.M - 1 or u <= data.tu[index + 1]):
            pi = index
            break
    for index in range(data.N):
        if v >= data.tv[index] and (index == data.N - 1 or v <= data.tv[index + 1]):
            pj = index
            break
    s_local = u - data.tu[pi]
    t_local = v - data.tv[pj]
    patch = data.patches[pi * data.N + pj]
    x = y = z = 0.0
    for p in range(4):
        tp = t_local**p
        for q in range(4):
            sq = s_local**q
            idx = 4 * p + q
            x += patch.coeff_x[idx] * sq * tp
            y += patch.coeff_y[idx] * sq * tp
            z += patch.coeff_z[idx] * sq * tp
    return [x, y, z]


def ruledSurfacePoint(data: Obj | dict[str, Any], form: int, t: float, s: float, resolver: Any) -> list[float]:
    data = obj(data)
    c1 = resolver(data.de1)
    c2 = resolver(data.de2)
    if not c1 or not c2:
        raise IgesError(make_diag("error", 0, SECTION.PARAMETER, "Ruled Surface has invalid DE pointer for de1 or de2", "§4.17"))
    if form == 0:
        sp1 = curveNativeSpan(c1.type, c1.form, c1.data)
        sp2 = curveNativeSpan(c2.type, c2.form, c2.data)
        u1 = sp1[0] + t * (sp1[1] - sp1[0])
        u2 = sp2[1] + t * (sp2[0] - sp2[1]) if data.dirflg == 1 else sp2[0] + t * (sp2[1] - sp2[0])
    else:
        u1 = t
        u2 = -t if data.dirflg == 1 else t
    p1 = sampleCurvePoint(c1, u1, resolver)
    p2 = sampleCurvePoint(c2, u2, resolver)
    return [
        (1 - s) * p1[0] + s * p2[0],
        (1 - s) * p1[1] + s * p2[1],
        (1 - s) * p1[2] + s * p2[2],
    ]


def rotateAroundAxis(point: list[float], origin: list[float], axis: list[float], theta: float) -> list[float]:
    vector = vec_sub(point, origin)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)
    term1 = vec_scale(vector, cos_theta)
    term2 = vec_scale(vec_cross(axis, vector), sin_theta)
    term3 = vec_scale(axis, vec_dot(axis, vector) * (1 - cos_theta))
    return vec_add(origin, vec_add(vec_add(term1, term2), term3))


def surfaceOfRevolutionPoint(data: Obj | dict[str, Any], t: float, s: float, resolver: Any) -> list[float]:
    data = obj(data)
    axis_line = resolver(data.l)
    generatrix = resolver(data.c)
    if not axis_line or not generatrix:
        raise IgesError(make_diag("error", 0, SECTION.PARAMETER, "Surface of Revolution has invalid DE pointer", "§4.18"))
    axis = vec_norm(vec_sub(axis_line.data.terminate, axis_line.data.start))
    generator_point = sampleCurvePoint(generatrix, t, resolver)
    return rotateAroundAxis(generator_point, axis_line.data.start, axis, s)


def tabulatedCylinderPoint(data: Obj | dict[str, Any], t: float, s: float, resolver: Any) -> list[float]:
    data = obj(data)
    directrix = resolver(data.de)
    if not directrix:
        raise IgesError(make_diag("error", 0, SECTION.PARAMETER, "Tabulated Cylinder has invalid directrix DE pointer", "§4.19"))
    span = curveNativeSpan(directrix.type, directrix.form, directrix.data)
    start_point = sampleCurvePoint(directrix, span[0], resolver)
    directrix_point = sampleCurvePoint(directrix, t, resolver)
    generator = vec_sub(data.terminate_point, start_point)
    return vec_add(directrix_point, vec_scale(generator, s))


def numericalSurfaceNormal(entity_type: int, form: int, xform_de: int, data: Obj, u: float, v: float, resolver: Any) -> list[float]:
    eps = 1e-4
    point = evaluateEntity(entity_type, form, xform_de, data, u, v, resolver, True)["point"]
    pu = evaluateEntity(entity_type, form, xform_de, data, u + eps, v, resolver, True)["point"]
    pv = evaluateEntity(entity_type, form, xform_de, data, u, v + eps, resolver, True)["point"]
    return vec_norm(vec_cross(vec_sub(pu, point), vec_sub(pv, point)))


def analyticSurfaceBasis(entity_type: int, form: int, data: Obj | dict[str, Any], resolver: Any) -> Obj | None:
    data = obj(data)
    deloc = resolver(data.deloc)
    if not deloc:
        return None
    origin = deloc.data.coords or [0, 0, 0]
    if entity_type == 190:
        normal = resolver(data.denrml)
        ref_dir = resolver(data.derefd) if data.derefd else None
        if not normal:
            return None
        z_axis = vec_norm([normal.data.x, normal.data.y, normal.data.z])
        if ref_dir:
            direction = [ref_dir.data.x, ref_dir.data.y, ref_dir.data.z]
            x_axis = vec_norm(vec_sub(direction, vec_scale(z_axis, vec_dot(direction, z_axis))))
        else:
            x_axis = [1.0, 0.0, 0.0]
        y_axis = vec_cross(z_axis, x_axis)
        return obj({"C": origin, "x": x_axis, "y": y_axis, "z": z_axis})
    if entity_type in {192, 194, 198} or (entity_type == 196 and form == 1):
        axis = resolver(data.deaxis)
        ref_dir = resolver(data.derefd) if data.derefd else None
        if not axis:
            return None
        z_axis = vec_norm([axis.data.x, axis.data.y, axis.data.z])
        if ref_dir:
            direction = [ref_dir.data.x, ref_dir.data.y, ref_dir.data.z]
            x_axis = vec_norm(vec_sub(direction, vec_scale(z_axis, vec_dot(direction, z_axis))))
        else:
            x_axis = [1.0, 0.0, 0.0]
        y_axis = vec_cross(z_axis, x_axis)
        return obj({"C": origin, "x": x_axis, "y": y_axis, "z": z_axis})
    return None


def analyticSurfacePoint(entity_type: int, form: int, data: Obj | dict[str, Any], u: float, v: float, resolver: Any) -> list[float]:
    basis = analyticSurfaceBasis(entity_type, form, data, resolver)
    if not basis:
        raise IgesError(
            make_diag("error", 0, SECTION.PARAMETER, f"Analytic surface type {entity_type} is missing required references", "§§4.50-4.54")
        )
    data = obj(data)
    dr = lambda angle: angle * math.pi / 180.0
    if entity_type == 190:
        return vec_add(basis.C, vec_add(vec_scale(basis.x, u), vec_scale(basis.y, v)))
    if entity_type == 192:
        u_r = dr(u)
        radial = vec_add(vec_scale(basis.x, data.radius * math.cos(u_r)), vec_scale(basis.y, data.radius * math.sin(u_r)))
        return vec_add(basis.C, vec_add(radial, vec_scale(basis.z, v)))
    if entity_type == 194:
        u_r = dr(u)
        s_r = dr(data.sangle)
        radius = data.radius + v * math.tan(s_r)
        radial = vec_add(vec_scale(basis.x, radius * math.cos(u_r)), vec_scale(basis.y, radius * math.sin(u_r)))
        return vec_add(basis.C, vec_add(radial, vec_scale(basis.z, v)))
    if entity_type == 196:
        u_r = dr(u)
        v_r = dr(v)
        horiz = vec_add(vec_scale(basis.x, math.cos(u_r)), vec_scale(basis.y, math.sin(u_r)))
        radial = vec_scale(horiz, data.radius * math.cos(v_r))
        return vec_add(basis.C, vec_add(radial, vec_scale(basis.z, data.radius * math.sin(v_r))))
    if entity_type == 198:
        u_r = dr(u)
        v_r = dr(v)
        coeff = data.majrad + data.minrad * math.cos(u_r)
        horiz = vec_add(vec_scale(basis.x, math.cos(v_r)), vec_scale(basis.y, -math.sin(v_r)))
        return vec_add(basis.C, vec_add(vec_scale(horiz, coeff), vec_scale(basis.z, data.minrad * math.sin(u_r))))
    raise IgesError(make_diag("error", 0, SECTION.PARAMETER, f"Unsupported analytic surface type {entity_type}", "§§4.50-4.54"))


def surfaceNormal(entity_type: int, form: int, data: Obj | dict[str, Any], u: float, v: float, resolver: Any) -> list[float] | None:
    if entity_type not in {190, 192, 194, 196, 198}:
        return None
    basis = analyticSurfaceBasis(entity_type, form, data, resolver)
    if not basis:
        return None
    data = obj(data)
    dr = lambda angle: angle * math.pi / 180.0
    if entity_type == 190:
        return basis.z
    if entity_type == 192:
        u_r = dr(u)
        return vec_add(vec_scale(basis.x, math.cos(u_r)), vec_scale(basis.y, math.sin(u_r)))
    if entity_type == 194:
        u_r = dr(u)
        s_r = dr(data.sangle)
        radial = vec_add(vec_scale(basis.x, math.cos(u_r)), vec_scale(basis.y, math.sin(u_r)))
        return vec_norm(vec_sub(vec_scale(radial, math.cos(s_r)), vec_scale(basis.z, math.sin(s_r))))
    if entity_type == 196:
        u_r = dr(u)
        v_r = dr(v)
        horiz = vec_add(vec_scale(basis.x, math.cos(u_r)), vec_scale(basis.y, math.sin(u_r)))
        return vec_add(vec_scale(horiz, math.cos(v_r)), vec_scale(basis.z, math.sin(v_r)))
    if entity_type == 198:
        u_r = dr(u)
        v_r = dr(v)
        horiz = vec_add(vec_scale(basis.x, math.cos(v_r)), vec_scale(basis.y, -math.sin(v_r)))
        return vec_add(vec_scale(horiz, math.cos(u_r)), vec_scale(basis.z, math.sin(u_r)))
    return None


def surfaceRefParams(entity_type: int, form: int, data: Obj | dict[str, Any], resolver: Any) -> Obj:
    data = obj(data)
    if entity_type == 114:
        return obj({"u": 0.5 * (data.tu[0] + data.tu[-1]), "v": 0.5 * (data.tv[0] + data.tv[-1])})
    if entity_type == 118:
        if form == 1:
            c1 = resolver(data.de1) if resolver else None
            if c1:
                span = curveNativeSpan(c1.type, c1.form, c1.data)
                return obj({"u": 0.5 * (span[0] + span[1]), "v": 0.5})
        return obj({"u": 0.5, "v": 0.5})
    if entity_type == 120:
        curve = resolver(data.c) if resolver else None
        if curve:
            span = curveNativeSpan(curve.type, curve.form, curve.data)
            return obj({"u": 0.5 * (span[0] + span[1]), "v": 0.5 * (data.sa + data.ta)})
        return obj({"u": 0.0, "v": 0.0})
    if entity_type == 122:
        directrix = resolver(data.de) if resolver else None
        if directrix:
            span = curveNativeSpan(directrix.type, directrix.form, directrix.data)
            return obj({"u": 0.5 * (span[0] + span[1]), "v": 0.5})
        return obj({"u": 0.0, "v": 0.5})
    if entity_type == 128:
        return obj({"u": 0.5 * (data.u0 + data.u1), "v": 0.5 * (data.v0 + data.v1)})
    if entity_type == 140:
        base = resolver(data.de) if resolver else None
        if base:
            return surfaceRefParams(base.type, base.form, base.data, resolver)
        return obj({"u": 0.0, "v": 0.0})
    if entity_type in {190, 192, 194, 196, 198}:
        return obj({"u": 0.0, "v": 0.0})
    return obj({"u": 0.0, "v": 0.0})


def offsetSurfacePoint(data: Obj | dict[str, Any], t: float, s: float, resolver: Any) -> list[float]:
    data = obj(data)
    base = resolver(data.de)
    if not base:
        raise IgesError(
            make_diag("error", 0, SECTION.PARAMETER, f"Offset Surface has invalid base surface DE pointer {data.de}", "§4.30")
        )
    base_point = evaluateEntity(base.type, base.form, base.xform_de, base.data, t, s, resolver, True)["point"]
    normal = surfaceNormal(base.type, base.form, base.data, t, s, resolver)
    if not normal:
        normal = numericalSurfaceNormal(base.type, base.form, base.xform_de, base.data, t, s, resolver)
    indicator = [data.nx, data.ny, data.nz]
    ref_params = surfaceRefParams(base.type, base.form, base.data, resolver)
    ref_normal = surfaceNormal(base.type, base.form, base.data, ref_params.u, ref_params.v, resolver)
    if not ref_normal:
        ref_normal = numericalSurfaceNormal(base.type, base.form, base.xform_de, base.data, ref_params.u, ref_params.v, resolver)
    if ref_normal and vec_dot(ref_normal, indicator) < 0:
        normal = vec_scale(normal, -1)
    return vec_add(base_point, vec_scale(normal, data.d))


def evaluateEntity(entity_type: int, form: int, xform_de: int, data: Any, t: float, s: float | None, resolver: Any, no_xform: bool = False) -> dict[str, Any]:
    data = obj(data)
    point: list[float] | None = None

    if entity_type == 110:
        point = vec_add(data.start, vec_scale(vec_sub(data.terminate, data.start), t))
    elif entity_type == 100:
        radius = math.sqrt((data.x2 - data.x1) ** 2 + (data.y2 - data.y1) ** 2)
        point = [data.x1 + radius * math.cos(t), data.y1 + radius * math.sin(t), data.zt]
    elif entity_type == 104:
        if form == 1:
            a = math.sqrt(-data.F / data.A)
            b = math.sqrt(-data.F / data.C)
            point = [a * math.cos(t), b * math.sin(t), data.zt]
        elif form == 2:
            if data.F * data.A < 0 and data.F * data.C > 0:
                a = math.sqrt(-data.F / data.A)
                b = math.sqrt(data.F / data.C)
                point = [a / math.cos(t), b * math.tan(t), data.zt]
            else:
                a = math.sqrt(data.F / data.A)
                b = math.sqrt(-data.F / data.C)
                point = [a * math.tan(t), b / math.cos(t), data.zt]
        elif form == 3:
            point = [t, -(data.A / data.E) * t * t, data.zt]
        else:
            raise IgesError(make_diag("error", 0, SECTION.PARAMETER, f"Conic Arc form {form} not supported by eval", "§4.5"))
    elif entity_type == 106:
        idx_float = max(0, min(data.n - 1, t))
        index = max(0, min(data.n - 2, math.floor(idx_float)))
        frac = idx_float - index
        pa = sampleCopiousTuple(data, index)
        pb = sampleCopiousTuple(data, index + 1)
        point = [
            pa[0] + frac * (pb[0] - pa[0]),
            pa[1] + frac * (pb[1] - pa[1]),
            pa[2] + frac * (pb[2] - pa[2]),
        ]
    elif entity_type == 102:
        parts = [resolver(de) for de in data.constituents]
        spans: list[Obj] = []
        acc_total = 0.0
        for part in parts:
            if not part:
                continue
            if part.type in {116, 132}:
                spans.append(obj({"part": part, "span": [0, 0]}))
                continue
            span = curveNativeSpan(part.type, part.form, part.data)
            spans.append(obj({"part": part, "span": span}))
            acc_total += span[1] - span[0]
        acc = 0.0
        chosen = None
        local = t
        for entry in spans:
            width = entry.span[1] - entry.span[0]
            if t <= acc + width + 1e-12:
                chosen = entry
                local = t - acc + entry.span[0]
                break
            acc += width
        if chosen is None and spans:
            chosen = spans[-1]
            local = chosen.span[1]
        if not chosen:
            raise IgesError(make_diag("error", 0, SECTION.PARAMETER, "Composite Curve has no evaluable constituents", "§4.4"))
        point = evaluateEntity(chosen.part.type, chosen.part.form, chosen.part.xform_de, chosen.part.data, local, None, resolver, False)["point"]
    elif entity_type == 112:
        seg_index = 0
        while seg_index < len(data.segments) - 1 and t > data.breakpoints[seg_index + 1]:
            seg_index += 1
        local_t = t - data.breakpoints[seg_index]
        seg = data.segments[seg_index]
        point = [
            seg.ax + seg.bx * local_t + seg.cx * local_t * local_t + seg.dx * local_t * local_t * local_t,
            seg.ay + seg.by * local_t + seg.cy * local_t * local_t + seg.dy * local_t * local_t * local_t,
            seg.az + seg.bz * local_t + seg.cz * local_t * local_t + seg.dz * local_t * local_t * local_t,
        ]
    elif entity_type == 126:
        point = bsplineCurvePoint(data, t)
    elif entity_type == 128:
        point = bsplineSurfacePoint(data, t, 0.0 if s is None else s)
    elif entity_type == 130:
        base = resolver(data.de1)
        if not base:
            raise IgesError(make_diag("error", 0, SECTION.PARAMETER, f"Offset Curve has invalid base curve DE pointer {data.de1}", "§4.25"))
        if data.flag != 1:
            raise IgesError(
                make_diag(
                    "error",
                    0,
                    SECTION.PARAMETER,
                    f"Offset Curve evaluator supports only FLAG=1 (uniform offset); got FLAG={data.flag}",
                    "§4.25",
                )
            )
        base_pt = sampleCurvePoint(base, t, resolver)
        point = [base_pt[0] + data.d1 * data.vx, base_pt[1] + data.d1 * data.vy, base_pt[2] + data.d1 * data.vz]
    elif entity_type == 114:
        point = splineSurfacePoint(data, t, 0.0 if s is None else s)
    elif entity_type == 118:
        point = ruledSurfacePoint(data, form, t, 0.0 if s is None else s, resolver)
    elif entity_type == 120:
        point = surfaceOfRevolutionPoint(data, t, 0.0 if s is None else s, resolver)
    elif entity_type == 122:
        point = tabulatedCylinderPoint(data, t, 0.0 if s is None else s, resolver)
    elif entity_type == 140:
        point = offsetSurfacePoint(data, t, 0.0 if s is None else s, resolver)
    elif entity_type in {190, 192, 194, 196, 198}:
        point = analyticSurfacePoint(entity_type, form, data, t, 0.0 if s is None else s, resolver)
    else:
        raise IgesError(
            make_diag("error", 0, SECTION.PARAMETER, f"entity type {entity_type} is not parametric for iges eval", "§1.5")
        )

    if not no_xform:
        point = applyXform(point, xform_de, resolver)
    return {"point": point}


def cmdParse(args: Obj) -> int:
    try:
        text = read_file(args.input)
    except Exception as exc:  # noqa: BLE001
        write_json(args.output, make_error(str(exc), "§1", 0, "unknown"))
        return 1
    file_result = read_iges_file(text)
    if not file_result.ok:
        write_json(args.output, error_from_diagnostics(file_result.diagnostics))
        return 1
    diags = validate(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities}))
    if diags:
        write_json(args.output, error_from_diagnostics(diags))
        return 1
    try:
        canonical = build_canonical_json(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities}))
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, IgesError):
            write_json(args.output, error_from_diagnostics([exc.diag]))
            return 1
        write_json(args.output, make_error(str(exc), "§3", 0, "unknown"))
        return 1
    write_json(args.output, canonical)
    return 0


def cmdWrite(args: Obj) -> int:
    try:
        raw = Path(args.input).read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(json.dumps(make_error(str(exc), "§1")) + "\n")
        return 1
    try:
        payload = obj(json.loads(raw))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(json.dumps(make_error(f"JSON parse error: {exc}", "§2")) + "\n")
        return 1
    try:
        iges_file = build_iges_from_canonical_json(payload)
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, IgesError):
            sys.stderr.write(json.dumps(error_from_diagnostics([exc.diag])) + "\n")
            return 1
        sys.stderr.write(json.dumps(make_error(str(exc), "§3")) + "\n")
        return 1
    diags = validateWriteInput(iges_file)
    if diags:
        sys.stderr.write(json.dumps(error_from_diagnostics(diags)) + "\n")
        return 1
    out = write_iges_file(iges_file.start_lines, iges_file["global"], iges_file.entities)
    write_file(args.output, out)
    return 0


def cmdRoundtrip(args: Obj) -> int:
    try:
        text = read_file(args.input)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(json.dumps(make_error(str(exc), "§1")) + "\n")
        return 1
    file_result = read_iges_file(text)
    if not file_result.ok:
        sys.stderr.write(json.dumps(error_from_diagnostics(file_result.diagnostics)) + "\n")
        return 1
    diags = validate(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities}))
    if diags:
        sys.stderr.write(json.dumps(error_from_diagnostics(diags)) + "\n")
        return 1
    out = write_iges_file(file_result.start_lines, file_result["global"], file_result.entities)
    write_file(args.output, out)
    return 0


def cmdQuery(args: Obj) -> int:
    try:
        de = int(args.de, 10)
    except Exception:  # noqa: BLE001
        de = 0
    if de < 1 or de % 2 == 0:
        write_json(args.output, make_error(f"invalid --de {args.de}", "§1.2", 0, SECTION.DIRECTORY))
        return 1
    try:
        text = read_file(args.input)
    except Exception as exc:  # noqa: BLE001
        write_json(args.output, make_error(str(exc), "§1"))
        return 1
    file_result = read_iges_file(text)
    if not file_result.ok:
        write_json(args.output, error_from_diagnostics(file_result.diagnostics))
        return 1
    diags = validate(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities}))
    if diags:
        write_json(args.output, error_from_diagnostics(diags))
        return 1
    idx = (de - 1) // 2
    if idx < 0 or idx >= len(file_result.entities):
        write_json(args.output, make_error(f"DE index {de} out of range", "§1.2", 0, SECTION.DIRECTORY))
        return 1
    try:
        canonical = build_canonical_json(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities}))
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, IgesError):
            write_json(args.output, error_from_diagnostics([exc.diag]))
            return 1
        write_json(args.output, make_error(str(exc), "§3"))
        return 1
    write_json(args.output, canonical["entities"][idx])
    return 0


def cmdEval(args: Obj) -> int:
    try:
        de = int(args.de, 10)
    except Exception:  # noqa: BLE001
        de = 0
    if de < 1 or de % 2 == 0:
        write_json(args.output, make_error(f"invalid --de {args.de}", "§1.2", 0, SECTION.DIRECTORY))
        return 1
    if args.t is None:
        write_json(args.output, make_error("eval requires --t", "§1.5"))
        return 1
    t = float(args.t)
    s = float(args.s) if args.s is not None else None
    try:
        text = read_file(args.input)
    except Exception as exc:  # noqa: BLE001
        write_json(args.output, make_error(str(exc), "§1"))
        return 1
    file_result = read_iges_file(text)
    if not file_result.ok:
        write_json(args.output, error_from_diagnostics(file_result.diagnostics))
        return 1
    diags = validate(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities}))
    if diags:
        write_json(args.output, error_from_diagnostics(diags))
        return 1
    idx = (de - 1) // 2
    if idx < 0 or idx >= len(file_result.entities):
        write_json(args.output, make_error(f"DE index {de} out of range", "§1.2", 0, SECTION.DIRECTORY))
        return 1
    try:
        canonical = obj(build_canonical_json(obj({"start_lines": file_result.start_lines, "global": file_result["global"], "entities": file_result.entities})))
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, IgesError):
            write_json(args.output, error_from_diagnostics([exc.diag]))
            return 1
        write_json(args.output, make_error(str(exc), "§3"))
        return 1
    record = canonical.entities[idx]
    entity_type = record.entity.type
    form = record.entity.form
    is_curve = isCurveForEval(entity_type, form)
    is_surface = isSurfaceForEval(entity_type)
    if not is_curve and not is_surface:
        write_json(args.output, make_error(f"entity type {entity_type} is not parametric", "§1.5", 0, SECTION.PARAMETER))
        return 1
    if is_curve and s is not None:
        write_json(args.output, make_error("Curve entity does not accept --s", "§1.5", 0, SECTION.PARAMETER))
        return 1
    if is_surface and s is None:
        write_json(args.output, make_error("Surface entity requires --s", "§1.5", 0, SECTION.PARAMETER))
        return 1
    resolver = makeResolver(canonical)
    try:
        result = evaluateEntity(entity_type, form, record.directory_entry.xform_matrix or 0, record.entity.data, t, s, resolver, False)
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, IgesError):
            write_json(args.output, error_from_diagnostics([exc.diag]))
            return 1
        write_json(args.output, make_error(str(exc), "§3"))
        return 1
    write_json(
        args.output,
        {
            "ok": True,
            "point": result["point"],
            "tangent": None,
            "normal": None,
            "error": None,
        },
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if not args:
        sys.stderr.write(json.dumps(make_error("invalid arguments", "§1")) + "\n")
        return 1
    try:
        if args.subcommand == "parse":
            return cmdParse(args)
        if args.subcommand == "write":
            return cmdWrite(args)
        if args.subcommand == "query":
            return cmdQuery(args)
        if args.subcommand == "eval":
            return cmdEval(args)
        if args.subcommand == "roundtrip":
            return cmdRoundtrip(args)
        sys.stderr.write(json.dumps(make_error(f"unknown subcommand '{args.subcommand}'", "§1")) + "\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"iges: uncaught {exc}\n")
        return 2
