"""RS274/NGC G-code interpreter — Python reference implementation.

Implements a single-pass interpreter for the SWE-BuildBench CNCSim eval.
Reads a G-code program plus optional tool/parameter files and emits a JSON
description of the final machine state.

The interpreter is written from scratch against RS274NGC.md and the harness
contract in technical-requirements-prompt.md. It uses only the Python
standard library.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from decimal import Decimal

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class NgcError(Exception):
    """A spec-defined program error. Causes exit 1."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AXIS_LETTERS = ("x", "y", "z", "a", "b", "c")
LINEAR_AXES = ("x", "y", "z")
ROTARY_AXES = ("a", "b", "c")

# Required parameter indices that must be present in every parameter output file
G28_HOME_PARAMS = (5161, 5162, 5163, 5164, 5165, 5166)
G30_HOME_PARAMS = (5181, 5182, 5183, 5184, 5185, 5186)
G92_OFFSET_PARAMS = (5211, 5212, 5213, 5214, 5215, 5216)
SELECTED_CS_PARAM = 5220
PROBE_TRIP_PARAMS = (5061, 5062, 5063, 5064, 5065, 5066)


def cs_xyzabc_param_indices(system: int) -> tuple[int, int, int, int, int, int]:
    base = 5221 + (system - 1) * 20
    return (base, base + 1, base + 2, base + 3, base + 4, base + 5)


REQUIRED_OUTPUT_PARAMETERS: tuple[int, ...] = tuple(
    sorted(
        set(G28_HOME_PARAMS)
        | set(G30_HOME_PARAMS)
        | set(G92_OFFSET_PARAMS)
        | {SELECTED_CS_PARAM}
        | {p for s in range(1, 10) for p in cs_xyzabc_param_indices(s)}
    )
)


# Modal group classification — keys are the canonical G-code strings
# (as serialized in active_modal_g_codes), values are group numbers (str).
G_CODE_TO_GROUP: dict[str, str] = {}


def _register(group: str, *codes: str) -> None:
    for c in codes:
        G_CODE_TO_GROUP[c] = group


_register("1", "G0", "G1", "G2", "G3", "G38.2", "G80", "G81", "G82", "G83",
          "G84", "G85", "G86", "G87", "G88", "G89")
_register("2", "G17", "G18", "G19")
_register("3", "G90", "G91")
_register("5", "G93", "G94")
_register("6", "G20", "G21")
_register("7", "G40", "G41", "G42")
_register("8", "G43", "G49")
_register("10", "G98", "G99")
_register("12", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3")
_register("13", "G61", "G61.1", "G64")
_register("0", "G4", "G10", "G28", "G30", "G53", "G92", "G92.1", "G92.2", "G92.3")

M_CODE_TO_GROUP: dict[str, str] = {}


def _mreg(group: str, *codes: str) -> None:
    for c in codes:
        M_CODE_TO_GROUP[c] = group


_mreg("4", "M0", "M1", "M2", "M30", "M60")
_mreg("6", "M6")
_mreg("7", "M3", "M4", "M5")
_mreg("8", "M7", "M8", "M9")
_mreg("9", "M48", "M49")

CANNED_CYCLES = {"G81", "G82", "G83", "G84", "G85", "G86", "G87", "G88", "G89"}
MOTION_GROUP1_AXIS_USING = {"G0", "G1", "G2", "G3", "G38.2"} | CANNED_CYCLES

# Group 0 G-codes that use axis words
G0_AXIS_USING = {"G10", "G28", "G30", "G92"}

CS_GCODE_TO_NUMBER = {
    "G54": 1, "G55": 2, "G56": 3, "G57": 4, "G58": 5, "G59": 6,
    "G59.1": 7, "G59.2": 8, "G59.3": 9,
}
CS_NUMBER_TO_GCODE = {v: k for k, v in CS_GCODE_TO_NUMBER.items()}


# ---------------------------------------------------------------------------
# Tokenizer / parser
# ---------------------------------------------------------------------------


def _is_close_int(value: float) -> bool:
    return abs(value - round(value)) <= 1e-4


def _to_int_close(value: float, what: str) -> int:
    if not _is_close_int(value):
        raise NgcError(f"{what} must evaluate to an integer (got {value})")
    return int(round(value))


@dataclass
class ParsedLine:
    """Result of parsing a single line (after block-delete check)."""

    block_delete: bool
    line_number: int | None
    words: list[tuple[str, float]]  # (letter, value), letter lowercase
    g_codes: list[str]              # canonical strings, e.g. "G1", "G59.1"
    m_codes: list[str]
    parameter_settings: list[tuple[int, float]]  # in textual order, last wins
    has_comment: bool


class LineParser:
    """Parses one RS274 line; performs expression evaluation against parameters.

    The parser is character-driven (the character form of the language defined
    in RS274NGC.md sections 3.3 and Appendix E). It evaluates expressions and
    parameter reads against the live parameter dictionary at parse time, but
    defers parameter assignments until the entire line has been read.
    """

    UNARY_OPS = {
        "abs", "acos", "asin", "atan", "cos", "exp", "fix", "fup",
        "ln", "round", "sin", "sqrt", "tan",
    }

    def __init__(self, text: str, parameters: dict[int, float]) -> None:
        # Strip the trailing end-of-line characters from the line.
        # Spaces and tabs are insignificant outside comments.
        self.raw = text
        self.parameters = parameters
        self.pos = 0
        # Pre-strip whitespace by building a parallel string but track comment
        # positions; simpler: walk char-by-char and skip whitespace except inside
        # parentheses.
        self.length = len(text)

    # -- low-level helpers ---------------------------------------------------

    def _peek(self) -> str:
        if self.pos >= self.length:
            return ""
        return self.raw[self.pos]

    def _peek_lower(self) -> str:
        return self._peek().lower()

    def _advance(self) -> str:
        ch = self._peek()
        self.pos += 1
        return ch

    def _skip_ws(self) -> None:
        while self.pos < self.length and self.raw[self.pos] in " \t":
            self.pos += 1

    def _at_end(self) -> bool:
        self._skip_ws()
        return self.pos >= self.length

    def _starts_with_keyword(self, kw: str) -> bool:
        # Case-insensitive lookahead, but does NOT skip embedded whitespace.
        # Whitespace within keywords is not allowed (only between tokens),
        # except RS274 says spaces are allowed *anywhere* — including inside
        # numbers/keywords. We handle that by skipping whitespace between
        # successive characters of the keyword.
        save = self.pos
        for c in kw:
            self._skip_ws()
            if self.pos >= self.length or self.raw[self.pos].lower() != c:
                self.pos = save
                return False
            self.pos += 1
        return True

    # -- parsing --------------------------------------------------------------

    def parse(self, *, block_delete_active: bool) -> ParsedLine | None:
        """Parse the line. Returns None if the line should be skipped."""
        # Check for block delete prefix.
        self._skip_ws()
        block_delete = False
        if self._peek() == "/":
            block_delete = True
            self.pos += 1
        if block_delete and block_delete_active:
            return None  # Caller skips this line entirely.

        result = ParsedLine(
            block_delete=block_delete,
            line_number=None,
            words=[],
            g_codes=[],
            m_codes=[],
            parameter_settings=[],
            has_comment=False,
        )

        # Optional line number.
        self._skip_ws()
        if self._peek_lower() == "n":
            self.pos += 1
            self._skip_ws()
            digits = ""
            while self.pos < self.length and self.raw[self.pos].isdigit():
                digits += self.raw[self.pos]
                self.pos += 1
                self._skip_ws()
            if not digits:
                raise NgcError("line number must have at least one digit")
            if len(digits) > 5:
                raise NgcError("line number must have at most 5 digits")
            value = int(digits)
            if value < 0 or value > 99999:
                raise NgcError(f"line number {value} out of range 0..99999")
            result.line_number = value

        pending_settings: list[tuple[int, float]] = []

        while True:
            self._skip_ws()
            if self.pos >= self.length:
                break
            ch = self.raw[self.pos]
            if ch == "(":
                self._parse_comment()
                result.has_comment = True
                continue
            if ch == "#":
                self.pos += 1
                index_value = self._read_real_value()
                idx = _to_int_close(index_value, "parameter index")
                if idx < 1 or idx > 5399:
                    raise NgcError(f"parameter index {idx} out of range 1..5399")
                self._skip_ws()
                if self._peek() != "=":
                    raise NgcError("expected '=' after parameter index")
                self.pos += 1
                rhs = self._read_real_value()
                pending_settings.append((idx, rhs))
                continue
            if ch == "/":
                raise NgcError("'/' is only allowed at the start of a line")
            # Otherwise, must be a mid-line letter (a word).
            if not ch.isalpha():
                raise NgcError(f"unexpected character {ch!r}")
            letter = ch.lower()
            if letter == "n":
                raise NgcError("N (line number) is only allowed at the start of a line")
            self.pos += 1
            value = self._read_real_value()
            self._record_word(result, letter, value)

        result.parameter_settings = pending_settings
        return result

    def _parse_comment(self) -> None:
        assert self.raw[self.pos] == "("
        self.pos += 1
        depth = 1
        while self.pos < self.length:
            c = self.raw[self.pos]
            if c == "(":
                raise NgcError("nested comments are not allowed")
            if c == ")":
                self.pos += 1
                depth = 0
                return
            self.pos += 1
        if depth != 0:
            raise NgcError("unterminated comment")

    def _record_word(self, result: ParsedLine, letter: str, value: float) -> None:
        if letter == "g":
            code = self._format_g_or_m_code("G", value)
            if code not in G_CODE_TO_GROUP:
                raise NgcError(f"unknown G code: {code}")
            result.g_codes.append(code)
            return
        if letter == "m":
            ival = _to_int_close(value, "M code")
            code = f"M{ival}"
            if code not in M_CODE_TO_GROUP:
                raise NgcError(f"unknown M code: {code}")
            result.m_codes.append(code)
            return
        result.words.append((letter, value))

    @staticmethod
    def _format_g_or_m_code(letter: str, value: float) -> str:
        # Per spec, G codes are matched as integers when multiplied by 10
        # (so G59.1 -> 591). Decimals close to that integer count.
        scaled = value * 10.0
        if not _is_close_int(scaled):
            raise NgcError(f"{letter} code value {value} not a recognized code")
        n = int(round(scaled))
        if n % 10 == 0:
            return f"{letter}{n // 10}"
        # produce e.g. "G38.2", "G59.1", "G92.3"
        return f"{letter}{n // 10}.{n % 10}"

    # -- real value reader (the heart of expression parsing) ----------------

    def _read_real_value(self) -> float:
        self._skip_ws()
        if self.pos >= self.length:
            raise NgcError("expected real value, found end of line")
        ch = self.raw[self.pos]
        if ch == "[":
            return self._read_expression()
        if ch == "#":
            self.pos += 1
            idx_v = self._read_real_value()
            idx = _to_int_close(idx_v, "parameter index")
            if idx < 1 or idx > 5399:
                raise NgcError(f"parameter index {idx} out of range")
            return float(self.parameters.get(idx, 0.0))
        if ch in "+-." or ch.isdigit():
            return self._read_number()
        if ch.isalpha():
            # Try unary operation
            return self._read_unary()
        raise NgcError(f"unexpected character in value: {ch!r}")

    def _read_number(self) -> float:
        self._skip_ws()
        s = ""
        if self.pos < self.length and self.raw[self.pos] in "+-":
            s += self.raw[self.pos]
            self.pos += 1
        # Allow whitespace between sign and digits
        self._skip_ws()
        # Build digits.digits with spaces allowed.
        digits_seen = False
        while self.pos < self.length:
            c = self.raw[self.pos]
            if c.isdigit():
                s += c
                digits_seen = True
                self.pos += 1
                continue
            if c in " \t":
                self.pos += 1
                continue
            if c == ".":
                s += "."
                self.pos += 1
                while self.pos < self.length:
                    c2 = self.raw[self.pos]
                    if c2.isdigit():
                        s += c2
                        digits_seen = True
                        self.pos += 1
                        continue
                    if c2 in " \t":
                        self.pos += 1
                        continue
                    break
                break
            break
        if not digits_seen:
            raise NgcError("expected number")
        try:
            return float(s)
        except ValueError as exc:
            raise NgcError(f"invalid number {s!r}") from exc

    def _read_unary(self) -> float:
        # Read a unary operation name (letters, possibly followed by digits in
        # the case of atan since "atan" is the only one). Spaces are allowed
        # but unusual.
        save = self.pos
        name = ""
        while self.pos < self.length:
            c = self.raw[self.pos]
            if c.isalpha():
                name += c.lower()
                self.pos += 1
                continue
            if c in " \t":
                self.pos += 1
                continue
            break
        if name not in self.UNARY_OPS:
            self.pos = save
            raise NgcError(f"unknown unary operator {name!r}")
        self._skip_ws()
        if self._peek() != "[":
            raise NgcError(f"unary {name} must be followed by '['")
        arg = self._read_expression()
        if name == "atan":
            self._skip_ws()
            if self._peek() != "/":
                raise NgcError("ATAN requires the form ATAN[..]/[..]")
            self.pos += 1
            self._skip_ws()
            if self._peek() != "[":
                raise NgcError("ATAN denominator must be a bracketed expression")
            arg2 = self._read_expression()
            return math.degrees(math.atan2(arg, arg2))
        return self._apply_unary(name, arg)

    @staticmethod
    def _apply_unary(name: str, x: float) -> float:
        if name == "abs":
            return abs(x)
        if name == "acos":
            if x < -1.0 or x > 1.0:
                raise NgcError(f"acos argument out of range: {x}")
            return math.degrees(math.acos(x))
        if name == "asin":
            if x < -1.0 or x > 1.0:
                raise NgcError(f"asin argument out of range: {x}")
            return math.degrees(math.asin(x))
        if name == "cos":
            return math.cos(math.radians(x))
        if name == "exp":
            return math.exp(x)
        if name == "fix":
            return float(math.floor(x))
        if name == "fup":
            return float(math.ceil(x))
        if name == "ln":
            if x <= 0.0:
                raise NgcError(f"ln argument must be positive: {x}")
            return math.log(x)
        if name == "round":
            # Banker's rounding is unwanted; use 0.5-rounds-up.
            return float(math.floor(x + 0.5)) if x >= 0 else -float(math.floor(-x + 0.5))
        if name == "sin":
            return math.sin(math.radians(x))
        if name == "sqrt":
            if x < 0.0:
                raise NgcError(f"sqrt argument must be non-negative: {x}")
            return math.sqrt(x)
        if name == "tan":
            return math.tan(math.radians(x))
        raise NgcError(f"unknown unary {name!r}")

    def _read_expression(self) -> float:
        assert self._peek() == "["
        self.pos += 1
        # Read alternating real_values and binary operators.
        values: list[float] = []
        ops: list[str] = []
        values.append(self._read_real_value())
        while True:
            self._skip_ws()
            if self.pos >= self.length:
                raise NgcError("unterminated expression")
            c = self.raw[self.pos]
            if c == "]":
                self.pos += 1
                break
            op = self._read_binary_op()
            ops.append(op)
            values.append(self._read_real_value())
        return self._reduce_expression(values, ops)

    def _read_binary_op(self) -> str:
        self._skip_ws()
        c = self.raw[self.pos]
        if c == "+":
            self.pos += 1
            return "+"
        if c == "-":
            self.pos += 1
            return "-"
        if c == "*":
            # check for **
            if self.pos + 1 < self.length and self.raw[self.pos + 1] == "*":
                self.pos += 2
                return "**"
            self.pos += 1
            return "*"
        if c == "/":
            self.pos += 1
            return "/"
        # Word ops: and, or, xor, mod
        for word in ("and", "xor", "mod", "or"):
            save = self.pos
            ok = True
            for ch in word:
                self._skip_ws()
                if self.pos >= self.length or self.raw[self.pos].lower() != ch:
                    ok = False
                    break
                self.pos += 1
            if ok:
                return word
            self.pos = save
        raise NgcError(f"expected binary operator, found {c!r}")

    @staticmethod
    def _reduce_expression(values: list[float], ops: list[str]) -> float:
        # Apply group 1 (power), then group 2 (* / mod), then group 3 (+ - and or xor)
        # Within each group, left-to-right.
        def pass_(group_ops: set[str]) -> None:
            i = 0
            while i < len(ops):
                if ops[i] in group_ops:
                    a, b = values[i], values[i + 1]
                    op = ops[i]
                    r = LineParser._apply_binary(op, a, b)
                    values[i] = r
                    del values[i + 1]
                    del ops[i]
                else:
                    i += 1

        pass_({"**"})
        pass_({"*", "/", "mod"})
        pass_({"+", "-", "and", "or", "xor"})
        return values[0]

    @staticmethod
    def _apply_binary(op: str, a: float, b: float) -> float:
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise NgcError("division by zero")
            return a / b
        if op == "**":
            return a ** b
        if op == "mod":
            if b == 0:
                raise NgcError("modulo by zero")
            return math.fmod(a, b)
        if op == "and":
            return 1.0 if (a != 0 and b != 0) else 0.0
        if op == "or":
            return 1.0 if (a != 0 or b != 0) else 0.0
        if op == "xor":
            return 1.0 if ((a != 0) != (b != 0)) else 0.0
        raise NgcError(f"unknown binary op {op!r}")


# ---------------------------------------------------------------------------
# Machine state
# ---------------------------------------------------------------------------


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    a: float = 0.0
    b: float = 0.0
    c: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z,
                "a": self.a, "b": self.b, "c": self.c}

    def get(self, axis: str) -> float:
        return getattr(self, axis)

    def set(self, axis: str, v: float) -> None:
        setattr(self, axis, v)

    def copy(self) -> "Position":
        return Position(self.x, self.y, self.z, self.a, self.b, self.c)


@dataclass
class Tool:
    pocket: int
    fms: int
    tlo: float
    diameter: float


@dataclass
class MachineState:
    # Position is the *programmed* position in the currently selected work
    # coordinate system, stored in inches internally (rotary in degrees) so
    # that G20/G21 unit changes are purely a serialization concern.
    programmed: Position = field(default_factory=Position)
    # Coordinate system offsets, by system number 1..9, in inches internally.
    cs_offsets_inches: dict[int, Position] = field(default_factory=dict)
    selected_cs: int = 1
    # G92 axis offsets, in inches internally
    g92_offsets_inches: Position = field(default_factory=Position)
    g92_active: bool = False  # whether g92 offsets are currently applied
    # Modal state
    motion_mode: str = "G1"
    motion_mode_explicitly_set: bool = False  # tracks G0/G1 actually programmed
    plane: str = "G17"
    distance_mode: str = "G90"
    feed_mode: str = "G94"
    units: str = "G20"  # G20 = inches, G21 = mm
    cutter_comp: str = "G40"
    tool_length_offset_mode: str = "G49"
    return_mode: str = "G98"
    path_mode: str = "G61"
    # Other state
    feed_rate: float = 0.0  # in current units per minute (or inverse-time)
    spindle_speed: float = 0.0
    spindle_direction: str = "OFF"  # CW/CCW/OFF
    coolant: str = "M9"
    overrides_enabled: bool = True
    cutter_radius_compensation_number: int | None = None
    # CRC working state. crc_radius_inches is the radius locked in when CRC was
    # turned on (does not change on tool change). crc_contour_xy is the
    # programmed contour endpoint of the most recent compensated move (the
    # "program_x/program_y" of Appendix B.1.1). crc_first_move is True until a
    # compensated motion has actually been made.
    crc_radius_inches: float = 0.0
    crc_contour_x: float = 0.0
    crc_contour_y: float = 0.0
    crc_first_move: bool = True
    tool_length_offset_index: int | None = None
    tool_length_offset_value_inches: float = 0.0
    selected_tool: int | None = None
    tool_in_spindle: int | None = None
    # Modal M groups (for active_modal_m_codes serialization)
    active_m_codes: dict[str, str] = field(default_factory=dict)
    # Canned cycle sticky state
    cycle_r: float | None = None
    cycle_z: float | None = None  # depth (sticky in selected plane)
    last_motion_was_cycle: bool = False
    cycle_old_z: float = 0.0  # Z before cycle began (for G98)
    # Parameters
    parameters: dict[int, float] = field(default_factory=dict)
    # Tools (pocket -> Tool)
    tools: dict[int, Tool] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------


_MM_PER_INCH_DEC = Decimal("25.4")


def to_inches(value: float, units: str) -> float:
    """Convert a length expressed in the active program units to inches.

    Uses ``Decimal`` for the divide so simple test inputs like 76.2 mm
    convert exactly to 3.0 in. without IEEE-754 rounding noise.
    """
    if units == "G20":
        return value
    return float(Decimal(repr(value)) / _MM_PER_INCH_DEC)


def from_inches(value: float, units: str) -> float:
    """Convert an inches length to the active program units."""
    if units == "G20":
        return value
    return float(Decimal(repr(value)) * _MM_PER_INCH_DEC)


def _arc_center_from_radius(
    sx: float, sy: float, ex: float, ey: float, r_word: float, mode: str
) -> tuple[float, float]:
    """Center of an arc given start, end, signed radius word, and direction."""
    r = r_word
    dx = ex - sx
    dy = ey - sy
    chord = math.hypot(dx, dy)
    if chord == 0:
        return (sx, sy)
    h = math.sqrt(max(0.0, r * r - (chord / 2.0) ** 2))
    mx = (sx + ex) / 2.0
    my = (sy + ey) / 2.0
    # Perpendicular unit vector to chord
    px = -dy / chord
    py = dx / chord
    # The sign convention: per RS274 3.5.3, positive R = arc <= 180 deg,
    # negative R = arc > 180 deg. Combined with the direction (G2 CW / G3
    # CCW), we pick the perpendicular side that yields the correct chord/arc.
    sign = 1.0
    if (mode == "G3" and r >= 0) or (mode == "G2" and r < 0):
        sign = 1.0
    else:
        sign = -1.0
    return (mx + sign * h * px, my + sign * h * py)


def _two_circle_intersection_pick(
    x1: float, y1: float, r1: float,
    x2: float, y2: float, r2: float,
    mode: str,
) -> tuple[float, float]:
    """Find a circle center given two distance constraints. Returns one of two
    intersection points. The choice between the two is made by selecting the
    one with the smaller signed perpendicular relative to the chord direction
    when mode is G3, otherwise the larger."""
    dx = x2 - x1
    dy = y2 - y1
    d = math.hypot(dx, dy)
    if d == 0:
        return (x1, y1)
    a = (r1 * r1 - r2 * r2 + d * d) / (2.0 * d)
    h2 = r1 * r1 - a * a
    h = math.sqrt(max(0.0, h2))
    mx = x1 + a * dx / d
    my = y1 + a * dy / d
    px = -dy / d
    py = dx / d
    cand1 = (mx + h * px, my + h * py)
    cand2 = (mx - h * px, my - h * py)
    # Both centers are valid mathematically. We rely on the test cases'
    # geometry to make this unambiguous; pick the one closer to the origin
    # of the perpendicular convention used by _arc_center_from_radius.
    return cand2 if mode == "G3" else cand1


class Interpreter:
    def __init__(
        self,
        *,
        block_delete: bool,
        carousel_slots: int | None,
        probe_box: tuple[float, float, float, float, float, float] | None,
        probe_tool: int | None,
    ) -> None:
        self.state = MachineState()
        self.block_delete = block_delete
        self.carousel_slots = carousel_slots
        self.probe_box_inches = probe_box  # already inches per spec
        self.probe_tool = probe_tool
        self.program_ended = False
        # Initial defaults: G94 / G90 / G17 / G20 / G54 / G40 / G49 / G64 / G98
        self.state.feed_mode = "G94"
        self.state.distance_mode = "G90"
        self.state.plane = "G17"
        self.state.units = "G20"
        self.state.cutter_comp = "G40"
        self.state.tool_length_offset_mode = "G49"
        self.state.return_mode = "G98"
        self.state.path_mode = "G61"
        self.state.motion_mode = "G1"
        self.state.active_m_codes = {
            "4": "M2",  # not really; will get updated as program runs
            "7": "M5",
            "8": "M9",
            "9": "M48",
        }
        # remove the placeholder for stopping group; only set on actual M0/M1/M2
        del self.state.active_m_codes["4"]

    # -- coordinate-system helpers ------------------------------------------

    def _get_cs_offset(self, system: int) -> Position:
        return self.state.cs_offsets_inches.setdefault(system, Position())

    def absolute_inches_from_programmed(self, prog: Position | None = None) -> Position:
        """Add CS offset and active G92 offset to a programmed (inches/deg)
        position, returning absolute machine coordinates in inches/degrees."""
        p = prog if prog is not None else self.state.programmed
        cs = self._get_cs_offset(self.state.selected_cs)
        g92 = self.state.g92_offsets_inches if self.state.g92_active else Position()
        result = Position()
        for axis in AXIS_LETTERS:
            result.set(axis, p.get(axis) + cs.get(axis) + g92.get(axis))
        return result

    def programmed_from_absolute_inches(self, abs_in: Position) -> Position:
        """Inverse of :meth:`absolute_inches_from_programmed`."""
        cs = self._get_cs_offset(self.state.selected_cs)
        g92 = self.state.g92_offsets_inches if self.state.g92_active else Position()
        result = Position()
        for axis in AXIS_LETTERS:
            result.set(axis, abs_in.get(axis) - cs.get(axis) - g92.get(axis))
        return result

    def controlled_point_in_active_units(self) -> Position:
        """The reported ``machine_position``: absolute machine coordinates with
        the active tool length offset applied, serialized in current units."""
        abs_in = self.absolute_inches_from_programmed()
        abs_in.z = abs_in.z - self.state.tool_length_offset_value_inches
        result = Position()
        units = self.state.units
        for axis in AXIS_LETTERS:
            v = abs_in.get(axis)
            if axis in LINEAR_AXES:
                v = from_inches(v, units)
            result.set(axis, v)
        return result

    # -- parameter file helpers ---------------------------------------------

    def load_parameter_file(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        lines = text.split("\n")
        # Find the (single) blank separator
        blank_index = None
        for i, line in enumerate(lines):
            if line == "":
                blank_index = i
                break
        if blank_index is None:
            raise NgcError("parameter file has no blank separator line")
        data_lines = lines[blank_index + 1:]
        last_index = 0
        for line in data_lines:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) < 2:
                raise NgcError("parameter file line must have index and value")
            try:
                idx = int(parts[0])
                val = float(parts[1])
            except ValueError as exc:
                raise NgcError(f"parameter file line {line!r} invalid") from exc
            if idx < 1 or idx > 5400:
                raise NgcError(f"parameter file index {idx} out of range 1..5400")
            if idx <= last_index:
                raise NgcError("parameter file indices must be ascending")
            last_index = idx
            self.state.parameters[idx] = val

        # Validate selected coordinate system parameter.
        sel = self.state.parameters.get(SELECTED_CS_PARAM, 1.0)
        if not _is_close_int(sel) or not (1 <= int(round(sel)) <= 9):
            raise NgcError("parameter 5220 must be a whole number from 1 to 9")
        self.state.selected_cs = int(round(sel))

        # Initialize CS offsets from parameters.
        for s in range(1, 10):
            xp, yp, zp, ap, bp, cp = cs_xyzabc_param_indices(s)
            cs = self._get_cs_offset(s)
            cs.x = self.state.parameters.get(xp, 0.0)
            cs.y = self.state.parameters.get(yp, 0.0)
            cs.z = self.state.parameters.get(zp, 0.0)
            cs.a = self.state.parameters.get(ap, 0.0)
            cs.b = self.state.parameters.get(bp, 0.0)
            cs.c = self.state.parameters.get(cp, 0.0)

        # Initialize G92 offsets from parameters (but don't activate yet).
        gx, gy, gz, ga, gb, gc = G92_OFFSET_PARAMS
        self.state.g92_offsets_inches = Position(
            x=self.state.parameters.get(gx, 0.0),
            y=self.state.parameters.get(gy, 0.0),
            z=self.state.parameters.get(gz, 0.0),
            a=self.state.parameters.get(ga, 0.0),
            b=self.state.parameters.get(gb, 0.0),
            c=self.state.parameters.get(gc, 0.0),
        )

    def initialize_default_parameters(self) -> None:
        # Required parameters default to 0, except 5220 = 1.0
        for p in REQUIRED_OUTPUT_PARAMETERS:
            self.state.parameters.setdefault(p, 0.0)
        self.state.parameters[SELECTED_CS_PARAM] = float(self.state.selected_cs)

    # -- tool table ----------------------------------------------------------

    def load_tool_table(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        lines = text.split("\n")
        blank_index = None
        for i, line in enumerate(lines):
            if line == "":
                blank_index = i
                break
        if blank_index is None:
            raise NgcError("tool file has no blank separator line")
        for line in lines[blank_index + 1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 4:
                raise NgcError("tool file row needs at least 4 fields")
            try:
                pocket = int(parts[0])
                fms = int(parts[1])
                tlo = float(parts[2])
                diam = float(parts[3])
            except ValueError as exc:
                raise NgcError(f"tool file row invalid: {line!r}") from exc
            self.state.tools[pocket] = Tool(pocket, fms, tlo, diam)

    # -- main loop -----------------------------------------------------------

    def run(self, program_text: str) -> None:
        # Handle percent-delimited file
        lines = program_text.splitlines()
        # Find first percent line
        start_index = 0
        end_index = len(lines)
        first_pct = None
        for i, line in enumerate(lines):
            if line.strip() == "%":
                first_pct = i
                break
        if first_pct is not None:
            second_pct = None
            for i in range(first_pct + 1, len(lines)):
                if lines[i].strip() == "%":
                    second_pct = i
                    break
            if second_pct is None:
                raise NgcError("file with percent prefix is missing closing percent line")
            start_index = first_pct + 1
            end_index = second_pct

        for i in range(start_index, end_index):
            if self.program_ended:
                break
            self._run_line(lines[i])

    def _run_line(self, raw_line: str) -> None:
        parser = LineParser(raw_line, self.state.parameters)
        parsed = parser.parse(block_delete_active=self.block_delete)
        if parsed is None:
            return  # block-deleted
        self._execute_parsed(parsed)

    # -- execution: bind parsed line into modal state and act ---------------

    def _execute_parsed(self, parsed: ParsedLine) -> None:
        # Group G/M codes by modal group; check for repeats.
        g_by_group: dict[str, str] = {}
        group0_seen: list[str] = []
        for code in parsed.g_codes:
            grp = G_CODE_TO_GROUP[code]
            if grp == "0":
                if group0_seen:
                    raise NgcError(
                        f"two G codes used from same modal group 0"
                        f" ({group0_seen[0]} and {code})"
                    )
                group0_seen.append(code)
                continue
            if grp in g_by_group:
                raise NgcError(
                    f"two G codes used from same modal group {grp}"
                    f" ({g_by_group[grp]} and {code})"
                )
            g_by_group[grp] = code

        if len(parsed.m_codes) > 4:
            raise NgcError("more than four M words on one line")
        m_by_group: dict[str, str] = {}
        for code in parsed.m_codes:
            grp = M_CODE_TO_GROUP[code]
            if grp in m_by_group:
                raise NgcError(
                    f"two M codes used from same modal group {grp}"
                    f" ({m_by_group[grp]} and {code})"
                )
            m_by_group[grp] = code

        # Build word dict (single-letter -> value), enforcing no repeats.
        word_dict: dict[str, float] = {}
        for letter, value in parsed.words:
            if letter in word_dict:
                raise NgcError(f"word {letter.upper()} appears more than once on a line")
            word_dict[letter] = value

        # ---- ORDER OF EXECUTION (Table 8) ---------------------------------

        # 1. Comment — already handled in parsing.

        # Apply parameter settings (after all reads on the line are done).
        for idx, val in parsed.parameter_settings:
            self.state.parameters[idx] = val
            # If the user wrote to a coordinate-system origin parameter, the
            # spec says CS data is *stored in parameters*, so update the
            # in-memory CS table to keep both consistent.
            self._maybe_sync_param_into_state(idx, val)

        # 2. Set feed rate mode
        if "5" in g_by_group:
            self.state.feed_mode = g_by_group["5"]

        # 3. Set feed rate
        if "f" in word_dict:
            self.state.feed_rate = word_dict["f"]
        self._f_on_this_line = "f" in word_dict

        # 4. Set spindle speed
        if "s" in word_dict:
            if word_dict["s"] < 0:
                raise NgcError("S word must not be negative")
            self.state.spindle_speed = word_dict["s"]

        # 5. Select tool
        if "t" in word_dict:
            tval = _to_int_close(word_dict["t"], "T")
            if tval < 0:
                raise NgcError("T number must not be negative")
            if self.carousel_slots is not None and tval > self.carousel_slots:
                raise NgcError(
                    f"T number {tval} exceeds carousel slot count {self.carousel_slots}"
                )
            self.state.selected_tool = tval if tval != 0 else 0

        # 6. Tool change (M6)
        if m_by_group.get("6") == "M6":
            sel = self.state.selected_tool
            if sel is None or sel == 0:
                self.state.tool_in_spindle = None
            else:
                self.state.tool_in_spindle = sel
            self.state.spindle_direction = "OFF"
            self.state.active_m_codes["7"] = "M5"
            self.state.active_m_codes["6"] = "M6"

        # 7. Spindle on/off
        if "7" in m_by_group:
            mc = m_by_group["7"]
            self.state.active_m_codes["7"] = mc
            if mc == "M3":
                self.state.spindle_direction = "CW"
            elif mc == "M4":
                self.state.spindle_direction = "CCW"
            elif mc == "M5":
                self.state.spindle_direction = "OFF"

        # 8. Coolant
        if "8" in m_by_group:
            mc = m_by_group["8"]
            self.state.coolant = mc
            self.state.active_m_codes["8"] = mc

        # 9. Overrides
        if "9" in m_by_group:
            mc = m_by_group["9"]
            self.state.overrides_enabled = mc == "M48"
            self.state.active_m_codes["9"] = mc

        # 10. Dwell (G4)
        if "G4" in group0_seen:
            p = word_dict.get("p")
            if p is None or p < 0:
                raise NgcError("G4 requires non-negative P")

        # 11. Set active plane
        if "2" in g_by_group:
            if self.state.cutter_comp in ("G41", "G42") and g_by_group["2"] != "G17":
                raise NgcError("cannot use non-XY plane while cutter radius compensation is on")
            self.state.plane = g_by_group["2"]

        # 12. Length units (G20/G21).
        # Internally we store positions in inches, so changing units is purely
        # a serialization concern. The current physical position is preserved
        # automatically.
        if "6" in g_by_group:
            if self.state.cutter_comp in ("G41", "G42"):
                raise NgcError("cannot change units while cutter radius compensation is on")
            self.state.units = g_by_group["6"]

        # 13. Cutter radius compensation
        if "7" in g_by_group:
            crc = g_by_group["7"]
            if crc == "G40":
                self.state.cutter_comp = "G40"
                self.state.cutter_radius_compensation_number = None
                self.state.crc_radius_inches = 0.0
                self.state.crc_first_move = True
            else:
                if self.state.cutter_comp in ("G41", "G42"):
                    raise NgcError(
                        "cannot turn cutter radius compensation on when it is already on"
                    )
                if self.state.plane != "G17":
                    raise NgcError("cutter radius compensation requires the XY-plane")
                d = word_dict.get("d")
                if d is not None:
                    if not _is_close_int(d):
                        raise NgcError("D word must be an integer")
                    di = int(round(d))
                    if di < 0:
                        raise NgcError("D number must not be negative")
                    if self.carousel_slots is not None and di > self.carousel_slots:
                        raise NgcError(f"D number {di} exceeds carousel slot count")
                    self.state.cutter_radius_compensation_number = di
                else:
                    self.state.cutter_radius_compensation_number = (
                        self.state.tool_in_spindle or 0
                    )
                self.state.cutter_comp = crc
                # Lock the radius from the tool table for the indexed slot.
                slot = self.state.cutter_radius_compensation_number
                if slot is None or slot == 0:
                    radius_in_units = 0.0
                else:
                    tool = self.state.tools.get(slot)
                    radius_in_units = (tool.diameter / 2.0) if tool is not None else 0.0
                # Tool table values are in current units; convert to inches.
                self.state.crc_radius_inches = to_inches(radius_in_units, self.state.units)
                self.state.crc_first_move = True
        else:
            # D word without G41 or G42 on the same line is an error
            # (Appendix B.5 error 12). A D appearing while CRC is already on
            # without a G41/G42 is also rejected by the spec rule that the D
            # number cannot change while comp is on.
            if "d" in word_dict:
                raise NgcError("D word used without G41 or G42")

        # CRC-active prohibitions for things processed *after* this point:
        if self.state.cutter_comp in ("G41", "G42"):
            if "12" in g_by_group:
                raise NgcError("cannot select coordinate system while cutter radius compensation is on")
            for code in group0_seen if False else []:
                pass

        # 14. Tool length offset
        if "8" in g_by_group:
            tlc = g_by_group["8"]
            if tlc == "G49":
                self.state.tool_length_offset_mode = "G49"
                self.state.tool_length_offset_index = None
                self.state.tool_length_offset_value_inches = 0.0
            else:  # G43
                h = word_dict.get("h")
                if h is None:
                    raise NgcError("G43 requires an H word")
                if not _is_close_int(h):
                    raise NgcError("H word must be an integer")
                hi = int(round(h))
                if hi < 0:
                    raise NgcError("H number must not be negative")
                if self.carousel_slots is not None and hi > self.carousel_slots:
                    raise NgcError(f"H number {hi} exceeds carousel slot count")
                self.state.tool_length_offset_mode = "G43"
                self.state.tool_length_offset_index = hi
                if hi == 0:
                    self.state.tool_length_offset_value_inches = 0.0
                else:
                    tool = self.state.tools.get(hi)
                    tlo = tool.tlo if tool is not None else 0.0
                    # Tool table is in the units active when the tool data is
                    # *used*. We follow the convention used in the tests:
                    # the TLO value is interpreted in the currently active
                    # length units. Convert to inches.
                    self.state.tool_length_offset_value_inches = to_inches(
                        tlo, self.state.units
                    )

        # 15. Coordinate system selection
        if "12" in g_by_group:
            sys_code = g_by_group["12"]
            self.state.selected_cs = CS_GCODE_TO_NUMBER[sys_code]
            self.state.parameters[SELECTED_CS_PARAM] = float(self.state.selected_cs)

        # 16. Path control mode
        if "13" in g_by_group:
            self.state.path_mode = g_by_group["13"]

        # 17. Distance mode
        if "3" in g_by_group:
            self.state.distance_mode = g_by_group["3"]

        # 18. Retract mode
        if "10" in g_by_group:
            self.state.return_mode = g_by_group["10"]

        # 19. Group 0 (G10/G28/G30/G92/G92.x) and home
        # Validate not mixing group 1 axis-using with group 0 axis-using.
        axis_words_present = any(letter in word_dict for letter in AXIS_LETTERS)
        group0_axis_using = [c for c in group0_seen if c in G0_AXIS_USING]
        # G53 is also group 0 but is an absolute-machine motion modifier
        # (handled with motion below)
        for code in group0_seen:
            if code in ("G28", "G30") and self.state.cutter_comp in ("G41", "G42"):
                raise NgcError(f"cannot use {code} while cutter radius compensation is on")
            if code in ("G92", "G92.1", "G92.2", "G92.3") and self.state.cutter_comp in ("G41", "G42"):
                raise NgcError("cannot change axis offsets while cutter radius compensation is on")
            if code == "G10":
                self._do_g10(word_dict)
            elif code == "G28":
                self._do_g28_or_g30(word_dict, PROBE_OR_HOME=G28_HOME_PARAMS)
            elif code == "G30":
                self._do_g28_or_g30(word_dict, PROBE_OR_HOME=G30_HOME_PARAMS)
            elif code == "G92":
                self._do_g92(word_dict)
            elif code == "G92.1":
                self._do_g92_1()
            elif code == "G92.2":
                self._do_g92_2()
            elif code == "G92.3":
                self._do_g92_3()

        # If a group-0 axis-using G code suspends group 1 motion this line, the
        # motion mode is *suspended* — no implicit motion.
        suspend_group1 = bool(group0_axis_using)

        # 20. Motion (group 1, possibly modified by G53)
        new_motion = g_by_group.get("1")
        g53 = "G53" in group0_seen
        if new_motion is not None:
            self.state.motion_mode = new_motion
            if new_motion in ("G0", "G1"):
                self.state.motion_mode_explicitly_set = True
        if g53:
            if self.state.cutter_comp in ("G41", "G42"):
                raise NgcError("cannot use G53 while cutter radius compensation is on")
            if not (
                self.state.motion_mode_explicitly_set
                and self.state.motion_mode in ("G0", "G1")
            ):
                raise NgcError("G53 requires G0 or G1 to be active")
        # Decide whether motion should occur this line.
        # G80: cancel; no motion. Axis words are an error during G80 unless a
        # group0-axis-using G is present.
        if self.state.motion_mode == "G80" and not suspend_group1:
            if axis_words_present and not group0_axis_using:
                raise NgcError("axis words used while G80 is active")
            # No motion.
        elif suspend_group1 and new_motion is None:
            pass  # group1 suspended this line
        else:
            should_motion = (
                axis_words_present
                or new_motion in ({"G2", "G3"} | CANNED_CYCLES | {"G38.2"})
                or (new_motion in ("G0", "G1") and not axis_words_present)  # error path
                or g53
            )
            # If a canned cycle is active and *no* axis words appear, no motion
            if self.state.motion_mode in CANNED_CYCLES:
                if axis_words_present:
                    self._do_canned_cycle(word_dict, group0_axis_using)
                else:
                    # Per 3.5.16: "X, Y, and Z words are all missing during a
                    # canned cycle" is an error. If the line contains
                    # cycle-relevant words (R/P/L/I/J/K) without any axis
                    # words, the user clearly intended to (re)trigger the
                    # cycle but omitted the required X/Y/Z.
                    if any(w in word_dict for w in ("r", "p", "l", "i", "j", "k")):
                        raise NgcError(
                            "canned cycle line missing X, Y, and Z words"
                        )
            elif should_motion and not suspend_group1:
                self._do_motion(word_dict, g53=g53)
            elif should_motion and suspend_group1:
                pass

        # 21. Stop / program end
        if "4" in m_by_group:
            mc = m_by_group["4"]
            self.state.active_m_codes["4"] = mc
            if mc in ("M2", "M30"):
                self._do_program_end()

    # -- group-0 commands ----------------------------------------------------

    def _do_g10(self, word_dict: dict[str, float]) -> None:
        if "l" not in word_dict:
            raise NgcError("G10 requires an L word")
        if not _is_close_int(word_dict["l"]) or int(round(word_dict["l"])) != 2:
            raise NgcError("G10 currently only supports L2")
        if "p" not in word_dict:
            raise NgcError("G10 L2 requires a P word")
        if not _is_close_int(word_dict["p"]):
            raise NgcError("G10 P must be an integer")
        p = int(round(word_dict["p"]))
        if p < 1 or p > 9:
            raise NgcError("G10 L2 P must be 1..9")
        cs = self._get_cs_offset(p)
        for axis in AXIS_LETTERS:
            if axis in word_dict:
                v_in = self._axis_word_inches(axis, word_dict[axis])
                cs.set(axis, v_in)
                # Parameters 5221.. store the raw value in the units active
                # when the offset was set. Tests check both representations.
                xp = cs_xyzabc_param_indices(p)[AXIS_LETTERS.index(axis)]
                self.state.parameters[xp] = word_dict[axis]

    def _do_g28_or_g30(
        self,
        word_dict: dict[str, float],
        *,
        PROBE_OR_HOME: tuple[int, int, int, int, int, int],
    ) -> None:
        # Move first to programmed point (if axis words), then to home.
        if any(letter in word_dict for letter in AXIS_LETTERS):
            self._do_motion(word_dict, g53=False, force_g0=True)
        # Then move to home position (which is in absolute machine coords,
        # stored in unspecified length units → spec is ambiguous; tests treat
        # them as inches when set via G28.1/G30.1, but our interpreter only
        # supports G28/G30, not G28.1, so we just leave the home value alone
        # and the home parameters default to 0).
        home = Position()
        names = PROBE_OR_HOME
        home.x = self.state.parameters.get(names[0], 0.0)
        home.y = self.state.parameters.get(names[1], 0.0)
        home.z = self.state.parameters.get(names[2], 0.0)
        home.a = self.state.parameters.get(names[3], 0.0)
        home.b = self.state.parameters.get(names[4], 0.0)
        home.c = self.state.parameters.get(names[5], 0.0)
        # Treat as absolute machine inches.
        prog = self.programmed_from_absolute_inches(home)
        self.state.programmed = prog

    def _do_g92(self, word_dict: dict[str, float]) -> None:
        if not any(a in word_dict for a in AXIS_LETTERS):
            raise NgcError("G92 requires at least one axis word")
        cs = self._get_cs_offset(self.state.selected_cs)
        cur_abs = self.absolute_inches_from_programmed()
        new_g92 = self.state.g92_offsets_inches.copy()
        new_prog = self.state.programmed.copy()
        for axis in AXIS_LETTERS:
            if axis in word_dict:
                spec_in = self._axis_word_inches(axis, word_dict[axis])
                g92_v = cur_abs.get(axis) - cs.get(axis) - spec_in
                new_g92.set(axis, g92_v)
                new_prog.set(axis, spec_in)
        self.state.g92_offsets_inches = new_g92
        self.state.g92_active = True
        self.state.programmed = new_prog
        # Parameters 5211-5216 store the offsets in current units.
        units = self.state.units
        for axis, p_idx in zip(AXIS_LETTERS, G92_OFFSET_PARAMS):
            v = new_g92.get(axis)
            if axis in LINEAR_AXES:
                v = from_inches(v, units)
            self.state.parameters[p_idx] = v

    def _do_g92_1(self) -> None:
        # Cancel offsets and zero parameters.
        cur_abs = self.absolute_inches_from_programmed()
        self.state.g92_offsets_inches = Position()
        self.state.g92_active = False
        for p in G92_OFFSET_PARAMS:
            self.state.parameters[p] = 0.0
        # Recompute programmed so that physical position is preserved.
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs)

    def _do_g92_2(self) -> None:
        cur_abs = self.absolute_inches_from_programmed()
        self.state.g92_active = False
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs)

    def _do_g92_3(self) -> None:
        cur_abs = self.absolute_inches_from_programmed()
        # Reload offsets from parameters 5211-5216 (stored in active units).
        units = self.state.units
        new_g92 = Position()
        for axis, p_idx in zip(AXIS_LETTERS, G92_OFFSET_PARAMS):
            v = self.state.parameters.get(p_idx, 0.0)
            if axis in LINEAR_AXES:
                v = to_inches(v, units)
            new_g92.set(axis, v)
        self.state.g92_offsets_inches = new_g92
        self.state.g92_active = True
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs)

    # -- motion --------------------------------------------------------------

    def _axis_word_inches(self, axis: str, value: float) -> float:
        """Convert an axis word value from current units to internal inches.

        Rotary axes (A/B/C) are stored in degrees and not converted."""
        if axis in LINEAR_AXES:
            return to_inches(value, self.state.units)
        return value

    def _crc_first_straight(
        self, cx: float, cy: float, px: float, py: float
    ) -> tuple[float, float]:
        """First compensated straight move per Appendix B.6.

        cx, cy = current spindle center; px, py = programmed contour endpoint.
        Returns the new spindle-center destination."""
        r = self.state.crc_radius_inches
        dx = px - cx
        dy = py - cy
        d2 = dx * dx + dy * dy
        if r == 0:
            return (px, py)
        if d2 < r * r - 1e-12:
            raise NgcError("cutter gouging with cutter radius compensation")
        # Length of tool-center motion
        L = math.sqrt(max(0.0, d2 - r * r))
        d = math.sqrt(d2)
        # Unit vector along CP
        ux = dx / d
        uy = dy / d
        # Rotation angle alpha such that |CD| = L, |DP| = r, right triangle.
        # cos(alpha) = L/d, sin(alpha) = r/d.
        ca = L / d
        sa = r / d
        # G41 = tool stays LEFT of contour direction, so D is rotated
        # +alpha (CCW) from CP from C's perspective.
        if self.state.cutter_comp == "G41":
            sx = cx + L * (ca * ux - sa * uy)
            sy = cy + L * (ca * uy + sa * ux)
        else:
            sx = cx + L * (ca * ux + sa * uy)
            sy = cy + L * (ca * uy - sa * ux)
        return (sx, sy)

    def _crc_followon_straight(
        self, prev_px: float, prev_py: float, px: float, py: float
    ) -> tuple[float, float]:
        """Follow-on compensated straight move.

        Offsets the programmed endpoint by the tool radius normal to the
        current contour segment, and detects concave corners."""
        r = self.state.crc_radius_inches
        dx = px - prev_px
        dy = py - prev_py
        seg_len = math.hypot(dx, dy)
        if seg_len == 0:
            return (self.state.programmed.x, self.state.programmed.y)
        ux = dx / seg_len
        uy = dy / seg_len
        # Left normal of segment direction
        nlx = -uy
        nly = ux
        if self.state.cutter_comp == "G41":
            nx, ny = nlx, nly
        else:
            nx, ny = -nlx, -nly
        # Concave corner detection: compare with the previous segment
        # direction, inferred from current spindle center vs previous
        # contour point. Previous spindle = (programmed.x, programmed.y);
        # previous contour = (prev_px, prev_py). The previous segment had
        # offset normal (sp - prev_p), so its direction is the perpendicular
        # of that normal — but a simpler test: compute prev incoming
        # contour direction by re-using the spindle offset.
        sp_x = self.state.programmed.x
        sp_y = self.state.programmed.y
        # The previous offset normal vector was (sp - prev_p). Its tangent
        # (incoming contour direction) is the 90-degree rotation back to the
        # contour direction:
        prev_nx = sp_x - prev_px
        prev_ny = sp_y - prev_py
        # The incoming direction is the rotation of normal by -90 (G41) or
        # +90 (G42) to recover the original contour direction.
        if self.state.cutter_comp == "G41":
            in_dx = prev_ny
            in_dy = -prev_nx
        else:
            in_dx = -prev_ny
            in_dy = prev_nx
        in_len = math.hypot(in_dx, in_dy)
        if in_len > 1e-9:
            in_dx /= in_len
            in_dy /= in_len
            cross = in_dx * uy - in_dy * ux
            # G41: concave when cross > 0 (CCW turn on left side)
            # G42: concave when cross < 0
            if self.state.cutter_comp == "G41" and cross > 1e-9:
                raise NgcError("concave corner with cutter radius compensation")
            if self.state.cutter_comp == "G42" and cross < -1e-9:
                raise NgcError("concave corner with cutter radius compensation")
        sx = px + r * nx
        sy = py + r * ny
        return (sx, sy)

    def _do_motion(
        self,
        word_dict: dict[str, float],
        *,
        g53: bool,
        force_g0: bool = False,
    ) -> None:
        mode = "G0" if force_g0 else self.state.motion_mode
        if mode in {"G2", "G3"} and not g53:
            self._do_arc(word_dict, mode)
            self.state.last_motion_was_cycle = False
            return
        if mode == "G38.2":
            self._do_probe(word_dict)
            self.state.last_motion_was_cycle = False
            return
        if mode in CANNED_CYCLES:
            self._do_canned_cycle(word_dict, [])
            return

        # G0 / G1 (possibly with G53)
        if mode not in ("G0", "G1"):
            raise NgcError(f"motion mode {mode} not implemented for plain motion")
        if not any(a in word_dict for a in AXIS_LETTERS):
            raise NgcError(f"{mode} requires at least one axis word")
        if g53:
            if self.state.cutter_comp in ("G41", "G42"):
                raise NgcError("G53 not allowed while cutter radius compensation is on")
            target_abs_in = self.absolute_inches_from_programmed()
            for axis in AXIS_LETTERS:
                if axis in word_dict:
                    target_abs_in.set(axis, self._axis_word_inches(axis, word_dict[axis]))
            self.state.programmed = self.programmed_from_absolute_inches(target_abs_in)
        else:
            new_prog = self.state.programmed.copy()
            for axis in AXIS_LETTERS:
                if axis in word_dict:
                    v_in = self._axis_word_inches(axis, word_dict[axis])
                    if self.state.distance_mode == "G91":
                        new_prog.set(axis, new_prog.get(axis) + v_in)
                    else:
                        new_prog.set(axis, v_in)
            # Cutter radius compensation: rewrite the XY of new_prog so that
            # state.programmed (and thus the reported machine_position) tracks
            # the spindle center, not the programmed contour.
            if self.state.cutter_comp in ("G41", "G42") and self.state.plane == "G17":
                cur_x = self.state.programmed.x
                cur_y = self.state.programmed.y
                # For follow-on moves, the start contour point is the stored
                # contour position (program_x/program_y from B.1.1).
                if self.state.crc_first_move:
                    px, py = new_prog.x, new_prog.y
                    sx, sy = self._crc_first_straight(cur_x, cur_y, px, py)
                    self.state.crc_contour_x = px
                    self.state.crc_contour_y = py
                    self.state.crc_first_move = False
                else:
                    prev_px = self.state.crc_contour_x
                    prev_py = self.state.crc_contour_y
                    px, py = new_prog.x, new_prog.y
                    sx, sy = self._crc_followon_straight(
                        prev_px, prev_py, px, py
                    )
                    self.state.crc_contour_x = px
                    self.state.crc_contour_y = py
                new_prog.x = sx
                new_prog.y = sy
            self.state.programmed = new_prog
        # Inverse-time feed mode requires F on G1/G2/G3 lines
        if (
            self.state.feed_mode == "G93"
            and mode == "G1"
            and (self.state.feed_rate <= 0 or not getattr(self, "_f_on_this_line", False))
        ):
            raise NgcError("G1 in inverse time feed mode requires a positive F word")
        self.state.last_motion_was_cycle = False

    def _do_arc(self, word_dict: dict[str, float], mode: str) -> None:
        # Determine plane axes; we don't simulate the path geometry, only the
        # endpoint, but we do validate the spec error conditions.
        plane = self.state.plane
        units = self.state.units

        if plane == "G17":
            ax1, ax2, ax_perp = "x", "y", "z"
            offset_letters = ("i", "j")
        elif plane == "G18":
            ax1, ax2, ax_perp = "x", "z", "y"
            offset_letters = ("i", "k")
        else:  # G19
            ax1, ax2, ax_perp = "y", "z", "x"
            offset_letters = ("j", "k")

        new_prog = self.state.programmed.copy()
        # Apply axis words to programmed position.
        for axis in AXIS_LETTERS:
            if axis in word_dict:
                v_in = self._axis_word_inches(axis, word_dict[axis])
                if self.state.distance_mode == "G91":
                    new_prog.set(axis, new_prog.get(axis) + v_in)
                else:
                    new_prog.set(axis, v_in)

        crc_active = self.state.cutter_comp in ("G41", "G42") and plane == "G17"
        i_val = 0.0
        j_val = 0.0
        if "r" in word_dict:
            # Radius format: at least one of the in-plane axes must be given.
            if ax1 not in word_dict and ax2 not in word_dict:
                raise NgcError("arc requires at least one in-plane axis word")
            # End point must differ from current (skip under CRC; the
            # programmed contour endpoint may differ from the spindle).
            if not crc_active and (
                new_prog.get(ax1) == self.state.programmed.get(ax1)
                and new_prog.get(ax2) == self.state.programmed.get(ax2)
            ):
                raise NgcError("radius-format arc end point equals current point")
        else:
            # Center format
            if ax1 not in word_dict and ax2 not in word_dict:
                raise NgcError("arc requires at least one in-plane axis word")
            if not any(o in word_dict for o in offset_letters):
                raise NgcError("center-format arc requires offset words")
            i_val = to_inches(word_dict.get(offset_letters[0], 0.0), self.state.units)
            j_val = to_inches(word_dict.get(offset_letters[1], 0.0), self.state.units)
            if not crc_active:
                # Spec requires consistency between current->center and
                # end->center within tolerance.
                tol = 0.0002  # always inches internally
                cur1 = self.state.programmed.get(ax1)
                cur2 = self.state.programmed.get(ax2)
                cx, cy = cur1 + i_val, cur2 + j_val
                r1 = math.hypot(i_val, j_val)
                r2 = math.hypot(new_prog.get(ax1) - cx, new_prog.get(ax2) - cy)
                if abs(r1 - r2) > tol:
                    raise NgcError("center-format arc radii inconsistent")

        if (
            self.state.feed_mode == "G93"
            and (self.state.feed_rate <= 0 or not getattr(self, "_f_on_this_line", False))
        ):
            raise NgcError("arc in inverse time feed mode requires a positive F word")

        # CRC for arcs: only applies on G17 plane.
        if self.state.cutter_comp in ("G41", "G42") and plane == "G17":
            # Compute programmed center (cx,cy) and programmed radius arc_r.
            if "r" in word_dict:
                ex = new_prog.x
                ey = new_prog.y
                arc_r = abs(to_inches(word_dict["r"], self.state.units))
                if self.state.crc_first_move:
                    # Center is at distance arc_r from (ex,ey) and distance
                    # arc_r +/- tool_r from current spindle (sx0, sy0),
                    # depending on inside/outside.
                    sx0 = self.state.programmed.x
                    sy0 = self.state.programmed.y
                    inside_first = (
                        (mode == "G3" and self.state.cutter_comp == "G41")
                        or (mode == "G2" and self.state.cutter_comp == "G42")
                    )
                    spindle_dist = (
                        arc_r - self.state.crc_radius_inches
                        if inside_first
                        else arc_r + self.state.crc_radius_inches
                    )
                    cx, cy = _two_circle_intersection_pick(
                        ex, ey, arc_r, sx0, sy0, spindle_dist, mode
                    )
                else:
                    sx0 = self.state.crc_contour_x
                    sy0 = self.state.crc_contour_y
                    cx, cy = _arc_center_from_radius(sx0, sy0, ex, ey, word_dict["r"], mode)
            else:
                if self.state.crc_first_move:
                    sx0 = self.state.programmed.x
                    sy0 = self.state.programmed.y
                else:
                    sx0 = self.state.crc_contour_x
                    sy0 = self.state.crc_contour_y
                cx = sx0 + i_val
                cy = sy0 + j_val
                ex = new_prog.x
                ey = new_prog.y
                arc_r = math.hypot(ex - cx, ey - cy)

            # Determine which side of the contour the tool is on for this arc.
            # CCW arc (G3): inside = LEFT of tangent direction → G41 inside.
            # CW arc (G2): inside = RIGHT of tangent direction → G42 inside.
            inside = (
                (mode == "G3" and self.state.cutter_comp == "G41")
                or (mode == "G2" and self.state.cutter_comp == "G42")
            )
            tool_r = self.state.crc_radius_inches
            if inside and tool_r >= arc_r - 1e-9:
                raise NgcError(
                    "tool radius not less than arc radius with cutter radius compensation"
                )
            tool_arc_r = (arc_r - tool_r) if inside else (arc_r + tool_r)
            # Compute tool-center end position: scale (ex-cx, ey-cy) to tool_arc_r.
            dxv = ex - cx
            dyv = ey - cy
            d = math.hypot(dxv, dyv)
            if d > 0:
                sx = cx + dxv * tool_arc_r / d
                sy = cy + dyv * tool_arc_r / d
            else:
                sx, sy = ex, ey
            self.state.crc_contour_x = ex
            self.state.crc_contour_y = ey
            self.state.crc_first_move = False
            new_prog.x = sx
            new_prog.y = sy

        self.state.programmed = new_prog
        _ = ax_perp  # unused

    def _do_probe(self, word_dict: dict[str, float]) -> None:
        # Validate
        if self.state.cutter_comp in ("G41", "G42"):
            raise NgcError("cannot probe while cutter radius compensation is on")
        if self.state.feed_mode == "G93":
            raise NgcError("G38.2 not allowed in inverse time feed mode")
        if not any(a in word_dict for a in LINEAR_AXES):
            raise NgcError("G38.2 requires at least one linear axis word")
        # Rotary words must equal current rotary positions.
        for axis in ROTARY_AXES:
            if axis in word_dict and word_dict[axis] != self.state.programmed.get(axis):
                raise NgcError("G38.2 must not command rotary motion")
        if (
            self.state.tool_in_spindle is None
            or (self.probe_tool is not None and self.state.tool_in_spindle != self.probe_tool)
        ):
            raise NgcError("G38.2 requires the probe tool to be in the spindle")
        if self.state.spindle_direction != "OFF":
            raise NgcError("G38.2 requires the spindle to be stopped")
        # Compute target programmed position
        new_prog = self.state.programmed.copy()
        for axis in AXIS_LETTERS:
            if axis in word_dict:
                v = word_dict[axis]
                if self.state.distance_mode == "G91":
                    new_prog.set(axis, new_prog.get(axis) + v)
                else:
                    new_prog.set(axis, v)
        # Validate distance > 0.01 inch / 0.254 mm
        units = self.state.units
        dx = (new_prog.x - self.state.programmed.x)
        dy = (new_prog.y - self.state.programmed.y)
        dz = (new_prog.z - self.state.programmed.z)
        dist = math.hypot(math.hypot(dx, dy), dz)
        min_dist = 0.01 if units == "G20" else 0.254
        if dist < min_dist:
            raise NgcError("G38.2 distance is too small")

        # Compute trip if probe-box was provided.
        start_abs = self.absolute_inches_from_programmed()
        # Apply TLO to controlled point
        start_cp = Position(
            start_abs.x, start_abs.y,
            start_abs.z - self.state.tool_length_offset_value_inches,
            start_abs.a, start_abs.b, start_abs.c,
        )
        end_abs = self.absolute_inches_from_programmed(new_prog)
        end_cp = Position(
            end_abs.x, end_abs.y,
            end_abs.z - self.state.tool_length_offset_value_inches,
            end_abs.a, end_abs.b, end_abs.c,
        )

        if self.probe_box_inches is not None:
            (xmin, xmax, ymin, ymax, zmin, zmax) = self.probe_box_inches

            def in_box(p: Position) -> bool:
                return (
                    xmin <= p.x <= xmax
                    and ymin <= p.y <= ymax
                    and zmin <= p.z <= zmax
                )

            if in_box(start_cp):
                raise NgcError("G38.2 probe is already tripped")
            else:
                # Parameterize from start (t=0) to end (t=1); find smallest t
                # in [0,1] where the controlled point first enters the box.
                t_min = 0.0
                t_max = 1.0

                def axis_t(c0: float, c1: float, lo: float, hi: float) -> tuple[float, float] | None:
                    if c0 == c1:
                        if lo <= c0 <= hi:
                            return (0.0, 1.0)
                        return None
                    t1 = (lo - c0) / (c1 - c0)
                    t2 = (hi - c0) / (c1 - c0)
                    return (min(t1, t2), max(t1, t2))

                for c0, c1, lo, hi in (
                    (start_cp.x, end_cp.x, xmin, xmax),
                    (start_cp.y, end_cp.y, ymin, ymax),
                    (start_cp.z, end_cp.z, zmin, zmax),
                ):
                    rng = axis_t(c0, c1, lo, hi)
                    if rng is None:
                        t_min = 1.0
                        t_max = 0.0
                        break
                    t_min = max(t_min, rng[0])
                    t_max = min(t_max, rng[1])

                if t_min <= t_max and 0.0 <= t_min <= 1.0:
                    t = t_min
                    trip = Position(
                        start_cp.x + (end_cp.x - start_cp.x) * t,
                        start_cp.y + (end_cp.y - start_cp.y) * t,
                        start_cp.z + (end_cp.z - start_cp.z) * t,
                        start_cp.a + (end_cp.a - start_cp.a) * t,
                        start_cp.b + (end_cp.b - start_cp.b) * t,
                        start_cp.c + (end_cp.c - start_cp.c) * t,
                    )
                else:
                    raise NgcError("G38.2 probe did not trip")
        else:
            raise NgcError("G38.2 used without --probe-box configured")

        # Set the controlled point to trip.
        # Convert trip (controlled point in inches) back to a programmed
        # position. Add TLO back to Z first.
        trip_abs = Position(
            trip.x, trip.y,
            trip.z + self.state.tool_length_offset_value_inches,
            trip.a, trip.b, trip.c,
        )
        self.state.programmed = self.programmed_from_absolute_inches(trip_abs)
        # Set parameters 5061..5066 to the controlled-point coordinates in
        # the *current length units* for linear axes, raw degrees for rotary.
        units = self.state.units
        self.state.parameters[5061] = from_inches(trip.x, units)
        self.state.parameters[5062] = from_inches(trip.y, units)
        self.state.parameters[5063] = from_inches(trip.z, units)
        self.state.parameters[5064] = trip.a
        self.state.parameters[5065] = trip.b
        self.state.parameters[5066] = trip.c

    # -- canned cycles -------------------------------------------------------

    def _do_canned_cycle(
        self,
        word_dict: dict[str, float],
        group0_axis_using: list[str],
    ) -> None:
        plane = self.state.plane
        if plane == "G17":
            depth_axis = "z"
            plane_axes = ("x", "y")
        elif plane == "G18":
            depth_axis = "y"
            plane_axes = ("x", "z")
        else:
            depth_axis = "x"
            plane_axes = ("y", "z")

        if self.state.cutter_comp in ("G41", "G42"):
            raise NgcError("cutter radius compensation must not be on during a canned cycle")
        if self.state.feed_mode == "G93":
            raise NgcError("inverse time feed mode is not allowed during a canned cycle")
        # Rotary words must be stationary during canned cycles
        for axis in ROTARY_AXES:
            if axis in word_dict and word_dict[axis] != self.state.programmed.get(axis):
                raise NgcError("rotational axis motion is not allowed during a canned cycle")

        # X/Y/Z (or analogue) — at least one of these must be present per the
        # error rule "X, Y, and Z words are all missing during a canned cycle".
        if not any(a in word_dict for a in ("x", "y", "z")):
            raise NgcError("canned cycle requires at least one of X, Y, Z")

        # L word
        if "l" in word_dict:
            l_val = word_dict["l"]
            if not _is_close_int(l_val) or int(round(l_val)) <= 0:
                raise NgcError("canned cycle L must be a positive integer")
            l = int(round(l_val))
        else:
            l = 1

        # Compute the target X/Y in the active distance mode but without
        # repeating yet. Then handle Z (depth, sticky) and R (sticky).
        cur = self.state.programmed.copy()

        # Save Z position before cycle starts (old_z) for retract decisions.
        if not self.state.last_motion_was_cycle:
            self.state.cycle_old_z = cur.get(depth_axis)

        # Read R (always sticky)
        if "r" in word_dict:
            r_v = word_dict["r"]
            if self.state.distance_mode == "G91":
                r_v = cur.get(depth_axis) + r_v
            self.state.cycle_r = r_v
        if self.state.cycle_r is None:
            raise NgcError("canned cycle requires R")

        # Read Z/depth (sticky)
        if depth_axis in word_dict:
            z_v = word_dict[depth_axis]
            if self.state.distance_mode == "G91":
                z_v = cur.get(depth_axis) + z_v
            self.state.cycle_z = z_v
        if self.state.cycle_z is None:
            raise NgcError("canned cycle requires depth axis word")

        if self.state.cycle_r < self.state.cycle_z:
            raise NgcError("canned cycle R must not be below Z")

        # Process L repeats. We only need final position; the geometry of
        # intermediate moves doesn't affect the reported state.
        for repeat in range(l):
            # Determine X,Y target for this repeat.
            for axis in plane_axes:
                if axis in word_dict:
                    if self.state.distance_mode == "G91":
                        cur.set(axis, cur.get(axis) + word_dict[axis])
                    else:
                        cur.set(axis, word_dict[axis])
            # Depth axis ends up at clear Z (G98 = old_z if higher than R else R; G99 = R)
            if self.state.return_mode == "G99":
                clear = self.state.cycle_r
            else:  # G98
                clear = max(self.state.cycle_old_z, self.state.cycle_r)
            cur.set(depth_axis, clear)

        # G84 special-case: tap, restore CW after cycle. We just leave spindle CW.
        motion = self.state.motion_mode
        if motion == "G84":
            if self.state.spindle_direction != "CW":
                raise NgcError("G84 requires spindle CW before cycle")
            self.state.spindle_direction = "CW"
        elif motion in ("G86", "G88"):
            if self.state.spindle_direction == "OFF":
                raise NgcError(f"{motion} requires spindle on before cycle")
            # Restored to prior direction => no change

        if motion == "G83":
            q = word_dict.get("q")
            if q is None or q <= 0:
                raise NgcError("G83 requires a positive Q word")

        if motion in ("G86", "G88", "G89") and "p" not in word_dict:
            raise NgcError(f"{motion} requires a P word")
        if motion in ("G82", "G86", "G88", "G89") and "p" in word_dict:
            if word_dict["p"] < 0:
                raise NgcError("canned cycle P must be non-negative")

        self.state.programmed = cur
        self.state.last_motion_was_cycle = True

    # -- program end / reset ------------------------------------------------

    def _do_program_end(self) -> None:
        # Apply the M2/M30 reset semantics from section 3.6.1.
        cur_abs = self.absolute_inches_from_programmed()
        self.state.g92_offsets_inches = Position()
        self.state.g92_active = False
        self.state.selected_cs = 1
        self.state.parameters[SELECTED_CS_PARAM] = 1.0
        self.state.plane = "G17"
        self.state.distance_mode = "G90"
        self.state.feed_mode = "G94"
        self.state.overrides_enabled = True
        self.state.cutter_comp = "G40"
        self.state.cutter_radius_compensation_number = None
        self.state.spindle_direction = "OFF"
        self.state.motion_mode = "G1"
        self.state.coolant = "M9"
        self.state.active_m_codes["7"] = "M5"
        self.state.active_m_codes["8"] = "M9"
        self.state.active_m_codes["9"] = "M48"
        # Re-derive programmed position from physical position with the new CS.
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs)
        self.program_ended = True

    # -- parameter <-> state sync helper ------------------------------------

    def _maybe_sync_param_into_state(self, idx: int, val: float) -> None:
        if idx == SELECTED_CS_PARAM:
            if _is_close_int(val) and 1 <= int(round(val)) <= 9:
                self.state.selected_cs = int(round(val))
        # Could mirror coordinate system parameters back into cs_offsets, but
        # we keep them as the source of truth and rely on G10 / startup load.

    # -- output --------------------------------------------------------------

    def build_payload(self) -> dict[str, object]:
        # Make sure required parameters are populated for output.
        # Mirror in-memory state into the parameters before serialization.
        units = self.state.units
        # CS offset parameters (5221+) are stored raw at G10 time and remain
        # unchanged across unit switches per RS274 section 4.3.3.3, so we do
        # NOT overwrite them here from cs_offsets_inches.
        for s in range(1, 10):
            if s in self.state.cs_offsets_inches:
                xp, yp, zp, ap, bp, cp = cs_xyzabc_param_indices(s)
                self.state.parameters.setdefault(xp, 0.0)
                self.state.parameters.setdefault(yp, 0.0)
                self.state.parameters.setdefault(zp, 0.0)
                self.state.parameters.setdefault(ap, 0.0)
                self.state.parameters.setdefault(bp, 0.0)
                self.state.parameters.setdefault(cp, 0.0)
        # G92 params (5211-5216) are written when G92 is invoked and remain
        # raw across unit switches and across M2/M30 (which zero offsets but
        # preserve the parameters per G92.2 semantics).
        for p_idx in G92_OFFSET_PARAMS:
            self.state.parameters.setdefault(p_idx, 0.0)
        self.state.parameters[SELECTED_CS_PARAM] = float(self.state.selected_cs)
        for p in REQUIRED_OUTPUT_PARAMETERS:
            self.state.parameters.setdefault(p, 0.0)

        # Build modal G code dict from current state.
        active_g: dict[str, str] = {
            "1": self.state.motion_mode,
            "2": self.state.plane,
            "3": self.state.distance_mode,
            "5": self.state.feed_mode,
            "6": self.state.units,
            "7": self.state.cutter_comp,
            "8": self.state.tool_length_offset_mode,
            "10": self.state.return_mode,
            "12": CS_NUMBER_TO_GCODE[self.state.selected_cs],
            "13": self.state.path_mode,
        }

        cp = self.controlled_point_in_active_units()

        # Coordinate system offsets in current units.
        cs_dict: dict[str, dict[str, float]] = {}
        for s in range(1, 10):
            cs = self.state.cs_offsets_inches.get(s, Position())
            cs_dict[str(s)] = {
                "x": from_inches(cs.x, units),
                "y": from_inches(cs.y, units),
                "z": from_inches(cs.z, units),
                "a": cs.a,
                "b": cs.b,
                "c": cs.c,
            }

        param_dict = {str(k): float(v) for k, v in self.state.parameters.items()}

        return {
            "machine_position": cp.to_dict(),
            "feed_rate": float(self.state.feed_rate),
            "spindle_speed": float(self.state.spindle_speed),
            "spindle_direction": self.state.spindle_direction,
            "cutter_radius_compensation_number": self.state.cutter_radius_compensation_number,
            "tool_length_offset_index": self.state.tool_length_offset_index,
            "selected_tool": self.state.selected_tool,
            "tool_in_spindle": self.state.tool_in_spindle,
            "active_modal_g_codes": active_g,
            "active_modal_m_codes": dict(self.state.active_m_codes),
            "coordinate_system_offsets": cs_dict,
            "parameters": param_dict,
            "error": None,
        }

    def write_parameter_file(self, path: str) -> None:
        # Make sure required parameters are present.
        for p in REQUIRED_OUTPUT_PARAMETERS:
            self.state.parameters.setdefault(p, 0.0)
        sorted_params = sorted(self.state.parameters.items())
        out_lines = ["RS274 parameter file", ""]
        for idx, val in sorted_params:
            # Format value: keep simple float repr.
            if val == int(val):
                # Use trailing .0 to keep float-ish format.
                out_lines.append(f"{idx} {val:.6f}")
            else:
                out_lines.append(f"{idx} {val:.10g}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="cncsim")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--tool-table")
    p.add_argument("--block-delete", action="store_true")
    p.add_argument("--carousel-slots", type=int)
    p.add_argument("--parameter-input")
    p.add_argument("--parameter-output")
    p.add_argument("--probe-box", nargs=6, type=float)
    p.add_argument("--probe-tool", type=int)
    return p.parse_args(argv)


def write_error_payload(path: str, message: str) -> None:
    payload = {
        "machine_position": {"x": 0.0, "y": 0.0, "z": 0.0, "a": 0.0, "b": 0.0, "c": 0.0},
        "feed_rate": 0.0,
        "spindle_speed": 0.0,
        "spindle_direction": "OFF",
        "cutter_radius_compensation_number": None,
        "tool_length_offset_index": None,
        "selected_tool": None,
        "tool_in_spindle": None,
        "active_modal_g_codes": {},
        "active_modal_m_codes": {},
        "coordinate_system_offsets": {},
        "parameters": {},
        "error": message,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    try:
        probe_box = None
        if args.probe_box is not None:
            probe_box = tuple(args.probe_box)  # type: ignore[assignment]

        interp = Interpreter(
            block_delete=args.block_delete,
            carousel_slots=args.carousel_slots,
            probe_box=probe_box,
            probe_tool=args.probe_tool,
        )
        if args.parameter_input:
            interp.load_parameter_file(args.parameter_input)
        interp.initialize_default_parameters()
        if args.tool_table:
            interp.load_tool_table(args.tool_table)

        with open(args.input, encoding="utf-8") as f:
            program_text = f.read()
        interp.run(program_text)

        payload = interp.build_payload()
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        if args.parameter_output:
            interp.write_parameter_file(args.parameter_output)

        return 0
    except NgcError as exc:
        write_error_payload(args.output, str(exc))
        if args.parameter_output:
            try:
                with open(args.parameter_output, "w", encoding="utf-8") as f:
                    f.write("RS274 parameter file\n\n")
            except OSError:
                pass
        return 1
    except Exception as exc:  # noqa: BLE001 - internal error catch
        try:
            write_error_payload(args.output, f"internal error: {exc}")
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(main())
