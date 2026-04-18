#!/usr/bin/env node
// IGES reference implementation (JavaScript / Node.js).
//
// Implements the five-subcommand CLI defined in
// Evals/IGES/prompt/technical-requirements-prompt.md:
//   parse / write / query / eval / roundtrip
//
// The implementation is structured to mirror the C++ reference
// implementation so that behavior is symmetric across languages:
//   - file_reader / writer: 80-column fixed-format physical records
//   - param_tokenizer: free-format data per §2.2.3
//   - global_section: 26 Global fields per §2.2.4.3
//   - directory_entry: 20 DE fields per §2.2.4.4
//   - entity_parsers: per-entity PD parsers (87 types)
//   - entity_writers: per-entity PD serializers
//   - canonical_json: parse→JSON and JSON→write converters
//   - validate: parse-path + write-path structural validation
//   - eval_helpers: parametric entity evaluation
//
// Error output goes to `--output` for parse/query/eval (JSON envelope
// per TR §1.4) and to stderr for write/roundtrip (matching the C++
// ref-impl behavior documented in TR §1.3 / §1.4).

"use strict";

const fs = require("fs");
const path = require("path");

// ──────────────────────────────────────────────────────────────────────────
// Argument parsing and subcommand dispatch
// ──────────────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  // Accept: iges <subcommand> [--input <p>] [--output <p>] [--de <n>]
  //                           [--t <f>] [--s <f>]
  if (argv.length === 0) return null;
  const subcommand = argv[0];
  const args = { subcommand, input: null, output: null, de: null, t: null, s: null };
  for (let i = 1; i < argv.length; i++) {
    const tok = argv[i];
    if (tok === "--input") args.input = argv[++i];
    else if (tok === "--output") args.output = argv[++i];
    else if (tok === "--de") args.de = argv[++i];
    else if (tok === "--t") args.t = argv[++i];
    else if (tok === "--s") args.s = argv[++i];
    else return null;
  }
  return args;
}

function makeError(message, specRef, line = 0, section = "unknown", diagnostics = []) {
  return {
    ok: false,
    error: message,
    spec_ref: specRef,
    line: line,
    section: section,
    diagnostics: diagnostics,
  };
}

function writeJson(outputPath, obj) {
  fs.writeFileSync(outputPath, JSON.stringify(obj, null, 2) + "\n", "utf-8");
}

function readFile(inputPath) {
  return fs.readFileSync(inputPath, { encoding: "latin1" });
}

function writeFile(outputPath, content) {
  fs.writeFileSync(outputPath, content, { encoding: "latin1" });
}

// ──────────────────────────────────────────────────────────────────────────
// Types / enums
// ──────────────────────────────────────────────────────────────────────────

// §2.2.4.3.14 Units flag → string map
const UNITS_BY_CODE = {
  1: "inches", 2: "millimeters", 3: "see_field_15",
  4: "feet", 5: "miles", 6: "meters", 7: "kilometers",
  8: "mils", 9: "microns", 10: "centimeters", 11: "microinches",
};
const UNITS_TO_CODE = Object.fromEntries(
  Object.entries(UNITS_BY_CODE).map(([k, v]) => [v, Number(k)])
);

// §2.2.4.3.23 Version flag → string map
const SPEC_VERSION_BY_CODE = {
  1: "v1_0", 2: "ansi_1981", 3: "v2_0", 4: "v3_0",
  5: "asme_1987", 6: "v4_0", 7: "asme_1989",
  8: "v5_0", 9: "v5_2", 10: "v5_1", 11: "v5_3",
};
const SPEC_VERSION_TO_CODE = Object.fromEntries(
  Object.entries(SPEC_VERSION_BY_CODE).map(([k, v]) => [v, Number(k)])
);

// §2.2.4.3.24 Drafting standard flag → string map
const DRAFTING_STD_BY_CODE = {
  0: "none", 1: "iso", 2: "afnor", 3: "ansi",
  4: "bsi", 5: "csa", 6: "din", 7: "jis",
};
const DRAFTING_STD_TO_CODE = Object.fromEntries(
  Object.entries(DRAFTING_STD_BY_CODE).map(([k, v]) => [v, Number(k)])
);

// Status Number sub-fields per §2.2.4.4.9
const BLANK_BY_CODE = { 0: "visible", 1: "blanked" };
const BLANK_TO_CODE = { visible: 0, blanked: 1 };

const SUBORDINATE_BY_CODE = {
  0: "independent", 1: "physically_dependent",
  2: "logically_dependent", 3: "both",
};
const SUBORDINATE_TO_CODE = Object.fromEntries(
  Object.entries(SUBORDINATE_BY_CODE).map(([k, v]) => [v, Number(k)])
);

const ENTITY_USE_BY_CODE = {
  0: "geometry", 1: "annotation", 2: "definition",
  3: "other", 4: "logical_positional",
  5: "parametric_2d", 6: "construction_geometry",
};
const ENTITY_USE_TO_CODE = Object.fromEntries(
  Object.entries(ENTITY_USE_BY_CODE).map(([k, v]) => [v, Number(k)])
);

const HIERARCHY_BY_CODE = {
  0: "global_top_down", 1: "global_defer", 2: "use_property",
};
const HIERARCHY_TO_CODE = Object.fromEntries(
  Object.entries(HIERARCHY_BY_CODE).map(([k, v]) => [v, Number(k)])
);

// ──────────────────────────────────────────────────────────────────────────
// Diagnostics
// ──────────────────────────────────────────────────────────────────────────

// Section kinds (for error envelope "section" field)
const SECTION = {
  FLAG: "flag",
  START: "start",
  GLOBAL: "global",
  DIRECTORY: "directory",
  PARAMETER: "parameter",
  TERMINATE: "terminate",
  UNKNOWN: "unknown",
};

function makeDiag(severity, line, section, message, specRef) {
  return { severity, line, section, message, spec_ref: specRef };
}

function errorFromDiagnostics(diags) {
  if (diags.length === 0) {
    return makeError("Unknown parse error", "§3");
  }
  const primary = diags[0];
  return {
    ok: false,
    error: primary.message,
    spec_ref: primary.spec_ref,
    line: primary.line,
    section: primary.section,
    diagnostics: diags.slice(),
  };
}

class IgesError extends Error {
  constructor(diag) {
    super(diag.message);
    this.diag = diag;
  }
}

// ──────────────────────────────────────────────────────────────────────────
// File format: physical records, section split, line padding
// ──────────────────────────────────────────────────────────────────────────

// Split raw IGES text into 80-column physical records.
function readPhysicalLines(text) {
  // IGES lines are 80 chars + newline. Split on \n and trim CR.
  const lines = text.split(/\r?\n/);
  if (lines.length > 0 && lines[lines.length - 1] === "") lines.pop();
  return lines;
}

function sectionLetter(line) {
  // Column 73 (0-indexed 72) holds S/G/D/P/T.
  if (line.length < 73) return null;
  return line[72];
}

function groupBySection(lines) {
  const g = { S: [], G: [], D: [], P: [], T: [], F: [] };
  for (const line of lines) {
    const s = sectionLetter(line);
    if (s && g[s] !== undefined) g[s].push(line);
  }
  return g;
}

// Pad a data string to columns 1-72, then append the section letter
// and a right-justified 7-digit sequence number.
function padSectionLine(data, section, seq) {
  const body = data.padEnd(72).slice(0, 72);
  const seqStr = String(seq).padStart(7);
  return `${body}${section}${seqStr}`;
}

// Pad a Parameter-Data record: columns 1-64 are data, 65 is space,
// 66-72 is the DE back-pointer, 73 is 'P', 74-80 is the P-section seq.
function padParamLine(data, deSeq, pSeq) {
  const body = data.padEnd(64).slice(0, 64);
  const back = String(deSeq).padStart(7);
  const pSeqStr = String(pSeq).padStart(7);
  return `${body} ${back}P${pSeqStr}`;
}

// ──────────────────────────────────────────────────────────────────────────
// Parameter tokenizer: free-format PD / Global data per §2.2.3
// ──────────────────────────────────────────────────────────────────────────

class ParamTokenizer {
  constructor(data, pd = ",", rd = ";") {
    this.data = data;
    this.pd = pd;
    this.rd = rd;
    this.pos = 0;
    this.terminated = false; // true once record delimiter seen
  }

  // Peek current character or null if past end.
  _peek() {
    return this.pos < this.data.length ? this.data[this.pos] : null;
  }

  // Consume one raw field up to the next delimiter. Returns the raw
  // field string (may be empty) and advances past the delimiter.
  // Sets this.terminated if the terminating delimiter was the record
  // delimiter.
  _nextField() {
    if (this.terminated) return { kind: "raw", raw: "" }; // defaulted
    // Hollerith handling: if the next non-space chars match NH where N
    // is a positive integer, consume exactly N chars after the H.
    // Otherwise read until the next pd or rd character.
    let start = this.pos;
    // Scan for Hollerith: leading optional whitespace + digits + 'H'
    let i = start;
    while (i < this.data.length && this.data[i] === " ") i++;
    let digitStart = i;
    while (i < this.data.length && /\d/.test(this.data[i])) i++;
    if (i > digitStart && this.data[i] === "H") {
      // Hollerith string. Parse the count.
      const n = parseInt(this.data.slice(digitStart, i), 10);
      const textStart = i + 1;
      const textEnd = textStart + n;
      if (textEnd > this.data.length) {
        throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
          `Hollerith length ${n} exceeds remaining data`, "§2.2.2.3"));
      }
      // Advance past Hollerith text; then expect a delimiter.
      this.pos = textEnd;
      // Skip whitespace after hollerith body.
      while (this.pos < this.data.length && this.data[this.pos] === " ") this.pos++;
      // Field terminator: pd or rd. Consume it.
      if (this.pos < this.data.length) {
        const c = this.data[this.pos];
        if (c === this.rd) { this.terminated = true; this.pos++; }
        else if (c === this.pd) { this.pos++; }
        // Otherwise leave pos as-is; free-format end.
      }
      // Strip trailing spaces from hollerith body? Spec §2.2.2.3 says
      // blanks are part of strings. Keep as-is.
      return { kind: "hollerith", raw: this.data.slice(textStart, textEnd) };
    }
    // Non-Hollerith: scan raw until pd or rd.
    let end = start;
    while (end < this.data.length) {
      const c = this.data[end];
      if (c === this.pd || c === this.rd) break;
      end++;
    }
    const raw = this.data.slice(start, end);
    // Consume the delimiter (if any).
    if (end < this.data.length) {
      const d = this.data[end];
      if (d === this.rd) this.terminated = true;
      this.pos = end + 1;
    } else {
      this.pos = end;
    }
    return { kind: "raw", raw: raw };
  }

  // Public API: integer, real, string, pointer, logical. Each takes
  // an optional default; if the field is empty AND a default is given
  // (not undefined), the default is returned. If the field is empty
  // and no default given, the function throws.

  nextInteger(defaultValue) {
    const f = this._nextField();
    const raw = (f.kind === "raw" ? f.raw : "").trim();
    if (raw === "") {
      if (defaultValue !== undefined) return defaultValue;
      throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
        "required integer field is empty", "§2.2.2.1"));
    }
    if (!/^[+-]?\d+$/.test(raw)) {
      throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
        `invalid integer literal: '${raw}'`, "§2.2.2.1"));
    }
    const n = parseInt(raw, 10);
    if (!Number.isFinite(n)) {
      throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
        `integer out of range: '${raw}'`, "§2.2.2.1"));
    }
    return n;
  }

  nextReal(defaultValue) {
    const f = this._nextField();
    let raw = (f.kind === "raw" ? f.raw : "").trim();
    if (raw === "") {
      if (defaultValue !== undefined) return defaultValue;
      throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
        "required real field is empty", "§2.2.2.2"));
    }
    // IGES reals can use D for double-precision exponent. Convert
    // to E for JavaScript parseFloat.
    const normalized = raw.replace(/[dD]/g, "e").replace(/^\s+/, "");
    const n = Number(normalized);
    if (!Number.isFinite(n)) {
      throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
        `invalid real literal: '${raw}'`, "§2.2.2.2"));
    }
    // Additional syntax check: the IGES real must have at least one
    // of decimal point or exponent. "5" without either is technically
    // an integer. We accept it to match ref-impl leniency.
    return n;
  }

  nextString(defaultValue) {
    const f = this._nextField();
    if (f.kind === "hollerith") {
      const text = f.raw;
      // §2.2.2.3: strings shall not contain ASCII control characters.
      for (let i = 0; i < text.length; i++) {
        const c = text.charCodeAt(i);
        if ((c >= 0x00 && c <= 0x1F) || c === 0x7F) {
          throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
            "Hollerith string contains ASCII control character",
            "§2.2.2.3"));
        }
      }
      return text;
    }
    // Non-Hollerith raw → empty or defaulted.
    const raw = f.raw.trim();
    if (raw === "") {
      if (defaultValue !== undefined) return defaultValue;
      throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
        "required string field is empty", "§2.2.2.3"));
    }
    // Unusual: a non-empty non-Hollerith string in a string field.
    throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
      `expected Hollerith string, got '${raw}'`, "§2.2.2.3"));
  }

  nextPointer(defaultValue) {
    // Pointers are just integers (possibly negated).
    return this.nextInteger(defaultValue === undefined ? 0 : defaultValue);
  }

  nextLogical(defaultValue) {
    const f = this._nextField();
    const raw = (f.kind === "raw" ? f.raw : "").trim();
    if (raw === "") {
      if (defaultValue !== undefined) return defaultValue;
      return false;
    }
    if (raw === "0") return false;
    if (raw === "1") return true;
    throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
      `invalid logical literal '${raw}'; must be 0 or 1`, "§2.2.2.6"));
  }

  atEnd() {
    return this.terminated || this.pos >= this.data.length;
  }
}

// ──────────────────────────────────────────────────────────────────────────
// Parameter writer (serialize values into free-format PD strings)
// ──────────────────────────────────────────────────────────────────────────

function formatReal(v) {
  // Match the ref-impl's %.15g format behavior. Ensure the output
  // contains a decimal point so parsers treat it as real, and emit at
  // least one fractional digit ("1.0" not "1.") to match the tests'
  // substring expectations (e.g. `"1.0" in p_body`).
  if (!Number.isFinite(v)) {
    throw new Error(`cannot format non-finite real: ${v}`);
  }
  if (Object.is(v, -0)) v = 0;
  let s = v.toString();
  if (s.includes("e") || s.includes("E")) {
    // Scientific form: ensure mantissa has a decimal point.
    s = s.replace(/^(-?\d+)(e[+-]?\d+)$/i, "$1.0$2");
    return s;
  }
  if (!s.includes(".")) s += ".0";
  return s;
}

function formatInteger(v) {
  if (!Number.isInteger(v)) {
    throw new Error(`cannot format non-integer: ${v}`);
  }
  return String(v);
}

function formatHollerith(s) {
  // Encode as <N>H<...N chars...>
  const bytes = Buffer.from(s, "latin1");
  return `${bytes.length}H${s}`;
}

class ParamWriter {
  constructor(pd = ",", rd = ";") {
    this.pd = pd;
    this.rd = rd;
    this.parts = [];
  }

  _push(val) { this.parts.push(val); }

  writeInteger(v) { this._push(formatInteger(v)); return this; }
  writeReal(v) { this._push(formatReal(v)); return this; }
  writeString(s) { this._push(formatHollerith(s)); return this; }
  writePointer(v) { this._push(formatInteger(v)); return this; }
  writeLogical(b) { this._push(b ? "1" : "0"); return this; }

  build() {
    // Join with pd, terminate with rd.
    return this.parts.join(this.pd) + this.rd;
  }

  // Start PD with the entity type as the first field.
  static forEntity(type, pd = ",", rd = ";") {
    const pw = new ParamWriter(pd, rd);
    pw._push(formatInteger(type));
    return pw;
  }
}

// ──────────────────────────────────────────────────────────────────────────
// Global section parse/write
// ──────────────────────────────────────────────────────────────────────────

function parseTimestamp(s) {
  // Accept 15-char YYYYMMDD.HHNNSS or 13-char YYMMDD.HHNNSS per §2.2.4.3.18
  if (!s) return null;
  const m15 = s.match(/^(\d{4})(\d{2})(\d{2})\.(\d{2})(\d{2})(\d{2})$/);
  const m13 = s.match(/^(\d{2})(\d{2})(\d{2})\.(\d{2})(\d{2})(\d{2})$/);
  if (m15) {
    return {
      year: +m15[1], month: +m15[2], day: +m15[3],
      hour: +m15[4], minute: +m15[5], second: +m15[6],
    };
  }
  if (m13) {
    return {
      year: 1900 + (+m13[1]), month: +m13[2], day: +m13[3],
      hour: +m13[4], minute: +m13[5], second: +m13[6],
    };
  }
  throw new IgesError(makeDiag("error", 0, SECTION.GLOBAL,
    `invalid timestamp '${s}'`, "§2.2.4.3.18"));
}

function formatTimestamp(ts) {
  if (!ts) return "";
  const y = String(ts.year).padStart(4, "0");
  const mo = String(ts.month).padStart(2, "0");
  const d = String(ts.day).padStart(2, "0");
  const h = String(ts.hour).padStart(2, "0");
  const mi = String(ts.minute).padStart(2, "0");
  const s = String(ts.second).padStart(2, "0");
  return `${y}${mo}${d}.${h}${mi}${s}`;
}

// Detect the delimiters from the first two fields of a Global-section
// payload. Returns { pd, rd, pos } where pos is the offset past the
// two delimiter fields.
function detectDelimiters(data) {
  let pd = ",";
  let rd = ";";
  let pos = 0;
  // Field 1 (param delimiter): "1Hx" or default.
  if (data.length > 2 && data[0] === "1" && data[1] === "H") {
    pd = data[2];
    pos = 3;
    if (pos < data.length && (data[pos] === "," || data[pos] === pd)) pos++;
  } else if (data.length > 0 && data[0] === ",") {
    pos = 1;
  }
  // Field 2 (record delimiter): "1Hy" or default.
  if (pos + 2 < data.length && data[pos] === "1" && data[pos+1] === "H") {
    rd = data[pos+2];
    pos += 3;
    if (pos < data.length && (data[pos] === pd || data[pos] === ",")) pos++;
  } else if (pos < data.length && (data[pos] === pd || data[pos] === ",")) {
    pos++;
  }
  return { pd, rd, pos };
}

function parseGlobalSection(data) {
  const { pd, rd, pos } = detectDelimiters(data);
  const remaining = data.slice(pos);
  const tok = new ParamTokenizer(remaining, pd, rd);
  const g = {
    param_delimiter: pd,
    record_delimiter: rd,
  };
  const diags = [];
  const push = (e) => {
    if (e.diag) { e.diag.section = SECTION.GLOBAL; diags.push(e.diag); }
    else diags.push(makeDiag("error", 0, SECTION.GLOBAL, String(e), "§2.2.4.3"));
  };
  const tryCall = (fn) => {
    try { return fn(); } catch (e) { push(e); return null; }
  };

  g.product_id_sender = tryCall(() => tok.nextString());
  g.file_name = tryCall(() => tok.nextString());
  g.native_system_id = tryCall(() => tok.nextString());
  g.preprocessor_version = tryCall(() => tok.nextString());
  g.integer_bits = tryCall(() => tok.nextInteger());
  g.sp_magnitude = tryCall(() => tok.nextInteger());
  g.sp_significance = tryCall(() => tok.nextInteger());
  g.dp_magnitude = tryCall(() => tok.nextInteger());
  g.dp_significance = tryCall(() => tok.nextInteger());
  g.product_id_receiver = tryCall(() => tok.nextString(g.product_id_sender || ""));
  g.model_space_scale = tryCall(() => tok.nextReal(1.0));
  const unitsCode = tryCall(() => tok.nextInteger(1));
  g.units = UNITS_BY_CODE[unitsCode] || "inches";
  g.units_name = tryCall(() => tok.nextString("IN"));
  g.max_line_weight_grads = tryCall(() => tok.nextInteger(1));
  g.max_line_weight_width = tryCall(() => tok.nextReal(0.0));
  const ts18 = tryCall(() => tok.nextString());
  g.file_timestamp = ts18 != null ? tryCall(() => parseTimestamp(ts18)) : null;
  g.min_resolution = tryCall(() => tok.nextReal(0.0));
  g.max_coordinate = tryCall(() => tok.nextReal(0.0));
  g.author = tryCall(() => tok.nextString(""));
  g.organization = tryCall(() => tok.nextString(""));
  let vcode = tryCall(() => tok.nextInteger(3));
  if (vcode != null) {
    if (vcode < 1) vcode = 3;
    if (vcode > 11) vcode = 11;
  }
  g.spec_version = SPEC_VERSION_BY_CODE[vcode] || "v2_0";
  const dcode = tryCall(() => tok.nextInteger(0));
  g.drafting_std = DRAFTING_STD_BY_CODE[dcode] || "none";
  const ts25 = tryCall(() => tok.nextString(""));
  g.model_timestamp = (ts25 && ts25.length > 0)
    ? tryCall(() => parseTimestamp(ts25))
    : null;
  g.app_protocol = tryCall(() => tok.nextString(""));

  return { global: g, diagnostics: diags };
}

function writeGlobalSection(g) {
  const pd = g.param_delimiter || ",";
  const rd = g.record_delimiter || ";";
  const pw = new ParamWriter(pd, rd);
  // Field 1: always emit the parameter delimiter as an explicit 1H
  // Hollerith (per the ref-impl's choice of spec §2.2.3.1 combination
  // 2). This guarantees unambiguous parsing of custom delimiters and
  // matches what the C++ writer emits.
  pw.writeString(pd);
  // Field 2: always emit the record delimiter as 1H Hollerith too.
  pw.writeString(rd);

  pw.writeString(g.product_id_sender || "");
  pw.writeString(g.file_name || "");
  pw.writeString(g.native_system_id || "");
  pw.writeString(g.preprocessor_version || "");
  pw.writeInteger(g.integer_bits != null ? g.integer_bits : 32);
  pw.writeInteger(g.sp_magnitude != null ? g.sp_magnitude : 38);
  pw.writeInteger(g.sp_significance != null ? g.sp_significance : 6);
  pw.writeInteger(g.dp_magnitude != null ? g.dp_magnitude : 308);
  pw.writeInteger(g.dp_significance != null ? g.dp_significance : 15);
  pw.writeString(g.product_id_receiver || g.product_id_sender || "");
  pw.writeReal(g.model_space_scale != null ? g.model_space_scale : 1.0);
  pw.writeInteger(UNITS_TO_CODE[g.units] != null ? UNITS_TO_CODE[g.units] : 1);
  pw.writeString(g.units_name || "IN");
  pw.writeInteger(g.max_line_weight_grads != null ? g.max_line_weight_grads : 1);
  pw.writeReal(g.max_line_weight_width != null ? g.max_line_weight_width : 0.0);
  pw.writeString(formatTimestamp(g.file_timestamp));
  pw.writeReal(g.min_resolution != null ? g.min_resolution : 0.0);
  pw.writeReal(g.max_coordinate != null ? g.max_coordinate : 0.0);
  pw.writeString(g.author || "");
  pw.writeString(g.organization || "");
  pw.writeInteger(SPEC_VERSION_TO_CODE[g.spec_version] != null ? SPEC_VERSION_TO_CODE[g.spec_version] : 3);
  pw.writeInteger(DRAFTING_STD_TO_CODE[g.drafting_std] != null ? DRAFTING_STD_TO_CODE[g.drafting_std] : 0);
  if (g.model_timestamp) pw.writeString(formatTimestamp(g.model_timestamp));
  else pw._push("");
  pw.writeString(g.app_protocol || "");

  return pw.build();
}

// ──────────────────────────────────────────────────────────────────────────
// Directory Entry parse/write
// ──────────────────────────────────────────────────────────────────────────

function parseStatusNumber(raw) {
  // 8-digit integer, four 2-digit sub-fields. Left-padded with spaces
  // when reading from an 8-col DE field.
  const padded = raw.trim().padStart(8, "0");
  if (padded.length !== 8) {
    throw new IgesError(makeDiag("error", 0, SECTION.DIRECTORY,
      `invalid status number '${raw}'`, "§2.2.4.4.9"));
  }
  const blank = parseInt(padded.slice(0, 2), 10);
  const subord = parseInt(padded.slice(2, 4), 10);
  const euse = parseInt(padded.slice(4, 6), 10);
  const hier = parseInt(padded.slice(6, 8), 10);
  return {
    blank: BLANK_BY_CODE[blank] || "visible",
    subordinate: SUBORDINATE_BY_CODE[subord] || "independent",
    entity_use: ENTITY_USE_BY_CODE[euse] || "geometry",
    hierarchy: HIERARCHY_BY_CODE[hier] || "global_top_down",
  };
}

function formatStatusNumber(st) {
  const b = BLANK_TO_CODE[st.blank || "visible"] || 0;
  const s = SUBORDINATE_TO_CODE[st.subordinate || "independent"] || 0;
  const e = ENTITY_USE_TO_CODE[st.entity_use || "geometry"] || 0;
  const h = HIERARCHY_TO_CODE[st.hierarchy || "global_top_down"] || 0;
  return (
    String(b).padStart(2, "0") +
    String(s).padStart(2, "0") +
    String(e).padStart(2, "0") +
    String(h).padStart(2, "0")
  );
}

function readField(line, startCol, width) {
  // 1-indexed columns; startCol is 0-indexed offset.
  return line.slice(startCol, startCol + width);
}

function parseIntField(raw, defaultValue = 0) {
  const t = raw.trim();
  if (t === "") return defaultValue;
  const n = parseInt(t, 10);
  if (!Number.isFinite(n)) {
    throw new IgesError(makeDiag("error", 0, SECTION.DIRECTORY,
      `invalid integer field '${raw}'`, "§2.2.4.4"));
  }
  return n;
}

function parseDirectoryEntry(line1, line2) {
  if (line1.length < 72 || line2.length < 72) {
    throw new IgesError(makeDiag("error", 0, SECTION.DIRECTORY,
      "directory entry lines too short", "§2.2.4.4"));
  }
  // Line 1: fields 1-9 plus the sequence suffix in cols 73-80.
  const entity_type1 = parseIntField(readField(line1, 0, 8));
  const param_data_ptr = parseIntField(readField(line1, 8, 8));
  const structure = parseIntField(readField(line1, 16, 8));
  const line_font = parseIntField(readField(line1, 24, 8));
  const level = parseIntField(readField(line1, 32, 8));
  const view = parseIntField(readField(line1, 40, 8));
  const xform_matrix = parseIntField(readField(line1, 48, 8));
  const label_display = parseIntField(readField(line1, 56, 8));
  const status = parseStatusNumber(readField(line1, 64, 8));
  // Line 2: entity_type (field 11, must match field 1), line_weight,
  // color, param_line_count, form, reserved, reserved, entity_label,
  // entity_subscript, sequence suffix.
  const line_weight = parseIntField(readField(line2, 8, 8));
  const color = parseIntField(readField(line2, 16, 8));
  const param_line_count = parseIntField(readField(line2, 24, 8));
  const form = parseIntField(readField(line2, 32, 8));
  // §2.2.4.4.18: entity label is right-justified in the 8-col field.
  // Strip padding spaces on parse so the canonical JSON returns the
  // label the user originally supplied (e.g. "PART01", not "  PART01").
  const entity_label = readField(line2, 56, 8).trim();
  const entity_subscript = parseIntField(readField(line2, 64, 8));

  return {
    entity_type: entity_type1,
    param_data_ptr,
    structure,
    line_font,
    level,
    view,
    xform_matrix,
    label_display,
    status,
    line_weight,
    color,
    param_line_count,
    form,
    entity_label,
    entity_subscript,
  };
}

function formatDirectoryEntry(de, deSeq) {
  const f = (v, w = 8) => String(v).padStart(w);
  const fs = (s, w = 8) => s.padStart(w).slice(0, w);
  const line1data =
    f(de.entity_type) +
    f(de.param_data_ptr || 0) +
    f(de.structure || 0) +
    f(de.line_font || 0) +
    f(de.level || 0) +
    f(de.view || 0) +
    f(de.xform_matrix || 0) +
    f(de.label_display || 0) +
    fs(formatStatusNumber(de.status || {}));
  const line1 = line1data + "D" + String(deSeq).padStart(7);
  const line2data =
    f(de.entity_type) +
    f(de.line_weight || 0) +
    f(de.color || 0) +
    f(de.param_line_count || 0) +
    f(de.form || 0) +
    "        " + // field 16 reserved
    "        " + // field 17 reserved
    fs(de.entity_label || "") +
    f(de.entity_subscript || 0);
  const line2 = line2data + "D" + String(deSeq + 1).padStart(7);
  return [line1, line2];
}

// ──────────────────────────────────────────────────────────────────────────
// File reader: parse an IGES file into IgesFile { start_lines, global, entities[] }
// Each entity is { de, pd_string } for raw-level work.
// ──────────────────────────────────────────────────────────────────────────

function readIgesFile(text) {
  const lines = readPhysicalLines(text);
  const grouped = groupBySection(lines);
  const diags = [];

  if (grouped.S.length === 0) {
    diags.push(makeDiag("error", 0, SECTION.START,
      "no Start section lines found", "§2.2.4.2"));
  }
  if (grouped.G.length === 0) {
    diags.push(makeDiag("error", 0, SECTION.GLOBAL,
      "no Global section lines found", "§2.2.4.3"));
  }
  if (grouped.T.length === 0) {
    diags.push(makeDiag("error", 0, SECTION.TERMINATE,
      "no Terminate section line found", "§2.2.4.6"));
  }

  if (diags.length > 0) {
    return { ok: false, diagnostics: diags };
  }

  // Start section: columns 1-72 (trim trailing spaces). Reject ASCII
  // control characters per §2.2.4.2.
  const startLines = [];
  for (const l of grouped.S) {
    const body = l.slice(0, 72);
    for (let i = 0; i < body.length; i++) {
      const c = body.charCodeAt(i);
      if ((c >= 0x00 && c <= 0x1F && c !== 0x20) || c === 0x7F) {
        diags.push(makeDiag("error", 0, SECTION.START,
          "Start section contains ASCII control character",
          "§2.2.4.2"));
        return { ok: false, diagnostics: diags };
      }
    }
    startLines.push(body.trimEnd());
  }

  // Global: concatenate all G-line data (cols 1-72) verbatim. Per-line
  // trim would corrupt Hollerith strings whose content ends with a
  // space at the line boundary — trailing padding spaces only exist
  // AFTER the record delimiter (end of last G-line), so it's safe to
  // strip only at the end of the concatenated payload.
  const globalData = grouped.G.map(l => l.slice(0, 72)).join("")
    .replace(/\s+$/, "");
  const gr = parseGlobalSection(globalData);
  if (gr.diagnostics.length > 0) {
    return { ok: false, diagnostics: gr.diagnostics };
  }
  const global = gr.global;

  // Directory Entries: pairs of lines.
  if (grouped.D.length % 2 !== 0) {
    diags.push(makeDiag("error", 0, SECTION.DIRECTORY,
      "odd number of DE lines", "§2.2.4.4"));
    return { ok: false, diagnostics: diags };
  }
  // Build DE list.
  const des = [];
  for (let i = 0; i < grouped.D.length; i += 2) {
    try {
      const de = parseDirectoryEntry(grouped.D[i], grouped.D[i + 1]);
      des.push(de);
    } catch (e) {
      diags.push(e.diag || makeDiag("error", 0, SECTION.DIRECTORY,
        String(e), "§2.2.4.4"));
      return { ok: false, diagnostics: diags };
    }
  }

  // Parameter data: group P-lines by DE back-pointer and concatenate.
  // P-line format: cols 1-64 data, col 65 space, cols 66-72 DE seq, col 73 'P', cols 74-80 P seq.
  const pdByDe = new Map();
  for (const line of grouped.P) {
    const body = line.slice(0, 64);
    const back = parseInt(line.slice(65, 72).trim(), 10);
    if (!pdByDe.has(back)) pdByDe.set(back, "");
    pdByDe.set(back, pdByDe.get(back) + body);
  }

  // Assemble entities: each DE has a sequence number of 2*i+1; find its PD.
  const entities = [];
  for (let i = 0; i < des.length; i++) {
    const de = des[i];
    const deSeq = 2 * i + 1;
    let pd = pdByDe.get(deSeq) || "";
    // Trim trailing spaces.
    pd = pd.replace(/\s+$/, "");
    // Truncate at the record delimiter so embedded comments don't
    // poison downstream parsers. The tokenizer also stops at rd, so
    // this is defensive.
    entities.push({ de, pd_string: pd });
  }

  return { ok: true, start_lines: startLines, global, entities };
}

// ──────────────────────────────────────────────────────────────────────────
// File writer: assemble S/G/D/P/T sections into the full 80-col output
// ──────────────────────────────────────────────────────────────────────────

function splitPdIntoLines(pdString, entityType, deSeq, startPSeq, pd) {
  // Each P-line data area is cols 1-64. We split the PD string on
  // delimiter boundaries to avoid breaking Hollerith strings awkwardly.
  // Simplification: split at 64-char chunks, allowing breaks anywhere.
  // Hollerith strings can span physical lines per §2.2.2.
  const lines = [];
  let pSeq = startPSeq;
  for (let pos = 0; pos < pdString.length; pos += 64) {
    const chunk = pdString.slice(pos, pos + 64);
    const line = padParamLine(chunk, deSeq, pSeq);
    lines.push(line);
    pSeq++;
  }
  if (lines.length === 0) {
    lines.push(padParamLine("", deSeq, pSeq));
    pSeq++;
  }
  return { lines, nextPSeq: pSeq, lineCount: lines.length };
}

function writeIgesFile(startLines, global, entities) {
  const pd = global.param_delimiter || ",";
  let output = "";

  // Start section: at least one line required.
  const sLines = startLines.length > 0 ? startLines : [""];
  let sCount = 0;
  for (const line of sLines) {
    sCount++;
    output += padSectionLine(line, "S", sCount) + "\n";
  }

  // Global section: split on 72-col chunks.
  const gPayload = writeGlobalSection(global);
  let gCount = 0;
  if (gPayload.length === 0) {
    gCount++;
    output += padSectionLine("", "G", gCount) + "\n";
  } else {
    for (let p = 0; p < gPayload.length; p += 72) {
      gCount++;
      output += padSectionLine(gPayload.slice(p, p + 72), "G", gCount) + "\n";
    }
  }

  // PD + DE sections: generate PD first to compute pd_start_seq and
  // pd_line_count per entity.
  const pdInfos = [];
  let pSeq = 1;
  for (let i = 0; i < entities.length; i++) {
    const ent = entities[i];
    const deSeq = 2 * i + 1;
    const r = splitPdIntoLines(ent.pd_string, ent.de.entity_type, deSeq, pSeq, pd);
    pdInfos.push({ start: pSeq, count: r.lineCount, lines: r.lines });
    pSeq = r.nextPSeq;
  }
  const pCount = pSeq - 1;

  // DE section with re-derived param_data_ptr / param_line_count.
  let dCount = 0;
  const deLines = [];
  for (let i = 0; i < entities.length; i++) {
    const ent = entities[i];
    const de = Object.assign({}, ent.de, {
      param_data_ptr: pdInfos[i].start,
      param_line_count: pdInfos[i].count,
    });
    const pair = formatDirectoryEntry(de, 2 * i + 1);
    deLines.push(...pair);
    dCount += 2;
  }
  for (const line of deLines) output += line + "\n";

  // PD lines
  for (const info of pdInfos) {
    for (const line of info.lines) output += line + "\n";
  }

  // Terminate section
  const tBody =
    "S" + String(sCount).padStart(7) +
    "G" + String(gCount).padStart(7) +
    "D" + String(dCount).padStart(7) +
    "P" + String(pCount).padStart(7);
  output += padSectionLine(tBody, "T", 1) + "\n";

  return output;
}

// ──────────────────────────────────────────────────────────────────────────
// Entity registry
// ──────────────────────────────────────────────────────────────────────────
//
// Each entry provides:
//   parse(tok, form) → data object matching TR §2.6 schema
//   write(data, pw)  → appends PD fields to the ParamWriter
//
// The data object IS the canonical JSON `data` payload — no separate
// toJson/fromJson layer. All fields use the schema names from the TR
// Appendix A so the object round-trips through JSON.stringify/parse.

const ENTITIES = {};

function registerEntity(type, parser, writer) {
  ENTITIES[type] = { parse: parser, write: writer };
}

// ──── §4.2 Null Entity (Type 0) ────
registerEntity(0,
  () => ({}),
  (d, pw) => { /* nothing */ }
);

// ──── §4.3 Circular Arc (Type 100) ────
registerEntity(100,
  (tok) => ({
    zt: tok.nextReal(0),
    x1: tok.nextReal(0), y1: tok.nextReal(0),
    x2: tok.nextReal(0), y2: tok.nextReal(0),
    x3: tok.nextReal(0), y3: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writeReal(d.zt); pw.writeReal(d.x1); pw.writeReal(d.y1);
    pw.writeReal(d.x2); pw.writeReal(d.y2); pw.writeReal(d.x3); pw.writeReal(d.y3);
  }
);

// ──── §4.4 Composite Curve (Type 102) ────
registerEntity(102,
  (tok) => {
    const n = tok.nextInteger(0);
    const constituents = [];
    for (let i = 0; i < n; i++) constituents.push(tok.nextPointer(0));
    return { constituents };
  },
  (d, pw) => {
    pw.writeInteger(d.constituents.length);
    for (const p of d.constituents) pw.writePointer(p);
  }
);

// ──── §4.5 Conic Arc (Type 104) ────
registerEntity(104,
  (tok) => ({
    A: tok.nextReal(0), B: tok.nextReal(0), C: tok.nextReal(0),
    D: tok.nextReal(0), E: tok.nextReal(0), F: tok.nextReal(0),
    zt: tok.nextReal(0),
    x1: tok.nextReal(0), y1: tok.nextReal(0),
    x2: tok.nextReal(0), y2: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writeReal(d.A); pw.writeReal(d.B); pw.writeReal(d.C);
    pw.writeReal(d.D); pw.writeReal(d.E); pw.writeReal(d.F);
    pw.writeReal(d.zt);
    pw.writeReal(d.x1); pw.writeReal(d.y1);
    pw.writeReal(d.x2); pw.writeReal(d.y2);
  }
);

// ──── §4.6/4.7/4.8/4.9/4.10/4.11 Copious Data (Type 106, all forms) ────
registerEntity(106,
  (tok) => {
    const ip = tok.nextInteger(0);
    const n = tok.nextInteger(0);
    const d = { ip, n, zt: 0, data: [] };
    let perTuple = 0;
    if (ip === 1) { d.zt = tok.nextReal(0); perTuple = 2; }
    else if (ip === 2) perTuple = 3;
    else if (ip === 3) perTuple = 6;
    const total = n * perTuple;
    for (let i = 0; i < total; i++) d.data.push(tok.nextReal(0));
    return d;
  },
  (d, pw) => {
    pw.writeInteger(d.ip);
    pw.writeInteger(d.n);
    if (d.ip === 1) pw.writeReal(d.zt || 0);
    for (const v of (d.data || [])) pw.writeReal(v);
  }
);

// ──── §4.12 Plane (Type 108) ────
registerEntity(108,
  (tok) => ({
    A: tok.nextReal(0), B: tok.nextReal(0), C: tok.nextReal(0), D: tok.nextReal(0),
    ptr: tok.nextPointer(0),
    x: tok.nextReal(0), y: tok.nextReal(0), z: tok.nextReal(0),
    size: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writeReal(d.A); pw.writeReal(d.B); pw.writeReal(d.C); pw.writeReal(d.D);
    pw.writePointer(d.ptr || 0);
    pw.writeReal(d.x); pw.writeReal(d.y); pw.writeReal(d.z);
    pw.writeReal(d.size || 0);
  }
);

// ──── §4.13 Line (Type 110), form 0/1/2 ────
registerEntity(110,
  (tok) => {
    const x1 = tok.nextReal(), y1 = tok.nextReal(), z1 = tok.nextReal();
    const x2 = tok.nextReal(), y2 = tok.nextReal(), z2 = tok.nextReal();
    // §3.2.5: reject degenerate Lines (zero arc length).
    if (x1 === x2 && y1 === y2 && z1 === z2) {
      throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
        "Line (Type 110) has coincident start and terminate points (zero arc length)",
        "§3.2.5"));
    }
    return { start: [x1, y1, z1], terminate: [x2, y2, z2] };
  },
  (d, pw) => {
    const [x1, y1, z1] = d.start;
    const [x2, y2, z2] = d.terminate;
    if (x1 === x2 && y1 === y2 && z1 === z2) {
      throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
        "Line (Type 110) has coincident start and terminate points (zero arc length)",
        "§3.2.5"));
    }
    pw.writeReal(x1); pw.writeReal(y1); pw.writeReal(z1);
    pw.writeReal(x2); pw.writeReal(y2); pw.writeReal(z2);
  }
);

// ──── §4.14 Parametric Spline Curve (Type 112) ────
registerEntity(112,
  (tok) => {
    const ctype = tok.nextInteger(0);
    const H = tok.nextInteger(0);
    const ndim = tok.nextInteger(0);
    const N = tok.nextInteger(0);
    const breakpoints = [];
    for (let i = 0; i <= N; i++) breakpoints.push(tok.nextReal(0));
    const segments = [];
    for (let i = 0; i < N; i++) {
      segments.push({
        ax: tok.nextReal(0), bx: tok.nextReal(0), cx: tok.nextReal(0), dx: tok.nextReal(0),
        ay: tok.nextReal(0), by: tok.nextReal(0), cy: tok.nextReal(0), dy: tok.nextReal(0),
        az: tok.nextReal(0), bz: tok.nextReal(0), cz: tok.nextReal(0), dz: tok.nextReal(0),
      });
    }
    const tp = {
      tpx0: tok.nextReal(0), tpx1: tok.nextReal(0), tpx2: tok.nextReal(0), tpx3: tok.nextReal(0),
      tpy0: tok.nextReal(0), tpy1: tok.nextReal(0), tpy2: tok.nextReal(0), tpy3: tok.nextReal(0),
      tpz0: tok.nextReal(0), tpz1: tok.nextReal(0), tpz2: tok.nextReal(0), tpz3: tok.nextReal(0),
    };
    return { ctype, H, ndim, breakpoints, segments, ...tp };
  },
  (d, pw) => {
    pw.writeInteger(d.ctype); pw.writeInteger(d.H); pw.writeInteger(d.ndim);
    const N = d.segments.length;
    pw.writeInteger(N);
    for (const b of d.breakpoints) pw.writeReal(b);
    for (const s of d.segments) {
      pw.writeReal(s.ax); pw.writeReal(s.bx); pw.writeReal(s.cx); pw.writeReal(s.dx);
      pw.writeReal(s.ay); pw.writeReal(s.by); pw.writeReal(s.cy); pw.writeReal(s.dy);
      pw.writeReal(s.az); pw.writeReal(s.bz); pw.writeReal(s.cz); pw.writeReal(s.dz);
    }
    pw.writeReal(d.tpx0); pw.writeReal(d.tpx1); pw.writeReal(d.tpx2); pw.writeReal(d.tpx3);
    pw.writeReal(d.tpy0); pw.writeReal(d.tpy1); pw.writeReal(d.tpy2); pw.writeReal(d.tpy3);
    pw.writeReal(d.tpz0); pw.writeReal(d.tpz1); pw.writeReal(d.tpz2); pw.writeReal(d.tpz3);
  }
);

// ──── §4.15 Parametric Spline Surface (Type 114) ────
registerEntity(114,
  (tok) => {
    const ctype = tok.nextInteger(0);
    const ptype = tok.nextInteger(0);
    const M = tok.nextInteger(0);
    const N = tok.nextInteger(0);
    const tu = [];
    for (let i = 0; i <= M; i++) tu.push(tok.nextReal(0));
    const tv = [];
    for (let i = 0; i <= N; i++) tv.push(tok.nextReal(0));
    const patches = [];
    for (let i = 0; i < M * N; i++) {
      const cx = [], cy = [], cz = [];
      for (let j = 0; j < 16; j++) cx.push(tok.nextReal(0));
      for (let j = 0; j < 16; j++) cy.push(tok.nextReal(0));
      for (let j = 0; j < 16; j++) cz.push(tok.nextReal(0));
      patches.push({ coeff_x: cx, coeff_y: cy, coeff_z: cz });
    }
    return { ctype, ptype, M, N, tu, tv, patches };
  },
  (d, pw) => {
    pw.writeInteger(d.ctype); pw.writeInteger(d.ptype);
    pw.writeInteger(d.M); pw.writeInteger(d.N);
    for (const v of d.tu) pw.writeReal(v);
    for (const v of d.tv) pw.writeReal(v);
    for (const p of d.patches) {
      for (const v of p.coeff_x) pw.writeReal(v);
      for (const v of p.coeff_y) pw.writeReal(v);
      for (const v of p.coeff_z) pw.writeReal(v);
    }
  }
);

// ──── §4.16 Point (Type 116) ────
registerEntity(116,
  (tok) => ({
    coords: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    display_symbol: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writeReal(d.coords[0]); pw.writeReal(d.coords[1]); pw.writeReal(d.coords[2]);
    pw.writePointer(d.display_symbol || 0);
  }
);

// ──── §4.17 Ruled Surface (Type 118) ────
registerEntity(118,
  (tok) => ({
    de1: tok.nextPointer(0), de2: tok.nextPointer(0),
    dirflg: tok.nextInteger(0), devflg: tok.nextInteger(0),
  }),
  (d, pw) => {
    pw.writePointer(d.de1); pw.writePointer(d.de2);
    pw.writeInteger(d.dirflg || 0); pw.writeInteger(d.devflg || 0);
  }
);

// ──── §4.18 Surface of Revolution (Type 120) ────
registerEntity(120,
  (tok) => ({
    l: tok.nextPointer(0), c: tok.nextPointer(0),
    sa: tok.nextReal(0), ta: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writePointer(d.l); pw.writePointer(d.c);
    pw.writeReal(d.sa); pw.writeReal(d.ta);
  }
);

// ──── §4.19 Tabulated Cylinder (Type 122) ────
registerEntity(122,
  (tok) => ({
    de: tok.nextPointer(0),
    terminate_point: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writePointer(d.de);
    pw.writeReal(d.terminate_point[0]);
    pw.writeReal(d.terminate_point[1]);
    pw.writeReal(d.terminate_point[2]);
  }
);

// ──── §4.20 Direction (Type 123) ────
registerEntity(123,
  (tok) => ({
    x: tok.nextReal(0), y: tok.nextReal(0), z: tok.nextReal(0),
  }),
  (d, pw) => { pw.writeReal(d.x); pw.writeReal(d.y); pw.writeReal(d.z); }
);

// ──── §4.21 Transformation Matrix (Type 124) ────
registerEntity(124,
  (tok) => {
    const r00 = tok.nextReal(0), r01 = tok.nextReal(0), r02 = tok.nextReal(0);
    const t0 = tok.nextReal(0);
    const r10 = tok.nextReal(0), r11 = tok.nextReal(0), r12 = tok.nextReal(0);
    const t1 = tok.nextReal(0);
    const r20 = tok.nextReal(0), r21 = tok.nextReal(0), r22 = tok.nextReal(0);
    const t2 = tok.nextReal(0);
    return {
      rotation: [[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]],
      translation: [t0, t1, t2],
    };
  },
  (d, pw) => {
    const r = d.rotation, t = d.translation;
    pw.writeReal(r[0][0]); pw.writeReal(r[0][1]); pw.writeReal(r[0][2]); pw.writeReal(t[0]);
    pw.writeReal(r[1][0]); pw.writeReal(r[1][1]); pw.writeReal(r[1][2]); pw.writeReal(t[1]);
    pw.writeReal(r[2][0]); pw.writeReal(r[2][1]); pw.writeReal(r[2][2]); pw.writeReal(t[2]);
  }
);

// ──── §4.22 Flash (Type 125) ────
registerEntity(125,
  (tok) => ({
    x: tok.nextReal(0), y: tok.nextReal(0),
    dim1: tok.nextReal(0), dim2: tok.nextReal(0), rot: tok.nextReal(0),
    de: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writeReal(d.x); pw.writeReal(d.y);
    pw.writeReal(d.dim1 || 0); pw.writeReal(d.dim2 || 0); pw.writeReal(d.rot || 0);
    pw.writePointer(d.de || 0);
  }
);

// ──── §4.23 Rational B-Spline Curve (Type 126) ────
registerEntity(126,
  (tok) => {
    const K = tok.nextInteger(0);
    const M = tok.nextInteger(0);
    const prop1 = tok.nextInteger(0);
    const prop2 = tok.nextInteger(0);
    const prop3 = tok.nextInteger(0);
    const prop4 = tok.nextInteger(0);
    const N = 1 + K - M;
    const A = N + 2 * M;
    const knots = [];
    for (let i = 0; i <= A; i++) knots.push(tok.nextReal(0));
    const weights = [];
    for (let i = 0; i <= K; i++) weights.push(tok.nextReal(0));
    const control_points = [];
    for (let i = 0; i <= K; i++) {
      control_points.push([tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]);
    }
    const v0 = tok.nextReal(0);
    const v1 = tok.nextReal(0);
    const plane_normal = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
    return { K, M, prop1, prop2, prop3, prop4, knots, weights, control_points, v0, v1, plane_normal };
  },
  (d, pw) => {
    pw.writeInteger(d.K); pw.writeInteger(d.M);
    pw.writeInteger(d.prop1); pw.writeInteger(d.prop2);
    pw.writeInteger(d.prop3); pw.writeInteger(d.prop4);
    for (const v of d.knots) pw.writeReal(v);
    for (const v of d.weights) pw.writeReal(v);
    for (const p of d.control_points) { pw.writeReal(p[0]); pw.writeReal(p[1]); pw.writeReal(p[2]); }
    pw.writeReal(d.v0); pw.writeReal(d.v1);
    pw.writeReal(d.plane_normal[0]); pw.writeReal(d.plane_normal[1]); pw.writeReal(d.plane_normal[2]);
  }
);

// ──── §4.24 Rational B-Spline Surface (Type 128) ────
registerEntity(128,
  (tok) => {
    const K1 = tok.nextInteger(0);
    const K2 = tok.nextInteger(0);
    const M1 = tok.nextInteger(0);
    const M2 = tok.nextInteger(0);
    const prop1 = tok.nextInteger(0);
    const prop2 = tok.nextInteger(0);
    const prop3 = tok.nextInteger(0);
    const prop4 = tok.nextInteger(0);
    const prop5 = tok.nextInteger(0);
    const N1 = 1 + K1 - M1;
    const N2 = 1 + K2 - M2;
    const A = N1 + 2 * M1;
    const B = N2 + 2 * M2;
    const C = (K1 + 1) * (K2 + 1);
    const knots_u = [];
    for (let i = 0; i <= A; i++) knots_u.push(tok.nextReal(0));
    const knots_v = [];
    for (let i = 0; i <= B; i++) knots_v.push(tok.nextReal(0));
    const weights = [];
    for (let i = 0; i < C; i++) weights.push(tok.nextReal(0));
    const control_points = [];
    for (let i = 0; i < C; i++) {
      control_points.push([tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]);
    }
    return {
      K1, K2, M1, M2, prop1, prop2, prop3, prop4, prop5,
      knots_u, knots_v, weights, control_points,
      u0: tok.nextReal(0), u1: tok.nextReal(0),
      v0: tok.nextReal(0), v1: tok.nextReal(0),
    };
  },
  (d, pw) => {
    pw.writeInteger(d.K1); pw.writeInteger(d.K2);
    pw.writeInteger(d.M1); pw.writeInteger(d.M2);
    pw.writeInteger(d.prop1); pw.writeInteger(d.prop2);
    pw.writeInteger(d.prop3); pw.writeInteger(d.prop4); pw.writeInteger(d.prop5);
    for (const v of d.knots_u) pw.writeReal(v);
    for (const v of d.knots_v) pw.writeReal(v);
    for (const w of d.weights) pw.writeReal(w);
    for (const p of d.control_points) { pw.writeReal(p[0]); pw.writeReal(p[1]); pw.writeReal(p[2]); }
    pw.writeReal(d.u0); pw.writeReal(d.u1); pw.writeReal(d.v0); pw.writeReal(d.v1);
  }
);

// ──── §4.25 Offset Curve (Type 130) ────
registerEntity(130,
  (tok) => ({
    de1: tok.nextPointer(0),
    flag: tok.nextInteger(0),
    de2: tok.nextPointer(0),
    ndim: tok.nextInteger(0),
    ptype: tok.nextInteger(0),
    d1: tok.nextReal(0),
    td1: tok.nextReal(0),
    d2: tok.nextReal(0),
    td2: tok.nextReal(0),
    vx: tok.nextReal(0), vy: tok.nextReal(0), vz: tok.nextReal(0),
    tt1: tok.nextReal(0), tt2: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writePointer(d.de1); pw.writeInteger(d.flag);
    pw.writePointer(d.de2 || 0); pw.writeInteger(d.ndim || 0); pw.writeInteger(d.ptype || 0);
    pw.writeReal(d.d1 || 0); pw.writeReal(d.td1 || 0);
    pw.writeReal(d.d2 || 0); pw.writeReal(d.td2 || 0);
    pw.writeReal(d.vx); pw.writeReal(d.vy); pw.writeReal(d.vz);
    pw.writeReal(d.tt1); pw.writeReal(d.tt2);
  }
);

// ──── §4.26 Connect Point (Type 132) ────
registerEntity(132,
  (tok) => ({
    location: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    display_symbol: tok.nextPointer(0),
    tf: tok.nextInteger(0),
    ff: tok.nextInteger(0),
    cid: tok.nextString(""),
    pttcid: tok.nextPointer(0),
    cfn: tok.nextString(""),
    pttcfn: tok.nextPointer(0),
    cpid: tok.nextInteger(0),
    fc: tok.nextInteger(0),
    sf: tok.nextInteger(0),
    psfi: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writeReal(d.location[0]); pw.writeReal(d.location[1]); pw.writeReal(d.location[2]);
    pw.writePointer(d.display_symbol || 0);
    pw.writeInteger(d.tf || 0); pw.writeInteger(d.ff || 0);
    pw.writeString(d.cid || ""); pw.writePointer(d.pttcid || 0);
    pw.writeString(d.cfn || ""); pw.writePointer(d.pttcfn || 0);
    pw.writeInteger(d.cpid || 0); pw.writeInteger(d.fc || 0);
    pw.writeInteger(d.sf || 0); pw.writePointer(d.psfi || 0);
  }
);

// ──── §4.27 Node (Type 134) ────
registerEntity(134,
  (tok) => ({
    x: tok.nextReal(0), y: tok.nextReal(0), z: tok.nextReal(0),
    ndcsp: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writeReal(d.x); pw.writeReal(d.y); pw.writeReal(d.z);
    pw.writePointer(d.ndcsp || 0);
  }
);

// ──── §4.28 Finite Element (Type 136) ────
registerEntity(136,
  (tok) => {
    const itop = tok.nextInteger(0);
    const n = tok.nextInteger(0);
    const nodes = [];
    for (let i = 0; i < n; i++) nodes.push(tok.nextPointer(0));
    const etyp = tok.nextString("");
    return { itop, n, nodes, etyp };
  },
  (d, pw) => {
    pw.writeInteger(d.itop); pw.writeInteger(d.nodes.length);
    for (const p of d.nodes) pw.writePointer(p);
    pw.writeString(d.etyp || "");
  }
);

// ──── §4.29 Nodal Displacement and Rotation (Type 138) ────
registerEntity(138,
  (tok) => {
    const nc = tok.nextInteger(0);
    const gp = [];
    for (let i = 0; i < nc; i++) gp.push(tok.nextPointer(0));
    const nn = tok.nextInteger(0);
    const nodes = [];
    for (let i = 0; i < nn; i++) {
      const node_id = tok.nextInteger(0);
      const np = tok.nextPointer(0);
      const cases = [];
      for (let j = 0; j < nc; j++) {
        cases.push({
          x: tok.nextReal(0), y: tok.nextReal(0), z: tok.nextReal(0),
          rx: tok.nextReal(0), ry: tok.nextReal(0), rz: tok.nextReal(0),
        });
      }
      nodes.push({ node_id, np, cases });
    }
    return { nc, gp, nn, nodes };
  },
  (d, pw) => {
    pw.writeInteger(d.nc);
    for (const p of d.gp) pw.writePointer(p);
    pw.writeInteger(d.nn);
    for (const nd of d.nodes) {
      pw.writeInteger(nd.node_id); pw.writePointer(nd.np);
      for (const c of nd.cases) {
        pw.writeReal(c.x); pw.writeReal(c.y); pw.writeReal(c.z);
        pw.writeReal(c.rx); pw.writeReal(c.ry); pw.writeReal(c.rz);
      }
    }
  }
);

// ──── §4.30 Offset Surface (Type 140) ────
registerEntity(140,
  (tok) => ({
    nx: tok.nextReal(0), ny: tok.nextReal(0), nz: tok.nextReal(0),
    d: tok.nextReal(0),
    de: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writeReal(d.nx); pw.writeReal(d.ny); pw.writeReal(d.nz);
    pw.writeReal(d.d); pw.writePointer(d.de);
  }
);

// ──── §4.31 Boundary (Type 141) ────
registerEntity(141,
  (tok) => {
    const type = tok.nextInteger(0);
    const pref = tok.nextInteger(0);
    const sptr = tok.nextPointer(0);
    const n = tok.nextInteger(0);
    const curves = [];
    for (let i = 0; i < n; i++) {
      const crvpt = tok.nextPointer(0);
      const sense = tok.nextInteger(0);
      const k = tok.nextInteger(0);
      const pscpt = [];
      for (let j = 0; j < k; j++) pscpt.push(tok.nextPointer(0));
      curves.push({ crvpt, sense, k, pscpt });
    }
    return { type, pref, sptr, n, curves };
  },
  (d, pw) => {
    pw.writeInteger(d.type); pw.writeInteger(d.pref); pw.writePointer(d.sptr);
    pw.writeInteger(d.curves.length);
    for (const c of d.curves) {
      pw.writePointer(c.crvpt); pw.writeInteger(c.sense);
      pw.writeInteger(c.pscpt.length);
      for (const p of c.pscpt) pw.writePointer(p);
    }
  }
);

// ──── §4.32 Curve on a Parametric Surface (Type 142) ────
registerEntity(142,
  (tok) => ({
    crtn: tok.nextInteger(0),
    sptr: tok.nextPointer(0),
    bptr: tok.nextPointer(0),
    cptr: tok.nextPointer(0),
    pref: tok.nextInteger(0),
  }),
  (d, pw) => {
    pw.writeInteger(d.crtn); pw.writePointer(d.sptr);
    pw.writePointer(d.bptr); pw.writePointer(d.cptr);
    pw.writeInteger(d.pref);
  }
);

// ──── §4.33 Bounded Surface (Type 143) ────
registerEntity(143,
  (tok) => {
    const type = tok.nextInteger(0);
    const sptr = tok.nextPointer(0);
    const n = tok.nextInteger(0);
    const bdpt = [];
    for (let i = 0; i < n; i++) bdpt.push(tok.nextPointer(0));
    return { type, sptr, n, bdpt };
  },
  (d, pw) => {
    pw.writeInteger(d.type); pw.writePointer(d.sptr);
    pw.writeInteger(d.bdpt.length);
    for (const p of d.bdpt) pw.writePointer(p);
  }
);

// ──── §4.34 Trimmed Parametric Surface (Type 144) ────
registerEntity(144,
  (tok) => {
    const pts = tok.nextPointer(0);
    const n1 = tok.nextInteger(0);
    const n2 = tok.nextInteger(0);
    const pto = tok.nextPointer(0);
    const pti = [];
    for (let i = 0; i < n2; i++) pti.push(tok.nextPointer(0));
    return { pts, n1, n2, pto, pti };
  },
  (d, pw) => {
    pw.writePointer(d.pts); pw.writeInteger(d.n1); pw.writeInteger(d.n2);
    pw.writePointer(d.pto);
    for (const p of d.pti) pw.writePointer(p);
  }
);

// ──── §4.35 Nodal Results (Type 146) ────
registerEntity(146,
  (tok) => {
    const gnote = tok.nextPointer(0);
    const scn = tok.nextInteger(0);
    const time = tok.nextReal(0);
    const nv = tok.nextInteger(0);
    const nn = tok.nextInteger(0);
    const nodes = [];
    for (let i = 0; i < nn; i++) {
      const node_id = tok.nextInteger(0);
      const np = tok.nextPointer(0);
      const values = [];
      for (let j = 0; j < nv; j++) values.push(tok.nextReal(0));
      nodes.push({ node_id, np, values });
    }
    return { gnote, scn, time, nv, nn, nodes };
  },
  (d, pw) => {
    pw.writePointer(d.gnote); pw.writeInteger(d.scn);
    pw.writeReal(d.time); pw.writeInteger(d.nv); pw.writeInteger(d.nn);
    for (const n of d.nodes) {
      pw.writeInteger(n.node_id); pw.writePointer(n.np);
      for (const v of n.values) pw.writeReal(v);
    }
  }
);

// ──── §4.36 Element Results (Type 148) ────
registerEntity(148,
  (tok) => {
    const gnote = tok.nextPointer(0);
    const scn = tok.nextInteger(0);
    const time = tok.nextReal(0);
    const nv = tok.nextInteger(0);
    const rrf = tok.nextInteger(0);
    const ne = tok.nextInteger(0);
    const elements = [];
    for (let i = 0; i < ne; i++) {
      const en = tok.nextInteger(0);
      const ep = tok.nextPointer(0);
      const itop = tok.nextInteger(0);
      const nl = tok.nextInteger(0);
      const dlf = tok.nextInteger(0);
      const nrl = tok.nextInteger(0);
      const rdrl = [];
      for (let j = 0; j < nrl; j++) rdrl.push(tok.nextInteger(0));
      const numv = tok.nextInteger(0);
      const values = [];
      for (let j = 0; j < numv; j++) values.push(tok.nextReal(0));
      elements.push({ en, ep, itop, nl, dlf, nrl, rdrl, numv, values });
    }
    return { gnote, scn, time, nv, rrf, ne, elements };
  },
  (d, pw) => {
    pw.writePointer(d.gnote); pw.writeInteger(d.scn); pw.writeReal(d.time);
    pw.writeInteger(d.nv); pw.writeInteger(d.rrf); pw.writeInteger(d.ne);
    for (const el of d.elements) {
      pw.writeInteger(el.en); pw.writePointer(el.ep);
      pw.writeInteger(el.itop); pw.writeInteger(el.nl);
      pw.writeInteger(el.dlf); pw.writeInteger(el.nrl);
      for (const r of el.rdrl) pw.writeInteger(r);
      pw.writeInteger(el.numv);
      for (const v of el.values) pw.writeReal(v);
    }
  }
);

// ──── §4.37 Block (Type 150) ────
registerEntity(150,
  (tok) => ({
    lx: tok.nextReal(0), ly: tok.nextReal(0), lz: tok.nextReal(0),
    corner: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    x_axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    z_axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.lx); pw.writeReal(d.ly); pw.writeReal(d.lz);
    pw.writeReal(d.corner[0]); pw.writeReal(d.corner[1]); pw.writeReal(d.corner[2]);
    pw.writeReal(d.x_axis[0]); pw.writeReal(d.x_axis[1]); pw.writeReal(d.x_axis[2]);
    pw.writeReal(d.z_axis[0]); pw.writeReal(d.z_axis[1]); pw.writeReal(d.z_axis[2]);
  }
);

// ──── §4.38 Right Angular Wedge (Type 152) ────
registerEntity(152,
  (tok) => ({
    lx: tok.nextReal(0), ly: tok.nextReal(0), lz: tok.nextReal(0),
    ltx: tok.nextReal(0),
    corner: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    x_axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    z_axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.lx); pw.writeReal(d.ly); pw.writeReal(d.lz); pw.writeReal(d.ltx);
    pw.writeReal(d.corner[0]); pw.writeReal(d.corner[1]); pw.writeReal(d.corner[2]);
    pw.writeReal(d.x_axis[0]); pw.writeReal(d.x_axis[1]); pw.writeReal(d.x_axis[2]);
    pw.writeReal(d.z_axis[0]); pw.writeReal(d.z_axis[1]); pw.writeReal(d.z_axis[2]);
  }
);

// ──── §4.39 Right Circular Cylinder (Type 154) ────
registerEntity(154,
  (tok) => ({
    h: tok.nextReal(0), r: tok.nextReal(0),
    face_center: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.h); pw.writeReal(d.r);
    pw.writeReal(d.face_center[0]); pw.writeReal(d.face_center[1]); pw.writeReal(d.face_center[2]);
    pw.writeReal(d.axis[0]); pw.writeReal(d.axis[1]); pw.writeReal(d.axis[2]);
  }
);

// ──── §4.40 Right Circular Cone Frustum (Type 156) ────
registerEntity(156,
  (tok) => ({
    h: tok.nextReal(0), r1: tok.nextReal(0), r2: tok.nextReal(0),
    face_center: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.h); pw.writeReal(d.r1); pw.writeReal(d.r2);
    pw.writeReal(d.face_center[0]); pw.writeReal(d.face_center[1]); pw.writeReal(d.face_center[2]);
    pw.writeReal(d.axis[0]); pw.writeReal(d.axis[1]); pw.writeReal(d.axis[2]);
  }
);

// ──── §4.41 Sphere (Type 158) ────
registerEntity(158,
  (tok) => ({
    radius: tok.nextReal(0),
    center: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.radius);
    pw.writeReal(d.center[0]); pw.writeReal(d.center[1]); pw.writeReal(d.center[2]);
  }
);

// ──── §4.42 Torus (Type 160) ────
registerEntity(160,
  (tok) => ({
    r1: tok.nextReal(0), r2: tok.nextReal(0),
    center: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.r1); pw.writeReal(d.r2);
    pw.writeReal(d.center[0]); pw.writeReal(d.center[1]); pw.writeReal(d.center[2]);
    pw.writeReal(d.axis[0]); pw.writeReal(d.axis[1]); pw.writeReal(d.axis[2]);
  }
);

// ──── §4.43 Solid of Revolution (Type 162) ────
registerEntity(162,
  (tok) => ({
    ptr: tok.nextPointer(0), f: tok.nextReal(0),
    axis_point: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    axis_dir: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writePointer(d.ptr); pw.writeReal(d.f);
    pw.writeReal(d.axis_point[0]); pw.writeReal(d.axis_point[1]); pw.writeReal(d.axis_point[2]);
    pw.writeReal(d.axis_dir[0]); pw.writeReal(d.axis_dir[1]); pw.writeReal(d.axis_dir[2]);
  }
);

// ──── §4.44 Solid of Linear Extrusion (Type 164) ────
registerEntity(164,
  (tok) => ({
    ptr: tok.nextPointer(0), length: tok.nextReal(0),
    direction: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writePointer(d.ptr); pw.writeReal(d.length);
    pw.writeReal(d.direction[0]); pw.writeReal(d.direction[1]); pw.writeReal(d.direction[2]);
  }
);

// ──── §4.45 Ellipsoid (Type 168) ────
registerEntity(168,
  (tok) => ({
    lx: tok.nextReal(0), ly: tok.nextReal(0), lz: tok.nextReal(0),
    center: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    x_axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    z_axis: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writeReal(d.lx); pw.writeReal(d.ly); pw.writeReal(d.lz);
    pw.writeReal(d.center[0]); pw.writeReal(d.center[1]); pw.writeReal(d.center[2]);
    pw.writeReal(d.x_axis[0]); pw.writeReal(d.x_axis[1]); pw.writeReal(d.x_axis[2]);
    pw.writeReal(d.z_axis[0]); pw.writeReal(d.z_axis[1]); pw.writeReal(d.z_axis[2]);
  }
);

// ──── §4.46 Boolean Tree (Type 180) ────
registerEntity(180,
  (tok) => {
    const n = tok.nextInteger(0);
    const entries = [];
    for (let i = 0; i < n; i++) entries.push(tok.nextInteger(0));
    return { n, entries };
  },
  (d, pw) => {
    pw.writeInteger(d.entries.length);
    for (const v of d.entries) pw.writeInteger(v);
  }
);

// ──── §4.47 Selected Component (Type 182) ────
registerEntity(182,
  (tok) => ({
    btree: tok.nextPointer(0),
    sel_point: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
  }),
  (d, pw) => {
    pw.writePointer(d.btree);
    pw.writeReal(d.sel_point[0]); pw.writeReal(d.sel_point[1]); pw.writeReal(d.sel_point[2]);
  }
);

// ──── §4.48 Solid Assembly (Type 184) ────
registerEntity(184,
  (tok) => {
    const n = tok.nextInteger(0);
    const items = [];
    for (let i = 0; i < n; i++) items.push(tok.nextPointer(0));
    const transforms = [];
    for (let i = 0; i < n; i++) transforms.push(tok.nextPointer(0));
    return { n, items, transforms };
  },
  (d, pw) => {
    pw.writeInteger(d.items.length);
    for (const p of d.items) pw.writePointer(p);
    for (const p of d.transforms) pw.writePointer(p);
  }
);

// ──── §4.49 MSBO (Type 186) ────
registerEntity(186,
  (tok) => {
    const shell = tok.nextPointer(0);
    const sof = tok.nextLogical(false);
    const n = tok.nextInteger(0);
    const voids = [];
    for (let i = 0; i < n; i++) {
      voids.push({ shell: tok.nextPointer(0), orientation: tok.nextLogical(false) });
    }
    return { shell, sof, n, voids };
  },
  (d, pw) => {
    pw.writePointer(d.shell); pw.writeLogical(d.sof);
    pw.writeInteger(d.voids.length);
    for (const v of d.voids) { pw.writePointer(v.shell); pw.writeLogical(v.orientation); }
  }
);

// ──── §4.50 Plane Surface (Type 190) ────
registerEntity(190,
  (tok, form) => {
    const deloc = tok.nextPointer(0);
    const denrml = tok.nextPointer(0);
    const derefd = (form === 1) ? tok.nextPointer(0) : 0;
    return { deloc, denrml, derefd };
  },
  (d, pw, form) => {
    pw.writePointer(d.deloc); pw.writePointer(d.denrml);
    if (form === 1) pw.writePointer(d.derefd || 0);
  }
);

// ──── §4.51 Cylindrical Surface (Type 192) ────
registerEntity(192,
  (tok, form) => {
    const deloc = tok.nextPointer(0);
    const deaxis = tok.nextPointer(0);
    const radius = tok.nextReal(0);
    const derefd = (form === 1) ? tok.nextPointer(0) : 0;
    return { deloc, deaxis, radius, derefd };
  },
  (d, pw, form) => {
    pw.writePointer(d.deloc); pw.writePointer(d.deaxis); pw.writeReal(d.radius);
    if (form === 1) pw.writePointer(d.derefd || 0);
  }
);

// ──── §4.52 Conical Surface (Type 194) ────
registerEntity(194,
  (tok, form) => {
    const deloc = tok.nextPointer(0);
    const deaxis = tok.nextPointer(0);
    const radius = tok.nextReal(0);
    const sangle = tok.nextReal(0);
    const derefd = (form === 1) ? tok.nextPointer(0) : 0;
    return { deloc, deaxis, radius, sangle, derefd };
  },
  (d, pw, form) => {
    pw.writePointer(d.deloc); pw.writePointer(d.deaxis);
    pw.writeReal(d.radius); pw.writeReal(d.sangle);
    if (form === 1) pw.writePointer(d.derefd || 0);
  }
);

// ──── §4.53 Spherical Surface (Type 196) ────
registerEntity(196,
  (tok, form) => {
    const deloc = tok.nextPointer(0);
    const radius = tok.nextReal(0);
    const deaxis = (form === 1) ? tok.nextPointer(0) : 0;
    const derefd = (form === 1) ? tok.nextPointer(0) : 0;
    return { deloc, radius, deaxis, derefd };
  },
  (d, pw, form) => {
    pw.writePointer(d.deloc); pw.writeReal(d.radius);
    if (form === 1) { pw.writePointer(d.deaxis || 0); pw.writePointer(d.derefd || 0); }
  }
);

// ──── §4.54 Toroidal Surface (Type 198) ────
registerEntity(198,
  (tok, form) => {
    const deloc = tok.nextPointer(0);
    const deaxis = tok.nextPointer(0);
    const majrad = tok.nextReal(0);
    const minrad = tok.nextReal(0);
    const derefd = (form === 1) ? tok.nextPointer(0) : 0;
    return { deloc, deaxis, majrad, minrad, derefd };
  },
  (d, pw, form) => {
    pw.writePointer(d.deloc); pw.writePointer(d.deaxis);
    pw.writeReal(d.majrad); pw.writeReal(d.minrad);
    if (form === 1) pw.writePointer(d.derefd || 0);
  }
);

// ──── §4.55 Angular Dimension (Type 202) ────
registerEntity(202,
  (tok) => ({
    denote: tok.nextPointer(0),
    dewit1: tok.nextPointer(0), dewit2: tok.nextPointer(0),
    xt: tok.nextReal(0), yt: tok.nextReal(0),
    radius: tok.nextReal(0),
    dearrw1: tok.nextPointer(0), dearrw2: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writePointer(d.dewit1); pw.writePointer(d.dewit2);
    pw.writeReal(d.xt); pw.writeReal(d.yt); pw.writeReal(d.radius);
    pw.writePointer(d.dearrw1); pw.writePointer(d.dearrw2);
  }
);

// ──── §4.56 Curve Dimension (Type 204) ────
registerEntity(204,
  (tok) => ({
    denote: tok.nextPointer(0),
    decurv1: tok.nextPointer(0), decurv2: tok.nextPointer(0),
    dearr1: tok.nextPointer(0), dearr2: tok.nextPointer(0),
    dewit1: tok.nextPointer(0), dewit2: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writePointer(d.decurv1); pw.writePointer(d.decurv2);
    pw.writePointer(d.dearr1); pw.writePointer(d.dearr2);
    pw.writePointer(d.dewit1); pw.writePointer(d.dewit2);
  }
);

// ──── §4.57 Diameter Dimension (Type 206) ────
registerEntity(206,
  (tok) => ({
    denote: tok.nextPointer(0),
    dearrw1: tok.nextPointer(0), dearrw2: tok.nextPointer(0),
    xt: tok.nextReal(0), yt: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writePointer(d.dearrw1); pw.writePointer(d.dearrw2);
    pw.writeReal(d.xt); pw.writeReal(d.yt);
  }
);

// ──── §4.58 Flag Note (Type 208) ────
registerEntity(208,
  (tok) => {
    const xt = tok.nextReal(0), yt = tok.nextReal(0), zt = tok.nextReal(0);
    const angle = tok.nextReal(0);
    const denote = tok.nextPointer(0);
    const n = tok.nextInteger(0);
    const leaders = [];
    for (let i = 0; i < n; i++) leaders.push(tok.nextPointer(0));
    return { xt, yt, zt, angle, denote, n, leaders };
  },
  (d, pw) => {
    pw.writeReal(d.xt); pw.writeReal(d.yt); pw.writeReal(d.zt);
    pw.writeReal(d.angle); pw.writePointer(d.denote);
    pw.writeInteger(d.leaders.length);
    for (const p of d.leaders) pw.writePointer(p);
  }
);

// ──── §4.59 General Label (Type 210) ────
registerEntity(210,
  (tok) => {
    const denote = tok.nextPointer(0);
    const n = tok.nextInteger(0);
    const leaders = [];
    for (let i = 0; i < n; i++) leaders.push(tok.nextPointer(0));
    return { denote, n, leaders };
  },
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writeInteger(d.leaders.length);
    for (const p of d.leaders) pw.writePointer(p);
  }
);

// ──── §4.60 General Note (Type 212) ────
registerEntity(212,
  (tok) => {
    const ns = tok.nextInteger(0);
    const strings = [];
    for (let i = 0; i < ns; i++) {
      strings.push({
        nc: tok.nextInteger(0), wc: tok.nextReal(0), hc: tok.nextReal(0),
        fc: tok.nextInteger(0), slant: tok.nextReal(0), angle: tok.nextReal(0),
        mirror: tok.nextInteger(0), vh: tok.nextInteger(0),
        start: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
        text: tok.nextString(""),
      });
    }
    return { ns, strings };
  },
  (d, pw) => {
    pw.writeInteger(d.strings.length);
    for (const s of d.strings) {
      pw.writeInteger(s.nc); pw.writeReal(s.wc); pw.writeReal(s.hc);
      pw.writeInteger(s.fc); pw.writeReal(s.slant); pw.writeReal(s.angle);
      pw.writeInteger(s.mirror); pw.writeInteger(s.vh);
      pw.writeReal(s.start[0]); pw.writeReal(s.start[1]); pw.writeReal(s.start[2]);
      pw.writeString(s.text || "");
    }
  }
);

// ──── §4.60.x New General Note (Type 213) ────
registerEntity(213,
  (tok) => {
    const d = {
      txtcw: tok.nextReal(0), txtch: tok.nextReal(0),
      justcd: tok.nextInteger(0),
      txtcx: tok.nextReal(0), txtcy: tok.nextReal(0), txtcz: tok.nextReal(0),
      txtag: tok.nextReal(0),
      baselx: tok.nextReal(0), basely: tok.nextReal(0), baselz: tok.nextReal(0),
      nils: tok.nextReal(0),
    };
    const ns = tok.nextInteger(0);
    const strings = [];
    for (let i = 0; i < ns; i++) {
      strings.push({
        fixvar: tok.nextInteger(0),
        chrwid: tok.nextReal(0), chrhgt: tok.nextReal(0),
        cspace: tok.nextReal(0), lspace: tok.nextReal(0),
        font: tok.nextInteger(0), chrang: tok.nextReal(0),
        cctext: tok.nextString(""),
        nc: tok.nextInteger(0),
        wt: tok.nextReal(0), ht: tok.nextReal(0),
        chrset: tok.nextInteger(0),
        sl: tok.nextReal(0), a: tok.nextReal(0),
        m: tok.nextInteger(0), vh: tok.nextInteger(0),
        xs: tok.nextReal(0), ys: tok.nextReal(0), zs: tok.nextReal(0),
        text: tok.nextString(""),
      });
    }
    d.ns = ns; d.strings = strings;
    return d;
  },
  (d, pw) => {
    pw.writeReal(d.txtcw); pw.writeReal(d.txtch); pw.writeInteger(d.justcd);
    pw.writeReal(d.txtcx); pw.writeReal(d.txtcy); pw.writeReal(d.txtcz);
    pw.writeReal(d.txtag);
    pw.writeReal(d.baselx); pw.writeReal(d.basely); pw.writeReal(d.baselz);
    pw.writeReal(d.nils);
    pw.writeInteger(d.strings.length);
    for (const s of d.strings) {
      pw.writeInteger(s.fixvar);
      pw.writeReal(s.chrwid); pw.writeReal(s.chrhgt);
      pw.writeReal(s.cspace); pw.writeReal(s.lspace);
      pw.writeInteger(s.font); pw.writeReal(s.chrang);
      pw.writeString(s.cctext || "");
      pw.writeInteger(s.nc);
      pw.writeReal(s.wt); pw.writeReal(s.ht);
      pw.writeInteger(s.chrset);
      pw.writeReal(s.sl); pw.writeReal(s.a);
      pw.writeInteger(s.m); pw.writeInteger(s.vh);
      pw.writeReal(s.xs); pw.writeReal(s.ys); pw.writeReal(s.zs);
      pw.writeString(s.text || "");
    }
  }
);

// ──── §4.61 Leader Arrow (Type 214) ────
registerEntity(214,
  (tok) => {
    const n = tok.nextInteger(0);
    const ad1 = tok.nextReal(0), ad2 = tok.nextReal(0);
    const zt = tok.nextReal(0);
    const xh = tok.nextReal(0), yh = tok.nextReal(0);
    const segments = [];
    for (let i = 0; i < n; i++) {
      segments.push({ x: tok.nextReal(0), y: tok.nextReal(0) });
    }
    return { n, ad1, ad2, zt, xh, yh, segments };
  },
  (d, pw) => {
    pw.writeInteger(d.segments.length);
    pw.writeReal(d.ad1); pw.writeReal(d.ad2);
    pw.writeReal(d.zt); pw.writeReal(d.xh); pw.writeReal(d.yh);
    for (const s of d.segments) { pw.writeReal(s.x); pw.writeReal(s.y); }
  }
);

// ──── §4.62 Linear Dimension (Type 216) ────
registerEntity(216,
  (tok) => ({
    denote: tok.nextPointer(0),
    dearrw1: tok.nextPointer(0), dearrw2: tok.nextPointer(0),
    dewit1: tok.nextPointer(0), dewit2: tok.nextPointer(0),
    xt: tok.nextReal(0), yt: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writePointer(d.dearrw1); pw.writePointer(d.dearrw2);
    pw.writePointer(d.dewit1); pw.writePointer(d.dewit2);
    pw.writeReal(d.xt); pw.writeReal(d.yt);
  }
);

// ──── §4.63 Ordinate Dimension (Type 218) ────
registerEntity(218,
  (tok, form) => {
    const denote = tok.nextPointer(0);
    if (form === 1) {
      return { form, denote, dewit: 0, deord: tok.nextPointer(0), desupp: tok.nextPointer(0) };
    }
    return { form: form || 0, denote, dewit: tok.nextPointer(0), deord: 0, desupp: 0 };
  },
  (d, pw, form) => {
    pw.writePointer(d.denote);
    if (form === 1) { pw.writePointer(d.deord || 0); pw.writePointer(d.desupp || 0); }
    else pw.writePointer(d.dewit || 0);
  }
);

// ──── §4.64 Point Dimension (Type 220) ────
registerEntity(220,
  (tok) => ({
    denote: tok.nextPointer(0),
    dearrw: tok.nextPointer(0),
    degeom: tok.nextPointer(0),
  }),
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writePointer(d.dearrw); pw.writePointer(d.degeom);
  }
);

// ──── §4.65 Radius Dimension (Type 222) ────
registerEntity(222,
  (tok, form) => {
    const denote = tok.nextPointer(0);
    const dearrw = tok.nextPointer(0);
    const xt = tok.nextReal(0);
    const yt = tok.nextReal(0);
    const dearrw2 = (form === 1) ? tok.nextPointer(0) : 0;
    return { form: form || 0, denote, dearrw, xt, yt, dearrw2 };
  },
  (d, pw, form) => {
    pw.writePointer(d.denote); pw.writePointer(d.dearrw);
    pw.writeReal(d.xt); pw.writeReal(d.yt);
    if (form === 1) pw.writePointer(d.dearrw2 || 0);
  }
);

// ──── §4.66 General Symbol (Type 228) ────
registerEntity(228,
  (tok) => {
    const denote = tok.nextPointer(0);
    const n = tok.nextInteger(0);
    const geometries = [];
    for (let i = 0; i < n; i++) geometries.push(tok.nextPointer(0));
    const l = tok.nextInteger(0);
    const leaders = [];
    for (let i = 0; i < l; i++) leaders.push(tok.nextPointer(0));
    return { denote, n, geometries, l, leaders };
  },
  (d, pw) => {
    pw.writePointer(d.denote);
    pw.writeInteger(d.geometries.length);
    for (const p of d.geometries) pw.writePointer(p);
    pw.writeInteger(d.leaders.length);
    for (const p of d.leaders) pw.writePointer(p);
  }
);

// ──── §4.67 Sectioned Area (Type 230) ────
registerEntity(230,
  (tok) => {
    const bndp = tok.nextPointer(0);
    const patrn = tok.nextInteger(0);
    const xt = tok.nextReal(0), yt = tok.nextReal(0), zt = tok.nextReal(0);
    const dist = tok.nextReal(0), angle = tok.nextReal(0);
    const n = tok.nextInteger(0);
    const islands = [];
    for (let i = 0; i < n; i++) islands.push(tok.nextPointer(0));
    return { bndp, patrn, xt, yt, zt, dist, angle, n, islands };
  },
  (d, pw) => {
    pw.writePointer(d.bndp); pw.writeInteger(d.patrn);
    pw.writeReal(d.xt); pw.writeReal(d.yt); pw.writeReal(d.zt);
    pw.writeReal(d.dist); pw.writeReal(d.angle);
    pw.writeInteger(d.islands.length);
    for (const p of d.islands) pw.writePointer(p);
  }
);

// ──── §4.69 Associativity Definition (Type 302) ────
registerEntity(302,
  (tok) => {
    const k = tok.nextInteger(0);
    const classes = [];
    for (let i = 0; i < k; i++) {
      const bp = tok.nextInteger(0);
      const order = tok.nextInteger(0);
      const n = tok.nextInteger(0);
      const item_types = [];
      for (let j = 0; j < n; j++) item_types.push(tok.nextInteger(0));
      classes.push({ bp, order, n, item_types });
    }
    return { k, classes };
  },
  (d, pw) => {
    pw.writeInteger(d.classes.length);
    for (const c of d.classes) {
      pw.writeInteger(c.bp); pw.writeInteger(c.order);
      pw.writeInteger(c.item_types.length);
      for (const it of c.item_types) pw.writeInteger(it);
    }
  }
);

// ──── §4.70 Line Font Definition (Type 304) ────
registerEntity(304,
  (tok, form) => {
    const m = tok.nextInteger(0);
    if (form === 1) {
      return {
        form, m,
        l1: tok.nextPointer(0), l2: tok.nextReal(0), l3: tok.nextReal(0),
        segments: [], bitmask: "",
      };
    }
    const segments = [];
    for (let i = 0; i < m; i++) segments.push(tok.nextReal(0));
    const bitmask = tok.nextString("");
    return { form: form || 2, m, l1: 0, l2: 0, l3: 0, segments, bitmask };
  },
  (d, pw, form) => {
    pw.writeInteger(d.m);
    if (form === 1) {
      pw.writePointer(d.l1 || 0); pw.writeReal(d.l2 || 0); pw.writeReal(d.l3 || 0);
    } else {
      for (const s of d.segments) pw.writeReal(s);
      pw.writeString(d.bitmask || "");
    }
  }
);

// ──── §4.73 Subfigure Definition (Type 308) ────
registerEntity(308,
  (tok) => {
    const depth = tok.nextInteger(0);
    const name = tok.nextString("");
    const n = tok.nextInteger(0);
    const entities = [];
    for (let i = 0; i < n; i++) entities.push(tok.nextPointer(0));
    return { depth, name, n, entities };
  },
  (d, pw) => {
    pw.writeInteger(d.depth); pw.writeString(d.name || "");
    pw.writeInteger(d.entities.length);
    for (const p of d.entities) pw.writePointer(p);
  }
);

// ──── §4.74 Text Font Definition (Type 310) ────
registerEntity(310,
  (tok) => {
    const fc = tok.nextInteger(0);
    const fname = tok.nextString("");
    const sf = tok.nextInteger(0);
    const scale = tok.nextInteger(0);
    const n = tok.nextInteger(0);
    const characters = [];
    for (let i = 0; i < n; i++) {
      const ac = tok.nextInteger(0);
      const nx = tok.nextInteger(0);
      const ny = tok.nextInteger(0);
      const nm = tok.nextInteger(0);
      const motions = [];
      for (let j = 0; j < nm; j++) {
        motions.push({
          pf: tok.nextInteger(0), x: tok.nextInteger(0), y: tok.nextInteger(0),
        });
      }
      characters.push({ ac, nx, ny, nm, motions });
    }
    return { fc, fname, sf, scale, n, characters };
  },
  (d, pw) => {
    pw.writeInteger(d.fc); pw.writeString(d.fname || "");
    pw.writeInteger(d.sf); pw.writeInteger(d.scale);
    pw.writeInteger(d.characters.length);
    for (const c of d.characters) {
      pw.writeInteger(c.ac); pw.writeInteger(c.nx); pw.writeInteger(c.ny);
      pw.writeInteger(c.motions.length);
      for (const m of c.motions) {
        pw.writeInteger(m.pf); pw.writeInteger(m.x); pw.writeInteger(m.y);
      }
    }
  }
);

// ──── §4.75 Text Display Template (Type 312) ────
registerEntity(312,
  (tok) => ({
    cbw: tok.nextReal(0), cbh: tok.nextReal(0),
    fc: tok.nextInteger(0),
    sl: tok.nextReal(0), a: tok.nextReal(0),
    m: tok.nextInteger(0), vh: tok.nextInteger(0),
    xs: tok.nextReal(0), ys: tok.nextReal(0), zs: tok.nextReal(0),
  }),
  (d, pw) => {
    pw.writeReal(d.cbw); pw.writeReal(d.cbh);
    pw.writeInteger(d.fc);
    pw.writeReal(d.sl); pw.writeReal(d.a);
    pw.writeInteger(d.m); pw.writeInteger(d.vh);
    pw.writeReal(d.xs); pw.writeReal(d.ys); pw.writeReal(d.zs);
  }
);

// ──── §4.76 Color Definition (Type 314) ────
registerEntity(314,
  (tok) => ({
    red: tok.nextReal(0), green: tok.nextReal(0), blue: tok.nextReal(0),
    name: tok.nextString(""),
  }),
  (d, pw) => {
    pw.writeReal(d.red); pw.writeReal(d.green); pw.writeReal(d.blue);
    pw.writeString(d.name || "");
  }
);

// ──── §4.77 Units Data (Type 316) ────
registerEntity(316,
  (tok) => {
    const np = tok.nextInteger(0);
    const units = [];
    for (let i = 0; i < np; i++) {
      units.push({
        typ: tok.nextString(""),
        val: tok.nextString(""),
        sf: tok.nextReal(0),
      });
    }
    return { np, units };
  },
  (d, pw) => {
    pw.writeInteger(d.units.length);
    for (const u of d.units) {
      pw.writeString(u.typ || ""); pw.writeString(u.val || ""); pw.writeReal(u.sf);
    }
  }
);

// ──── §4.78 Network Subfigure Definition (Type 320) ────
registerEntity(320,
  (tok) => {
    const depth = tok.nextInteger(0);
    const name = tok.nextString("");
    const na = tok.nextInteger(0);
    const associated = [];
    for (let i = 0; i < na; i++) associated.push(tok.nextPointer(0));
    const tf = tok.nextInteger(0);
    const prd = tok.nextString("");
    const dptr = tok.nextPointer(0);
    const nc = tok.nextInteger(0);
    const connects = [];
    for (let i = 0; i < nc; i++) connects.push(tok.nextPointer(0));
    return { depth, name, na, associated, tf, prd, dptr, nc, connects };
  },
  (d, pw) => {
    pw.writeInteger(d.depth); pw.writeString(d.name || "");
    pw.writeInteger(d.associated.length);
    for (const p of d.associated) pw.writePointer(p);
    pw.writeInteger(d.tf); pw.writeString(d.prd || "");
    pw.writePointer(d.dptr || 0);
    pw.writeInteger(d.connects.length);
    for (const p of d.connects) pw.writePointer(p);
  }
);

// ──── §4.79 Attribute Table Definition (Type 322) ────
registerEntity(322,
  (tok, form) => {
    const name = tok.nextString("");
    const alt = tok.nextInteger(0);
    const na = tok.nextInteger(0);
    const attributes = [];
    for (let i = 0; i < na; i++) {
      const at = tok.nextInteger(0);
      const avdt = tok.nextInteger(0);
      const avc = tok.nextInteger(0);
      const values = [];
      const display_ptrs = [];
      if (form === 1 || form === 2) {
        for (let j = 0; j < avc; j++) {
          const v = readAttrValue(tok, avdt);
          values.push(v);
          if (form === 2) display_ptrs.push(tok.nextPointer(0));
        }
      }
      attributes.push({ at, avdt, avc, values, display_ptrs });
    }
    return { name, alt, na, attributes };
  },
  (d, pw, form) => {
    pw.writeString(d.name || ""); pw.writeInteger(d.alt);
    pw.writeInteger(d.attributes.length);
    for (const a of d.attributes) {
      pw.writeInteger(a.at); pw.writeInteger(a.avdt); pw.writeInteger(a.avc);
      if (form === 1 || form === 2) {
        for (let j = 0; j < a.avc; j++) {
          writeAttrValue(pw, a.avdt, a.values[j]);
          if (form === 2) pw.writePointer(a.display_ptrs[j] || 0);
        }
      }
    }
  }
);

function readAttrValue(tok, avdt) {
  switch (avdt) {
    case 1: case 6: return { kind: "int", value: tok.nextInteger(0) };
    case 2: return { kind: "real", value: tok.nextReal(0) };
    case 3: return { kind: "string", value: tok.nextString("") };
    case 4: return { kind: "pointer", value: tok.nextPointer(0) };
    default:
      throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
        `unsupported AVDT ${avdt}`, "§4.79"));
  }
}

function writeAttrValue(pw, avdt, v) {
  if (v && typeof v === "object" && "kind" in v) {
    const val = v.value;
    if (v.kind === "int" || v.kind === "pointer") pw.writeInteger(val);
    else if (v.kind === "real") pw.writeReal(val);
    else if (v.kind === "string") pw.writeString(val || "");
    else throw new Error(`unknown FieldValue kind: ${v.kind}`);
  } else {
    // Raw typed fallback based on AVDT.
    if (avdt === 1 || avdt === 6 || avdt === 4) pw.writeInteger(v | 0);
    else if (avdt === 2) pw.writeReal(Number(v) || 0);
    else if (avdt === 3) pw.writeString(String(v || ""));
    else throw new Error(`unknown AVDT ${avdt}`);
  }
}

// ──── §4.80 Associativity Instance (Type 402) ────
registerEntity(402,
  (tok) => {
    const n = tok.nextInteger(0);
    const entries = [];
    for (let i = 0; i < n; i++) entries.push(tok.nextPointer(0));
    return { n, entries };
  },
  (d, pw) => {
    pw.writeInteger(d.entries.length);
    for (const p of d.entries) pw.writePointer(p);
  }
);

// ──── §4.96 Drawing (Type 404) ────
registerEntity(404,
  (tok, form) => {
    const n = tok.nextInteger(0);
    const views = [];
    for (let i = 0; i < n; i++) {
      const view = tok.nextPointer(0);
      const x_origin = tok.nextReal(0);
      const y_origin = tok.nextReal(0);
      const angle = (form === 1) ? tok.nextReal(0) : 0;
      views.push({ view, x_origin, y_origin, angle });
    }
    const m = tok.nextInteger(0);
    const annotations = [];
    for (let i = 0; i < m; i++) annotations.push(tok.nextPointer(0));
    return { n, views, m, annotations };
  },
  (d, pw, form) => {
    pw.writeInteger(d.views.length);
    for (const v of d.views) {
      pw.writePointer(v.view); pw.writeReal(v.x_origin); pw.writeReal(v.y_origin);
      if (form === 1) pw.writeReal(v.angle || 0);
    }
    pw.writeInteger(d.annotations.length);
    for (const p of d.annotations) pw.writePointer(p);
  }
);

// ──── §4.97 Property (Type 406) ────
registerEntity(406,
  (tok) => {
    // Each property value is a FieldValue tagged variant. The form
    // determines how many values; but since we don't know AVDT here,
    // read values as raw-typed based on the tokenizer peek.
    const np = tok.nextInteger(0);
    const values = [];
    for (let i = 0; i < np; i++) values.push(readFieldValue(tok));
    return { np, values };
  },
  (d, pw) => {
    pw.writeInteger(d.values.length);
    for (const v of d.values) writeFieldValue(pw, v);
  }
);

function readFieldValue(tok) {
  // The ref-impl models this as a discriminated union. Without a
  // schema hint we read as real by default; tests supply tagged
  // objects on write so roundtrip works.
  const f = tok._nextField();
  const raw = (f.kind === "raw") ? f.raw.trim() : "";
  if (f.kind === "hollerith") return { kind: "string", value: f.raw };
  if (raw === "") return { kind: "defaulted", value: null };
  if (/^[+-]?\d+$/.test(raw)) return { kind: "int", value: parseInt(raw, 10) };
  const num = Number(raw.replace(/[dD]/g, "e"));
  if (Number.isFinite(num)) return { kind: "real", value: num };
  return { kind: "string", value: raw };
}

function writeFieldValue(pw, v) {
  if (!v || typeof v !== "object" || !("kind" in v)) {
    throw new Error(`Property value must be a tagged FieldValue: ${JSON.stringify(v)}`);
  }
  switch (v.kind) {
    case "int": pw.writeInteger(v.value | 0); break;
    case "real": pw.writeReal(Number(v.value) || 0); break;
    case "string": pw.writeString(String(v.value || "")); break;
    case "bool": pw.writeLogical(Boolean(v.value)); break;
    case "defaulted": pw.parts.push(""); break;
    default: throw new Error(`unknown FieldValue kind: ${v.kind}`);
  }
}

// ──── §4.133 Subfigure Instance (Type 408) ────
registerEntity(408,
  (tok) => ({
    de: tok.nextPointer(0),
    translation: [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)],
    scale: tok.nextReal(1),
  }),
  (d, pw) => {
    pw.writePointer(d.de);
    pw.writeReal(d.translation[0]); pw.writeReal(d.translation[1]); pw.writeReal(d.translation[2]);
    pw.writeReal(d.scale != null ? d.scale : 1);
  }
);

// ──── §4.134 View (Type 410) ────
// Form 0: view_number, scale, then variable-length clip_plane pointers.
// Form 1 (perspective view, §4.135): view_number, scale, then the
// fixed-shape perspective-projection fields. Clip planes are NOT
// written for form 1; the field exists in the JSON schema for
// uniformity but is only populated for form 0.
registerEntity(410,
  (tok, form) => {
    const view_number = tok.nextInteger(0);
    const scale = tok.nextReal(1);
    const d = {
      form: form || 0, view_number, scale, clip_planes: [],
      view_plane_normal: [0, 0, 1],
      view_reference_point: [0, 0, 0],
      center_of_projection: [0, 0, 0],
      view_up_vector: [0, 1, 0],
      view_plane_distance: 0,
      umin: 0, umax: 0, vmin: 0, vmax: 0,
      depth_clipping: 0, wmin: 0, wmax: 0,
    };
    if (form === 1) {
      d.view_plane_normal = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
      d.view_reference_point = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
      d.center_of_projection = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
      d.view_up_vector = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
      d.view_plane_distance = tok.nextReal(0);
      d.umin = tok.nextReal(0); d.umax = tok.nextReal(0);
      d.vmin = tok.nextReal(0); d.vmax = tok.nextReal(0);
      d.depth_clipping = tok.nextInteger(0);
      d.wmin = tok.nextReal(0); d.wmax = tok.nextReal(0);
    } else {
      // Form 0: read remaining pointers until record end.
      while (!tok.atEnd()) d.clip_planes.push(tok.nextPointer(0));
    }
    return d;
  },
  (d, pw, form) => {
    pw.writeInteger(d.view_number); pw.writeReal(d.scale);
    if (form === 1) {
      for (const v of d.view_plane_normal) pw.writeReal(v);
      for (const v of d.view_reference_point) pw.writeReal(v);
      for (const v of d.center_of_projection) pw.writeReal(v);
      for (const v of d.view_up_vector) pw.writeReal(v);
      pw.writeReal(d.view_plane_distance);
      pw.writeReal(d.umin); pw.writeReal(d.umax);
      pw.writeReal(d.vmin); pw.writeReal(d.vmax);
      pw.writeInteger(d.depth_clipping);
      pw.writeReal(d.wmin); pw.writeReal(d.wmax);
    } else {
      for (const p of d.clip_planes) pw.writePointer(p);
    }
  }
);

// ──── §4.136 Rectangular Array (Type 412) ────
registerEntity(412,
  (tok) => {
    const de = tok.nextPointer(0);
    const s = tok.nextReal(1);
    const position = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
    const nc = tok.nextInteger(0);
    const nr = tok.nextInteger(0);
    const dx = tok.nextReal(0), dy = tok.nextReal(0);
    const ax = tok.nextReal(0);
    const lc = tok.nextInteger(0);
    const ddf = tok.nextInteger(0);
    const positions = [];
    for (let i = 0; i < lc; i++) positions.push(tok.nextInteger(0));
    return { de, s, position, nc, nr, dx, dy, ax, lc, ddf, positions };
  },
  (d, pw) => {
    pw.writePointer(d.de); pw.writeReal(d.s != null ? d.s : 1);
    pw.writeReal(d.position[0]); pw.writeReal(d.position[1]); pw.writeReal(d.position[2]);
    pw.writeInteger(d.nc); pw.writeInteger(d.nr);
    pw.writeReal(d.dx); pw.writeReal(d.dy); pw.writeReal(d.ax);
    pw.writeInteger(d.positions.length); pw.writeInteger(d.ddf || 0);
    for (const p of d.positions) pw.writeInteger(p);
  }
);

// ──── §4.137 Circular Array (Type 414) ────
registerEntity(414,
  (tok) => {
    const de = tok.nextPointer(0);
    const ne = tok.nextInteger(0);
    const center = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)];
    const r = tok.nextReal(0);
    const as_ = tok.nextReal(0);
    const ad = tok.nextReal(0);
    const lc = tok.nextInteger(0);
    const ddf = tok.nextInteger(0);
    const positions = [];
    for (let i = 0; i < lc; i++) positions.push(tok.nextInteger(0));
    return { de, ne, center, r, as: as_, ad, lc, ddf, positions };
  },
  (d, pw) => {
    pw.writePointer(d.de); pw.writeInteger(d.ne);
    pw.writeReal(d.center[0]); pw.writeReal(d.center[1]); pw.writeReal(d.center[2]);
    pw.writeReal(d.r); pw.writeReal(d.as); pw.writeReal(d.ad);
    pw.writeInteger(d.positions.length); pw.writeInteger(d.ddf || 0);
    for (const p of d.positions) pw.writeInteger(p);
  }
);

// ──── §4.138 External Reference (Type 416) ────
registerEntity(416,
  (tok, form) => {
    if (form === 1) return { filename: tok.nextString(""), entity_name: "" };
    if (form === 3) return { filename: "", entity_name: tok.nextString("") };
    if (form === 4) return { filename: tok.nextString(""), entity_name: tok.nextString("") };
    // Forms 0 and 2
    return { filename: tok.nextString(""), entity_name: tok.nextString("") };
  },
  (d, pw, form) => {
    if (form === 1) pw.writeString(d.filename || "");
    else if (form === 3) pw.writeString(d.entity_name || "");
    else if (form === 4) { pw.writeString(d.filename || ""); pw.writeString(d.entity_name || ""); }
    else { pw.writeString(d.filename || ""); pw.writeString(d.entity_name || ""); }
  }
);

// ──── §4.139 Nodal Load/Constraint (Type 418) ────
registerEntity(418,
  (tok) => {
    const nc = tok.nextInteger(0);
    const type = tok.nextInteger(0);
    const de = tok.nextPointer(0);
    const ptrs = [];
    for (let i = 0; i < nc; i++) ptrs.push(tok.nextPointer(0));
    return { nc, type, de, ptrs };
  },
  (d, pw) => {
    pw.writeInteger(d.nc); pw.writeInteger(d.type);
    pw.writePointer(d.de);
    for (const p of d.ptrs) pw.writePointer(p);
  }
);

// ──── §4.140 Network Subfigure Instance (Type 420) ────
registerEntity(420,
  (tok) => ({
    de: tok.nextPointer(0),
    x: tok.nextReal(0), y: tok.nextReal(0), z: tok.nextReal(0),
    xs: tok.nextReal(1),
    ys: tok.nextReal(1),
    zs: tok.nextReal(1),
    tf: tok.nextInteger(0),
    prd: tok.nextString(""),
    dptr: tok.nextPointer(0),
    nc: tok.nextInteger(0),
    cptrs: (() => {
      const cp = [];
      return cp;
    })(),
  }),
  // The above constructor pattern breaks for variable-length list:
  // rewrite more explicitly.
  null
);
// Re-register with explicit variable-length handling:
ENTITIES[420] = {
  parse: (tok) => {
    const de = tok.nextPointer(0);
    const x = tok.nextReal(0), y = tok.nextReal(0), z = tok.nextReal(0);
    const xs = tok.nextReal(1);
    const ys = tok.nextReal(1);
    const zs = tok.nextReal(1);
    const tf = tok.nextInteger(0);
    const prd = tok.nextString("");
    const dptr = tok.nextPointer(0);
    const nc = tok.nextInteger(0);
    const cptrs = [];
    for (let i = 0; i < nc; i++) cptrs.push(tok.nextPointer(0));
    return { de, x, y, z, xs, ys, zs, tf, prd, dptr, nc, cptrs };
  },
  write: (d, pw) => {
    pw.writePointer(d.de);
    pw.writeReal(d.x); pw.writeReal(d.y); pw.writeReal(d.z);
    pw.writeReal(d.xs != null ? d.xs : 1);
    pw.writeReal(d.ys != null ? d.ys : d.xs || 1);
    pw.writeReal(d.zs != null ? d.zs : d.xs || 1);
    pw.writeInteger(d.tf); pw.writeString(d.prd || "");
    pw.writePointer(d.dptr || 0);
    pw.writeInteger(d.cptrs.length);
    for (const p of d.cptrs) pw.writePointer(p);
  },
};

// ──── §4.142 Solid Instance (Type 430) ────
registerEntity(430,
  (tok) => ({ ptr: tok.nextPointer(0) }),
  (d, pw) => { pw.writePointer(d.ptr); }
);

// ──── §4.143.1 Vertex List (Type 502) ────
registerEntity(502,
  (tok) => {
    const n = tok.nextInteger(0);
    const vertices = [];
    for (let i = 0; i < n; i++) {
      vertices.push([tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]);
    }
    return { n, vertices };
  },
  (d, pw) => {
    pw.writeInteger(d.vertices.length);
    for (const v of d.vertices) { pw.writeReal(v[0]); pw.writeReal(v[1]); pw.writeReal(v[2]); }
  }
);

// ──── §4.144.1 Edge List (Type 504) ────
registerEntity(504,
  (tok) => {
    const n = tok.nextInteger(0);
    const edges = [];
    for (let i = 0; i < n; i++) {
      edges.push({
        curve: tok.nextPointer(0),
        svp: tok.nextPointer(0), sv: tok.nextInteger(0),
        tvp: tok.nextPointer(0), tv: tok.nextInteger(0),
      });
    }
    return { n, edges };
  },
  (d, pw) => {
    pw.writeInteger(d.edges.length);
    for (const e of d.edges) {
      pw.writePointer(e.curve);
      pw.writePointer(e.svp); pw.writeInteger(e.sv);
      pw.writePointer(e.tvp); pw.writeInteger(e.tv);
    }
  }
);

// ──── §4.145 Loop (Type 508) ────
registerEntity(508,
  (tok) => {
    const n = tok.nextInteger(0);
    const edge_uses = [];
    for (let i = 0; i < n; i++) {
      const type = tok.nextInteger(0);
      const edge = tok.nextPointer(0);
      const ndx = tok.nextInteger(0);
      const orientation = tok.nextLogical(false);
      const k = tok.nextInteger(0);
      const param_curves = [];
      for (let j = 0; j < k; j++) {
        param_curves.push({
          isoparametric: tok.nextLogical(false),
          curve: tok.nextPointer(0),
        });
      }
      edge_uses.push({ type, edge, ndx, orientation, k, param_curves });
    }
    return { n, edge_uses };
  },
  (d, pw) => {
    pw.writeInteger(d.edge_uses.length);
    for (const eu of d.edge_uses) {
      pw.writeInteger(eu.type); pw.writePointer(eu.edge);
      pw.writeInteger(eu.ndx); pw.writeLogical(eu.orientation);
      pw.writeInteger(eu.param_curves.length);
      for (const pc of eu.param_curves) {
        pw.writeLogical(pc.isoparametric); pw.writePointer(pc.curve);
      }
    }
  }
);

// ──── §4.146 Face (Type 510) ────
registerEntity(510,
  (tok) => {
    const surf = tok.nextPointer(0);
    const n = tok.nextInteger(0);
    const outer_loop_flag = tok.nextLogical(false);
    const loops = [];
    for (let i = 0; i < n; i++) loops.push(tok.nextPointer(0));
    return { surf, n, outer_loop_flag, loops };
  },
  (d, pw) => {
    pw.writePointer(d.surf);
    pw.writeInteger(d.loops.length);
    pw.writeLogical(d.outer_loop_flag);
    for (const p of d.loops) pw.writePointer(p);
  }
);

// ──── §4.147 Shell (Type 514) ────
registerEntity(514,
  (tok) => {
    const n = tok.nextInteger(0);
    const faces = [];
    for (let i = 0; i < n; i++) {
      faces.push({ face: tok.nextPointer(0), orientation: tok.nextLogical(false) });
    }
    return { n, faces };
  },
  (d, pw) => {
    pw.writeInteger(d.faces.length);
    for (const f of d.faces) { pw.writePointer(f.face); pw.writeLogical(f.orientation); }
  }
);

// ──────────────────────────────────────────────────────────────────────────
// Entity dispatch
// ──────────────────────────────────────────────────────────────────────────

function parseEntity(type, form, pdString, pd, rd) {
  const reg = ENTITIES[type];
  if (!reg) {
    throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
      `Unsupported entity type: ${type}`, "§3.2"));
  }
  const tok = new ParamTokenizer(pdString, pd, rd);
  // First field of PD is the entity type itself.
  const firstType = tok.nextInteger(type);
  if (firstType !== type) {
    // Mismatch between DE type and PD type — continue with DE as truth.
  }
  return reg.parse(tok, form);
}

function writeEntity(type, form, data, pd, rd) {
  const reg = ENTITIES[type];
  if (!reg) {
    throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
      `Unsupported entity type: ${type}`, "§3.2"));
  }
  const pw = ParamWriter.forEntity(type, pd, rd);
  reg.write(data, pw, form);
  return pw.build();
}

// ──────────────────────────────────────────────────────────────────────────
// Canonical JSON envelope: build from IgesFile, build from JSON
// ──────────────────────────────────────────────────────────────────────────

function deToJson(de) {
  return {
    entity_type: de.entity_type,
    param_data_ptr: de.param_data_ptr || 0,
    structure: de.structure || 0,
    line_font: de.line_font || 0,
    level: de.level || 0,
    view: de.view || 0,
    xform_matrix: de.xform_matrix || 0,
    label_display: de.label_display || 0,
    status: de.status,
    line_weight: de.line_weight || 0,
    color: de.color || 0,
    param_line_count: de.param_line_count || 0,
    form: de.form || 0,
    entity_label: de.entity_label || "",
    entity_subscript: de.entity_subscript || 0,
  };
}

function deFromJson(j) {
  return {
    entity_type: j.entity_type | 0,
    param_data_ptr: j.param_data_ptr | 0,
    structure: j.structure | 0,
    line_font: j.line_font | 0,
    level: j.level | 0,
    view: j.view | 0,
    xform_matrix: j.xform_matrix | 0,
    label_display: j.label_display | 0,
    status: j.status || {
      blank: "visible",
      subordinate: "independent",
      entity_use: "geometry",
      hierarchy: "global_top_down",
    },
    line_weight: j.line_weight | 0,
    color: j.color | 0,
    param_line_count: j.param_line_count | 0,
    form: j.form | 0,
    entity_label: j.entity_label || "",
    entity_subscript: j.entity_subscript | 0,
  };
}

function buildCanonicalJson(igesFile) {
  const entities = [];
  const pd = igesFile.global.param_delimiter || ",";
  const rd = igesFile.global.record_delimiter || ";";
  for (let i = 0; i < igesFile.entities.length; i++) {
    const raw = igesFile.entities[i];
    const type = raw.de.entity_type;
    const form = raw.de.form;
    const data = parseEntity(type, form, raw.pd_string, pd, rd);
    entities.push({
      de_index: 2 * i + 1,
      directory_entry: deToJson(raw.de),
      entity: { type, form, data },
    });
  }
  return {
    start_lines: igesFile.start_lines,
    global: igesFile.global,
    entities,
  };
}

function buildIgesFromCanonicalJson(j) {
  const startLines = j.start_lines || [];
  const global = j.global;
  const entities = [];
  const pd = global.param_delimiter || ",";
  const rd = global.record_delimiter || ";";
  const arr = j.entities || [];
  if (!Array.isArray(arr)) {
    throw new IgesError(makeDiag("error", 0, SECTION.UNKNOWN,
      "'entities' must be an array", "§2.1"));
  }
  for (const e of arr) {
    const de = deFromJson(e.directory_entry || {});
    const type = e.entity.type | 0;
    const form = e.entity.form | 0;
    de.entity_type = type;
    de.form = form;
    const pdString = writeEntity(type, form, e.entity.data, pd, rd);
    entities.push({ de, pd_string: pdString });
  }
  return { start_lines: startLines, global, entities };
}

// ──────────────────────────────────────────────────────────────────────────
// Validation
// ──────────────────────────────────────────────────────────────────────────

function validateSharedDe(igesFile, validDeSeqs) {
  const diags = [];
  for (let i = 0; i < igesFile.entities.length; i++) {
    const ent = igesFile.entities[i];
    const deSeq = 2 * i + 1;
    const t = ent.de.entity_type;
    if (t < 0) {
      diags.push(makeDiag("error", 0, SECTION.DIRECTORY,
        `DE ${deSeq} has negative entity type ${t}`, "§2.2.4.4"));
    }
    if (ent.de.xform_matrix && !validDeSeqs.has(ent.de.xform_matrix)) {
      diags.push(makeDiag("error", 0, SECTION.DIRECTORY,
        `DE ${deSeq} xform_matrix points to non-existent DE ${ent.de.xform_matrix}`, "§2.2.4.4"));
    }
    if (ent.de.view && !validDeSeqs.has(ent.de.view)) {
      diags.push(makeDiag("error", 0, SECTION.DIRECTORY,
        `DE ${deSeq} view points to non-existent DE ${ent.de.view}`, "§2.2.4.4"));
    }
    if (ent.de.label_display && !validDeSeqs.has(ent.de.label_display)) {
      diags.push(makeDiag("error", 0, SECTION.DIRECTORY,
        `DE ${deSeq} label_display points to non-existent DE ${ent.de.label_display}`, "§2.2.4.4"));
    }
  }
  return diags;
}

function validateGlobal(g) {
  const diags = [];
  if ((g.integer_bits | 0) <= 0) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 7 (integer_bits) is not positive", "§2.2.4.3"));
  if ((g.sp_magnitude | 0) <= 0) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 8 (sp_magnitude) is not positive", "§2.2.4.3"));
  if ((g.sp_significance | 0) <= 0) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 9 (sp_significance) is not positive", "§2.2.4.3"));
  if ((g.dp_magnitude | 0) <= 0) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 10 (dp_magnitude) is not positive", "§2.2.4.3"));
  if ((g.dp_significance | 0) <= 0) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 11 (dp_significance) is not positive", "§2.2.4.3"));
  if (!(g.model_space_scale > 0)) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 13 (model_space_scale) is not positive", "§2.2.4.3"));
  if ((g.max_line_weight_grads | 0) <= 0) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 16 (max_line_weight_grads) is not positive", "§2.2.4.3"));
  if (!(g.min_resolution > 0)) diags.push(makeDiag("error", 0, SECTION.GLOBAL,
    "Global field 19 (min_resolution) is not positive", "§2.2.4.3"));
  return diags;
}

function validate(igesFile) {
  const diags = [];
  const validDeSeqs = new Set();
  for (let i = 0; i < igesFile.entities.length; i++) validDeSeqs.add(2 * i + 1);
  diags.push(...validateSharedDe(igesFile, validDeSeqs));
  for (let i = 0; i < igesFile.entities.length; i++) {
    const ent = igesFile.entities[i];
    const deSeq = 2 * i + 1;
    if (ent.de.param_line_count <= 0 && ent.de.entity_type !== 0) {
      diags.push(makeDiag("error", 0, SECTION.DIRECTORY,
        `DE ${deSeq} param_line_count is ${ent.de.param_line_count} for non-null entity type ${ent.de.entity_type}`,
        "§2.2.4.4"));
    }
    if ((!ent.pd_string || ent.pd_string.length === 0) && ent.de.entity_type !== 0) {
      diags.push(makeDiag("error", 0, SECTION.PARAMETER,
        `DE ${deSeq} has empty parameter data for entity type ${ent.de.entity_type}`,
        "§2.2.4.5"));
    }
  }
  diags.push(...validateGlobal(igesFile.global));
  return diags;
}

function validateWriteInput(igesFile) {
  const diags = [];
  const validDeSeqs = new Set();
  for (let i = 0; i < igesFile.entities.length; i++) validDeSeqs.add(2 * i + 1);
  diags.push(...validateSharedDe(igesFile, validDeSeqs));
  diags.push(...validateGlobal(igesFile.global));
  return diags;
}

// ──────────────────────────────────────────────────────────────────────────
// Eval dispatch
// ──────────────────────────────────────────────────────────────────────────

const CURVE_TYPES = new Set([100, 102, 104, 106, 110, 112, 126, 130]);
const SURFACE_TYPES = new Set([114, 118, 120, 122, 128, 140, 190, 192, 194, 196, 198]);

function isCurveForEval(type, form) {
  if (CURVE_TYPES.has(type)) {
    if (type === 106) return form === 11 || form === 12 || form === 63;
    return true;
  }
  return false;
}

function isSurfaceForEval(type) {
  return SURFACE_TYPES.has(type);
}

function vecAdd(a, b) { return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function vecSub(a, b) { return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function vecScale(a, s) { return [a[0]*s, a[1]*s, a[2]*s]; }
function vecDot(a, b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
function vecCross(a, b) {
  return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
}
function vecNorm(a) {
  const m = Math.sqrt(vecDot(a, a));
  if (m === 0) return [0, 0, 0];
  return [a[0]/m, a[1]/m, a[2]/m];
}
function matVec(R, v) {
  return [
    R[0][0]*v[0] + R[0][1]*v[1] + R[0][2]*v[2],
    R[1][0]*v[0] + R[1][1]*v[1] + R[1][2]*v[2],
    R[2][0]*v[0] + R[2][1]*v[1] + R[2][2]*v[2],
  ];
}

// Resolve an entity by DE index. Returns { type, form, xform_de, data } or null.
function makeResolver(canonical) {
  const byDe = new Map();
  for (const rec of canonical.entities) {
    byDe.set(rec.de_index, {
      type: rec.entity.type,
      form: rec.entity.form,
      xform_de: rec.directory_entry.xform_matrix || 0,
      data: rec.entity.data,
    });
  }
  return (de) => byDe.get(de) || null;
}

function sampleCurvePoint(ent, t, resolver) {
  return evaluateEntity(ent.type, ent.form, ent.xform_de, ent.data, t, null, resolver, /*noXform=*/true).point;
}

function curveNativeSpan(type, form, data) {
  switch (type) {
    case 100: {
      const sa = Math.atan2(data.y2 - data.y1, data.x2 - data.x1);
      let ta = Math.atan2(data.y3 - data.y1, data.x3 - data.x1);
      if (ta <= sa) ta += 2 * Math.PI;
      return [sa, ta];
    }
    case 104: return [data.x1, data.x2]; // rough placeholder — varies by form
    case 106: return [0, data.n - 1];
    case 110: return [0, 1];
    case 112: {
      const b = data.breakpoints;
      return [b[0], b[b.length - 1]];
    }
    case 126: return [data.v0, data.v1];
    case 130: return [data.tt1, data.tt2];
    case 102: {
      // Composite: sum native spans of constituent curves.
      // Handled by the composite evaluator directly.
      return [0, 1];
    }
    default: return [0, 1];
  }
}

function applyXform(point, xformDe, resolver) {
  if (!xformDe) return point;
  const m = resolver(xformDe);
  if (!m || m.type !== 124) return point;
  return vecAdd(matVec(m.data.rotation, point), m.data.translation);
}

function evaluateEntity(type, form, xformDe, data, t, s, resolver, noXform = false) {
  let point = null;
  switch (type) {
    case 110: {
      const p1 = data.start, p2 = data.terminate;
      point = vecAdd(p1, vecScale(vecSub(p2, p1), t));
      break;
    }
    case 100: {
      const r = Math.sqrt((data.x2 - data.x1) ** 2 + (data.y2 - data.y1) ** 2);
      point = [data.x1 + r * Math.cos(t), data.y1 + r * Math.sin(t), data.zt];
      break;
    }
    case 104: {
      if (form === 1) {
        const a = Math.sqrt(-data.F / data.A);
        const b = Math.sqrt(-data.F / data.C);
        point = [a * Math.cos(t), b * Math.sin(t), data.zt];
      } else if (form === 2) {
        let a, b;
        if (data.F * data.A < 0 && data.F * data.C > 0) {
          a = Math.sqrt(-data.F / data.A);
          b = Math.sqrt(data.F / data.C);
          point = [a / Math.cos(t), b * Math.tan(t), data.zt];
        } else {
          a = Math.sqrt(data.F / data.A);
          b = Math.sqrt(-data.F / data.C);
          point = [a * Math.tan(t), b / Math.cos(t), data.zt];
        }
      } else if (form === 3) {
        // Parabola: C(t) = (t, -(A/E) t^2, zT) per §4.5
        const ratio = data.A / data.E;
        point = [t, -ratio * t * t, data.zt];
      } else {
        throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
          `Conic Arc form ${form} not supported by eval`, "§4.5"));
      }
      break;
    }
    case 106: {
      // Forms 11/12/63: piecewise linear. t ∈ [0, N-1].
      const n = data.n;
      const idxFloat = Math.max(0, Math.min(n - 1, t));
      const i = Math.max(0, Math.min(n - 2, Math.floor(idxFloat)));
      const frac = idxFloat - i;
      const pa = sampleCopiousTuple(data, i);
      const pb = sampleCopiousTuple(data, i + 1);
      point = [
        pa[0] + frac * (pb[0] - pa[0]),
        pa[1] + frac * (pb[1] - pa[1]),
        pa[2] + frac * (pb[2] - pa[2]),
      ];
      break;
    }
    case 102: {
      // Composite: accumulate spans of constituent curves.
      const parts = data.constituents.map((de) => resolver(de));
      const spans = [];
      let total = 0;
      for (const p of parts) {
        if (!p) continue;
        if (p.type === 116 || p.type === 132) { spans.push({ part: p, span: [0, 0] }); continue; }
        const sp = curveNativeSpan(p.type, p.form, p.data);
        spans.push({ part: p, span: sp });
        total += sp[1] - sp[0];
      }
      // Find which constituent contains t.
      let acc = 0;
      let chosen = null;
      let local = t;
      for (const entry of spans) {
        const w = entry.span[1] - entry.span[0];
        if (t <= acc + w + 1e-12) { chosen = entry; local = t - acc + entry.span[0]; break; }
        acc += w;
      }
      if (!chosen) {
        const last = spans[spans.length - 1];
        chosen = last; local = last.span[1];
      }
      const childRes = evaluateEntity(
        chosen.part.type, chosen.part.form, chosen.part.xform_de,
        chosen.part.data, local, null, resolver, false
      );
      point = childRes.point;
      break;
    }
    case 112: {
      const b = data.breakpoints;
      const seg = data.segments;
      let i = 0;
      while (i < seg.length - 1 && t > b[i + 1]) i++;
      const s = t - b[i];
      const sg = seg[i];
      point = [
        sg.ax + sg.bx * s + sg.cx * s * s + sg.dx * s * s * s,
        sg.ay + sg.by * s + sg.cy * s * s + sg.dy * s * s * s,
        sg.az + sg.bz * s + sg.cz * s * s + sg.dz * s * s * s,
      ];
      break;
    }
    case 126: {
      // Rational B-Spline Curve — Cox-de Boor with weights.
      point = bsplineCurvePoint(data, t);
      break;
    }
    case 128: {
      point = bsplineSurfacePoint(data, t, s);
      break;
    }
    case 130: {
      // Offset Curve FLAG=1: O(t) = r(t) + d1 * (vx,vy,vz) (ref-impl convention)
      const base = resolver(data.de1);
      if (!base) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
        `Offset Curve has invalid base curve DE pointer ${data.de1}`, "§4.25"));
      if (data.flag !== 1) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
        `Offset Curve evaluator supports only FLAG=1 (uniform offset); got FLAG=${data.flag}`,
        "§4.25"));
      const basePt = sampleCurvePoint(base, t, resolver);
      point = [
        basePt[0] + data.d1 * data.vx,
        basePt[1] + data.d1 * data.vy,
        basePt[2] + data.d1 * data.vz,
      ];
      break;
    }
    case 114: {
      point = splineSurfacePoint(data, t, s);
      break;
    }
    case 118: {
      point = ruledSurfacePoint(data, form, t, s, resolver);
      break;
    }
    case 120: {
      point = surfaceOfRevolutionPoint(data, t, s, resolver);
      break;
    }
    case 122: {
      point = tabulatedCylinderPoint(data, t, s, resolver);
      break;
    }
    case 140: {
      point = offsetSurfacePoint(data, t, s, resolver);
      break;
    }
    case 190: case 192: case 194: case 196: case 198: {
      point = analyticSurfacePoint(type, form, data, t, s, resolver);
      break;
    }
    default:
      throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
        `entity type ${type} is not parametric for iges eval`, "§1.5"));
  }
  if (!noXform) point = applyXform(point, xformDe, resolver);
  return { point };
}

function sampleCopiousTuple(data, i) {
  if (data.ip === 1) {
    return [data.data[i * 2], data.data[i * 2 + 1], data.zt];
  }
  if (data.ip === 2) {
    return [data.data[i * 3], data.data[i * 3 + 1], data.data[i * 3 + 2]];
  }
  return [data.data[i * 6], data.data[i * 6 + 1], data.data[i * 6 + 2]];
}

// Cox-de Boor basis
function bsplineBasis(t, knots, m, i) {
  // Compute N_{i,m}(t) using the recursive definition.
  // Start with N_{j,0}(t) for j around i-m..i.
  const n = knots.length - 1;
  const N = new Array(m + 1);
  for (let j = 0; j <= m; j++) {
    const idx = i + j;
    N[j] = (knots[idx] <= t && t < knots[idx + 1]) ? 1 : 0;
    // Handle the right-endpoint edge: at t = last knot, make basis 1 for the last span.
    if (idx === n - 1 && t === knots[n]) N[j] = 1;
  }
  for (let k = 1; k <= m; k++) {
    for (let j = 0; j <= m - k; j++) {
      const idx = i + j;
      const denom1 = knots[idx + k] - knots[idx];
      const denom2 = knots[idx + k + 1] - knots[idx + 1];
      const a = denom1 !== 0 ? (t - knots[idx]) / denom1 * N[j] : 0;
      const b = denom2 !== 0 ? (knots[idx + k + 1] - t) / denom2 * N[j + 1] : 0;
      N[j] = a + b;
    }
  }
  return N[0];
}

function bsplineCurvePoint(d, t) {
  const K = d.K, M = d.M;
  const knots = d.knots;
  const weights = d.weights;
  const controls = d.control_points;
  // Clamp t to [v0, v1].
  if (t < d.v0) t = d.v0;
  if (t > d.v1) t = d.v1;
  let num = [0, 0, 0];
  let den = 0;
  for (let i = 0; i <= K; i++) {
    const b = bsplineBasis(t, knots, M, i);
    const w = weights[i] * b;
    num = vecAdd(num, vecScale(controls[i], w));
    den += w;
  }
  if (den === 0) return [0, 0, 0];
  return [num[0] / den, num[1] / den, num[2] / den];
}

function bsplineSurfacePoint(d, u, v) {
  const K1 = d.K1, K2 = d.K2, M1 = d.M1, M2 = d.M2;
  const kU = d.knots_u, kV = d.knots_v;
  const weights = d.weights;
  const controls = d.control_points;
  if (u < d.u0) u = d.u0;
  if (u > d.u1) u = d.u1;
  if (v < d.v0) v = d.v0;
  if (v > d.v1) v = d.v1;
  let num = [0, 0, 0];
  let den = 0;
  for (let i = 0; i <= K1; i++) {
    const bi = bsplineBasis(u, kU, M1, i);
    for (let j = 0; j <= K2; j++) {
      const bj = bsplineBasis(v, kV, M2, j);
      const idx = i * (K2 + 1) + j;
      const w = weights[idx] * bi * bj;
      num = vecAdd(num, vecScale(controls[idx], w));
      den += w;
    }
  }
  if (den === 0) return [0, 0, 0];
  return [num[0] / den, num[1] / den, num[2] / den];
}

function splineSurfacePoint(d, u, v) {
  // Find patch index (i, j)
  let pi = 0, pj = 0;
  for (let i = 0; i < d.M; i++) {
    if (u >= d.tu[i] && (i === d.M - 1 || u <= d.tu[i + 1])) { pi = i; break; }
  }
  for (let j = 0; j < d.N; j++) {
    if (v >= d.tv[j] && (j === d.N - 1 || v <= d.tv[j + 1])) { pj = j; break; }
  }
  const sLocal = u - d.tu[pi];
  const tLocal = v - d.tv[pj];
  const patch = d.patches[pi * d.N + pj];
  let x = 0, y = 0, z = 0;
  for (let p = 0; p < 4; p++) {
    const tp = Math.pow(tLocal, p);
    for (let q = 0; q < 4; q++) {
      const sq = Math.pow(sLocal, q);
      const idx = 4 * p + q;
      x += patch.coeff_x[idx] * sq * tp;
      y += patch.coeff_y[idx] * sq * tp;
      z += patch.coeff_z[idx] * sq * tp;
    }
  }
  return [x, y, z];
}

function ruledSurfacePoint(d, form, t, s, resolver) {
  const c1 = resolver(d.de1);
  const c2 = resolver(d.de2);
  if (!c1 || !c2) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
    "Ruled Surface has invalid DE pointer for de1 or de2", "§4.17"));
  let u1 = 0, u2 = 0;
  if (form === 0) {
    const sp1 = curveNativeSpan(c1.type, c1.form, c1.data);
    const sp2 = curveNativeSpan(c2.type, c2.form, c2.data);
    u1 = sp1[0] + t * (sp1[1] - sp1[0]);
    u2 = (d.dirflg === 1)
      ? sp2[1] + t * (sp2[0] - sp2[1])
      : sp2[0] + t * (sp2[1] - sp2[0]);
  } else {
    u1 = t; u2 = (d.dirflg === 1) ? -t : t;
  }
  const p1 = sampleCurvePoint(c1, u1, resolver);
  const p2 = sampleCurvePoint(c2, u2, resolver);
  return [
    (1 - s) * p1[0] + s * p2[0],
    (1 - s) * p1[1] + s * p2[1],
    (1 - s) * p1[2] + s * p2[2],
  ];
}

function surfaceOfRevolutionPoint(d, t, s, resolver) {
  const axisL = resolver(d.l);
  const gen = resolver(d.c);
  if (!axisL || !gen) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
    "Surface of Revolution has invalid DE pointer", "§4.18"));
  // Axis: from line start to line terminate. Axis direction is terminate - start (per §4.18).
  const axStart = axisL.data.start;
  const axEnd = axisL.data.terminate;
  const axis = vecNorm(vecSub(axEnd, axStart));
  const generatorPt = sampleCurvePoint(gen, t, resolver);
  // Rotate generatorPt around (axStart, axis) by angle s (in radians).
  return rotateAroundAxis(generatorPt, axStart, axis, s);
}

function rotateAroundAxis(p, origin, axis, theta) {
  // Rodrigues' rotation formula.
  const v = vecSub(p, origin);
  const c = Math.cos(theta);
  const si = Math.sin(theta);
  const k = axis;
  const term1 = vecScale(v, c);
  const term2 = vecScale(vecCross(k, v), si);
  const term3 = vecScale(k, vecDot(k, v) * (1 - c));
  const rotated = vecAdd(vecAdd(term1, term2), term3);
  return vecAdd(origin, rotated);
}

function tabulatedCylinderPoint(d, t, s, resolver) {
  const directrix = resolver(d.de);
  if (!directrix) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
    "Tabulated Cylinder has invalid directrix DE pointer", "§4.19"));
  const sp = curveNativeSpan(directrix.type, directrix.form, directrix.data);
  const startPt = sampleCurvePoint(directrix, sp[0], resolver);
  const dirPt = sampleCurvePoint(directrix, t, resolver);
  const gen = vecSub(d.terminate_point, startPt);
  return vecAdd(dirPt, vecScale(gen, s));
}

function offsetSurfacePoint(d, t, s, resolver) {
  const base = resolver(d.de);
  if (!base) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
    `Offset Surface has invalid base surface DE pointer ${d.de}`, "§4.30"));
  const basePt = evaluateEntity(base.type, base.form, base.xform_de, base.data, t, s, resolver, true).point;
  // Prefer an analytical normal; fall back to central differences for
  // surfaces where we don't have a closed-form normal.
  let n = surfaceNormal(base.type, base.form, base.data, t, s, resolver);
  if (!n) n = numericalSurfaceNormal(base.type, base.form, base.xform_de, base.data, t, s, resolver);
  const indicator = [d.nx, d.ny, d.nz];
  const refParams = surfaceRefParams(base.type, base.form, base.data, resolver);
  let nR = surfaceNormal(base.type, base.form, base.data, refParams.u, refParams.v, resolver);
  if (!nR) nR = numericalSurfaceNormal(base.type, base.form, base.xform_de, base.data, refParams.u, refParams.v, resolver);
  if (nR && vecDot(nR, indicator) < 0) {
    n = vecScale(n, -1);
  }
  return vecAdd(basePt, vecScale(n, d.d));
}

function numericalSurfaceNormal(type, form, xformDe, data, u, v, resolver) {
  const eps = 1e-4;
  const p = evaluateEntity(type, form, xformDe, data, u, v, resolver, true).point;
  const pu = evaluateEntity(type, form, xformDe, data, u + eps, v, resolver, true).point;
  const pv = evaluateEntity(type, form, xformDe, data, u, v + eps, resolver, true).point;
  return vecNorm(vecCross(vecSub(pu, p), vecSub(pv, p)));
}

// Analytical surface-normal computations for the analytic surface
// types defined in §§4.50–4.54. Returns null for surface types that
// don't have a closed-form normal implemented here (ruled, swept,
// spline surfaces) — callers fall back to numerical differentiation.
function surfaceNormal(type, form, data, u, v, resolver) {
  if (type === 190 || type === 192 || type === 194 || type === 196 || type === 198) {
    const basis = analyticSurfaceBasis(type, form, data, resolver);
    if (!basis) return null;
    const { x, y, z } = basis;
    const dr = (a) => a * Math.PI / 180;
    if (type === 190) return z;
    if (type === 192) {
      const uR = dr(u);
      return vecAdd(vecScale(x, Math.cos(uR)), vecScale(y, Math.sin(uR)));
    }
    if (type === 194) {
      const uR = dr(u);
      const sR = dr(data.sangle);
      const radial = vecAdd(vecScale(x, Math.cos(uR)), vecScale(y, Math.sin(uR)));
      // Outward normal: cos(s)*radial - sin(s)*z.
      const c = Math.cos(sR), si = Math.sin(sR);
      return vecNorm(vecSub(vecScale(radial, c), vecScale(z, si)));
    }
    if (type === 196) {
      const uR = dr(u);
      const vR = dr(v);
      const horiz = vecAdd(vecScale(x, Math.cos(uR)), vecScale(y, Math.sin(uR)));
      return vecAdd(vecScale(horiz, Math.cos(vR)), vecScale(z, Math.sin(vR)));
    }
    if (type === 198) {
      const uR = dr(u);
      const vR = dr(v);
      // Normal at (u, v) points outward from the minor-circle center:
      // cos(u)*(cos(v)*x - sin(v)*y) + sin(u)*z.
      const horiz = vecAdd(vecScale(x, Math.cos(vR)), vecScale(y, -Math.sin(vR)));
      return vecAdd(vecScale(horiz, Math.cos(uR)), vecScale(z, Math.sin(uR)));
    }
  }
  return null;
}

function surfaceRefParams(type, form, data, resolver) {
  // Mirror the C++ ref-impl's `surface_reference_parameters`.
  switch (type) {
    case 114: {
      const tu = data.tu, tv = data.tv;
      return { u: 0.5 * (tu[0] + tu[tu.length - 1]),
               v: 0.5 * (tv[0] + tv[tv.length - 1]) };
    }
    case 118:
      if (form === 1) {
        const c1 = resolver ? resolver(data.de1) : null;
        if (c1) {
          const sp = curveNativeSpan(c1.type, c1.form, c1.data);
          return { u: 0.5 * (sp[0] + sp[1]), v: 0.5 };
        }
      }
      return { u: 0.5, v: 0.5 };
    case 120: {
      const c = resolver ? resolver(data.c) : null;
      if (c) {
        const sp = curveNativeSpan(c.type, c.form, c.data);
        return { u: 0.5 * (sp[0] + sp[1]), v: 0.5 * (data.sa + data.ta) };
      }
      return { u: 0, v: 0 };
    }
    case 122: {
      const d = resolver ? resolver(data.de) : null;
      if (d) {
        const sp = curveNativeSpan(d.type, d.form, d.data);
        return { u: 0.5 * (sp[0] + sp[1]), v: 0.5 };
      }
      return { u: 0, v: 0.5 };
    }
    case 128:
      return { u: 0.5 * (data.u0 + data.u1), v: 0.5 * (data.v0 + data.v1) };
    case 140: {
      const base = resolver ? resolver(data.de) : null;
      if (base) return surfaceRefParams(base.type, base.form, base.data, resolver);
      return { u: 0, v: 0 };
    }
    case 190: case 192: case 194: case 196: case 198:
      return { u: 0, v: 0 };
    default: return { u: 0, v: 0 };
  }
}

function analyticSurfaceBasis(type, form, data, resolver) {
  // Build {C, x, y, z, extra} basis for analytic surface types.
  const deloc = resolver(data.deloc);
  if (!deloc) return null;
  const C = deloc.data.coords || [0, 0, 0];
  if (type === 190) {
    const denrml = resolver(data.denrml);
    const derefd = data.derefd ? resolver(data.derefd) : null;
    if (!denrml) return null;
    const z = vecNorm([denrml.data.x, denrml.data.y, denrml.data.z]);
    let x;
    if (derefd) {
      const d = [derefd.data.x, derefd.data.y, derefd.data.z];
      x = vecNorm(vecSub(d, vecScale(z, vecDot(d, z))));
    } else {
      x = [1, 0, 0];
    }
    const y = vecCross(z, x);
    return { C, x, y, z };
  }
  // For 192/194/198: deaxis + derefd.
  if (type === 192 || type === 194 || type === 198) {
    const deaxis = resolver(data.deaxis);
    const derefd = data.derefd ? resolver(data.derefd) : null;
    if (!deaxis) return null;
    const z = vecNorm([deaxis.data.x, deaxis.data.y, deaxis.data.z]);
    let x;
    if (derefd) {
      const d = [derefd.data.x, derefd.data.y, derefd.data.z];
      x = vecNorm(vecSub(d, vecScale(z, vecDot(d, z))));
    } else {
      x = [1, 0, 0];
    }
    const y = vecCross(z, x);
    return { C, x, y, z };
  }
  // 196 form 1: deaxis + derefd.
  if (type === 196 && form === 1) {
    const deaxis = resolver(data.deaxis);
    const derefd = data.derefd ? resolver(data.derefd) : null;
    if (!deaxis) return null;
    const z = vecNorm([deaxis.data.x, deaxis.data.y, deaxis.data.z]);
    let x;
    if (derefd) {
      const d = [derefd.data.x, derefd.data.y, derefd.data.z];
      x = vecNorm(vecSub(d, vecScale(z, vecDot(d, z))));
    } else {
      x = [1, 0, 0];
    }
    const y = vecCross(z, x);
    return { C, x, y, z };
  }
  return null;
}

function analyticSurfacePoint(type, form, data, u, v, resolver) {
  const basis = analyticSurfaceBasis(type, form, data, resolver);
  if (!basis) throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
    `Analytic surface type ${type} is missing required references`, "§§4.50-4.54"));
  const { C, x, y, z } = basis;
  const dr = (a) => a * Math.PI / 180; // degrees → radians
  if (type === 190) {
    return vecAdd(C, vecAdd(vecScale(x, u), vecScale(y, v)));
  }
  if (type === 192) {
    const uR = dr(u);
    const r = data.radius;
    const radial = vecAdd(vecScale(x, r * Math.cos(uR)), vecScale(y, r * Math.sin(uR)));
    return vecAdd(C, vecAdd(radial, vecScale(z, v)));
  }
  if (type === 194) {
    const uR = dr(u);
    const sR = dr(data.sangle);
    const r = data.radius + v * Math.tan(sR);
    const radial = vecAdd(vecScale(x, r * Math.cos(uR)), vecScale(y, r * Math.sin(uR)));
    return vecAdd(C, vecAdd(radial, vecScale(z, v)));
  }
  if (type === 196) {
    const uR = dr(u);
    const vR = dr(v);
    const r = data.radius;
    const horiz = vecAdd(vecScale(x, Math.cos(uR)), vecScale(y, Math.sin(uR)));
    const radial = vecScale(horiz, r * Math.cos(vR));
    return vecAdd(C, vecAdd(radial, vecScale(z, r * Math.sin(vR))));
  }
  if (type === 198) {
    const uR = dr(u);
    const vR = dr(v);
    const R = data.majrad;
    const r = data.minrad;
    const coeff = R + r * Math.cos(uR);
    // From §4.54: σ(u,v) = C + (R + r cos u)(cos v · x - sin v · y) + r sin u · z
    const horiz = vecAdd(vecScale(x, Math.cos(vR)), vecScale(y, -Math.sin(vR)));
    return vecAdd(C, vecAdd(vecScale(horiz, coeff), vecScale(z, r * Math.sin(uR))));
  }
  throw new IgesError(makeDiag("error", 0, SECTION.PARAMETER,
    `Unsupported analytic surface type ${type}`, "§§4.50-4.54"));
}

// ──────────────────────────────────────────────────────────────────────────
// Subcommand handlers
// ──────────────────────────────────────────────────────────────────────────

function cmdParse(args) {
  let text;
  try { text = readFile(args.input); }
  catch (e) { writeJson(args.output, makeError(e.message, "§1", 0, "unknown")); return 1; }
  const fileResult = readIgesFile(text);
  if (!fileResult.ok) { writeJson(args.output, errorFromDiagnostics(fileResult.diagnostics)); return 1; }
  const diags = validate({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities });
  if (diags.length > 0) { writeJson(args.output, errorFromDiagnostics(diags)); return 1; }
  let canonical;
  try {
    canonical = buildCanonicalJson({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities });
  } catch (e) {
    if (e instanceof IgesError) { writeJson(args.output, errorFromDiagnostics([e.diag])); return 1; }
    writeJson(args.output, makeError(String(e), "§3", 0, "unknown")); return 1;
  }
  writeJson(args.output, canonical);
  return 0;
}

function cmdWrite(args) {
  let raw;
  try { raw = fs.readFileSync(args.input, "utf-8"); }
  catch (e) { process.stderr.write(JSON.stringify(makeError(e.message, "§1")) + "\n"); return 1; }
  let j;
  try { j = JSON.parse(raw); }
  catch (e) { process.stderr.write(JSON.stringify(makeError(`JSON parse error: ${e.message}`, "§2")) + "\n"); return 1; }
  let igesFile;
  try { igesFile = buildIgesFromCanonicalJson(j); }
  catch (e) {
    if (e instanceof IgesError) { process.stderr.write(JSON.stringify(errorFromDiagnostics([e.diag])) + "\n"); return 1; }
    process.stderr.write(JSON.stringify(makeError(String(e), "§3")) + "\n"); return 1;
  }
  const diags = validateWriteInput(igesFile);
  if (diags.length > 0) {
    process.stderr.write(JSON.stringify(errorFromDiagnostics(diags)) + "\n");
    return 1;
  }
  const out = writeIgesFile(igesFile.start_lines, igesFile.global, igesFile.entities);
  writeFile(args.output, out);
  return 0;
}

function cmdRoundtrip(args) {
  let text;
  try { text = readFile(args.input); }
  catch (e) { process.stderr.write(JSON.stringify(makeError(e.message, "§1")) + "\n"); return 1; }
  const fileResult = readIgesFile(text);
  if (!fileResult.ok) { process.stderr.write(JSON.stringify(errorFromDiagnostics(fileResult.diagnostics)) + "\n"); return 1; }
  const diags = validate({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities });
  if (diags.length > 0) { process.stderr.write(JSON.stringify(errorFromDiagnostics(diags)) + "\n"); return 1; }
  const out = writeIgesFile(fileResult.start_lines, fileResult.global, fileResult.entities);
  writeFile(args.output, out);
  return 0;
}

function cmdQuery(args) {
  const de = parseInt(args.de, 10);
  if (!Number.isFinite(de) || de < 1 || de % 2 === 0) {
    writeJson(args.output, makeError(`invalid --de ${args.de}`, "§1.2", 0, SECTION.DIRECTORY));
    return 1;
  }
  let text;
  try { text = readFile(args.input); }
  catch (e) { writeJson(args.output, makeError(e.message, "§1")); return 1; }
  const fileResult = readIgesFile(text);
  if (!fileResult.ok) { writeJson(args.output, errorFromDiagnostics(fileResult.diagnostics)); return 1; }
  const diags = validate({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities });
  if (diags.length > 0) { writeJson(args.output, errorFromDiagnostics(diags)); return 1; }
  const idx = (de - 1) / 2;
  if (idx < 0 || idx >= fileResult.entities.length) {
    writeJson(args.output, makeError(`DE index ${de} out of range`, "§1.2", 0, SECTION.DIRECTORY));
    return 1;
  }
  let canonical;
  try { canonical = buildCanonicalJson({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities }); }
  catch (e) {
    if (e instanceof IgesError) { writeJson(args.output, errorFromDiagnostics([e.diag])); return 1; }
    writeJson(args.output, makeError(String(e), "§3")); return 1;
  }
  writeJson(args.output, canonical.entities[idx]);
  return 0;
}

function cmdEval(args) {
  const de = parseInt(args.de, 10);
  if (!Number.isFinite(de) || de < 1 || de % 2 === 0) {
    writeJson(args.output, makeError(`invalid --de ${args.de}`, "§1.2", 0, SECTION.DIRECTORY));
    return 1;
  }
  if (args.t == null) {
    writeJson(args.output, makeError("eval requires --t", "§1.5"));
    return 1;
  }
  const t = Number(args.t);
  const s = args.s != null ? Number(args.s) : null;
  let text;
  try { text = readFile(args.input); }
  catch (e) { writeJson(args.output, makeError(e.message, "§1")); return 1; }
  const fileResult = readIgesFile(text);
  if (!fileResult.ok) { writeJson(args.output, errorFromDiagnostics(fileResult.diagnostics)); return 1; }
  const diags = validate({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities });
  if (diags.length > 0) { writeJson(args.output, errorFromDiagnostics(diags)); return 1; }
  const idx = (de - 1) / 2;
  if (idx < 0 || idx >= fileResult.entities.length) {
    writeJson(args.output, makeError(`DE index ${de} out of range`, "§1.2", 0, SECTION.DIRECTORY));
    return 1;
  }
  let canonical;
  try { canonical = buildCanonicalJson({ start_lines: fileResult.start_lines, global: fileResult.global, entities: fileResult.entities }); }
  catch (e) {
    if (e instanceof IgesError) { writeJson(args.output, errorFromDiagnostics([e.diag])); return 1; }
    writeJson(args.output, makeError(String(e), "§3")); return 1;
  }
  const record = canonical.entities[idx];
  const type = record.entity.type;
  const form = record.entity.form;
  const isCurve = isCurveForEval(type, form);
  const isSurface = isSurfaceForEval(type);
  if (!isCurve && !isSurface) {
    writeJson(args.output, makeError(`entity type ${type} is not parametric`, "§1.5", 0, SECTION.PARAMETER));
    return 1;
  }
  if (isCurve && s != null) {
    writeJson(args.output, makeError("Curve entity does not accept --s", "§1.5", 0, SECTION.PARAMETER));
    return 1;
  }
  if (isSurface && s == null) {
    writeJson(args.output, makeError("Surface entity requires --s", "§1.5", 0, SECTION.PARAMETER));
    return 1;
  }
  const resolver = makeResolver(canonical);
  let result;
  try {
    result = evaluateEntity(
      type, form, record.directory_entry.xform_matrix || 0,
      record.entity.data, t, s, resolver, false);
  } catch (e) {
    if (e instanceof IgesError) { writeJson(args.output, errorFromDiagnostics([e.diag])); return 1; }
    writeJson(args.output, makeError(String(e), "§3")); return 1;
  }
  writeJson(args.output, {
    ok: true,
    point: result.point,
    tangent: null,
    normal: null,
    error: null,
  });
  return 0;
}

// ──────────────────────────────────────────────────────────────────────────
// main()
// ──────────────────────────────────────────────────────────────────────────

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) {
    process.stderr.write(JSON.stringify(makeError("invalid arguments", "§1")) + "\n");
    process.exit(1);
  }
  let code;
  try {
    switch (args.subcommand) {
      case "parse": code = cmdParse(args); break;
      case "write": code = cmdWrite(args); break;
      case "query": code = cmdQuery(args); break;
      case "eval": code = cmdEval(args); break;
      case "roundtrip": code = cmdRoundtrip(args); break;
      default:
        process.stderr.write(JSON.stringify(makeError(`unknown subcommand '${args.subcommand}'`, "§1")) + "\n");
        process.exit(1);
    }
  } catch (e) {
    process.stderr.write(`iges: uncaught ${e && e.stack || e}\n`);
    process.exit(2);
  }
  process.exit(code);
}

main();

