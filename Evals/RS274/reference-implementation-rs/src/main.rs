// RS274/NGC G-code interpreter — Rust reference implementation.
//
// Direct port of reference-implementation-py/main.py. Single-file design
// matches the C++ and JS ref-impls. Uses only `serde` + `serde_json`
// (with `preserve_order`) so output JSON key ordering matches the Python
// reference exactly.

#![allow(clippy::too_many_arguments)]
#![allow(clippy::many_single_char_names)]
#![allow(clippy::float_cmp)]

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::process::ExitCode;

use serde_json::{json, Map, Value};

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
struct NgcError(String);

impl std::fmt::Display for NgcError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}

impl std::error::Error for NgcError {}

type NgcResult<T> = Result<T, NgcError>;

fn ngc(msg: impl Into<String>) -> NgcError {
    NgcError(msg.into())
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AXIS_LETTERS: [char; 6] = ['x', 'y', 'z', 'a', 'b', 'c'];
const LINEAR_AXES: [char; 3] = ['x', 'y', 'z'];
const ROTARY_AXES: [char; 3] = ['a', 'b', 'c'];

const G28_HOME_PARAMS: [u32; 6] = [5161, 5162, 5163, 5164, 5165, 5166];
const G30_HOME_PARAMS: [u32; 6] = [5181, 5182, 5183, 5184, 5185, 5186];
const G92_OFFSET_PARAMS: [u32; 6] = [5211, 5212, 5213, 5214, 5215, 5216];
const SELECTED_CS_PARAM: u32 = 5220;

fn cs_xyzabc_param_indices(system: u32) -> [u32; 6] {
    let base = 5221 + (system - 1) * 20;
    [base, base + 1, base + 2, base + 3, base + 4, base + 5]
}

fn required_output_parameters() -> Vec<u32> {
    let mut s: std::collections::BTreeSet<u32> = std::collections::BTreeSet::new();
    for p in G28_HOME_PARAMS.iter().chain(G30_HOME_PARAMS.iter())
        .chain(G92_OFFSET_PARAMS.iter()) {
        s.insert(*p);
    }
    s.insert(SELECTED_CS_PARAM);
    for sys in 1..=9 {
        for p in cs_xyzabc_param_indices(sys) {
            s.insert(p);
        }
    }
    s.into_iter().collect()
}

const RAPID_RATE_IPM: f64 = 1000.0;
const STATE_ONLY_EPSILON: f64 = 0.0001;

const MM_PER_INCH: f64 = 25.4;

fn is_linear(ax: char) -> bool {
    LINEAR_AXES.contains(&ax)
}

fn axis_index(ax: char) -> usize {
    AXIS_LETTERS.iter().position(|&c| c == ax).expect("axis letter")
}

// Modal group classification.
fn g_code_to_group(code: &str) -> Option<&'static str> {
    // Group 1
    match code {
        "G0" | "G1" | "G2" | "G3" | "G38.2"
        | "G80" | "G81" | "G82" | "G83" | "G84" | "G85" | "G86" | "G87" | "G88" | "G89"
            => return Some("1"),
        "G17" | "G18" | "G19" => return Some("2"),
        "G90" | "G91" => return Some("3"),
        "G93" | "G94" => return Some("5"),
        "G20" | "G21" => return Some("6"),
        "G40" | "G41" | "G42" => return Some("7"),
        "G43" | "G49" => return Some("8"),
        "G98" | "G99" => return Some("10"),
        "G54" | "G55" | "G56" | "G57" | "G58" | "G59"
        | "G59.1" | "G59.2" | "G59.3" => return Some("12"),
        "G61" | "G61.1" | "G64" => return Some("13"),
        "G4" | "G10" | "G28" | "G30" | "G53"
        | "G92" | "G92.1" | "G92.2" | "G92.3" => return Some("0"),
        _ => None,
    }
}

fn m_code_to_group(code: &str) -> Option<&'static str> {
    match code {
        "M0" | "M1" | "M2" | "M30" | "M60" => Some("4"),
        "M6" => Some("6"),
        "M3" | "M4" | "M5" => Some("7"),
        "M7" | "M8" | "M9" => Some("8"),
        "M48" | "M49" => Some("9"),
        _ => None,
    }
}

fn is_canned_cycle(code: &str) -> bool {
    matches!(code, "G81" | "G82" | "G83" | "G84" | "G85" | "G86" | "G87" | "G88" | "G89")
}

fn is_group0_axis_using(code: &str) -> bool {
    matches!(code, "G10" | "G28" | "G30" | "G92")
}

fn cs_gcode_to_number(code: &str) -> Option<u32> {
    match code {
        "G54" => Some(1), "G55" => Some(2), "G56" => Some(3), "G57" => Some(4),
        "G58" => Some(5), "G59" => Some(6),
        "G59.1" => Some(7), "G59.2" => Some(8), "G59.3" => Some(9),
        _ => None,
    }
}

fn cs_number_to_gcode(n: u32) -> &'static str {
    match n {
        1 => "G54", 2 => "G55", 3 => "G56", 4 => "G57", 5 => "G58",
        6 => "G59", 7 => "G59.1", 8 => "G59.2", 9 => "G59.3",
        _ => "G54",
    }
}

fn is_nullable_scalar_field(k: &str) -> bool {
    matches!(k,
        "cutter_radius_compensation_number"
        | "tool_length_offset_index"
        | "selected_tool"
        | "tool_in_spindle"
    )
}

fn is_nested_field(k: &str) -> bool {
    matches!(k,
        "machine_position"
        | "coordinate_system_offsets"
        | "active_modal_g_codes"
        | "active_modal_m_codes"
        | "parameters"
    )
}

// ---------------------------------------------------------------------------
// Helpers: numeric
// ---------------------------------------------------------------------------

fn is_close_int(v: f64) -> bool {
    (v - v.round()).abs() <= 1e-4
}

fn to_int_close(v: f64, what: &str) -> NgcResult<i64> {
    if !is_close_int(v) {
        return Err(ngc(format!("{what} must evaluate to an integer (got {v})")));
    }
    Ok(v.round() as i64)
}

// Exact mm -> inch conversion that mirrors the Python Decimal("25.4") divide.
// Converts value in mm to inches, rounding to 10 significant digits to avoid
// IEEE-754 drift on inputs like 76.2.
fn to_inches_raw(value_mm: f64) -> f64 {
    // Python uses Decimal(repr(value)) / Decimal("25.4"), then back to float.
    // We approximate by rounding the quotient to ~12 decimal digits which
    // suffices for the test precision (1e-6 on positions).
    let q = value_mm / MM_PER_INCH;
    let scaled = (q * 1e12).round() / 1e12;
    scaled
}

fn from_inches_raw(value_in: f64) -> f64 {
    let q = value_in * MM_PER_INCH;
    let scaled = (q * 1e10).round() / 1e10;
    scaled
}

fn to_inches_units(value: f64, units: &str) -> f64 {
    if units == "G20" { value } else { to_inches_raw(value) }
}

fn from_inches_units(value: f64, units: &str) -> f64 {
    if units == "G20" { value } else { from_inches_raw(value) }
}

// ---------------------------------------------------------------------------
// Position
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, Default)]
struct Position {
    x: f64,
    y: f64,
    z: f64,
    a: f64,
    b: f64,
    c: f64,
}

impl Position {
    fn get(&self, axis: char) -> f64 {
        match axis {
            'x' => self.x, 'y' => self.y, 'z' => self.z,
            'a' => self.a, 'b' => self.b, 'c' => self.c,
            _ => 0.0,
        }
    }
    fn set(&mut self, axis: char, v: f64) {
        match axis {
            'x' => self.x = v, 'y' => self.y = v, 'z' => self.z = v,
            'a' => self.a = v, 'b' => self.b = v, 'c' => self.c = v,
            _ => {},
        }
    }
    fn to_map(&self) -> Map<String, Value> {
        let mut m = Map::new();
        m.insert("x".into(), json_num(self.x));
        m.insert("y".into(), json_num(self.y));
        m.insert("z".into(), json_num(self.z));
        m.insert("a".into(), json_num(self.a));
        m.insert("b".into(), json_num(self.b));
        m.insert("c".into(), json_num(self.c));
        m
    }
}

fn json_num(v: f64) -> Value {
    if v.is_finite() {
        Value::Number(serde_json::Number::from_f64(v).unwrap_or_else(|| 0.into()))
    } else {
        Value::Null
    }
}

// ---------------------------------------------------------------------------
// Tool table
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
struct Tool {
    _pocket: i64,
    _fms: i64,
    tlo: f64,
    diameter: f64,
}

// ---------------------------------------------------------------------------
// Parsed line
// ---------------------------------------------------------------------------

#[derive(Debug, Default)]
struct ParsedLine {
    _block_delete: bool,
    line_number: Option<i64>,
    words: Vec<(char, f64)>,
    g_codes: Vec<String>,
    m_codes: Vec<String>,
    parameter_settings: Vec<(u32, f64)>,
    _has_comment: bool,
}

// ---------------------------------------------------------------------------
// Line parser
// ---------------------------------------------------------------------------

struct LineParser<'a> {
    raw: &'a [char],
    pos: usize,
    parameters: &'a BTreeMap<u32, f64>,
}

impl<'a> LineParser<'a> {
    fn new(text_chars: &'a [char], parameters: &'a BTreeMap<u32, f64>) -> Self {
        LineParser { raw: text_chars, pos: 0, parameters }
    }

    fn peek(&self) -> char {
        if self.pos >= self.raw.len() { '\0' } else { self.raw[self.pos] }
    }

    fn skip_ws(&mut self) {
        while self.pos < self.raw.len() {
            let c = self.raw[self.pos];
            if c == ' ' || c == '\t' { self.pos += 1; } else { break; }
        }
    }

    fn parse(&mut self, block_delete_active: bool) -> NgcResult<Option<ParsedLine>> {
        self.skip_ws();
        let mut block_delete = false;
        if self.peek() == '/' {
            block_delete = true;
            self.pos += 1;
        }
        if block_delete && block_delete_active {
            return Ok(None);
        }

        let mut result = ParsedLine::default();
        result._block_delete = block_delete;

        self.skip_ws();
        if self.peek().to_ascii_lowercase() == 'n' {
            self.pos += 1;
            self.skip_ws();
            let mut digits = String::new();
            while self.pos < self.raw.len() && self.raw[self.pos].is_ascii_digit() {
                digits.push(self.raw[self.pos]);
                self.pos += 1;
                self.skip_ws();
            }
            if digits.is_empty() {
                return Err(ngc("line number must have at least one digit"));
            }
            if digits.len() > 5 {
                return Err(ngc("line number must have at most 5 digits"));
            }
            let n: i64 = digits.parse().map_err(|_| ngc("invalid line number"))?;
            if !(0..=99999).contains(&n) {
                return Err(ngc(format!("line number {n} out of range 0..99999")));
            }
            result.line_number = Some(n);
        }

        let mut pending: Vec<(u32, f64)> = Vec::new();

        loop {
            self.skip_ws();
            if self.pos >= self.raw.len() { break; }
            let ch = self.raw[self.pos];
            if ch == '(' {
                self.parse_comment()?;
                result._has_comment = true;
                continue;
            }
            if ch == '#' {
                self.pos += 1;
                let idx_v = self.read_real_value()?;
                let idx = to_int_close(idx_v, "parameter index")?;
                if !(1..=5399).contains(&idx) {
                    return Err(ngc(format!("parameter index {idx} out of range 1..5399")));
                }
                self.skip_ws();
                if self.peek() != '=' {
                    return Err(ngc("expected '=' after parameter index"));
                }
                self.pos += 1;
                let rhs = self.read_real_value()?;
                pending.push((idx as u32, rhs));
                continue;
            }
            if ch == '/' {
                return Err(ngc("'/' is only allowed at the start of a line"));
            }
            if !ch.is_ascii_alphabetic() {
                return Err(ngc(format!("unexpected character {:?}", ch)));
            }
            let letter = ch.to_ascii_lowercase();
            if letter == 'n' {
                return Err(ngc("N (line number) is only allowed at the start of a line"));
            }
            self.pos += 1;
            let value = self.read_real_value()?;
            self.record_word(&mut result, letter, value)?;
        }

        result.parameter_settings = pending;
        Ok(Some(result))
    }

    fn parse_comment(&mut self) -> NgcResult<()> {
        debug_assert_eq!(self.raw[self.pos], '(');
        self.pos += 1;
        while self.pos < self.raw.len() {
            let c = self.raw[self.pos];
            if c == '(' { return Err(ngc("nested comments are not allowed")); }
            if c == ')' { self.pos += 1; return Ok(()); }
            self.pos += 1;
        }
        Err(ngc("unterminated comment"))
    }

    fn record_word(&mut self, r: &mut ParsedLine, letter: char, value: f64) -> NgcResult<()> {
        if letter == 'g' {
            let code = Self::format_g_or_m('G', value)?;
            if g_code_to_group(&code).is_none() {
                return Err(ngc(format!("unknown G code: {code}")));
            }
            r.g_codes.push(code);
            return Ok(());
        }
        if letter == 'm' {
            let iv = to_int_close(value, "M code")?;
            let code = format!("M{iv}");
            if m_code_to_group(&code).is_none() {
                return Err(ngc(format!("unknown M code: {code}")));
            }
            r.m_codes.push(code);
            return Ok(());
        }
        r.words.push((letter, value));
        Ok(())
    }

    fn format_g_or_m(letter: char, value: f64) -> NgcResult<String> {
        let scaled = value * 10.0;
        if !is_close_int(scaled) {
            return Err(ngc(format!("{letter} code value {value} not a recognized code")));
        }
        let n = scaled.round() as i64;
        if n % 10 == 0 {
            Ok(format!("{letter}{}", n / 10))
        } else {
            Ok(format!("{letter}{}.{}", n / 10, n % 10))
        }
    }

    // --- value readers ------------------------------------------------------

    fn read_real_value(&mut self) -> NgcResult<f64> {
        self.skip_ws();
        if self.pos >= self.raw.len() {
            return Err(ngc("expected real value, found end of line"));
        }
        let ch = self.raw[self.pos];
        if ch == '[' { return self.read_expression(); }
        if ch == '#' {
            self.pos += 1;
            let iv = self.read_real_value()?;
            let idx = to_int_close(iv, "parameter index")?;
            if !(1..=5399).contains(&idx) {
                return Err(ngc(format!("parameter index {idx} out of range")));
            }
            return Ok(*self.parameters.get(&(idx as u32)).unwrap_or(&0.0));
        }
        if ch == '+' || ch == '-' || ch == '.' || ch.is_ascii_digit() {
            return self.read_number();
        }
        if ch.is_ascii_alphabetic() {
            return self.read_unary();
        }
        Err(ngc(format!("unexpected character in value: {:?}", ch)))
    }

    fn read_number(&mut self) -> NgcResult<f64> {
        self.skip_ws();
        let mut s = String::new();
        if self.pos < self.raw.len() && (self.raw[self.pos] == '+' || self.raw[self.pos] == '-') {
            s.push(self.raw[self.pos]);
            self.pos += 1;
        }
        self.skip_ws();
        let mut digits_seen = false;
        while self.pos < self.raw.len() {
            let c = self.raw[self.pos];
            if c.is_ascii_digit() {
                s.push(c);
                digits_seen = true;
                self.pos += 1;
                continue;
            }
            if c == ' ' || c == '\t' { self.pos += 1; continue; }
            if c == '.' {
                s.push('.');
                self.pos += 1;
                while self.pos < self.raw.len() {
                    let c2 = self.raw[self.pos];
                    if c2.is_ascii_digit() { s.push(c2); digits_seen = true; self.pos += 1; continue; }
                    if c2 == ' ' || c2 == '\t' { self.pos += 1; continue; }
                    break;
                }
                break;
            }
            break;
        }
        if !digits_seen {
            return Err(ngc("expected number"));
        }
        s.parse::<f64>().map_err(|_| ngc(format!("invalid number {s:?}")))
    }

    fn read_unary(&mut self) -> NgcResult<f64> {
        let save = self.pos;
        let mut name = String::new();
        while self.pos < self.raw.len() {
            let c = self.raw[self.pos];
            if c.is_ascii_alphabetic() { name.push(c.to_ascii_lowercase()); self.pos += 1; continue; }
            if c == ' ' || c == '\t' { self.pos += 1; continue; }
            break;
        }
        let unary_ops = ["abs","acos","asin","atan","cos","exp","fix","fup","ln","round","sin","sqrt","tan"];
        if !unary_ops.contains(&name.as_str()) {
            self.pos = save;
            return Err(ngc(format!("unknown unary operator {name:?}")));
        }
        self.skip_ws();
        if self.peek() != '[' {
            return Err(ngc(format!("unary {name} must be followed by '['")));
        }
        let arg = self.read_expression()?;
        if name == "atan" {
            self.skip_ws();
            if self.peek() != '/' {
                return Err(ngc("ATAN requires the form ATAN[..]/[..]"));
            }
            self.pos += 1;
            self.skip_ws();
            if self.peek() != '[' {
                return Err(ngc("ATAN denominator must be a bracketed expression"));
            }
            let arg2 = self.read_expression()?;
            return Ok(arg.atan2(arg2).to_degrees());
        }
        Self::apply_unary(&name, arg)
    }

    fn apply_unary(name: &str, x: f64) -> NgcResult<f64> {
        Ok(match name {
            "abs" => x.abs(),
            "acos" => {
                if !(-1.0..=1.0).contains(&x) { return Err(ngc(format!("acos argument out of range: {x}"))); }
                x.acos().to_degrees()
            }
            "asin" => {
                if !(-1.0..=1.0).contains(&x) { return Err(ngc(format!("asin argument out of range: {x}"))); }
                x.asin().to_degrees()
            }
            "cos" => x.to_radians().cos(),
            "exp" => x.exp(),
            "fix" => x.floor(),
            "fup" => x.ceil(),
            "ln" => {
                if x <= 0.0 { return Err(ngc(format!("ln argument must be positive: {x}"))); }
                x.ln()
            }
            "round" => {
                if x >= 0.0 { (x + 0.5).floor() } else { -((-x + 0.5).floor()) }
            }
            "sin" => x.to_radians().sin(),
            "sqrt" => {
                if x < 0.0 { return Err(ngc(format!("sqrt argument must be non-negative: {x}"))); }
                x.sqrt()
            }
            "tan" => x.to_radians().tan(),
            _ => return Err(ngc(format!("unknown unary {name:?}"))),
        })
    }

    fn read_expression(&mut self) -> NgcResult<f64> {
        debug_assert_eq!(self.peek(), '[');
        self.pos += 1;
        let mut values: Vec<f64> = Vec::new();
        let mut ops: Vec<String> = Vec::new();
        values.push(self.read_real_value()?);
        loop {
            self.skip_ws();
            if self.pos >= self.raw.len() {
                return Err(ngc("unterminated expression"));
            }
            let c = self.raw[self.pos];
            if c == ']' { self.pos += 1; break; }
            let op = self.read_binary_op()?;
            ops.push(op);
            values.push(self.read_real_value()?);
        }
        Self::reduce_expression(&mut values, &mut ops)
    }

    fn read_binary_op(&mut self) -> NgcResult<String> {
        self.skip_ws();
        if self.pos >= self.raw.len() {
            return Err(ngc("expected binary operator, found end of line"));
        }
        let c = self.raw[self.pos];
        if c == '+' { self.pos += 1; return Ok("+".into()); }
        if c == '-' { self.pos += 1; return Ok("-".into()); }
        if c == '*' {
            if self.pos + 1 < self.raw.len() && self.raw[self.pos + 1] == '*' {
                self.pos += 2; return Ok("**".into());
            }
            self.pos += 1; return Ok("*".into());
        }
        if c == '/' { self.pos += 1; return Ok("/".into()); }
        for word in ["and", "xor", "mod", "or"] {
            let save = self.pos;
            let mut ok = true;
            for ch in word.chars() {
                self.skip_ws();
                if self.pos >= self.raw.len() || self.raw[self.pos].to_ascii_lowercase() != ch {
                    ok = false; break;
                }
                self.pos += 1;
            }
            if ok { return Ok(word.into()); }
            self.pos = save;
        }
        Err(ngc(format!("expected binary operator, found {:?}", c)))
    }

    fn reduce_expression(values: &mut Vec<f64>, ops: &mut Vec<String>) -> NgcResult<f64> {
        fn pass(values: &mut Vec<f64>, ops: &mut Vec<String>, group: &[&str]) -> NgcResult<()> {
            let mut i = 0;
            while i < ops.len() {
                if group.contains(&ops[i].as_str()) {
                    let a = values[i];
                    let b = values[i + 1];
                    let op = ops[i].clone();
                    let r = apply_binary(&op, a, b)?;
                    values[i] = r;
                    values.remove(i + 1);
                    ops.remove(i);
                } else {
                    i += 1;
                }
            }
            Ok(())
        }
        pass(values, ops, &["**"])?;
        pass(values, ops, &["*", "/", "mod"])?;
        pass(values, ops, &["+", "-", "and", "or", "xor"])?;
        Ok(values[0])
    }
}

fn apply_binary(op: &str, a: f64, b: f64) -> NgcResult<f64> {
    Ok(match op {
        "+" => a + b,
        "-" => a - b,
        "*" => a * b,
        "/" => {
            if b == 0.0 { return Err(ngc("division by zero")); }
            a / b
        }
        "**" => a.powf(b),
        "mod" => {
            if b == 0.0 { return Err(ngc("modulo by zero")); }
            // Python math.fmod: same sign as a.
            a % b
        }
        "and" => if a != 0.0 && b != 0.0 { 1.0 } else { 0.0 },
        "or" => if a != 0.0 || b != 0.0 { 1.0 } else { 0.0 },
        "xor" => if (a != 0.0) != (b != 0.0) { 1.0 } else { 0.0 },
        _ => return Err(ngc(format!("unknown binary op {op:?}"))),
    })
}

// ---------------------------------------------------------------------------
// Machine state
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
struct MachineState {
    programmed: Position,
    cs_offsets_inches: BTreeMap<u32, Position>,
    selected_cs: u32,
    g92_offsets_inches: Position,
    g92_active: bool,
    motion_mode: String,
    motion_mode_explicitly_set: bool,
    plane: String,
    distance_mode: String,
    feed_mode: String,
    units: String,
    cutter_comp: String,
    tool_length_offset_mode: String,
    return_mode: String,
    path_mode: String,
    feed_rate: f64,
    spindle_speed: f64,
    spindle_direction: String,
    coolant: String,
    overrides_enabled: bool,
    cutter_radius_compensation_number: Option<i64>,
    crc_radius_inches: f64,
    crc_contour_x: f64,
    crc_contour_y: f64,
    crc_first_move: bool,
    tool_length_offset_index: Option<i64>,
    tool_length_offset_value_inches: f64,
    selected_tool: Option<i64>,
    tool_in_spindle: Option<i64>,
    active_m_codes: BTreeMap<String, String>,
    cycle_r: Option<f64>,
    cycle_z: Option<f64>,
    last_motion_was_cycle: bool,
    cycle_old_z: f64,
    parameters: BTreeMap<u32, f64>,
    tools: BTreeMap<i64, Tool>,
}

impl Default for MachineState {
    fn default() -> Self {
        MachineState {
            programmed: Position::default(),
            cs_offsets_inches: BTreeMap::new(),
            selected_cs: 1,
            g92_offsets_inches: Position::default(),
            g92_active: false,
            motion_mode: "G1".into(),
            motion_mode_explicitly_set: false,
            plane: "G17".into(),
            distance_mode: "G90".into(),
            feed_mode: "G94".into(),
            units: "G20".into(),
            cutter_comp: "G40".into(),
            tool_length_offset_mode: "G49".into(),
            return_mode: "G98".into(),
            path_mode: "G61".into(),
            feed_rate: 0.0,
            spindle_speed: 0.0,
            spindle_direction: "OFF".into(),
            coolant: "M9".into(),
            overrides_enabled: true,
            cutter_radius_compensation_number: None,
            crc_radius_inches: 0.0,
            crc_contour_x: 0.0,
            crc_contour_y: 0.0,
            crc_first_move: true,
            tool_length_offset_index: None,
            tool_length_offset_value_inches: 0.0,
            selected_tool: None,
            tool_in_spindle: None,
            active_m_codes: BTreeMap::new(),
            cycle_r: None,
            cycle_z: None,
            last_motion_was_cycle: false,
            cycle_old_z: 0.0,
            parameters: BTreeMap::new(),
            tools: BTreeMap::new(),
        }
    }
}

// ---------------------------------------------------------------------------
// Trace helpers
// ---------------------------------------------------------------------------

fn linear_path_length_inches(start: &Position, end: &Position) -> f64 {
    let xyz_sq: f64 = LINEAR_AXES.iter()
        .map(|&a| (end.get(a) - start.get(a)).powi(2))
        .sum();
    if xyz_sq > 0.0 { return xyz_sq.sqrt(); }
    let rot_sq: f64 = ROTARY_AXES.iter()
        .map(|&a| (end.get(a) - start.get(a)).powi(2))
        .sum();
    rot_sq.sqrt()
}

fn arc_sweep_and_length(
    s1: f64, s2: f64, e1: f64, e2: f64,
    c1: f64, c2: f64, direction: &str,
) -> (f64, f64) {
    let r = ((s1 - c1).powi(2) + (s2 - c2).powi(2)).sqrt();
    if r < 1e-15 { return (0.0, 0.0); }
    let start_angle = (s2 - c2).atan2(s1 - c1);
    let end_angle = (e2 - c2).atan2(e1 - c1);
    let mut sweep = end_angle - start_angle;
    if direction == "G2" {
        if sweep >= 0.0 { sweep -= 2.0 * std::f64::consts::PI; }
    } else {
        if sweep <= 0.0 { sweep += 2.0 * std::f64::consts::PI; }
    }
    if (s1 - e1).abs() < 1e-12 && (s2 - e2).abs() < 1e-12 {
        sweep = if direction == "G2" { -2.0 * std::f64::consts::PI } else { 2.0 * std::f64::consts::PI };
    }
    let arc_len = sweep.abs() * r;
    (sweep, arc_len)
}

fn rapid_duration(path_length_inches: f64) -> f64 {
    path_length_inches / (RAPID_RATE_IPM / 60.0)
}

fn feed_duration(
    path_length_inches: f64,
    feed_rate: f64,
    feed_mode: &str,
    units: &str,
    rotary_only: bool,
) -> f64 {
    if feed_mode == "G93" {
        if feed_rate > 0.0 { 60.0 / feed_rate } else { 0.0 }
    } else if rotary_only {
        if feed_rate <= 0.0 { 0.0 } else { path_length_inches / (feed_rate / 60.0) }
    } else {
        let rate_ipm = if units == "G20" { feed_rate } else { feed_rate / MM_PER_INCH };
        if rate_ipm <= 0.0 { 0.0 } else { path_length_inches / (rate_ipm / 60.0) }
    }
}

fn interpolate_position(start: &Position, end: &Position, frac: f64) -> Position {
    let mut p = Position::default();
    for a in AXIS_LETTERS {
        p.set(a, start.get(a) + frac * (end.get(a) - start.get(a)));
    }
    p
}

fn interpolate_arc_position(
    start_ax1: f64, start_ax2: f64,
    center_ax1: f64, center_ax2: f64,
    sweep: f64, radius: f64,
    axial_start: f64, axial_end: f64,
    frac: f64,
    ax1_name: char, ax2_name: char, perp_name: char,
    start_pos: &Position, end_pos: &Position,
) -> Position {
    let start_angle = (start_ax2 - center_ax2).atan2(start_ax1 - center_ax1);
    let angle = start_angle + sweep * frac;
    let mut p = interpolate_position(start_pos, end_pos, frac);
    p.set(ax1_name, center_ax1 + radius * angle.cos());
    p.set(ax2_name, center_ax2 + radius * angle.sin());
    p.set(perp_name, axial_start + frac * (axial_end - axial_start));
    p
}

fn step_sub_motion(duration: f64, path_length: f64, mode: &str, step: f64) -> Vec<f64> {
    if duration <= 0.0 || path_length <= 0.0 { return Vec::new(); }
    let mut fracs: Vec<f64> = Vec::new();
    if mode == "time" {
        let dt = step;
        let mut t = dt;
        while t < duration - 1e-12 {
            fracs.push(t / duration);
            t += dt;
        }
    } else if mode == "distance" {
        let ds = step;
        let mut d = ds;
        while d < path_length - 1e-12 {
            fracs.push(d / path_length);
            d += ds;
        }
    }
    fracs.push(1.0);
    fracs
}

fn step_arc_tolerance(radius: f64, sweep: f64, eps: f64) -> Vec<f64> {
    if radius < 1e-15 || sweep.abs() < 1e-15 { return vec![1.0]; }
    let ratio = eps / radius;
    if ratio >= 1.0 { return vec![1.0]; }
    let dtheta = 2.0 * (1.0 - ratio).acos();
    let total = sweep.abs();
    let mut fracs: Vec<f64> = Vec::new();
    let mut a = dtheta;
    while a < total - 1e-12 {
        fracs.push(a / total);
        a += dtheta;
    }
    fracs.push(1.0);
    fracs
}

// ---------------------------------------------------------------------------
// Delta encoding
// ---------------------------------------------------------------------------

fn compute_delta(prev: &Value, cur: &Value) -> Map<String, Value> {
    let mut delta: Map<String, Value> = Map::new();
    let (Value::Object(prev_map), Value::Object(cur_map)) = (prev, cur) else { return delta; };
    for (key, cv) in cur_map {
        if key == "error" { continue; }
        let pv = prev_map.get(key);
        if is_nested_field(key) {
            if key == "coordinate_system_offsets" {
                if let (Value::Object(cv_obj), Some(Value::Object(pv_obj))) = (cv, pv) {
                    // Compare per system, per axis.
                    let mut cs_delta: Map<String, Value> = Map::new();
                    for (sk, sv) in cv_obj {
                        if let Value::Object(sv_map) = sv {
                            let prev_sys_map: Map<String, Value> = match pv_obj.get(sk) {
                                Some(Value::Object(p)) => p.clone(),
                                _ => Map::new(),
                            };
                            let mut ax_delta: Map<String, Value> = Map::new();
                            for (ak, av) in sv_map {
                                if prev_sys_map.get(ak) != Some(av) {
                                    ax_delta.insert(ak.clone(), av.clone());
                                }
                            }
                            if !ax_delta.is_empty() {
                                cs_delta.insert(sk.clone(), Value::Object(ax_delta));
                            }
                        }
                    }
                    if !cs_delta.is_empty() {
                        delta.insert(key.clone(), Value::Object(cs_delta));
                    }
                } else if pv.is_none() {
                    delta.insert(key.clone(), cv.clone());
                }
            } else {
                // one-level dict
                let pv_map = match pv { Some(Value::Object(o)) => Some(o), _ => None };
                let mut d: Map<String, Value> = Map::new();
                if let Value::Object(cv_map) = cv {
                    for (k, v) in cv_map {
                        let match_prev = pv_map.map(|m| m.get(k) == Some(v)).unwrap_or(false);
                        if !match_prev {
                            d.insert(k.clone(), v.clone());
                        }
                    }
                }
                if !d.is_empty() {
                    delta.insert(key.clone(), Value::Object(d));
                }
            }
        } else if is_nullable_scalar_field(key) {
            if pv != Some(cv) {
                delta.insert(key.clone(), cv.clone());
            }
        } else {
            if pv != Some(cv) {
                if !cv.is_null() {
                    delta.insert(key.clone(), cv.clone());
                }
            }
        }
    }
    delta
}

fn merge_deltas(pending: &Map<String, Value>, new_delta: &Map<String, Value>) -> Map<String, Value> {
    let mut merged = pending.clone();
    for (k, v) in new_delta {
        if is_nested_field(k) {
            if let (Some(Value::Object(merged_obj)), Value::Object(new_obj)) =
                (merged.get_mut(k), v) {
                if k == "coordinate_system_offsets" {
                    for (sk, sv) in new_obj {
                        if let Some(Value::Object(merged_sys)) = merged_obj.get_mut(sk) {
                            if let Value::Object(sv_obj) = sv {
                                for (ak, av) in sv_obj {
                                    merged_sys.insert(ak.clone(), av.clone());
                                }
                            }
                        } else {
                            merged_obj.insert(sk.clone(), sv.clone());
                        }
                    }
                } else {
                    for (ik, iv) in new_obj {
                        merged_obj.insert(ik.clone(), iv.clone());
                    }
                }
            } else {
                merged.insert(k.clone(), v.clone());
            }
        } else {
            merged.insert(k.clone(), v.clone());
        }
    }
    merged
}

// ---------------------------------------------------------------------------
// Trace recorder
// ---------------------------------------------------------------------------

struct ArcParams {
    start_ax1: f64, start_ax2: f64,
    center_ax1: f64, center_ax2: f64,
    sweep: f64, radius: f64,
    axial_start: f64, axial_end: f64,
    ax1_name: char, ax2_name: char, perp_name: char,
}

struct TraceRecorder {
    stepping_mode: String,
    step_value: f64,
    /// Closure that converts a programmed position into the machine_position
    /// map as serialized in payloads (units conversion, TLO applied).
    initial_state: Map<String, Value>,
    entries: Vec<Map<String, Value>>,
    prev_full_state: Value,
    error_line_number: Option<i64>,
    error_block_segment_index: Option<i64>,
    line_number: i64,
    line_cum_time: f64,
    line_has_entries: bool,
    line_pending_deltas: Map<String, Value>,
    line_nonmodal: Option<Vec<String>>,
    line_motion_attempted: bool,
}

impl TraceRecorder {
    fn new(stepping_mode: String, step_value: f64) -> Self {
        TraceRecorder {
            stepping_mode,
            step_value,
            initial_state: Map::new(),
            entries: Vec::new(),
            prev_full_state: Value::Object(Map::new()),
            error_line_number: None,
            error_block_segment_index: None,
            line_number: 0,
            line_cum_time: 0.0,
            line_has_entries: false,
            line_pending_deltas: Map::new(),
            line_nonmodal: None,
            line_motion_attempted: false,
        }
    }

    fn capture_initial_state(&mut self, payload: &Value) {
        let mut initial = payload.clone();
        if let Value::Object(m) = &mut initial { m.remove("error"); }
        self.initial_state = if let Value::Object(m) = &initial { m.clone() } else { Map::new() };
        self.prev_full_state = initial;
    }

    fn begin_line(&mut self, line_number: i64) {
        self.line_number = line_number;
        self.line_cum_time = 0.0;
        self.line_has_entries = false;
        self.line_pending_deltas = Map::new();
        self.line_nonmodal = None;
        self.line_motion_attempted = false;
    }

    fn set_line_nonmodal(&mut self, codes: Vec<String>) {
        if codes.is_empty() { self.line_nonmodal = None; return; }
        let mut v = codes;
        v.sort();
        self.line_nonmodal = Some(v);
    }

    fn set_pending_deltas(&mut self, state_snapshot: &Value) {
        self.line_pending_deltas = compute_delta(&self.prev_full_state, state_snapshot);
    }

    fn emit_sub_motion(
        &mut self,
        start_pos: &Position, end_pos: &Position,
        duration: f64, path_length: f64,
        is_canned_cycle: bool, motion_kind: Option<&str>,
        current_state: &Value,
        pos_converter: &dyn Fn(&Position) -> Map<String, Value>,
        arc_params: Option<&ArcParams>,
    ) {
        self.line_motion_attempted = true;
        if duration <= 0.0 && path_length <= 0.0 { return; }

        let fracs: Vec<f64> = if arc_params.is_some() && self.stepping_mode == "tolerance" {
            let ap = arc_params.unwrap();
            step_arc_tolerance(ap.radius, ap.sweep, self.step_value)
        } else if arc_params.is_some() && self.stepping_mode == "distance" {
            step_sub_motion(duration, path_length, "distance", self.step_value)
        } else {
            step_sub_motion(duration, path_length, &self.stepping_mode, self.step_value)
        };

        for (i, &frac) in fracs.iter().enumerate() {
            let is_first_entry_of_sm = i == 0;
            let is_first_entry_of_line = !self.line_has_entries;

            let pos = if let Some(ap) = arc_params {
                interpolate_arc_position(
                    ap.start_ax1, ap.start_ax2, ap.center_ax1, ap.center_ax2,
                    ap.sweep, ap.radius, ap.axial_start, ap.axial_end,
                    frac, ap.ax1_name, ap.ax2_name, ap.perp_name,
                    start_pos, end_pos,
                )
            } else {
                interpolate_position(start_pos, end_pos, frac)
            };

            let sample_time = self.line_cum_time + frac * duration;

            let mut full_state = current_state.clone();
            if let Value::Object(m) = &mut full_state {
                m.insert("machine_position".into(), Value::Object(pos_converter(&pos)));
            }

            let mut delta = compute_delta(&self.prev_full_state, &full_state);

            if is_first_entry_of_line && !self.line_pending_deltas.is_empty() {
                delta = merge_deltas(&self.line_pending_deltas, &delta);
                self.line_pending_deltas = Map::new();
            }

            let mut entry: Map<String, Value> = Map::new();
            entry.insert("line_number".into(), Value::from(self.line_number));
            entry.insert("time".into(), json_num(sample_time));
            if is_canned_cycle && is_first_entry_of_sm {
                if let Some(mk) = motion_kind {
                    entry.insert("motion_kind".into(), Value::from(mk));
                }
            }
            if is_first_entry_of_line {
                if let Some(nm) = &self.line_nonmodal {
                    entry.insert("nonmodal_g_codes".into(),
                        Value::Array(nm.iter().map(|s| Value::from(s.clone())).collect()));
                }
            } else if is_first_entry_of_sm {
                if let Some(nm) = &self.line_nonmodal {
                    if nm.iter().any(|c| c == "G28" || c == "G30") {
                        entry.insert("nonmodal_g_codes".into(),
                            Value::Array(nm.iter().map(|s| Value::from(s.clone())).collect()));
                    }
                }
            }

            for (k, v) in &delta {
                entry.insert(k.clone(), v.clone());
            }

            self.entries.push(entry);
            self.prev_full_state = full_state;
            self.line_has_entries = true;
        }

        self.line_cum_time += duration;
    }

    fn emit_state_only(&mut self, current_state: &Value) {
        let full_state = current_state.clone();
        let delta = compute_delta(&self.prev_full_state, &full_state);
        if delta.is_empty() && self.line_nonmodal.is_none() {
            return;
        }
        let mut entry: Map<String, Value> = Map::new();
        entry.insert("line_number".into(), Value::from(self.line_number));
        entry.insert("time".into(), json_num(STATE_ONLY_EPSILON));
        if let Some(nm) = &self.line_nonmodal {
            entry.insert("nonmodal_g_codes".into(),
                Value::Array(nm.iter().map(|s| Value::from(s.clone())).collect()));
        }
        for (k, v) in &delta {
            entry.insert(k.clone(), v.clone());
        }
        self.entries.push(entry);
        self.prev_full_state = full_state;
        self.line_has_entries = true;
    }

    fn emit_dwell(&mut self, p_seconds: f64, current_state: &Value) {
        if p_seconds <= 0.0 {
            if let Some(nm) = &mut self.line_nonmodal {
                nm.retain(|c| c != "G4");
                if nm.is_empty() { self.line_nonmodal = None; }
            }
            return;
        }
        let full_state = current_state.clone();
        let mut delta = compute_delta(&self.prev_full_state, &full_state);
        if !self.line_pending_deltas.is_empty() {
            delta = merge_deltas(&self.line_pending_deltas, &delta);
            self.line_pending_deltas = Map::new();
        }
        let mut entry: Map<String, Value> = Map::new();
        entry.insert("line_number".into(), Value::from(self.line_number));
        entry.insert("time".into(), json_num(self.line_cum_time + p_seconds));
        if let Some(nm) = &self.line_nonmodal {
            entry.insert("nonmodal_g_codes".into(),
                Value::Array(nm.iter().map(|s| Value::from(s.clone())).collect()));
        }
        for (k, v) in &delta {
            entry.insert(k.clone(), v.clone());
        }
        self.entries.push(entry);
        self.prev_full_state = full_state;
        self.line_has_entries = true;
        self.line_cum_time += p_seconds;
    }

    fn build_trace(&self) -> Value {
        let mut out = Map::new();
        out.insert("initial_state".into(), Value::Object(self.initial_state.clone()));
        out.insert("entries".into(), Value::Array(
            self.entries.iter().map(|m| Value::Object(m.clone())).collect()
        ));
        out.insert("error_line_number".into(), match self.error_line_number {
            Some(n) => Value::from(n), None => Value::Null
        });
        out.insert("error_block_segment_index".into(), match self.error_block_segment_index {
            Some(n) => Value::from(n), None => Value::Null
        });
        Value::Object(out)
    }

    fn set_error(&mut self, line: i64, seg: Option<i64>) {
        self.error_line_number = Some(line);
        self.error_block_segment_index = seg;
    }
}

// ---------------------------------------------------------------------------
// Arc geometry helpers
// ---------------------------------------------------------------------------

fn arc_center_from_radius(
    sx: f64, sy: f64, ex: f64, ey: f64, r_word: f64, mode: &str,
) -> (f64, f64) {
    let r = r_word;
    let dx = ex - sx; let dy = ey - sy;
    let chord = (dx * dx + dy * dy).sqrt();
    if chord == 0.0 { return (sx, sy); }
    let h = (r * r - (chord / 2.0).powi(2)).max(0.0).sqrt();
    let mx = (sx + ex) / 2.0;
    let my = (sy + ey) / 2.0;
    let px = -dy / chord;
    let py = dx / chord;
    let sign = if (mode == "G3" && r >= 0.0) || (mode == "G2" && r < 0.0) { 1.0 } else { -1.0 };
    (mx + sign * h * px, my + sign * h * py)
}

fn two_circle_intersection_pick(
    x1: f64, y1: f64, r1: f64,
    x2: f64, y2: f64, r2: f64,
    mode: &str,
) -> (f64, f64) {
    let dx = x2 - x1; let dy = y2 - y1;
    let d = (dx * dx + dy * dy).sqrt();
    if d == 0.0 { return (x1, y1); }
    let a = (r1 * r1 - r2 * r2 + d * d) / (2.0 * d);
    let h = (r1 * r1 - a * a).max(0.0).sqrt();
    let mx = x1 + a * dx / d;
    let my = y1 + a * dy / d;
    let px = -dy / d;
    let py = dx / d;
    let cand1 = (mx + h * px, my + h * py);
    let cand2 = (mx - h * px, my - h * py);
    if mode == "G3" { cand2 } else { cand1 }
}

// ---------------------------------------------------------------------------
// Interpreter
// ---------------------------------------------------------------------------

struct Interpreter {
    state: MachineState,
    block_delete: bool,
    carousel_slots: Option<i64>,
    probe_box_inches: Option<(f64, f64, f64, f64, f64, f64)>,
    probe_tool: Option<i64>,
    program_ended: bool,
    current_line_number: i64,
    f_on_this_line: bool,
    trace: Option<TraceRecorder>,
}

impl Interpreter {
    fn new(
        block_delete: bool,
        carousel_slots: Option<i64>,
        probe_box: Option<(f64, f64, f64, f64, f64, f64)>,
        probe_tool: Option<i64>,
    ) -> Self {
        let mut st = MachineState::default();
        st.active_m_codes.insert("7".into(), "M5".into());
        st.active_m_codes.insert("8".into(), "M9".into());
        st.active_m_codes.insert("9".into(), "M48".into());
        Interpreter {
            state: st,
            block_delete,
            carousel_slots,
            probe_box_inches: probe_box,
            probe_tool,
            program_ended: false,
            current_line_number: 0,
            f_on_this_line: false,
            trace: None,
        }
    }

    // -- coordinate-system helpers ------------------------------------------

    fn get_cs_offset(&mut self, system: u32) -> Position {
        *self.state.cs_offsets_inches.entry(system).or_insert(Position::default())
    }

    fn set_cs_offset(&mut self, system: u32, p: Position) {
        self.state.cs_offsets_inches.insert(system, p);
    }

    fn absolute_inches_from_programmed(&mut self, prog: Option<Position>) -> Position {
        let p = prog.unwrap_or(self.state.programmed);
        let cs = self.get_cs_offset(self.state.selected_cs);
        let g92 = if self.state.g92_active { self.state.g92_offsets_inches } else { Position::default() };
        let mut r = Position::default();
        for a in AXIS_LETTERS {
            r.set(a, p.get(a) + cs.get(a) + g92.get(a));
        }
        r
    }

    fn programmed_from_absolute_inches(&mut self, abs_in: Position) -> Position {
        let cs = self.get_cs_offset(self.state.selected_cs);
        let g92 = if self.state.g92_active { self.state.g92_offsets_inches } else { Position::default() };
        let mut r = Position::default();
        for a in AXIS_LETTERS {
            r.set(a, abs_in.get(a) - cs.get(a) - g92.get(a));
        }
        r
    }

    fn controlled_point_in_active_units(&mut self, prog: Option<Position>) -> Position {
        let mut abs_in = self.absolute_inches_from_programmed(prog);
        abs_in.z -= self.state.tool_length_offset_value_inches;
        let mut r = Position::default();
        for a in AXIS_LETTERS {
            let v = abs_in.get(a);
            r.set(a, if is_linear(a) { from_inches_units(v, &self.state.units) } else { v });
        }
        r
    }

    fn axis_word_inches(&self, axis: char, value: f64) -> f64 {
        if is_linear(axis) { to_inches_units(value, &self.state.units) } else { value }
    }

    // -- parameter / tool file loaders --------------------------------------

    fn load_parameter_file(&mut self, path: &str) -> NgcResult<()> {
        let text = fs::read_to_string(path).map_err(|e| ngc(format!("parameter file: {e}")))?;
        let text = text.replace("\r\n", "\n");
        let lines: Vec<&str> = text.split('\n').collect();
        let mut blank: Option<usize> = None;
        for (i, line) in lines.iter().enumerate() {
            if line.is_empty() { blank = Some(i); break; }
        }
        let blank = blank.ok_or_else(|| ngc("parameter file has no blank separator line"))?;
        let mut last_idx: i64 = 0;
        let mut loaded_indices = std::collections::BTreeSet::new();
        for line in &lines[blank + 1..] {
            let s = line.trim();
            if s.is_empty() { continue; }
            let parts: Vec<&str> = s.split_ascii_whitespace().collect();
            if parts.len() < 2 {
                return Err(ngc("parameter file line must have index and value"));
            }
            let idx: i64 = parts[0].parse().map_err(|_| ngc(format!("parameter file line {line:?} invalid")))?;
            let val: f64 = parts[1].parse().map_err(|_| ngc(format!("parameter file line {line:?} invalid")))?;
            if !(1..=5400).contains(&idx) {
                return Err(ngc(format!("parameter file index {idx} out of range 1..5400")));
            }
            if idx <= last_idx {
                return Err(ngc("parameter file indices must be ascending"));
            }
            last_idx = idx;
            self.state.parameters.insert(idx as u32, val);
            loaded_indices.insert(idx as u32);
        }

        // RS274 3.2.1, Table 2: all six supported axes are required.
        // Defaults in machine state cannot replace entries missing from input.
        for idx in required_output_parameters() {
            if !loaded_indices.contains(&idx) {
                return Err(ngc(format!("parameter file missing required parameter {idx}")));
            }
        }

        let sel = *self.state.parameters.get(&SELECTED_CS_PARAM).unwrap_or(&1.0);
        if !is_close_int(sel) || !(1.0..=9.0).contains(&sel) {
            return Err(ngc("parameter 5220 must be a whole number from 1 to 9"));
        }
        self.state.selected_cs = sel.round() as u32;

        for s in 1..=9u32 {
            let [xp, yp, zp, ap, bp, cp] = cs_xyzabc_param_indices(s);
            let cs = Position {
                x: *self.state.parameters.get(&xp).unwrap_or(&0.0),
                y: *self.state.parameters.get(&yp).unwrap_or(&0.0),
                z: *self.state.parameters.get(&zp).unwrap_or(&0.0),
                a: *self.state.parameters.get(&ap).unwrap_or(&0.0),
                b: *self.state.parameters.get(&bp).unwrap_or(&0.0),
                c: *self.state.parameters.get(&cp).unwrap_or(&0.0),
            };
            self.set_cs_offset(s, cs);
        }

        let [gx, gy, gz, ga, gb, gc] = G92_OFFSET_PARAMS;
        self.state.g92_offsets_inches = Position {
            x: *self.state.parameters.get(&gx).unwrap_or(&0.0),
            y: *self.state.parameters.get(&gy).unwrap_or(&0.0),
            z: *self.state.parameters.get(&gz).unwrap_or(&0.0),
            a: *self.state.parameters.get(&ga).unwrap_or(&0.0),
            b: *self.state.parameters.get(&gb).unwrap_or(&0.0),
            c: *self.state.parameters.get(&gc).unwrap_or(&0.0),
        };
        Ok(())
    }

    fn initialize_default_parameters(&mut self) {
        for p in required_output_parameters() {
            self.state.parameters.entry(p).or_insert(0.0);
        }
        self.state.parameters.insert(SELECTED_CS_PARAM, self.state.selected_cs as f64);
    }

    fn load_tool_table(&mut self, path: &str) -> NgcResult<()> {
        let text = fs::read_to_string(path).map_err(|e| ngc(format!("tool file: {e}")))?;
        let text = text.replace("\r\n", "\n");
        let lines: Vec<&str> = text.split('\n').collect();
        let mut blank: Option<usize> = None;
        for (i, line) in lines.iter().enumerate() {
            if line.is_empty() { blank = Some(i); break; }
        }
        let blank = blank.ok_or_else(|| ngc("tool file has no blank separator line"))?;
        for line in &lines[blank + 1..] {
            if line.trim().is_empty() { continue; }
            let parts: Vec<&str> = line.split_ascii_whitespace().collect();
            if parts.len() < 4 {
                return Err(ngc("tool file row needs at least 4 fields"));
            }
            let pocket: i64 = parts[0].parse().map_err(|_| ngc(format!("tool file row invalid: {line:?}")))?;
            let fms: i64 = parts[1].parse().map_err(|_| ngc(format!("tool file row invalid: {line:?}")))?;
            let tlo: f64 = parts[2].parse().map_err(|_| ngc(format!("tool file row invalid: {line:?}")))?;
            let diam: f64 = parts[3].parse().map_err(|_| ngc(format!("tool file row invalid: {line:?}")))?;
            self.state.tools.insert(pocket, Tool { _pocket: pocket, _fms: fms, tlo, diameter: diam });
        }
        Ok(())
    }

    // -- main loop -----------------------------------------------------------

    fn run(&mut self, program_text: &str) -> NgcResult<()> {
        let program_text = program_text.replace("\r\n", "\n");
        let lines: Vec<&str> = program_text.split('\n').collect();
        let mut start_index = 0usize;
        let mut end_index = lines.len();

        let first_pct = lines.iter().position(|l| l.trim() == "%");
        if let Some(first) = first_pct {
            let second = lines[first + 1..].iter().position(|l| l.trim() == "%");
            match second {
                Some(off) => {
                    start_index = first + 1;
                    end_index = first + 1 + off;
                }
                None => return Err(ngc("file with percent prefix is missing closing percent line")),
            }
        }

        if self.trace.is_some() {
            let payload = self.build_payload();
            let payload_val = Value::Object(payload);
            self.trace.as_mut().unwrap().capture_initial_state(&payload_val);
        }

        for i in start_index..end_index {
            if self.program_ended { break; }
            self.current_line_number = (i + 1) as i64;
            self.run_line(lines[i])?;
        }
        Ok(())
    }

    fn run_line(&mut self, raw: &str) -> NgcResult<()> {
        let chars: Vec<char> = raw.chars().collect();
        let params = &self.state.parameters.clone();
        let mut parser = LineParser::new(&chars, params);
        let parsed = parser.parse(self.block_delete)?;
        if let Some(p) = parsed {
            self.execute_parsed(p)?;
        }
        Ok(())
    }

    // -- execute parsed line -------------------------------------------------

    fn execute_parsed(&mut self, parsed: ParsedLine) -> NgcResult<()> {
        // Group G/M codes.
        let mut g_by_group: BTreeMap<String, String> = BTreeMap::new();
        let mut group0_seen: Vec<String> = Vec::new();
        for code in &parsed.g_codes {
            let grp = g_code_to_group(code).expect("unknown g grouped");
            if grp == "0" {
                if !group0_seen.is_empty() {
                    return Err(ngc(format!(
                        "two G codes used from same modal group 0 ({} and {})",
                        group0_seen[0], code
                    )));
                }
                group0_seen.push(code.clone());
                continue;
            }
            if let Some(prev) = g_by_group.get(grp) {
                return Err(ngc(format!(
                    "two G codes used from same modal group {grp} ({prev} and {code})"
                )));
            }
            g_by_group.insert(grp.into(), code.clone());
        }

        if parsed.m_codes.len() > 4 {
            return Err(ngc("more than four M words on one line"));
        }
        let mut m_by_group: BTreeMap<String, String> = BTreeMap::new();
        for code in &parsed.m_codes {
            let grp = m_code_to_group(code).expect("unknown m grouped");
            if let Some(prev) = m_by_group.get(grp) {
                return Err(ngc(format!(
                    "two M codes used from same modal group {grp} ({prev} and {code})"
                )));
            }
            m_by_group.insert(grp.into(), code.clone());
        }

        // Build word dict.
        let mut word_dict: BTreeMap<char, f64> = BTreeMap::new();
        for (letter, value) in &parsed.words {
            if word_dict.contains_key(letter) {
                return Err(ngc(format!("word {} appears more than once on a line", letter.to_ascii_uppercase())));
            }
            word_dict.insert(*letter, *value);
        }

        // Trace: begin line.
        if self.trace.is_some() {
            let ln = self.current_line_number;
            let tr = self.trace.as_mut().unwrap();
            tr.begin_line(ln);
            if !group0_seen.is_empty() {
                tr.set_line_nonmodal(group0_seen.clone());
            }
        }

        // Apply parameter settings.
        for (idx, val) in &parsed.parameter_settings {
            self.state.parameters.insert(*idx, *val);
            self.maybe_sync_param_into_state(*idx, *val);
        }

        // 2. feed rate mode
        if let Some(fm) = g_by_group.get("5") {
            self.state.feed_mode = fm.clone();
        }

        // 3. feed rate
        if let Some(&f) = word_dict.get(&'f') {
            self.state.feed_rate = f;
        }
        self.f_on_this_line = word_dict.contains_key(&'f');

        // 4. spindle speed
        if let Some(&s) = word_dict.get(&'s') {
            if s < 0.0 { return Err(ngc("S word must not be negative")); }
            self.state.spindle_speed = s;
        }

        // 5. tool selection
        if let Some(&tv) = word_dict.get(&'t') {
            let ti = to_int_close(tv, "T")?;
            if ti < 0 { return Err(ngc("T number must not be negative")); }
            if let Some(slots) = self.carousel_slots {
                if ti > slots {
                    return Err(ngc(format!("T number {ti} exceeds carousel slot count {slots}")));
                }
            }
            self.state.selected_tool = Some(ti);
        }

        // 6. tool change M6
        if m_by_group.get("6").map(|s| s.as_str()) == Some("M6") {
            let sel = self.state.selected_tool;
            self.state.tool_in_spindle = match sel {
                Some(0) | None => None,
                Some(n) => Some(n),
            };
            self.state.spindle_direction = "OFF".into();
            self.state.active_m_codes.insert("7".into(), "M5".into());
            self.state.active_m_codes.insert("6".into(), "M6".into());
        }

        // 7. spindle on/off
        if let Some(mc) = m_by_group.get("7").cloned() {
            self.state.active_m_codes.insert("7".into(), mc.clone());
            self.state.spindle_direction = match mc.as_str() {
                "M3" => "CW".into(),
                "M4" => "CCW".into(),
                "M5" => "OFF".into(),
                _ => self.state.spindle_direction.clone(),
            };
        }

        // 8. coolant
        if let Some(mc) = m_by_group.get("8").cloned() {
            self.state.coolant = mc.clone();
            self.state.active_m_codes.insert("8".into(), mc);
        }

        // 9. overrides
        if let Some(mc) = m_by_group.get("9").cloned() {
            self.state.overrides_enabled = mc == "M48";
            self.state.active_m_codes.insert("9".into(), mc);
        }

        // 10. dwell (G4)
        if group0_seen.iter().any(|c| c == "G4") {
            let p = *word_dict.get(&'p').unwrap_or(&-1.0);
            if !word_dict.contains_key(&'p') || p < 0.0 {
                return Err(ngc("G4 requires non-negative P"));
            }
            if self.trace.is_some() {
                let payload = self.build_payload();
                let payload_val = Value::Object(payload);
                self.trace.as_mut().unwrap().emit_dwell(p, &payload_val);
            }
        }

        // 11. active plane
        if let Some(pl) = g_by_group.get("2").cloned() {
            if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") && pl != "G17" {
                return Err(ngc("cannot use non-XY plane while cutter radius compensation is on"));
            }
            self.state.plane = pl;
        }

        // 12. units
        if let Some(u) = g_by_group.get("6").cloned() {
            if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
                return Err(ngc("cannot change units while cutter radius compensation is on"));
            }
            self.state.units = u;
        }

        // 13. cutter radius compensation
        if let Some(crc) = g_by_group.get("7").cloned() {
            if crc == "G40" {
                self.state.cutter_comp = "G40".into();
                self.state.cutter_radius_compensation_number = None;
                self.state.crc_radius_inches = 0.0;
                self.state.crc_first_move = true;
            } else {
                if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
                    return Err(ngc("cannot turn cutter radius compensation on when it is already on"));
                }
                if self.state.plane != "G17" {
                    return Err(ngc("cutter radius compensation requires the XY-plane"));
                }
                let d_raw = word_dict.get(&'d').copied();
                let num = if let Some(d) = d_raw {
                    if !is_close_int(d) { return Err(ngc("D word must be an integer")); }
                    let di = d.round() as i64;
                    if di < 0 { return Err(ngc("D number must not be negative")); }
                    if let Some(slots) = self.carousel_slots {
                        if di > slots { return Err(ngc(format!("D number {di} exceeds carousel slot count"))); }
                    }
                    di
                } else {
                    self.state.tool_in_spindle.unwrap_or(0)
                };
                self.state.cutter_radius_compensation_number = Some(num);
                self.state.cutter_comp = crc;
                let radius_in_units = if num == 0 {
                    0.0
                } else if let Some(tool) = self.state.tools.get(&num) {
                    tool.diameter / 2.0
                } else {
                    0.0
                };
                self.state.crc_radius_inches = to_inches_units(radius_in_units, &self.state.units);
                self.state.crc_first_move = true;
            }
        } else {
            if word_dict.contains_key(&'d') {
                return Err(ngc("D word used without G41 or G42"));
            }
        }

        if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
            if g_by_group.contains_key("12") {
                return Err(ngc("cannot select coordinate system while cutter radius compensation is on"));
            }
        }

        // 14. tool length offset
        if let Some(tlc) = g_by_group.get("8").cloned() {
            if tlc == "G49" {
                self.state.tool_length_offset_mode = "G49".into();
                self.state.tool_length_offset_index = None;
                self.state.tool_length_offset_value_inches = 0.0;
            } else {
                let h = word_dict.get(&'h').copied().ok_or_else(|| ngc("G43 requires an H word"))?;
                if !is_close_int(h) { return Err(ngc("H word must be an integer")); }
                let hi = h.round() as i64;
                if hi < 0 { return Err(ngc("H number must not be negative")); }
                if let Some(slots) = self.carousel_slots {
                    if hi > slots { return Err(ngc(format!("H number {hi} exceeds carousel slot count"))); }
                }
                self.state.tool_length_offset_mode = "G43".into();
                self.state.tool_length_offset_index = Some(hi);
                if hi == 0 {
                    self.state.tool_length_offset_value_inches = 0.0;
                } else if let Some(tool) = self.state.tools.get(&hi) {
                    let tlo = tool.tlo;
                    self.state.tool_length_offset_value_inches = to_inches_units(tlo, &self.state.units);
                } else {
                    self.state.tool_length_offset_value_inches = 0.0;
                }
            }
        }

        // 15. CS selection
        if let Some(sys_code) = g_by_group.get("12").cloned() {
            let n = cs_gcode_to_number(&sys_code).expect("cs code");
            self.state.selected_cs = n;
            self.state.parameters.insert(SELECTED_CS_PARAM, n as f64);
        }

        // 16. path control mode
        if let Some(p) = g_by_group.get("13").cloned() {
            self.state.path_mode = p;
        }

        // 17. distance mode
        if let Some(d) = g_by_group.get("3").cloned() {
            self.state.distance_mode = d;
        }

        // 18. retract mode
        if let Some(r) = g_by_group.get("10").cloned() {
            self.state.return_mode = r;
        }

        // Trace: capture modal state changes.
        if let Some(tr) = self.trace.as_ref() {
            if !tr.line_has_entries {
                let payload = self.build_payload();
                let payload_val = Value::Object(payload);
                self.trace.as_mut().unwrap().set_pending_deltas(&payload_val);
            }
        }

        // 19. Group 0 (G10/G28/G30/G92/G92.x)
        let axis_words_present = AXIS_LETTERS.iter().any(|a| word_dict.contains_key(a));
        let group0_axis_using: Vec<String> = group0_seen.iter()
            .filter(|c| is_group0_axis_using(c))
            .cloned().collect();
        for code in &group0_seen.clone() {
            if (code == "G28" || code == "G30") &&
                matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
                return Err(ngc(format!("cannot use {code} while cutter radius compensation is on")));
            }
            if matches!(code.as_str(), "G92" | "G92.1" | "G92.2" | "G92.3") &&
                matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
                return Err(ngc("cannot change axis offsets while cutter radius compensation is on"));
            }
            match code.as_str() {
                "G10" => self.do_g10(&word_dict)?,
                "G28" => self.do_g28_or_g30(&word_dict, &G28_HOME_PARAMS)?,
                "G30" => self.do_g28_or_g30(&word_dict, &G30_HOME_PARAMS)?,
                "G92" => self.do_g92(&word_dict)?,
                "G92.1" => self.do_g92_1(),
                "G92.2" => self.do_g92_2(),
                "G92.3" => self.do_g92_3(),
                _ => {}
            }
        }

        let suspend_group1 = !group0_axis_using.is_empty();

        // 20. motion (group 1, possibly with G53)
        let new_motion = g_by_group.get("1").cloned();
        let g53 = group0_seen.iter().any(|c| c == "G53");
        if let Some(m) = &new_motion {
            self.state.motion_mode = m.clone();
            if m == "G0" || m == "G1" {
                self.state.motion_mode_explicitly_set = true;
            }
        }
        if g53 {
            if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
                return Err(ngc("cannot use G53 while cutter radius compensation is on"));
            }
            if !(self.state.motion_mode_explicitly_set &&
                 matches!(self.state.motion_mode.as_str(), "G0" | "G1")) {
                return Err(ngc("G53 requires G0 or G1 to be active"));
            }
        }

        if self.state.motion_mode == "G80" && !suspend_group1 {
            if axis_words_present && group0_axis_using.is_empty() {
                return Err(ngc("axis words used while G80 is active"));
            }
        } else if suspend_group1 && new_motion.is_none() {
            // suspend
        } else {
            let motion_cycle_active = is_canned_cycle(&self.state.motion_mode);
            if motion_cycle_active {
                if axis_words_present {
                    self.do_canned_cycle(&word_dict, &group0_axis_using)?;
                } else if ['r', 'p', 'l', 'i', 'j', 'k'].iter().any(|c| word_dict.contains_key(c)) {
                    return Err(ngc("canned cycle line missing X, Y, and Z words"));
                }
            } else {
                let should_motion = axis_words_present
                    || matches!(new_motion.as_deref(), Some("G2") | Some("G3") | Some("G38.2"))
                    || new_motion.as_deref().map(is_canned_cycle).unwrap_or(false)
                    || (matches!(new_motion.as_deref(), Some("G0") | Some("G1")) && !axis_words_present)
                    || g53;
                if should_motion && !suspend_group1 {
                    self.do_motion(&word_dict, g53, false)?;
                }
            }
        }

        // 21. program end
        if let Some(mc) = m_by_group.get("4").cloned() {
            self.state.active_m_codes.insert("4".into(), mc.clone());
            if mc == "M2" || mc == "M30" {
                self.do_program_end();
            }
        }

        // Trace end-of-line fallback.
        if self.trace.is_some() {
            let payload = self.build_payload();
            let payload_val = Value::Object(payload);
            let delta = compute_delta(&self.trace.as_ref().unwrap().prev_full_state, &payload_val);
            let tr = self.trace.as_mut().unwrap();
            if tr.line_motion_attempted && !tr.line_has_entries {
                tr.line_nonmodal = None;
            }
            if !delta.is_empty() || (!tr.line_has_entries && tr.line_nonmodal.is_some()) {
                if !tr.line_has_entries {
                    tr.emit_state_only(&payload_val);
                } else {
                    // Fold post-motion state changes into last entry.
                    let meta: std::collections::HashSet<&str> =
                        ["line_number","time","motion_kind","nonmodal_g_codes"].iter().copied().collect();
                    let nested: std::collections::HashSet<&str> =
                        ["machine_position","coordinate_system_offsets",
                         "active_modal_g_codes","active_modal_m_codes","parameters"].iter().copied().collect();
                    let last = tr.entries.last().unwrap().clone();
                    let mut scalar_conflict = false;
                    for (k, _) in &delta {
                        if !meta.contains(k.as_str()) && !nested.contains(k.as_str()) && last.contains_key(k) {
                            scalar_conflict = true;
                            break;
                        }
                    }
                    if scalar_conflict {
                        let time = last.get("time").cloned().unwrap_or(Value::Null);
                        let mut trail: Map<String, Value> = Map::new();
                        trail.insert("line_number".into(), Value::from(tr.line_number));
                        trail.insert("time".into(), time);
                        for (k, v) in &delta { trail.insert(k.clone(), v.clone()); }
                        tr.entries.push(trail);
                    } else {
                        let last_idx = tr.entries.len() - 1;
                        let merged = merge_deltas(&tr.entries[last_idx], &delta);
                        tr.entries[last_idx] = merged;
                    }
                    tr.prev_full_state = payload_val.clone();
                }
            }
        }
        Ok(())
    }

    // -- group-0 commands ----------------------------------------------------

    fn do_g10(&mut self, word_dict: &BTreeMap<char, f64>) -> NgcResult<()> {
        let l = *word_dict.get(&'l').ok_or_else(|| ngc("G10 requires an L word"))?;
        let li = to_int_close(l, "G10 L")?;
        if li != 2 { return Err(ngc("G10 currently only supports L2")); }
        let p_raw = *word_dict.get(&'p').ok_or_else(|| ngc("G10 L2 requires a P word"))?;
        if !is_close_int(p_raw) { return Err(ngc("G10 P must be an integer")); }
        let p = p_raw.round() as u32;
        if !(1..=9).contains(&p) { return Err(ngc("G10 L2 P must be 1..9")); }

        let changing_active = p == self.state.selected_cs;
        let abs_before = if changing_active {
            Some(self.absolute_inches_from_programmed(None))
        } else { None };

        let mut cs = self.get_cs_offset(p);
        for &axis in AXIS_LETTERS.iter() {
            if let Some(&v) = word_dict.get(&axis) {
                let v_in = self.axis_word_inches(axis, v);
                cs.set(axis, v_in);
                let xp = cs_xyzabc_param_indices(p)[axis_index(axis)];
                self.state.parameters.insert(xp, v);
            }
        }
        self.set_cs_offset(p, cs);
        if let Some(ab) = abs_before {
            self.state.programmed = self.programmed_from_absolute_inches(ab);
        }
        Ok(())
    }

    fn do_g28_or_g30(
        &mut self, word_dict: &BTreeMap<char, f64>, home_params: &[u32; 6],
    ) -> NgcResult<()> {
        if AXIS_LETTERS.iter().any(|a| word_dict.contains_key(a)) {
            self.do_motion(word_dict, false, true)?;
        }
        let trace_start = if self.trace.is_some() { Some(self.state.programmed) } else { None };
        let mut home = Position::default();
        home.x = *self.state.parameters.get(&home_params[0]).unwrap_or(&0.0);
        home.y = *self.state.parameters.get(&home_params[1]).unwrap_or(&0.0);
        home.z = *self.state.parameters.get(&home_params[2]).unwrap_or(&0.0);
        home.a = *self.state.parameters.get(&home_params[3]).unwrap_or(&0.0);
        home.b = *self.state.parameters.get(&home_params[4]).unwrap_or(&0.0);
        home.c = *self.state.parameters.get(&home_params[5]).unwrap_or(&0.0);
        let prog = self.programmed_from_absolute_inches(home);
        self.state.programmed = prog;

        if let Some(start) = trace_start {
            let path_len = linear_path_length_inches(&start, &self.state.programmed);
            let dur = rapid_duration(path_len);
            let payload = self.build_payload();
            let payload_val = Value::Object(payload);
            let conv = self.make_pos_converter();
            let end = self.state.programmed;
            if let Some(tr) = self.trace.as_mut() {
                tr.emit_sub_motion(
                    &start, &end, dur, path_len, false, None,
                    &payload_val, &*conv, None,
                );
            }
        }
        Ok(())
    }

    fn do_g92(&mut self, word_dict: &BTreeMap<char, f64>) -> NgcResult<()> {
        if !AXIS_LETTERS.iter().any(|a| word_dict.contains_key(a)) {
            return Err(ngc("G92 requires at least one axis word"));
        }
        let cs = self.get_cs_offset(self.state.selected_cs);
        let cur_abs = self.absolute_inches_from_programmed(None);
        let mut new_g92 = self.state.g92_offsets_inches;
        let mut new_prog = self.state.programmed;
        for &axis in AXIS_LETTERS.iter() {
            if let Some(&v) = word_dict.get(&axis) {
                let spec_in = self.axis_word_inches(axis, v);
                let g92v = cur_abs.get(axis) - cs.get(axis) - spec_in;
                new_g92.set(axis, g92v);
                new_prog.set(axis, spec_in);
            }
        }
        self.state.g92_offsets_inches = new_g92;
        self.state.g92_active = true;
        self.state.programmed = new_prog;

        let units = self.state.units.clone();
        for (i, &axis) in AXIS_LETTERS.iter().enumerate() {
            let p_idx = G92_OFFSET_PARAMS[i];
            let v = new_g92.get(axis);
            let v_stored = if is_linear(axis) { from_inches_units(v, &units) } else { v };
            self.state.parameters.insert(p_idx, v_stored);
        }
        Ok(())
    }

    fn do_g92_1(&mut self) {
        let cur_abs = self.absolute_inches_from_programmed(None);
        self.state.g92_offsets_inches = Position::default();
        self.state.g92_active = false;
        for p in G92_OFFSET_PARAMS { self.state.parameters.insert(p, 0.0); }
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs);
    }

    fn do_g92_2(&mut self) {
        let cur_abs = self.absolute_inches_from_programmed(None);
        self.state.g92_active = false;
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs);
    }

    fn do_g92_3(&mut self) {
        let cur_abs = self.absolute_inches_from_programmed(None);
        let units = self.state.units.clone();
        let mut new_g92 = Position::default();
        for (i, &axis) in AXIS_LETTERS.iter().enumerate() {
            let p_idx = G92_OFFSET_PARAMS[i];
            let raw = *self.state.parameters.get(&p_idx).unwrap_or(&0.0);
            let v = if is_linear(axis) { to_inches_units(raw, &units) } else { raw };
            new_g92.set(axis, v);
        }
        self.state.g92_offsets_inches = new_g92;
        self.state.g92_active = true;
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs);
    }

    // -- motion --------------------------------------------------------------

    fn do_motion(
        &mut self, word_dict: &BTreeMap<char, f64>, g53: bool, force_g0: bool,
    ) -> NgcResult<()> {
        let mode = if force_g0 { "G0".to_string() } else { self.state.motion_mode.clone() };
        if matches!(mode.as_str(), "G2" | "G3") && !g53 {
            self.do_arc(word_dict, &mode)?;
            self.state.last_motion_was_cycle = false;
            return Ok(());
        }
        if mode == "G38.2" {
            self.do_probe(word_dict)?;
            self.state.last_motion_was_cycle = false;
            return Ok(());
        }
        if is_canned_cycle(&mode) {
            self.do_canned_cycle(word_dict, &[])?;
            return Ok(());
        }

        if !matches!(mode.as_str(), "G0" | "G1") {
            return Err(ngc(format!("motion mode {mode} not implemented for plain motion")));
        }
        if !AXIS_LETTERS.iter().any(|a| word_dict.contains_key(a)) {
            return Err(ngc(format!("{mode} requires at least one axis word")));
        }

        let trace_start = if self.trace.is_some() { Some(self.state.programmed) } else { None };

        if g53 {
            let mut target = self.absolute_inches_from_programmed(None);
            for &axis in AXIS_LETTERS.iter() {
                if let Some(&v) = word_dict.get(&axis) {
                    target.set(axis, self.axis_word_inches(axis, v));
                }
            }
            self.state.programmed = self.programmed_from_absolute_inches(target);
        } else {
            let mut new_prog = self.state.programmed;
            for &axis in AXIS_LETTERS.iter() {
                if let Some(&v) = word_dict.get(&axis) {
                    let v_in = self.axis_word_inches(axis, v);
                    if self.state.distance_mode == "G91" {
                        new_prog.set(axis, new_prog.get(axis) + v_in);
                    } else {
                        new_prog.set(axis, v_in);
                    }
                }
            }
            if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") && self.state.plane == "G17" {
                let cur_x = self.state.programmed.x;
                let cur_y = self.state.programmed.y;
                if self.state.crc_first_move {
                    let (px, py) = (new_prog.x, new_prog.y);
                    let (sx, sy) = self.crc_first_straight(cur_x, cur_y, px, py)?;
                    self.state.crc_contour_x = px;
                    self.state.crc_contour_y = py;
                    self.state.crc_first_move = false;
                    new_prog.x = sx; new_prog.y = sy;
                } else {
                    let prev_px = self.state.crc_contour_x;
                    let prev_py = self.state.crc_contour_y;
                    let (px, py) = (new_prog.x, new_prog.y);
                    let (sx, sy) = self.crc_followon_straight(prev_px, prev_py, px, py)?;
                    self.state.crc_contour_x = px;
                    self.state.crc_contour_y = py;
                    new_prog.x = sx; new_prog.y = sy;
                }
            }
            self.state.programmed = new_prog;
        }

        if self.state.feed_mode == "G93" && mode == "G1"
            && (self.state.feed_rate <= 0.0 || !self.f_on_this_line)
        {
            return Err(ngc("G1 in inverse time feed mode requires a positive F word"));
        }

        if let Some(start) = trace_start {
            let end = self.state.programmed;
            let path_len = linear_path_length_inches(&start, &end);
            let rotary_only = LINEAR_AXES.iter().all(|&a| (end.get(a) - start.get(a)).abs() == 0.0);
            let dur = if mode == "G0" || force_g0 {
                rapid_duration(path_len)
            } else {
                feed_duration(path_len, self.state.feed_rate,
                              &self.state.feed_mode, &self.state.units, rotary_only)
            };
            let payload = self.build_payload();
            let payload_val = Value::Object(payload);
            let conv = self.make_pos_converter();
            if let Some(tr) = self.trace.as_mut() {
                tr.emit_sub_motion(
                    &start, &end, dur, path_len, false, None,
                    &payload_val, &*conv, None,
                );
            }
        }

        self.state.last_motion_was_cycle = false;
        Ok(())
    }

    // -- arc ------------------------------------------------------------------

    fn do_arc(&mut self, word_dict: &BTreeMap<char, f64>, mode: &str) -> NgcResult<()> {
        let plane = self.state.plane.clone();
        let units = self.state.units.clone();

        let (ax1, ax2, ax_perp, offset_letters): (char, char, char, (char, char)) = match plane.as_str() {
            "G17" => ('x', 'y', 'z', ('i', 'j')),
            "G18" => ('x', 'z', 'y', ('i', 'k')),
            _ => ('y', 'z', 'x', ('j', 'k')),
        };

        let trace_start = if self.trace.is_some() { Some(self.state.programmed) } else { None };
        let mut trace_crc_center: Option<(f64, f64)> = None;

        let mut new_prog = self.state.programmed;
        for &axis in AXIS_LETTERS.iter() {
            if let Some(&v) = word_dict.get(&axis) {
                let v_in = self.axis_word_inches(axis, v);
                if self.state.distance_mode == "G91" {
                    new_prog.set(axis, new_prog.get(axis) + v_in);
                } else {
                    new_prog.set(axis, v_in);
                }
            }
        }

        let crc_active = matches!(self.state.cutter_comp.as_str(), "G41" | "G42") && plane == "G17";
        let mut i_val = 0.0;
        let mut j_val = 0.0;

        if word_dict.contains_key(&'r') {
            if !word_dict.contains_key(&ax1) && !word_dict.contains_key(&ax2) {
                return Err(ngc("arc requires at least one in-plane axis word"));
            }
            if !crc_active
                && new_prog.get(ax1) == self.state.programmed.get(ax1)
                && new_prog.get(ax2) == self.state.programmed.get(ax2)
            {
                return Err(ngc("radius-format arc end point equals current point"));
            }
        } else {
            if !word_dict.contains_key(&offset_letters.0) && !word_dict.contains_key(&offset_letters.1) {
                return Err(ngc("center-format arc requires offset words"));
            }
            i_val = to_inches_units(*word_dict.get(&offset_letters.0).unwrap_or(&0.0), &units);
            j_val = to_inches_units(*word_dict.get(&offset_letters.1).unwrap_or(&0.0), &units);
            if !crc_active {
                let tol = 0.0002;
                let cur1 = self.state.programmed.get(ax1);
                let cur2 = self.state.programmed.get(ax2);
                let cx = cur1 + i_val;
                let cy = cur2 + j_val;
                let r1 = (i_val * i_val + j_val * j_val).sqrt();
                let r2 = ((new_prog.get(ax1) - cx).powi(2) + (new_prog.get(ax2) - cy).powi(2)).sqrt();
                if (r1 - r2).abs() > tol {
                    return Err(ngc("center-format arc radii inconsistent"));
                }
            }
        }

        if self.state.feed_mode == "G93"
            && (self.state.feed_rate <= 0.0 || !self.f_on_this_line)
        {
            return Err(ngc("arc in inverse time feed mode requires a positive F word"));
        }

        if crc_active {
            // Clarifications.md (v3.1.1): R is the tool-tip path radius,
            // I/J start at the current tool tip, and X/Y name the auxiliary
            // contour endpoint. Entry and continuation use the same geometry.
            let (ex, ey) = (new_prog.x, new_prog.y);
            let (sx0, sy0) = (self.state.programmed.x, self.state.programmed.y);
            let inside = (mode == "G3" && self.state.cutter_comp == "G41")
                || (mode == "G2" && self.state.cutter_comp == "G42");
            let tool_r = self.state.crc_radius_inches;
            let (cx, cy, arc_r) = if let Some(&radius_word) = word_dict.get(&'r') {
                let path_r = to_inches_units(radius_word, &units).abs();
                let aux_r = if inside { path_r + tool_r } else { path_r - tool_r };
                if aux_r <= 1e-9 {
                    return Err(ngc("tool radius not less than arc radius with cutter radius compensation"));
                }
                let chord = (ex - sx0).hypot(ey - sy0);
                if chord > aux_r + path_r + 1e-9 {
                    return Err(ngc("cutter compensation arc cannot be constructed"));
                }
                if chord <= (aux_r - path_r).abs() + 1e-9 {
                    return Err(ngc("degenerate cutter compensation arc"));
                }
                // A negative R selects the other (greater-than-semicircle)
                // center for the same G2/G3 traversal, per section 3.5.3.1.
                let center_mode = if radius_word < 0.0 {
                    if mode == "G3" { "G2" } else { "G3" }
                } else { mode };
                let (cx, cy) = two_circle_intersection_pick(
                    ex, ey, aux_r, sx0, sy0, path_r, center_mode,
                );
                (cx, cy, aux_r)
            } else {
                let cx = sx0 + i_val;
                let cy = sy0 + j_val;
                let arc_r = ((ex - cx).powi(2) + (ey - cy).powi(2)).sqrt();
                (cx, cy, arc_r)
            };

            if inside && tool_r >= arc_r - 1e-9 {
                return Err(ngc("tool radius not less than arc radius with cutter radius compensation"));
            }
            let tool_arc_r = if inside { arc_r - tool_r } else { arc_r + tool_r };
            let dxv = ex - cx; let dyv = ey - cy;
            let d = (dxv * dxv + dyv * dyv).sqrt();
            let (sx, sy) = if d > 0.0 {
                (cx + dxv * tool_arc_r / d, cy + dyv * tool_arc_r / d)
            } else { (ex, ey) };
            self.state.crc_contour_x = ex;
            self.state.crc_contour_y = ey;
            self.state.crc_first_move = false;
            new_prog.x = sx; new_prog.y = sy;
            trace_crc_center = Some((cx, cy));
        }

        self.state.programmed = new_prog;

        if let Some(start) = trace_start {
            let s1 = start.get(ax1); let s2 = start.get(ax2);
            let e1 = self.state.programmed.get(ax1); let e2 = self.state.programmed.get(ax2);
            let (c1, c2) = if let Some(c) = trace_crc_center {
                c
            } else if word_dict.contains_key(&'r') {
                let r_in = to_inches_units(word_dict[&'r'], &units);
                arc_center_from_radius(s1, s2, e1, e2, r_in, mode)
            } else {
                (s1 + i_val, s2 + j_val)
            };
            let (sweep, in_plane) = arc_sweep_and_length(s1, s2, e1, e2, c1, c2, mode);
            let axial_dist = (self.state.programmed.get(ax_perp) - start.get(ax_perp)).abs();
            let path_len = (in_plane * in_plane + axial_dist * axial_dist).sqrt();
            let dur = feed_duration(path_len, self.state.feed_rate,
                                    &self.state.feed_mode, &units, false);
            let radius = ((s1 - c1).powi(2) + (s2 - c2).powi(2)).sqrt();
            let payload = self.build_payload();
            let payload_val = Value::Object(payload);
            let conv = self.make_pos_converter();
            let end = self.state.programmed;
            let ap = ArcParams {
                start_ax1: s1, start_ax2: s2,
                center_ax1: c1, center_ax2: c2,
                sweep, radius,
                axial_start: start.get(ax_perp),
                axial_end: self.state.programmed.get(ax_perp),
                ax1_name: ax1, ax2_name: ax2, perp_name: ax_perp,
            };
            if let Some(tr) = self.trace.as_mut() {
                tr.emit_sub_motion(
                    &start, &end, dur, path_len, false, None,
                    &payload_val, &*conv, Some(&ap),
                );
            }
        }
        Ok(())
    }

    // -- CRC helpers ---------------------------------------------------------

    fn crc_first_straight(
        &self, cx: f64, cy: f64, px: f64, py: f64,
    ) -> NgcResult<(f64, f64)> {
        let r = self.state.crc_radius_inches;
        let dx = px - cx; let dy = py - cy;
        let d2 = dx * dx + dy * dy;
        if r == 0.0 { return Ok((px, py)); }
        if d2 < r * r - 1e-12 {
            return Err(ngc("cutter gouging with cutter radius compensation"));
        }
        let l = (d2 - r * r).max(0.0).sqrt();
        let d = d2.sqrt();
        let ux = dx / d; let uy = dy / d;
        let ca = l / d; let sa = r / d;
        let (sx, sy) = if self.state.cutter_comp == "G41" {
            (cx + l * (ca * ux - sa * uy), cy + l * (ca * uy + sa * ux))
        } else {
            (cx + l * (ca * ux + sa * uy), cy + l * (ca * uy - sa * ux))
        };
        Ok((sx, sy))
    }

    fn crc_followon_straight(
        &self, prev_px: f64, prev_py: f64, px: f64, py: f64,
    ) -> NgcResult<(f64, f64)> {
        let r = self.state.crc_radius_inches;
        let dx = px - prev_px; let dy = py - prev_py;
        let seg_len = (dx * dx + dy * dy).sqrt();
        if seg_len == 0.0 {
            return Ok((self.state.programmed.x, self.state.programmed.y));
        }
        let ux = dx / seg_len; let uy = dy / seg_len;
        let nlx = -uy; let nly = ux;
        let (nx, ny) = if self.state.cutter_comp == "G41" { (nlx, nly) } else { (-nlx, -nly) };

        let sp_x = self.state.programmed.x;
        let sp_y = self.state.programmed.y;
        let prev_nx = sp_x - prev_px;
        let prev_ny = sp_y - prev_py;
        let (in_dx_raw, in_dy_raw) = if self.state.cutter_comp == "G41" {
            (prev_ny, -prev_nx)
        } else {
            (-prev_ny, prev_nx)
        };
        let in_len = (in_dx_raw * in_dx_raw + in_dy_raw * in_dy_raw).sqrt();
        if in_len > 1e-9 {
            let in_dx = in_dx_raw / in_len;
            let in_dy = in_dy_raw / in_len;
            let cross = in_dx * uy - in_dy * ux;
            if self.state.cutter_comp == "G41" && cross > 1e-9 {
                return Err(ngc("concave corner with cutter radius compensation"));
            }
            if self.state.cutter_comp == "G42" && cross < -1e-9 {
                return Err(ngc("concave corner with cutter radius compensation"));
            }
        }
        Ok((px + r * nx, py + r * ny))
    }

    // -- probe ---------------------------------------------------------------

    fn do_probe(&mut self, word_dict: &BTreeMap<char, f64>) -> NgcResult<()> {
        let trace_start = if self.trace.is_some() { Some(self.state.programmed) } else { None };

        if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
            return Err(ngc("cannot probe while cutter radius compensation is on"));
        }
        if self.state.feed_mode == "G93" {
            return Err(ngc("G38.2 not allowed in inverse time feed mode"));
        }
        if !LINEAR_AXES.iter().any(|a| word_dict.contains_key(a)) {
            return Err(ngc("G38.2 requires at least one linear axis word"));
        }
        for &axis in ROTARY_AXES.iter() {
            if let Some(&v) = word_dict.get(&axis) {
                if v != self.state.programmed.get(axis) {
                    return Err(ngc("G38.2 must not command rotary motion"));
                }
            }
        }
        if self.state.tool_in_spindle.is_none()
            || (self.probe_tool.is_some()
                && self.state.tool_in_spindle != self.probe_tool)
        {
            return Err(ngc("G38.2 requires the probe tool to be in the spindle"));
        }
        if self.state.spindle_direction != "OFF" {
            return Err(ngc("G38.2 requires the spindle to be stopped"));
        }

        let mut new_prog = self.state.programmed;
        for &axis in AXIS_LETTERS.iter() {
            if let Some(&v) = word_dict.get(&axis) {
                let v_in = self.axis_word_inches(axis, v);
                if self.state.distance_mode == "G91" {
                    new_prog.set(axis, new_prog.get(axis) + v_in);
                } else {
                    new_prog.set(axis, v_in);
                }
            }
        }
        let dx = new_prog.x - self.state.programmed.x;
        let dy = new_prog.y - self.state.programmed.y;
        let dz = new_prog.z - self.state.programmed.z;
        let dist = (dx * dx + dy * dy + dz * dz).sqrt();
        if dist < 0.01 {
            return Err(ngc("G38.2 distance is too small"));
        }

        let start_abs = self.absolute_inches_from_programmed(None);
        let tlo = self.state.tool_length_offset_value_inches;
        let start_cp = Position { z: start_abs.z - tlo, ..start_abs };
        let end_abs = self.absolute_inches_from_programmed(Some(new_prog));
        let end_cp = Position { z: end_abs.z - tlo, ..end_abs };

        let pbox = self.probe_box_inches.ok_or_else(|| ngc("G38.2 used without --probe-box configured"))?;
        let (xmin, xmax, ymin, ymax, zmin, zmax) = pbox;

        let in_box = |p: &Position| -> bool {
            (xmin..=xmax).contains(&p.x)
            && (ymin..=ymax).contains(&p.y)
            && (zmin..=zmax).contains(&p.z)
        };

        if in_box(&start_cp) {
            return Err(ngc("G38.2 probe is already tripped"));
        }

        let axis_t = |c0: f64, c1: f64, lo: f64, hi: f64| -> Option<(f64, f64)> {
            if c0 == c1 {
                if lo <= c0 && c0 <= hi { Some((0.0, 1.0)) } else { None }
            } else {
                let t1 = (lo - c0) / (c1 - c0);
                let t2 = (hi - c0) / (c1 - c0);
                Some((t1.min(t2), t1.max(t2)))
            }
        };

        let mut t_min: f64 = 0.0;
        let mut t_max: f64 = 1.0;
        let mut hit_none = false;
        for (c0, c1, lo, hi) in [
            (start_cp.x, end_cp.x, xmin, xmax),
            (start_cp.y, end_cp.y, ymin, ymax),
            (start_cp.z, end_cp.z, zmin, zmax),
        ] {
            match axis_t(c0, c1, lo, hi) {
                Some((a, b)) => { t_min = t_min.max(a); t_max = t_max.min(b); }
                None => { hit_none = true; break; }
            }
        }

        let probe_tripped;
        let trip = if !hit_none && t_min <= t_max && (0.0..=1.0).contains(&t_min) {
            probe_tripped = true;
            let t = t_min;
            Position {
                x: start_cp.x + (end_cp.x - start_cp.x) * t,
                y: start_cp.y + (end_cp.y - start_cp.y) * t,
                z: start_cp.z + (end_cp.z - start_cp.z) * t,
                a: start_cp.a + (end_cp.a - start_cp.a) * t,
                b: start_cp.b + (end_cp.b - start_cp.b) * t,
                c: start_cp.c + (end_cp.c - start_cp.c) * t,
            }
        } else {
            probe_tripped = false;
            end_cp
        };

        let trip_abs = Position { z: trip.z + tlo, ..trip };
        self.state.programmed = self.programmed_from_absolute_inches(trip_abs);
        let units = self.state.units.clone();
        self.state.parameters.insert(5061, from_inches_units(trip.x, &units));
        self.state.parameters.insert(5062, from_inches_units(trip.y, &units));
        self.state.parameters.insert(5063, from_inches_units(trip.z, &units));
        self.state.parameters.insert(5064, trip.a);
        self.state.parameters.insert(5065, trip.b);
        self.state.parameters.insert(5066, trip.c);

        if let Some(start) = trace_start {
            let end = self.state.programmed;
            let path_len = linear_path_length_inches(&start, &end);
            let dur = feed_duration(path_len, self.state.feed_rate,
                                    &self.state.feed_mode, &self.state.units, false);
            let payload = self.build_payload();
            let payload_val = Value::Object(payload);
            let conv = self.make_pos_converter();
            if let Some(tr) = self.trace.as_mut() {
                tr.emit_sub_motion(&start, &end, dur, path_len, false, None,
                    &payload_val, &*conv, None);
            }
        }

        if !probe_tripped {
            return Err(ngc("G38.2 probe did not trip"));
        }
        Ok(())
    }

    // -- canned cycles --------------------------------------------------------

    fn cycle_sub_motion(&mut self, end: Position, kind: &str) {
        let start = self.state.programmed;
        self.state.programmed = end;
        if self.trace.is_some() {
            let path_len = linear_path_length_inches(&start, &self.state.programmed);
            if path_len > 0.0 {
                let dur = if kind == "rapid" {
                    rapid_duration(path_len)
                } else {
                    feed_duration(path_len, self.state.feed_rate,
                                  &self.state.feed_mode, &self.state.units, false)
                };
                let payload = self.build_payload();
                let payload_val = Value::Object(payload);
                let conv = self.make_pos_converter();
                let pgrm = self.state.programmed;
                if let Some(tr) = self.trace.as_mut() {
                    tr.emit_sub_motion(&start, &pgrm, dur, path_len, true, Some(kind),
                        &payload_val, &*conv, None);
                }
            }
        }
    }

    fn do_canned_cycle(
        &mut self, word_dict: &BTreeMap<char, f64>, _group0_axis_using: &[String],
    ) -> NgcResult<()> {
        let plane = self.state.plane.clone();
        let (depth_axis, plane_axes): (char, (char, char)) = match plane.as_str() {
            "G17" => ('z', ('x', 'y')),
            "G18" => ('y', ('x', 'z')),
            _ => ('x', ('y', 'z')),
        };

        if matches!(self.state.cutter_comp.as_str(), "G41" | "G42") {
            return Err(ngc("cutter radius compensation must not be on during a canned cycle"));
        }
        if self.state.feed_mode == "G93" {
            return Err(ngc("inverse time feed mode is not allowed during a canned cycle"));
        }
        for &axis in ROTARY_AXES.iter() {
            if let Some(&v) = word_dict.get(&axis) {
                if v != self.state.programmed.get(axis) {
                    return Err(ngc("rotational axis motion is not allowed during a canned cycle"));
                }
            }
        }
        if !['x', 'y', 'z'].iter().any(|a| word_dict.contains_key(a)) {
            return Err(ngc("canned cycle requires at least one of X, Y, Z"));
        }

        let l_count = if let Some(&l) = word_dict.get(&'l') {
            if !is_close_int(l) || l.round() as i64 <= 0 {
                return Err(ngc("canned cycle L must be a positive integer"));
            }
            l.round() as i64
        } else { 1 };

        if !self.state.last_motion_was_cycle {
            self.state.cycle_old_z = self.state.programmed.get(depth_axis);
        }

        if let Some(&r_v) = word_dict.get(&'r') {
            let r_v_final = if self.state.distance_mode == "G91" {
                self.state.programmed.get(depth_axis) + r_v
            } else { r_v };
            self.state.cycle_r = Some(r_v_final);
        }
        if self.state.cycle_r.is_none() {
            return Err(ngc("canned cycle requires R"));
        }

        if let Some(&z_v) = word_dict.get(&depth_axis) {
            let z_final = if self.state.distance_mode == "G91" {
                self.state.programmed.get(depth_axis) + z_v
            } else { z_v };
            self.state.cycle_z = Some(z_final);
        }
        if self.state.cycle_z.is_none() {
            return Err(ngc("canned cycle requires depth axis word"));
        }

        if self.state.cycle_r.unwrap() < self.state.cycle_z.unwrap() {
            return Err(ngc("canned cycle R must not be below Z"));
        }

        let motion = self.state.motion_mode.clone();
        if motion == "G84" {
            if self.state.spindle_direction != "CW" {
                return Err(ngc("G84 requires spindle CW before cycle"));
            }
        } else if matches!(motion.as_str(), "G86" | "G88") {
            if self.state.spindle_direction == "OFF" {
                return Err(ngc(format!("{motion} requires spindle on before cycle")));
            }
        }
        if motion == "G83" {
            let q = word_dict.get(&'q').copied().unwrap_or(0.0);
            if !word_dict.contains_key(&'q') || q <= 0.0 {
                return Err(ngc("G83 requires a positive Q word"));
            }
        }
        if matches!(motion.as_str(), "G86" | "G88" | "G89") && !word_dict.contains_key(&'p') {
            return Err(ngc(format!("{motion} requires a P word")));
        }
        if matches!(motion.as_str(), "G82" | "G86" | "G88" | "G89")
            && word_dict.contains_key(&'p')
        {
            if word_dict[&'p'] < 0.0 {
                return Err(ngc("canned cycle P must be non-negative"));
            }
        }

        let r_val = self.state.cycle_r.unwrap();
        let z_val = self.state.cycle_z.unwrap();
        let clear = if self.state.return_mode == "G99" {
            r_val
        } else {
            self.state.cycle_old_z.max(r_val)
        };

        for _ in 0..l_count {
            let mut target = self.state.programmed;
            for &axis in &[plane_axes.0, plane_axes.1] {
                if let Some(&v) = word_dict.get(&axis) {
                    if self.state.distance_mode == "G91" {
                        target.set(axis, target.get(axis) + v);
                    } else {
                        target.set(axis, v);
                    }
                }
            }

            let mut sm1_end = self.state.programmed;
            sm1_end.set(plane_axes.0, target.get(plane_axes.0));
            sm1_end.set(plane_axes.1, target.get(plane_axes.1));
            self.cycle_sub_motion(sm1_end, "rapid");

            let mut sm2_end = self.state.programmed;
            sm2_end.set(depth_axis, r_val);
            self.cycle_sub_motion(sm2_end, "rapid");

            match motion.as_str() {
                "G81" | "G82" => {
                    let mut e = self.state.programmed;
                    e.set(depth_axis, z_val);
                    self.cycle_sub_motion(e, "feed");
                    let mut e = self.state.programmed;
                    e.set(depth_axis, clear);
                    self.cycle_sub_motion(e, "rapid");
                }
                "G83" => {
                    let q_peck = word_dict[&'q'];
                    let mut current_depth = r_val;
                    while current_depth > z_val + 1e-12 {
                        let next_depth = (current_depth - q_peck).max(z_val);
                        let mut e = self.state.programmed;
                        e.set(depth_axis, next_depth);
                        self.cycle_sub_motion(e, "feed");
                        current_depth = next_depth;
                        if current_depth > z_val + 1e-12 {
                            let mut e = self.state.programmed;
                            e.set(depth_axis, r_val);
                            self.cycle_sub_motion(e, "rapid");
                            let mut e = self.state.programmed;
                            e.set(depth_axis, current_depth);
                            self.cycle_sub_motion(e, "rapid");
                        }
                    }
                    let mut e = self.state.programmed;
                    e.set(depth_axis, clear);
                    self.cycle_sub_motion(e, "rapid");
                }
                "G84" => {
                    let mut e = self.state.programmed;
                    e.set(depth_axis, z_val);
                    self.cycle_sub_motion(e, "feed");
                    self.state.spindle_direction = "CCW".into();
                    self.state.active_m_codes.insert("7".into(), "M4".into());
                    let mut e = self.state.programmed;
                    e.set(depth_axis, r_val);
                    self.cycle_sub_motion(e, "feed");
                    if (clear - r_val).abs() > 1e-12 {
                        let mut e = self.state.programmed;
                        e.set(depth_axis, clear);
                        self.cycle_sub_motion(e, "rapid");
                    }
                }
                "G85" => {
                    let mut e = self.state.programmed;
                    e.set(depth_axis, z_val);
                    self.cycle_sub_motion(e, "feed");
                    let mut e = self.state.programmed;
                    e.set(depth_axis, clear);
                    self.cycle_sub_motion(e, "feed");
                }
                "G86" | "G88" => {
                    let mut e = self.state.programmed;
                    e.set(depth_axis, z_val);
                    self.cycle_sub_motion(e, "feed");
                    let mut e = self.state.programmed;
                    e.set(depth_axis, clear);
                    self.cycle_sub_motion(e, "rapid");
                }
                "G87" => {
                    // RS274 3.5.16.8: I/J clearance, feed up to K,
                    // feed back down to Z, and retract through clearance.
                    // Clarifications.md supplies zero for omitted I/J/K.
                    let mut hole = self.state.programmed;
                    let mut offset = hole;
                    for (axis, word) in [(plane_axes.0, 'i'), (plane_axes.1, 'j')] {
                        offset.set(axis, hole.get(axis) + to_inches_units(
                            word_dict.get(&word).copied().unwrap_or(0.0), &self.state.units,
                        ));
                    }
                    let mut top = to_inches_units(
                        word_dict.get(&'k').copied().unwrap_or(0.0), &self.state.units,
                    );
                    if self.state.distance_mode == "G91" {
                        top += z_val;
                    }
                    let spindle_before = self.state.spindle_direction.clone();
                    let spindle_code_before = self.state.active_m_codes
                        .get("7").cloned().unwrap_or_else(|| "M5".into());
                    self.cycle_sub_motion(offset, "rapid");
                    self.state.spindle_direction = "OFF".into();
                    self.state.active_m_codes.insert("7".into(), "M5".into());
                    offset.set(depth_axis, z_val);
                    self.cycle_sub_motion(offset, "rapid");
                    hole.set(depth_axis, z_val);
                    self.cycle_sub_motion(hole, "rapid");
                    self.state.spindle_direction = spindle_before.clone();
                    self.state.active_m_codes.insert("7".into(), spindle_code_before.clone());
                    hole.set(depth_axis, top);
                    self.cycle_sub_motion(hole, "feed");
                    hole.set(depth_axis, z_val);
                    self.cycle_sub_motion(hole, "feed");
                    self.state.spindle_direction = "OFF".into();
                    self.state.active_m_codes.insert("7".into(), "M5".into());
                    self.cycle_sub_motion(offset, "rapid");
                    offset.set(depth_axis, clear);
                    self.cycle_sub_motion(offset, "rapid");
                    hole.set(depth_axis, clear);
                    self.cycle_sub_motion(hole, "rapid");
                    self.state.spindle_direction = spindle_before;
                    self.state.active_m_codes.insert("7".into(), spindle_code_before);
                }
                "G89" => {
                    let mut e = self.state.programmed;
                    e.set(depth_axis, z_val);
                    self.cycle_sub_motion(e, "feed");
                    let mut e = self.state.programmed;
                    e.set(depth_axis, clear);
                    self.cycle_sub_motion(e, "feed");
                }
                _ => {}
            }
        }

        if motion == "G84" {
            self.state.spindle_direction = "CW".into();
            self.state.active_m_codes.insert("7".into(), "M3".into());
        }

        self.state.last_motion_was_cycle = true;
        Ok(())
    }

    // -- program end ---------------------------------------------------------

    fn do_program_end(&mut self) {
        let cur_abs = self.absolute_inches_from_programmed(None);
        self.state.g92_offsets_inches = Position::default();
        self.state.g92_active = false;
        self.state.selected_cs = 1;
        self.state.parameters.insert(SELECTED_CS_PARAM, 1.0);
        self.state.plane = "G17".into();
        self.state.distance_mode = "G90".into();
        self.state.feed_mode = "G94".into();
        self.state.overrides_enabled = true;
        self.state.cutter_comp = "G40".into();
        self.state.cutter_radius_compensation_number = None;
        self.state.spindle_direction = "OFF".into();
        self.state.motion_mode = "G1".into();
        self.state.coolant = "M9".into();
        self.state.active_m_codes.insert("7".into(), "M5".into());
        self.state.active_m_codes.insert("8".into(), "M9".into());
        self.state.active_m_codes.insert("9".into(), "M48".into());
        self.state.programmed = self.programmed_from_absolute_inches(cur_abs);
        self.program_ended = true;
    }

    fn maybe_sync_param_into_state(&mut self, idx: u32, val: f64) {
        if idx == SELECTED_CS_PARAM {
            if is_close_int(val) && (1.0..=9.0).contains(&val) {
                self.state.selected_cs = val.round() as u32;
            }
        }
    }

    // -- build payload -------------------------------------------------------

    fn build_payload(&mut self) -> Map<String, Value> {
        let units = self.state.units.clone();
        // Ensure required parameters populated.
        for s in 1..=9u32 {
            if self.state.cs_offsets_inches.contains_key(&s) {
                let idxs = cs_xyzabc_param_indices(s);
                for idx in idxs {
                    self.state.parameters.entry(idx).or_insert(0.0);
                }
            }
        }
        for p in G92_OFFSET_PARAMS {
            self.state.parameters.entry(p).or_insert(0.0);
        }
        self.state.parameters.insert(SELECTED_CS_PARAM, self.state.selected_cs as f64);
        for p in required_output_parameters() {
            self.state.parameters.entry(p).or_insert(0.0);
        }

        let mut active_g = Map::new();
        active_g.insert("1".into(), Value::from(self.state.motion_mode.clone()));
        active_g.insert("2".into(), Value::from(self.state.plane.clone()));
        active_g.insert("3".into(), Value::from(self.state.distance_mode.clone()));
        active_g.insert("5".into(), Value::from(self.state.feed_mode.clone()));
        active_g.insert("6".into(), Value::from(self.state.units.clone()));
        active_g.insert("7".into(), Value::from(self.state.cutter_comp.clone()));
        active_g.insert("8".into(), Value::from(self.state.tool_length_offset_mode.clone()));
        active_g.insert("10".into(), Value::from(self.state.return_mode.clone()));
        active_g.insert("12".into(), Value::from(cs_number_to_gcode(self.state.selected_cs).to_string()));
        active_g.insert("13".into(), Value::from(self.state.path_mode.clone()));

        let cp = self.controlled_point_in_active_units(None);

        let mut cs_dict = Map::new();
        for s in 1..=9u32 {
            let cs = self.state.cs_offsets_inches.get(&s).copied().unwrap_or_default();
            let mut entry = Map::new();
            entry.insert("x".into(), json_num(from_inches_units(cs.x, &units)));
            entry.insert("y".into(), json_num(from_inches_units(cs.y, &units)));
            entry.insert("z".into(), json_num(from_inches_units(cs.z, &units)));
            entry.insert("a".into(), json_num(cs.a));
            entry.insert("b".into(), json_num(cs.b));
            entry.insert("c".into(), json_num(cs.c));
            cs_dict.insert(s.to_string(), Value::Object(entry));
        }

        let mut param_dict = Map::new();
        for (k, v) in &self.state.parameters {
            param_dict.insert(k.to_string(), json_num(*v));
        }

        let mut mcodes_dict = Map::new();
        for (k, v) in &self.state.active_m_codes {
            mcodes_dict.insert(k.clone(), Value::from(v.clone()));
        }

        let mut out = Map::new();
        out.insert("machine_position".into(), Value::Object(cp.to_map()));
        out.insert("feed_rate".into(), json_num(self.state.feed_rate));
        out.insert("spindle_speed".into(), json_num(self.state.spindle_speed));
        out.insert("spindle_direction".into(), Value::from(self.state.spindle_direction.clone()));
        out.insert("cutter_radius_compensation_number".into(),
            self.state.cutter_radius_compensation_number.map(Value::from).unwrap_or(Value::Null));
        out.insert("tool_length_offset_index".into(),
            self.state.tool_length_offset_index.map(Value::from).unwrap_or(Value::Null));
        out.insert("selected_tool".into(),
            self.state.selected_tool.map(Value::from).unwrap_or(Value::Null));
        out.insert("tool_in_spindle".into(),
            self.state.tool_in_spindle.map(Value::from).unwrap_or(Value::Null));
        out.insert("active_modal_g_codes".into(), Value::Object(active_g));
        out.insert("active_modal_m_codes".into(), Value::Object(mcodes_dict));
        out.insert("coordinate_system_offsets".into(), Value::Object(cs_dict));
        out.insert("parameters".into(), Value::Object(param_dict));
        out.insert("error".into(), Value::Null);
        out
    }

    fn write_parameter_file(&mut self, path: &str) -> NgcResult<()> {
        for p in required_output_parameters() {
            self.state.parameters.entry(p).or_insert(0.0);
        }
        let mut sorted: Vec<(u32, f64)> = self.state.parameters.iter()
            .map(|(k, v)| (*k, *v)).collect();
        sorted.sort_by_key(|(k, _)| *k);
        let mut lines: Vec<String> = vec!["RS274 parameter file".into(), "".into()];
        for (idx, val) in sorted {
            if val == val.trunc() && val.is_finite() {
                lines.push(format!("{idx} {val:.6}"));
            } else {
                // Use general-like formatting to ~10 significant digits
                lines.push(format!("{idx} {}", format_g_like_10(val)));
            }
        }
        let body = lines.join("\n") + "\n";
        fs::write(path, body).map_err(|e| ngc(format!("parameter output: {e}")))?;
        Ok(())
    }

    // -- helper for trace position conversion -------------------------------

    fn make_pos_converter(&mut self) -> Box<dyn Fn(&Position) -> Map<String, Value>> {
        let units = self.state.units.clone();
        let tlo = self.state.tool_length_offset_value_inches;
        let cs = self.get_cs_offset(self.state.selected_cs);
        let g92 = if self.state.g92_active { self.state.g92_offsets_inches } else { Position::default() };
        Box::new(move |prog: &Position| {
            let mut abs = Position::default();
            for a in AXIS_LETTERS {
                abs.set(a, prog.get(a) + cs.get(a) + g92.get(a));
            }
            abs.z -= tlo;
            let mut out = Map::new();
            for a in AXIS_LETTERS {
                let v = abs.get(a);
                let v2 = if is_linear(a) { from_inches_units(v, &units) } else { v };
                out.insert(a.to_string(), json_num(v2));
            }
            out
        })
    }
}

fn format_g_like_10(v: f64) -> String {
    // Emulate Python's f"{val:.10g}" reasonably.
    // Rust's default f64 Display uses the shortest round-trip representation.
    let s = format!("{v:.10e}");
    // Convert e-form to g-form.
    // Simpler: use {:.10} which gives 10 decimal places then trim.
    let fixed = format!("{:.10}", v);
    // Trim trailing zeros after the decimal point.
    if fixed.contains('.') {
        let trimmed = fixed.trim_end_matches('0').trim_end_matches('.').to_string();
        if trimmed.is_empty() { "0".into() } else { trimmed }
    } else {
        let _ = s;
        fixed
    }
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

struct CliArgs {
    input: String,
    output: String,
    tool_table: Option<String>,
    block_delete: bool,
    carousel_slots: Option<i64>,
    parameter_input: Option<String>,
    parameter_output: Option<String>,
    probe_box: Option<(f64, f64, f64, f64, f64, f64)>,
    probe_tool: Option<i64>,
    trace_output: Option<String>,
    trace_time_step: Option<f64>,
    trace_distance_step: Option<f64>,
    trace_position_tolerance: Option<f64>,
}

fn parse_cli_args(argv: &[String]) -> NgcResult<CliArgs> {
    let mut a = CliArgs {
        input: String::new(),
        output: String::new(),
        tool_table: None,
        block_delete: false,
        carousel_slots: None,
        parameter_input: None,
        parameter_output: None,
        probe_box: None,
        probe_tool: None,
        trace_output: None,
        trace_time_step: None,
        trace_distance_step: None,
        trace_position_tolerance: None,
    };
    let mut i = 0;
    while i < argv.len() {
        let k = &argv[i];
        let val = |i: &mut usize| -> NgcResult<String> {
            *i += 1;
            if *i >= argv.len() {
                return Err(ngc(format!("missing value for {}", argv[*i - 1])));
            }
            Ok(argv[*i].clone())
        };
        match k.as_str() {
            "--input" => { a.input = val(&mut i)?; }
            "--output" => { a.output = val(&mut i)?; }
            "--tool-table" => { a.tool_table = Some(val(&mut i)?); }
            "--block-delete" => { a.block_delete = true; }
            "--carousel-slots" => {
                let s = val(&mut i)?;
                a.carousel_slots = Some(s.parse().map_err(|_| ngc("invalid carousel-slots"))?);
            }
            "--parameter-input" => { a.parameter_input = Some(val(&mut i)?); }
            "--parameter-output" => { a.parameter_output = Some(val(&mut i)?); }
            "--probe-box" => {
                let mut vs = [0.0f64; 6];
                for j in 0..6 {
                    let s = val(&mut i)?;
                    vs[j] = s.parse().map_err(|_| ngc("invalid probe-box value"))?;
                }
                a.probe_box = Some((vs[0], vs[1], vs[2], vs[3], vs[4], vs[5]));
            }
            "--probe-tool" => {
                let s = val(&mut i)?;
                a.probe_tool = Some(s.parse().map_err(|_| ngc("invalid probe-tool"))?);
            }
            "--trace-output" => { a.trace_output = Some(val(&mut i)?); }
            "--trace-time-step" => {
                let s = val(&mut i)?;
                a.trace_time_step = Some(s.parse().map_err(|_| ngc("invalid trace-time-step"))?);
            }
            "--trace-distance-step" => {
                let s = val(&mut i)?;
                a.trace_distance_step = Some(s.parse().map_err(|_| ngc("invalid trace-distance-step"))?);
            }
            "--trace-position-tolerance" => {
                let s = val(&mut i)?;
                a.trace_position_tolerance = Some(s.parse().map_err(|_| ngc("invalid trace-position-tolerance"))?);
            }
            _ => return Err(ngc(format!("unknown CLI argument {k}"))),
        }
        i += 1;
    }
    if a.input.is_empty() { return Err(ngc("--input is required")); }
    if a.output.is_empty() { return Err(ngc("--output is required")); }
    Ok(a)
}

fn write_error_payload(path: &str, message: &str) {
    let payload = json!({
        "machine_position": {"x": 0.0, "y": 0.0, "z": 0.0, "a": 0.0, "b": 0.0, "c": 0.0},
        "feed_rate": 0.0,
        "spindle_speed": 0.0,
        "spindle_direction": "OFF",
        "cutter_radius_compensation_number": Value::Null,
        "tool_length_offset_index": Value::Null,
        "selected_tool": Value::Null,
        "tool_in_spindle": Value::Null,
        "active_modal_g_codes": Value::Object(Map::new()),
        "active_modal_m_codes": Value::Object(Map::new()),
        "coordinate_system_offsets": Value::Object(Map::new()),
        "parameters": Value::Object(Map::new()),
        "error": message,
    });
    let _ = fs::write(path, serde_json::to_string(&payload).unwrap_or_default());
}

fn validate_trace_args(a: &CliArgs) -> NgcResult<Option<(String, f64)>> {
    let provided: Vec<(&str, f64)> = [
        ("time", a.trace_time_step),
        ("distance", a.trace_distance_step),
        ("tolerance", a.trace_position_tolerance),
    ].into_iter().filter_map(|(m, v)| v.map(|vv| (m, vv))).collect();

    if a.trace_output.is_none() {
        if !provided.is_empty() {
            return Err(ngc("stepping flag provided without --trace-output"));
        }
        return Ok(None);
    }
    if provided.len() != 1 {
        return Err(ngc("--trace-output requires exactly one of --trace-time-step, --trace-distance-step, --trace-position-tolerance"));
    }
    let (mode, val) = provided[0];
    if val <= 0.0 {
        return Err(ngc(format!("trace stepping value must be positive (got {val})")));
    }
    Ok(Some((mode.to_string(), val)))
}

fn write_trace(path: &str, trace: &Value) -> NgcResult<()> {
    fs::write(path, serde_json::to_string(trace).map_err(|e| ngc(format!("trace: {e}")))?)
        .map_err(|e| ngc(format!("trace: {e}")))
}

fn run_main(argv: Vec<String>) -> ExitCode {
    let args = match parse_cli_args(&argv) {
        Ok(a) => a,
        Err(e) => {
            eprintln!("rs274: {e}");
            return ExitCode::from(2);
        }
    };

    let trace_cfg = match validate_trace_args(&args) {
        Ok(c) => c,
        Err(_) => {
            write_error_payload(&args.output, "invalid trace arguments");
            return ExitCode::from(1);
        }
    };

    let mut interp = Interpreter::new(
        args.block_delete,
        args.carousel_slots,
        args.probe_box,
        args.probe_tool,
    );

    let result: NgcResult<()> = (|| {
        if let Some(p) = &args.parameter_input {
            interp.load_parameter_file(p)?;
        }
        interp.initialize_default_parameters();
        if let Some(p) = &args.tool_table {
            interp.load_tool_table(p)?;
        }
        if let Some((mode, val)) = &trace_cfg {
            interp.trace = Some(TraceRecorder::new(mode.clone(), *val));
        }
        let program = fs::read_to_string(&args.input)
            .map_err(|e| ngc(format!("input: {e}")))?;
        interp.run(&program)?;
        let payload = interp.build_payload();
        fs::write(&args.output, serde_json::to_string(&Value::Object(payload))
            .map_err(|e| ngc(format!("output: {e}")))?)
            .map_err(|e| ngc(format!("output: {e}")))?;
        if let Some(p) = &args.parameter_output {
            interp.write_parameter_file(p)?;
        }
        if let (Some(tr), Some(path)) = (&interp.trace, &args.trace_output) {
            write_trace(path, &tr.build_trace())?;
        }
        Ok(())
    })();

    match result {
        Ok(()) => ExitCode::from(0),
        Err(e) => {
            write_error_payload(&args.output, &e.0);
            if let Some(path) = &args.trace_output {
                if let Some(tr) = interp.trace.as_mut() {
                    tr.set_error(interp.current_line_number, None);
                    let _ = write_trace(path, &tr.build_trace());
                }
            }
            ExitCode::from(1)
        }
    }
}

fn main() -> ExitCode {
    let argv: Vec<String> = env::args().skip(1).collect();
    run_main(argv)
}
