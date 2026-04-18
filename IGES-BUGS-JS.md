# IGES Eval — Bugs / Gaps Found While Porting to JavaScript

Findings surfaced while implementing `Evals/IGES/reference-implementation-js/main.js`. Categorized as:
- **Missing requirement** — tests or ref-impl-cpp rely on behavior not documented in the spec/TR.
- **Ambiguous requirement** — spec/TR leave a choice and the tests implicitly require a specific one.
- **Schema misalignment** — the TR §2 JSON schema suggests fields that aren't actually round-trip-able or vice versa.
- **Duplicate enforcement** — multiple tests verify the same invariant.

The JS port passes all 257 tests against the cpp suite, so none of these are blockers. They are correctness / clarity issues that a new implementer has to discover the hard way by running the hidden suite.

---

## 1. Delimiter writer must use §2.2.3.1 combination 2 (always explicit 1H)

**Category:** Missing requirement.

**Evidence:**
- Spec §2.2.3.1 lists four valid Global-section delimiter encodings. The C++ ref-impl writes `write_string(pd); write_string(rd);` unconditionally (`writer/global_writer.cpp:20-23`), producing combination 2 (explicit `1H,...1H;`).
- `test_free_format.py::test_custom_record_delimiter_is_honored_in_written_and_parsed_files` asserts `"1H,,1H#" in line[:72]`. That substring only appears if the writer emits combination 2; combinations 1/3/4 all fail the assertion.
- TR §1.1 / TR §4 say nothing about which encoding the writer must choose.

**Symptom:** A JS implementation that legitimately picks combination 4 (`,1H#,`) when the record delimiter is non-default will fail the test even though its output is a spec-conforming IGES file.

**Suggested fix:** Either document in TR that the write path must emit both delimiters as explicit 1H Hollerith strings, or relax the assertion to check `"#" in line[:72]` (which any valid encoding would satisfy).

---

## 2. Global-section Hollerith strings that span line boundaries must not be trimmed per-line on parse

**Category:** Missing requirement.

**Evidence:**
- The `ex2.iges` fixture contains a Global-section Hollerith string `25HIGES RFC Review Committee`. The 25 chars split across two G-lines: the first line ends with "...IGES RFC Review " (with a trailing space inside the Hollerith content), and the second line starts with "Committee,".
- `test_roundtrip_cli.py::test_roundtrip_is_idempotent[ex2.iges]` requires byte-identical output on the second roundtrip.
- A naive parser that does `g_lines.map(l => l[0..72].trimEnd()).join("")` will strip the trailing space from the first G-line, corrupting the Hollerith content ("Review" + "Committee" = "ReviewCommittee"). This produces a one-character shift on the second pass that the idempotence test catches.

**Symptom:** JS port initially failed only `test_roundtrip_is_idempotent[ex2.iges]` until I switched to `g_lines.map(l => l[0..72]).join("")` followed by one overall trailing-whitespace strip.

**Suggested fix:** Add a note to TR §4 or an implementation-guidance appendix: "When concatenating multiple Global-section physical records, preserve interior padding — only strip trailing whitespace from the concatenated payload once, after the record delimiter."

---

## 3. View (Type 410) form 0 vs form 1 have mutually exclusive wire formats; TR schema combines them

**Category:** Schema misalignment.

**Evidence:**
- Spec §4.134 (form 0) defines view_number + scale + variable-length clip_plane pointers.
- Spec §4.135 (form 1, perspective view) defines view_number + scale + fixed-shape perspective fields (view_plane_normal, view_reference_point, etc.). **No clip_planes are written for form 1.**
- TR §2.6 Appendix A declares a single `ViewData` type with BOTH `clip_planes: DEIndex[]` AND all the perspective fields. That implies both should round-trip for both forms.
- `test_structure_and_view_entities.py::test_view_form_one_roundtrips_perspective_fields` uses `"clip_planes": []` (empty) and expects every perspective field to roundtrip. `test_entity_roundtrips.py::test_view_roundtrip` uses form 0 with `"clip_planes": [0, 0, 0, 0, 0, 0]` and only asserts view_number / scale / clip_planes.

**Symptom:** A JS implementer reading TR §2.6 writes a parser that reads 6 clip_planes + 20 perspective fields for all forms, which fails form 1 parse (extra fields consume perspective values).

**Suggested fix:** Split the TR schema into `ViewForm0Data` and `ViewForm1Data` (discriminated union), or add a prose note: "Form 0 serializes only `clip_planes`; form 1 serializes only the perspective fields. The JSON schema lists both for convenience; write-path serializer must emit the form-appropriate subset."

---

## 4. Offset Surface reference-parameter choice for analytic surfaces is undocumented

**Category:** Ambiguous requirement.

**Evidence:**
- Spec §4.30 describes the indicator vector (Nx, Ny, Nz) as "the unit normal vector at the parameter values (Um, Vm)" with "Um = (u1 + u2)/2 and Vm = (v1 + v2)/2 if the surface is bounded, or Um = 0.0 and Vm = 0.0 if the surface is unbounded."
- For a Cylindrical Surface (§4.51), the parameter range is `0 ≤ u ≤ 360°` and `−∞ < v < ∞`. Per the spec's literal reading, Um=180° (bounded in u) and Vm=0 (unbounded in v).
- The C++ ref-impl (`reference-implementation-cpp/src/json/eval_helpers.cpp:369-374`) uses Um=0, Vm=0 for all five analytic surface types. That's the "unbounded" formula even though u is bounded.
- `test_geometric_eval.py::test_offset_surface_over_cylinder_expands_radius_on_indicator_side` expects (0, 2.5, 1) at (u=90, v=1) with indicator [1, 0, 0]. This only works with Um=0 (where the natural normal is +x, matching the indicator, so no flip). With Um=180° the natural normal would be −x, opposite the indicator, and the code would flip the normal, giving (0, 1.5, 1) — wrong.

**Symptom:** JS port initially used Um=180° for cylinder (matching spec literal) and failed 5 offset-surface tests until I switched to the C++ ref-impl's Um=0 convention.

**Suggested fix:** Add a note to TR §1.6: "For analytic surfaces (§§4.50-4.54), the offset-surface indicator reference parameter is (u=0, v=0) regardless of whether u is bounded. This differs from a literal reading of spec §4.30."

---

## 5. Entity Label right-justification is not clearly defined on parse

**Category:** Ambiguous requirement.

**Evidence:**
- Spec §2.2.4.4.18: "The entity label is right-justified within the field with leading space fill."
- TR §2.4: `entity_label: string` (just a string).
- `test_directory_entry.py::test_entity_label_and_subscript_roundtrip` uses `entity_label: "PART01"` (6 chars) and expects `data.entity_label == "PART01"` after roundtrip.
- If parsed as the raw 8-col field, the value would be `"  PART01"` (two leading spaces). If trimmed, `"PART01"`.

**Symptom:** JS port initially used `.trimEnd()` (matching the analogous code for similar fields) and got `"  PART01"` back, failing the test. Switching to `.trim()` fixed it.

**Suggested fix:** Add a note to TR §2.4: "On parse, `entity_label` has leading padding spaces stripped; on write, the label is right-justified within the 8-column field." Or: "`entity_label` round-trips as its trimmed form."

---

## 6. Count-field redundancy for variable-length arrays

**Category:** Schema misalignment.

**Evidence:** Many TR §2.6 schemas include both an explicit count field AND the array:
- Type 412 Rectangular Array: `lc: number, ddf: number, positions: number[]`
- Type 414 Circular Array: `lc: number, ddf: number, positions: number[]`
- Type 141 Boundary: each `BoundaryCurve` has `k: number, pscpt: DEIndex[]`
- Type 508 Loop: each `EdgeUse` has `k: number, param_curves: ParamSpaceCurve[]`
- Type 212 General Note: `ns: number, strings: NoteString[]`
- Type 302 Associativity Definition: each class has `n: number, item_types: number[]`
- etc.

The writer must re-derive the count from the array length (otherwise a mismatched `n` and `items.length` writes inconsistent data). The parser can trust either the count or the array length on JSON input.

**Symptom:** Not a bug per se, but the schema's redundancy is a trap: tests populate both consistently, and a JS port can fail subtly if it trusts the explicit count when it disagrees with the array length on write.

**Suggested fix:** TR §2.6 could note: "Array-length fields (`n`, `k`, `lc`, `np`, ...) that describe the length of a neighboring array field are derivable; the writer must emit `array.length`, and the parser may trust either."

---

## 7. Rectangular Array (Type 412) PD field order: lc before ddf

**Category:** Missing requirement.

**Evidence:**
- Spec §4.136 PD parameter order: `DE, SC, XP, YP, ZP, NC, NR, DX, DY, AX, LC, DDF, positions`. `LC` (list count) is parameter 11, `DDF` (do-don't flag) is parameter 12.
- TR §2.6 Appendix A lists the schema with comment "11: DO-DON'T list count" for `lc` and "12: DO-DON'T flag" for `ddf`.
- A JS implementer reading the TR schema in field order and writing in array order must preserve LC before DDF on the wire.

**Symptom:** If the writer emits DDF before LC, the parser reads DDF into LC and vice versa, producing silent data corruption that passes write but fails roundtrip.

**Suggested fix:** Not strictly needed — TR is unambiguous here. Just flagging that an implementer who relies on "reasonable" field ordering (e.g., "flag before count") will silently break.

---

## 8. FieldValue tagged-union default handling in Property (Type 406)

**Category:** Ambiguous requirement.

**Evidence:**
- TR §2.6: "Tagged-variant encoding for `FieldValue`" with `{"kind": "int" | "real" | "string" | "bool" | "defaulted", "value": ...}`.
- No test case exercises `kind: "defaulted"`. The implementation must infer that "defaulted" means "emit an empty PD field" — not obvious from the schema alone.
- Similarly, `bool` maps to Logical data per §2.2.2.6 but the tests don't cover Property entities with `kind: "bool"`.

**Suggested fix:** Either expand the test coverage for Property entities (add one test with a `defaulted` value and one with `bool`), or add prose to TR §2.6: "`{kind: 'defaulted'}` serializes as an empty PD field between delimiters; `{kind: 'bool'}` serializes as `0`/`1` per §2.2.2.6."

---

## 9. Real-format requires at least one fractional digit in PD output

**Category:** Missing requirement.

**Evidence:**
- Spec §2.2.2.2 allows `"1."` (integer part with decimal point, no fractional digits) as a valid real literal.
- `test_writer_format.py::test_real_values_in_parameter_records_include_decimal_points` asserts `"1.0" in p_body` — i.e., the substring `"1.0"` must appear, not just `"1."`.
- The C++ ref-impl uses `%.15g` format which emits `"1.0"` for integer-valued reals (or `"1"` + `.` suffix depending on implementation). JavaScript `Number.toString()` emits `"1"` for `1.0`, requiring post-processing to produce `"1.0"`.

**Symptom:** JS port initially produced `"1."` for integer-valued reals (by appending `"."` to `Number.toString()` when no decimal was present). The substring check `"1.0" in p_body` failed because `"1."` has no trailing `"0"`.

**Suggested fix:** Either relax the test to check `"1." in p_body OR "1.0" in p_body`, or add a note to TR §4: "Real values must be emitted with at least one fractional digit (`"1.0"` not `"1."`)."

---

## 10. Start-section ASCII control-character rejection — inconsistent categorization with §2.2.2.3

**Category:** Missing requirement.

**Evidence:**
- `test_data_types.py::test_control_character_in_start_section_is_rejected` (added in Round 2) writes `"A\x01B"` to a Start line and expects parse to reject with exit 1. The assertion references spec §2.2.4.2.
- Spec §2.2.4.2 says "Start Section lines... shall not contain any ASCII control characters (i.e., hexadecimal 00 through 1F and hexadecimal 7F)."
- §2.2.2.3 has the same language for Hollerith strings.
- My JS port's readIgesFile had to add an explicit scan of Start-section body bytes to reject control chars. The C++ parser happens to reject early during section splitting (because the physical-record parser barfs). Neither spec nor TR makes clear whether Start content validation is a parse-time check or a downstream property.

**Suggested fix:** Clarify in TR that `iges parse` must reject Start-section lines containing ASCII control characters. This is implicit via §2.2.4.2 but easy to miss.

---

## 11. Duplicate test: Form 11 eval vs Form 63 eval exercise the same code path

**Category:** Duplicate enforcement.

**Evidence:**
- `test_geometric_eval.py::test_copious_data_form11_at_vertex_returns_point`, `test_copious_data_form11_midpoint_interpolates` — Form 11.
- `test_geometric_eval.py::test_copious_data_form63_midpoint_interpolates` — Form 63.
- Spec §4.11: "The default parameterization is the same as defined for the planar linear path (Form 11)."
- Both forms invoke the same eval code path (my JS case `type === 106` handles them identically). If Form 11 is broken, Form 63 is broken the same way.

**Severity:** Low — it's reasonable to have at least one test per form even if code paths merge. But a note in the design doc ("Form 63 inherits Form 11's eval semantics; Form 63 tests are redundant if Form 11 is covered") would tell reviewers it's intentional.

---

## Summary

All 11 findings are minor — none break the contract for a correctly-implemented reference. But they cumulatively add ~0.5-1 day of "unexpected debugging" for an implementer writing a new ref-impl in a new language, because the hidden test suite encodes behavior that the TR / spec don't obviously require.

**Recommended prioritization:**
- **High** — add clarifications: items 1, 2, 3, 4 (each cost me direct test failures that took non-trivial debugging)
- **Medium** — either fix schema or add prose: items 5, 6, 8
- **Low** — cosmetic / prose-only: items 7, 9, 10, 11
