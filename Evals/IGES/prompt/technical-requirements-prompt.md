# Technical Requirements

For technical compatibility with the evaluation harness, please build the tool
as a single command-line program and emit results in the canonical JSON
format defined below. The binary should be named `iges`.

---

## 1. CLI Contract

The `iges` binary supports five subcommands. All subcommands take a final
`--output <path>` flag. For `parse`, `query`, and `eval`, `--output` is
the JSON result file. For `write` and `roundtrip`, `--output` is the
emitted `.iges` file path. The harness does not depend on stdout. On
`write` or `roundtrip` failure, the diagnostic JSON object described in
§1.4 is emitted on stderr and the `--output` path is left unwritten.

### 1.1 Subcommands

```
iges parse      --input <file.iges>  --output <out.json>
iges write      --input <file.json>  --output <out.iges>
iges query      --input <file.iges>  --de <n>  --output <entity.json>
iges eval       --input <file.iges>  --de <n>  --t <f>  [--s <f>]  --output <point.json>
iges roundtrip  --input <file.iges>  --output <out.iges>
```

- `parse` — Read an IGES file, emit canonical IGES-JSON (see §2).
- `write` — Read canonical IGES-JSON, emit a conforming 80-column IGES file.
- `query` — Read an IGES file, emit the JSON for the single entity whose DE
  sequence number (1-based, odd) is `<n>`. Output schema is one
  `entity` object (see §2.5).
- `eval` — Read an IGES file, evaluate the parametric curve or surface at
  entity `<n>` at parameter `<f>` (and `<s>` for surfaces). Output schema is
  defined in §1.5.
- `roundtrip` — Read an IGES file and write it back out. Equivalent to
  `parse` followed by `write` with no intermediate JSON file exposed.

### 1.2 Exit codes

- `0` — success.
- `1` — invalid input. Any input file that fails to parse, any malformed
  JSON, any invalid Directory Entry cross-reference (`view`,
  `xform_matrix`, `label_display`), any negative entity type, any zero
  `param_line_count` on a non-null entity, any unsupported entity type
  outside the shipped 87-type catalog, any Start-section line containing
  an ASCII control character (§2.2.4.2), any Hollerith string containing
  an ASCII control character (§2.2.2.3), any evaluation on a
  non-parametric entity, or any of the Global-field / entity-level
  structural-validation failures enumerated below.

  **Non-positive required Global numeric fields (all must be > 0):**
  field 7 `integer_bits`, field 8 `sp_magnitude`,
  field 9 `sp_significance`, field 10 `dp_magnitude`,
  field 11 `dp_significance`, field 13 `model_space_scale`,
  field 16 `max_line_weight_grads`, field 19 `min_resolution`. A zero
  or negative value in any of these fields is invalid input on both
  `parse` and `write`.

  **Degenerate curve / surface entities:** a Line entity (Type 110)
  with `start == terminate` has zero arc length and must be rejected
  per IGES 5.3 §3.2.5 ("All curves shall have non-zero arc length") on
  both `parse` and `write`.

  **`spec_version` out-of-range clamping (Global field 23):** values
  below the enumerated range default to `v2_0`; values greater than
  the highest enumerated code (`v5_3`, code 11) are clamped to
  `v5_3` per §2.2.4.3.23 ("Postprocessors finding an unrecognized
  value greater than 11 shall assign 11"). Clamping is a parse-time
  normalization, not an error — the parse succeeds and serializes
  the clamped value.

  **Missing required IGES sections:** a file missing the Start (`S`),
  Global (`G`), or Terminate (`T`) section is invalid input on `parse`.
  Directory (`D`) and Parameter (`P`) sections may be empty for a file
  with zero entities but must be structurally present as zero-length
  groups.

  **`query` subcommand DE validation:** `query --de <n>` with `n` ≤ 0,
  `n` even (DE sequence numbers are odd-valued per §2.4), or `n` not
  present in the file's directory is invalid input on `query`.

  **Error-message field identification:** the `error` field of the §1.4
  diagnostic envelope must contain a substring identifying the
  offending field or condition so that failures are
  machine-distinguishable. Use the canonical-JSON field name for
  Global-field and Directory-Entry errors: `"xform_matrix"`, `"view"`,
  `"label_display"`, `"param_line_count"`, `"model_space_scale"`,
  `"integer_bits"`, `"sp_magnitude"`, `"sp_significance"`,
  `"dp_magnitude"`, `"dp_significance"`, `"max_line_weight_grads"`,
  `"min_resolution"`. For non-field conditions, the substring
  `"negative entity type"` identifies that specific failure.
- `2` — internal error in the tool itself (panic, out-of-memory,
  unexpected exception).

### 1.3 Success output

On success, `parse` and `query` write JSON conforming to the schemas in
§2, and `eval` writes JSON conforming to §1.5. On success, `write` and
`roundtrip` emit only the `.iges` file at `--output`; the harness does
not require or inspect any JSON success-status sidecar for those two
subcommands.

### 1.4 Error output

On failure, `parse`, `query`, and `eval` write a diagnostic JSON object
to `--output`. `write` and `roundtrip` emit the same JSON object on
stderr and do not produce an `.iges` file at `--output`:

```ts
{
  "ok": false,
  "error": string,             // human-readable error message
  "spec_ref": string | null,   // e.g. "§2.2.2.1", or null if not attributable
  "line": number,              // 1-based input file line number, or 0 if unknown
  "section":
    | "flag"
    | "start"
    | "global"
    | "directory"
    | "parameter"
    | "terminate"
    | "unknown",
  "diagnostics": Diagnostic[]  // full diagnostic list (may be empty)
}

type Diagnostic = {
  severity: "info" | "warning" | "error",
  message: string,
  spec_ref: string | null,
  line: number,  // 1-based input file line number, or 0 if unknown
  section:
    | "flag"
    | "start"
    | "global"
    | "directory"
    | "parameter"
    | "terminate"
    | "unknown"
}
```

Exit code 1 when `"ok": false`. The top-level `error` / `spec_ref` /
`line` / `section` fields reflect the first blocking error; the full
diagnostic list goes in `diagnostics`.

### 1.5 `iges eval` output schema

```ts
{
  "ok": true,
  "point": [number, number, number],   // evaluated point (x, y, z)
  "tangent": [number, number, number] | null,   // curve tangent at t, or null
  "normal": [number, number, number] | null,    // surface normal at (t,s), or null
  "error": null
}
```

Supported entity types for `iges eval`:

- **Curves** (Types `100`, `102`, `104`, `106` forms `11`/`12`/`63`,
  `110`, `112`, `126`, `130`): `--t` required, `--s` rejected as
  invalid input. `tangent` may be `null` if the tool does not compute
  it.
- **Surfaces** (Types `114`, `118`, `120`, `122`, `128`, `140`, `190`,
  `192`, `194`, `196`, `198`): both `--t` and `--s` required;
  `tangent` must be `null`.

Any other entity type is non-parametric for this contract: `iges eval`
must exit `1` with a diagnostic whose `error` mentions that the entity
is not parametric.

### 1.6 `t` and `s` parameter convention

`t` and `s` are **native IGES entity parameters**, not harness-normalized
fractions. The CLI does not remap curves to `[0, 1]` or surfaces to
`[0, 1]²`; each entity type uses the parameter domain defined for it by
the IGES 5.3 spec.

**Curves**

- Type `100` Circular Arc: `t` is the angular parameter in radians, with
  `t = start_angle` at the start point `(x2, y2)` and `t = terminate_angle`
  at the terminate point `(x3, y3)`. The spec's default parameterization
  is `C(t) = (x1 + R·cos t, y1 + R·sin t, zt)` (§4.3).
- Type `102` Composite Curve: `t` is the composite parameter defined in
  §4.4 (default parameterization section), where each constituent curve
  `CC(i)` receives a sub-interval `[T(i), T(i+1)]` of the composite
  parameter line sized by its own parameterization. `iges eval`
  dispatches to the constituent curve with its native parameter.
- Type `104` Conic Arc: `t ∈ [t1, t2]` using the form-specific default
  parameterization in §4.5 (parabola `C(t) = (t, −(A/E)t², zT)`;
  ellipse `C(t) = (a cos t, b sin t, zT)`; hyperbola `(a sec t,
  b tan t, zT)` etc.). Transformation from definition space to model
  space uses the entity's Transformation Matrix pointer.
- Type `106` Copious Data (forms `11`/`12`/`63`): `t ∈ [0, N−1]` where
  `N` is the number of points, with local `[0, 1]` parameterization on
  each segment `[i, i+1]` per §4.6. Forms 11 and 63 are 2D paths at
  constant `zT`; form 12 is a 3D path.
- Type `110` Line: Form 0 uses `t ∈ [0, 1]` with
  `C(t) = P1 + t·(P2 − P1)` (§4.13). Forms 1 and 2 extend the domain
  to `[0, ∞)` and `(−∞, ∞)` respectively with the same formula.
- Type `112` Parametric Spline Curve: `t` is the native breakpoint
  parameter as declared in the entity's `T(i)` breakpoint array (§4.14).
- Type `126` Rational B-Spline Curve: `t` lies in the native spline
  parameter domain declared by the entity's `v0` / `v1` fields and its
  knot vector (§4.23).
- Type `130` Offset Curve: `t ∈ [TT1, TT2]` using the base curve's
  native parameter domain per §4.25. For this eval contract, hidden
  tests exercise only `FLAG = 1` (uniform offset), and the vector
  `(vx, vy, vz)` is used directly as the offset direction. Implementations
  may support `FLAG` 2/3 but are not required to.

**Surfaces**

- Type `114` Parametric Spline Surface: `(t, s)` are the native `u, v`
  breakpoint parameters of the surface patch grid (§4.15).
- Type `118` Ruled Surface: `t` in the shared domain of the two defining
  curves (normalized to a common `[0, 1]` by default per §4.17 form 0,
  or native per form 1), `s ∈ [0, 1]` across the rule.
- Type `120` Surface of Revolution: `t` in the generatrix's native
  parameter domain, `s ∈ [start_angle, terminate_angle]` in radians
  per §4.18.
- Type `122` Tabulated Cylinder: `t` in the directrix's native
  parameter domain, `s ∈ [0, 1]` along a fixed generatrix direction per
  §4.19. The fixed direction is the vector from the directrix start point
  to `terminate_point`; `s = 0` is the directrix point at parameter `t`
  and `s = 1` adds that same vector.
- Type `128` Rational B-Spline Surface: `(t, s)` lie in the native
  `(u, v)` parameter domain declared by the entity's `u0/u1/v0/v1` and
  its two knot vectors (§4.24).
- Type `140` Offset Surface: `(t, s)` in the base surface's native
  `(u, v)` parameter domain per §4.30. The indicator vector selects
  which global normal orientation is treated as positive; the evaluated
  point is the base-surface point plus `d` times that oriented unit normal.
  The indicator is compared against the base surface's natural normal at
  a fixed reference parameter pair `(Um, Vm)`:
  - Types 114, 128 (B-spline surfaces): `(Um, Vm)` is the midpoint of
    the entity's own parameter domain.
  - Types 118, 120, 122: `(Um, Vm)` is derived from the constituent
    curve(s)' native spans (midpoint) per §4.30.
  - Types 190, 192, 194, 196, 198 (analytic surfaces): `(Um, Vm) = (0, 0)`.
    This is the spec's unbounded-domain formula — the harness applies
    it to analytic surfaces regardless of whether `u` is nominally
    bounded `[0°, 360°]`, matching the reference implementation.
- Types `190`/`192`/`194`/`196`/`198` Analytic Surfaces: `(t, s)` follow
  the native `(u, v)` parameterizations documented in §§4.50–4.54
  (e.g. Cylindrical `u ∈ [0°, 360°]` and `v ∈ (−∞, ∞)`). The CLI uses
  degrees for `u` where the spec uses degrees; radians otherwise.

**Angle-range sweep convention.** For entities whose parameter domain
is an angle range `[start_angle, terminate_angle]` — specifically Type
`100` Circular Arc (the `t` range) and Type `120` Surface of Revolution
(the `s` range) — IGES 5.3 prescribes a forward sweep with
`0 < terminate_angle − start_angle ≤ 2π`. Evaluators traverse the
range in increasing-angle order; a full-turn loop is encoded as
`ta = sa + 2π`, not as `ta = sa`. Hidden tests honor this and do not
probe the complementary (wrap-around) arc.

Hidden tests call `iges eval` only with parameter values inside the
documented native domain of the target entity.

---

## 2. Canonical IGES-JSON Schema

This is the exchange format used by `parse`, `write`, and `query`. It is
defined to be lossless with respect to the IGES 5.3 Fixed Format: any
file that parses cleanly must round-trip through canonical IGES-JSON and
back to a semantically equivalent IGES file.

### 2.1 Type conventions

Field types in this document use TypeScript-style syntax. The following
aliases are used throughout:

```ts
// A 3D point or vector. Always a 3-element JSON array of numbers.
type Vec3 = [number, number, number];

// A 3x3 matrix, row-major. Always a 3x3 JSON array of numbers.
type Matrix3x3 = [
  [number, number, number],
  [number, number, number],
  [number, number, number]
];

// A 1-based Directory Entry sequence number (always odd), or 0 for "null".
type DEIndex = number;

// A free-form IGES timestamp. Year is 4-digit (e.g. 2026).
type Timestamp = {
  year: number, month: number, day: number,
  hour: number, minute: number, second: number
};

// IGES variant fields (DE fields 4, 5, 13) are serialized as raw signed
// integers. Positive values encode direct values; negative values encode
// DE pointers to the absolute value.
type LineFontVariant = number;  // field 4
type LevelVariant    = number;  // field 5
type ColorVariant    = number;  // field 13
```

All numeric fields are JSON `number`. Integers are emitted without a
decimal point; reals are emitted with at least one decimal digit (JSON
itself does not distinguish). The tool must preserve the IGES distinction
by placing values in the correct typed fields per the schemas below; it is
not required to preserve lexical formatting within a field.

### 2.2 Top-level envelope

The output of `iges parse` and the input of `iges write` is a single JSON
object:

```ts
{
  "start_lines": string[],      // Start section text, one entry per S-line (max 72 chars each)
  "global":      GlobalSection, // §2.3
  "entities":    EntityRecord[] // §2.5
}
```

### 2.3 `GlobalSection` — 26 fields

```ts
type GlobalSection = {
  param_delimiter:      string,  // field 1, one char, default ","
  record_delimiter:     string,  // field 2, one char, default ";"
  product_id_sender:    string,  // field 3  (required)
  file_name:            string,  // field 4  (required)
  native_system_id:     string,  // field 5  (required)
  preprocessor_version: string,  // field 6  (required)
  integer_bits:         number,  // field 7  (required)
  sp_magnitude:         number,  // field 8  (required)
  sp_significance:      number,  // field 9  (required)
  dp_magnitude:         number,  // field 10 (required)
  dp_significance:      number,  // field 11 (required)
  product_id_receiver:  string,  // field 12 (default = product_id_sender)
  model_space_scale:    number,  // field 13 (default 1.0)
  units:                Units,   // field 14 (default "inches")
  units_name:           string,  // field 15 (default "IN")
  max_line_weight_grads: number, // field 16 (default 1)
  max_line_weight_width: number, // field 17 (default 0.0)
  file_timestamp:       Timestamp, // field 18 (required)
  min_resolution:       number,  // field 19 (required)
  max_coordinate:       number,  // field 20 (default 0.0)
  author:               string,  // field 21 (default "")
  organization:         string,  // field 22 (default "")
  spec_version:         SpecVersion,     // field 23 (default "v2_0")
  drafting_std:         DraftingStandard, // field 24 (default "none")
  model_timestamp:      Timestamp | null, // field 25 (null = absent)
  app_protocol:         string   // field 26 (default "")
};

type Units = "inches" | "millimeters" | "see_field_15" | "feet" | "miles"
           | "meters" | "kilometers" | "mils" | "microns"
           | "centimeters" | "microinches";

type SpecVersion =
  | "v1_0"
  | "ansi_1981"
  | "v2_0"
  | "v3_0"
  | "asme_1987"
  | "v4_0"
  | "asme_1989"
  | "v5_0"
  | "v5_2"
  | "v5_1"
  | "v5_3";

type DraftingStandard =
  | "none"
  | "iso"
  | "afnor"
  | "ansi"
  | "bsi"
  | "csa"
  | "din"
  | "jis";
```

All defaults are applied per §3.1 of the specification. Fields that
default from another field (field 12 defaults to field 3) must be emitted
with the effective value — `iges parse` should resolve defaults, so the
JSON is fully populated after parsing.

### 2.4 `DirectoryEntry` — 20 fields

Every entity has an associated 20-field Directory Entry. Fields 1 and 11
are identical (both hold the entity type); fields 10 and 20 are sequence
numbers derived from position in the file and are not stored in JSON.

```ts
type DirectoryEntry = {
  entity_type:      number,           // fields 1, 11
  param_data_ptr:   number,           // field 2  (P-section line number)
  structure:        number,           // field 3  (0 or negative DE pointer)
  line_font:        LineFontVariant,  // field 4
  level:            LevelVariant,     // field 5
  view:             DEIndex,          // field 6
  xform_matrix:     DEIndex,          // field 7
  label_display:    DEIndex,          // field 8
  status:           StatusNumber,     // field 9  (4 sub-fields)
  line_weight:      number,           // field 12
  color:            ColorVariant,     // field 13 (raw signed integer)
  param_line_count: number,           // field 14 (number of P-section lines)
  form:             number,           // field 15 (form number)
  entity_label:     string,           // field 18 (up to 8 chars, trimmed)
  entity_subscript: number            // field 19
};
// entity_label round-trips as the trimmed form: the raw 8-col DE
// field is right-justified with leading-space padding on write, and
// the parser strips padding on parse so the canonical JSON carries
// the user-meaningful label (e.g. "PART01"), not its column-padded
// encoding ("  PART01"). See §2.2.4.4.18.

type StatusNumber = {
  blank: "visible" | "blanked",
  subordinate:
    | "independent"
    | "physically_dependent"
    | "logically_dependent"
    | "both",
  entity_use:
    | "geometry"
    | "annotation"
    | "definition"
    | "other"
    | "logical_positional"
    | "parametric_2d"
    | "construction_geometry",
  hierarchy: "global_top_down" | "global_defer" | "use_property"
};
```

On write, `param_data_ptr`, `param_line_count`, the sequence numbers
(fields 10, 20), and the reserved fields (16, 17) are all computed by the
writer from the emitted file layout; they can be absent on input to
`iges write` and must be present on output from `iges parse`.

### 2.5 `EntityRecord` — one parsed entity

```ts
type EntityRecord = {
  de_index:         DEIndex,        // this entity's own DE sequence number
  directory_entry:  DirectoryEntry, // §2.4
  entity:           Entity          // the typed PD data for this entity
};

type Entity = {
  type:  number,          // IGES entity type (100, 110, 126, ...)
  form:  number,          // form number (subtype)
  data:  EntityData       // see §2.6
};
```

The `type` and `form` in `Entity` must match `directory_entry.entity_type`
and `directory_entry.form`. The `data` shape is determined by `(type, form)`
per the per-entity schemas in §2.6.

### 2.6 Per-entity `data` schemas

The per-entity `data` shapes for all 87 IGES 5.3 entity types are listed
in the appendix below, in spec-section order. Form-dependent entities
(Drawing 404, External Reference 416, Line Font Definition 304, Ordinate
Dimension 218, Radius Dimension 222, View 410, Plane/Cylindrical/Conical/
Spherical/Toroidal Surface 190-198, Attribute Table Definition 322) have
a union of per-form shapes; see the individual entries.

When reading a file containing entity types outside this 87-entity
catalog, reject the file as invalid input with a severity `error`
diagnostic. Implementations may preserve raw Parameter Data for such
unsupported types as a tool-specific extension, but the harness does not
require `data.raw_pd` and hidden tests do not exercise it.

**Count-field redundancy.** Several entity schemas below include an
explicit integer count field next to a variable-length array (e.g.
`{n: number, items: DEIndex[]}`, `{nc: number, ..., positions:
number[]}`). These pairs are redundant by construction:

- **On `iges write`:** the writer must emit the array length as the
  count field. If the canonical JSON arrives with a mismatched
  `count` and `array.length`, the writer trusts `array.length`.
- **On `iges parse`:** the parser uses the count read from the PD
  stream to consume exactly that many elements. The output JSON
  carries both fields populated consistently.

This applies to (but is not limited to) `n` in Composite Curve (102),
Vertex List (502), Edge List (504), Loop (508), Shell (514); `nc`/`nr`
in Rectangular Array (412); `ne` in Circular Array (414); `np` in
Property (406), Units Data (316); `ns` in General Note (212), New
General Note (213); `k` in Boundary (141) sub-records and Loop (508)
sub-records; and any other field labeled "number of ..." immediately
preceding its corresponding array.

**[Entity data schemas appendix — see §A.]**

---

## 3. Numerical Tolerances

- For `iges eval`, the evaluated point must match the reference
  implementation within relative tolerance `1e-9` for each coordinate,
  with absolute tolerance `1e-12` when the reference value is near zero.
- For `iges roundtrip`, the canonical IGES-JSON of the read-then-written
  file must be semantically equal to the input's canonical IGES-JSON:
  integer fields exactly, real fields within relative `1e-12` / absolute
  `1e-15`, strings exactly (after Hollerith decoding), pointers exactly.
  Trailing-zero differences in real formatting are allowed.
- After one successful `iges roundtrip` normalization pass, a second
  `iges roundtrip` over the emitted file must be byte-identical to the
  first pass output. Visible and hidden tests rely on this fixed-point
  property to catch writer non-determinism.

---

## 4. File-Format Rules (non-negotiable)

These are mechanical file-format constraints; agents should not need to
re-derive them from the spec.

- All output `.iges` files are 80-column fixed-format ASCII. Each line is
  exactly 80 characters followed by a single `\n`. The final line is
  terminated with a trailing `\n`.
- Columns 73-80 contain the section character ('S', 'G', 'D', 'P', 'T')
  followed by a right-justified 7-digit sequence number, starting at
  0000001 for each section.
- Data in Start, Global, and Parameter sections occupies columns 1-72
  (64 for Parameter section, with columns 65-72 holding the DE back-pointer).
- Directory Entry records are exactly two 80-column lines (160 columns
  total) per entity.
- Hollerith strings are encoded `<N>H<...N chars...>`.
- Global-section field 1 (parameter delimiter) and field 2 (record
  delimiter) are always emitted as explicit 1-char Hollerith strings
  (`1H,` and `1H;` for the defaults, or `1Hα` and `1Hβ` for custom
  delimiters). Spec §2.2.3.1 allows four delimiter encodings; the
  harness requires the always-explicit form (combination 2) so that
  downstream tooling can read the delimiters without needing to
  back-track on defaults.
- Parsing the Global section: concatenate the body (cols 1-72) of
  every G-line verbatim — do not strip trailing padding per line.
  Only one trailing-whitespace strip is applied, to the concatenated
  payload as a whole. A per-line strip corrupts Hollerith strings
  whose content happens to end with a space at a G-line boundary.
- **Terminate section**: the writer emits exactly one T-line (the
  parser does not reject files with multiple T-lines, but a conforming
  writer always produces one). Columns 1-72 contain an 80-char field
  composed of four 8-column subfields giving the physical-line counts
  of the preceding sections, formatted as
  `S<nnnnnnn>G<nnnnnnn>D<nnnnnnn>P<nnnnnnn>` (section letter followed
  by a right-justified 7-digit count). Columns 73-80 use the standard
  section letter + sequence (`T      1`).
- **Empty Start section**: when the canonical JSON `start_lines` is
  an empty array, the writer still emits one blank S-line (72 spaces
  in cols 1-72, then `S      1`). A file with zero S-lines is
  invalid input.

**Free-format parsing rules (§2.2.3):**

- **Defaulted fields:** two consecutive delimiters in the Global or
  Parameter section represent an absent field; the field assumes its
  specified default. A trailing field absent before the record
  delimiter is also defaulted. `1.0,,1.0,` is three fields: `1.0`,
  default, `1.0`, (trailing empty field before the record delimiter
  is also defaulted, so four fields total if the record delimiter
  follows).
- **Hollerith content is opaque to delimiter scanning.** `<N>H<...N
  chars...>` reads exactly N bytes after the `H` regardless of any
  delimiter characters (including custom delimiters) that appear
  inside. The parser must not split Hollerith contents on the
  delimiter.
- **Prohibited delimiter characters** (Global fields 1 and 2): the
  parameter and record delimiters may not be digits `0-9`, `+`, `-`,
  `.`, `D`, `E`, `H`, space, or any ASCII control character (§2.2.3.1).
  A Global section advertising a prohibited delimiter must cause
  `parse` to exit 1 (either via a dedicated prohibited-char check or
  via incidental parse failure when the would-be delimiter is still
  read as a value character).
- **Trailing characters after the record delimiter** in the same
  physical line (before col 72) are tolerated and ignored. The parser
  must not raise on `,...;  extra comment  ` — the record delimiter
  `;` terminates the section.

**Entity transformation matrix application order (§4):**

For **every** entity type with a non-zero `xform_matrix` DE pointer
(field 7), `iges eval` first computes the point / tangent / normal in
the entity's own definition space using its native parameterization,
then applies the transformation matrix's rotation (for vectors) and
rotation-plus-translation (for points) as the final step. This
ordering applies to every evaluated entity type — curves (100, 102,
104, 106, 110, 112, 126, 130) and surfaces (114, 118, 120, 122, 128,
140, 190, 192, 194, 196, 198) — not just Conic Arc (104).

Details are in §2.2 of the specification.

---

## 5. Language-specific notes

A language-requirements document is concatenated after this one. It
describes the build system, standard-library rules, and dependency policy
for your target language.

---

## Appendix A — Per-entity `data` schemas

This appendix lists the TypeScript-style `data` schema for each of the 87
IGES 5.3 entity types covered by this eval, in entity-type-number order.
Schemas are mechanically extracted from the reference implementation; see
`Evals/IGES-SDK/scripts/extract_entity_schemas.py` for the extractor.

Conventions:

- Field names are lowercased versions of the IGES spec PD parameter names
  (e.g. `XT` → `xt`, `DENOTE` → `denote`).
- Nested types (`BoundaryCurve`, `NoteString`, etc.) are declared
  immediately before the parent `*Data` type they belong to.
- For **form-dependent** entities (marked with `— form-dependent`), the
  `data` schema lists the union of all possible fields across forms. The
  agent must decide per-form which fields are populated. See the spec in
  `docs/iges-5-3-specification.md` for the form-to-field mapping —
  specifically §4.131 (Drawing), §4.135 (External Reference), §4.91 (Line
  Font Definition), §4.61 (Ordinate Dimension), §4.63 (Radius Dimension),
  §4.134 (View), §4.50-§4.54 (parametric surface forms), and §4.79
  (Attribute Table Definition).
- **Form-dependent unused-field roundtrip:** a subset of
  form-dependent schemas (Types 218 Ordinate Dimension, 222 Radius
  Dimension, 304 Line Font Definition, 410 View) carry an explicit
  `form: number` field inside `data` in addition to the `form` on
  the outer `Entity` object. When present, the two must agree.
  Other form-dependent schemas (Types 190/192/194/196/198 analytic
  surfaces, 322 Attribute Table Definition, 404 Drawing, 416
  External Reference) select fields by the outer `Entity.form`
  alone and do not re-encode `form` inside `data` — see Appendix A
  for the per-type shape. In every form-dependent schema,
  unused-form fields (e.g., `deord`/`desupp` on Ordinate Dimension
  Form 0, `segments`/`bitmask` on Line Font Definition Form 1,
  `derefd` on Form 0 analytic surfaces, perspective fields on View
  Form 0) must be present in the canonical JSON with their
  zero/empty/default values (number → `0`, boolean → `false`, array
  → `[]`, string → `""`) and round-trip unchanged through
  write/parse. The writer omits them from the emitted PD record (or
  writes defaulted `,` fields); the parser restores them as the
  zero/empty default on read-back. Agents may not omit unused-form
  fields from the JSON shape.
- Fields the writer may re-derive (DE sequence numbers, param_data_ptr,
  param_line_count) are not marked optional in these types — the schemas
  describe the fully-resolved post-parse shape per §2.3 and §2.4.
- **Non-FieldValue boolean fields** (e.g., `outer_loop_flag` on Face
  (510), `logical` flags on MSBO and Shell entities) serialize in the
  PD record as the Logical wire form (`1` for true, `0` for false)
  per §2.2.2.6, matching the bool-kind FieldValue convention.
- **Direction entity (Type 123) and other ratio/direction fields do
  not normalize.** Values like `{x: 1, y: 2, z: 3}` round-trip
  verbatim — the parser must not normalize the direction vector to
  unit length. The canonical JSON stores the raw ratios as written.

### Type 0 — NullEntity

```ts
type NullData = {
};
```

### Type 100 — CircularArcEntity

```ts
type CircularArcData = {
  zt: number,  // ZT displacement from XT,YT plane
  x1: number,  // Center X
  y1: number,  // Center Y
  x2: number,  // Start X
  y2: number,  // Start Y
  x3: number,  // Terminate X
  y3: number,  // Terminate Y
};
```

### Type 102 — CompositeCurveEntity

```ts
type CompositeCurveData = {
  constituents: DEIndex[],  // pointers to constituent entity DEs
};
```

### Type 104 — ConicArcEntity

```ts
type ConicArcData = {
  A: number,
  B: number,
  C: number,
  D: number,
  E: number,
  F: number,
  zt: number,  // Z coordinate of the plane
  x1: number,  // Start point X
  y1: number,  // Start point Y
  x2: number,  // Terminate point X
  y2: number,  // Terminate point Y
};
```

### Type 106 — CopiousDataEntity

```ts
type CopiousDataData = {
  ip: number,  // interpretation flag: 1=2D, 2=3D, 3=3D+vector
  n: number,  // number of tuples
  zt: number,  // common z displacement (IP=1 only on the wire; present in JSON for every IP, default 0.0)
  data: number[],  // flat array: N*2, N*3, or N*6 values
};
```

### Type 108 — PlaneEntity

```ts
type PlaneData = {
  A: number,
  B: number,
  C: number,
  D: number,
  ptr: DEIndex,
  x: number,
  y: number,
  z: number,
  size: number,  // Size parameter for display symbol
};
```

### Type 110 — LineEntity

```ts
type LineData = {
  start: Vec3,  // P1
  terminate: Vec3,  // P2
};
```

### Type 112 — ParametricSplineCurveEntity

```ts
type SplineCurveSegment = {
  ax: number,
  bx: number,
  cx: number,
  dx: number,
  ay: number,
  by: number,
  cy: number,
  dy: number,
  az: number,
  bz: number,
  cz: number,
  dz: number
};

type ParametricSplineCurveData = {
  ctype: number,  // Spline type: 1=Linear,2=Quadratic,3=Cubic,4=WF,5=MWF,6=B-spline
  H: number,  // Degree of continuity w.r.t. arc length
  ndim: number,  // Number of dimensions: 2=planar, 3=nonplanar
  breakpoints: number[],  // N+1 breakpoints: T(1)..T(N+1)
  segments: SplineCurveSegment[],  // N segments
  tpx0: number,
  tpx1: number,
  tpx2: number,
  tpx3: number,
  tpy0: number,
  tpy1: number,
  tpy2: number,
  tpy3: number,
  tpz0: number,
  tpz1: number,
  tpz2: number,
  tpz3: number
};
```

### Type 114 — ParametricSplineSurfaceEntity

```ts
type SplineSurfacePatch = {
  // 48 coefficients per patch (16 for X, 16 for Y, 16 for Z).
  // X(u,v) = sum_{p=0..3} sum_{q=0..3} coeff_x[4*p+q] * s^q * t^p,
  // with s = u - tu[i], t = v - tv[j]. Same for coeff_y, coeff_z.
  coeff_x: number[],  // length 16 (AX,BX,CX,DX, EX,FX,GX,HX, KX,LX,MX,NX, PX,QX,RX,SX)
  coeff_y: number[],  // length 16
  coeff_z: number[]   // length 16
};

type ParametricSplineSurfaceData = {
  ctype: number,  // Spline boundary type
  ptype: number,  // Patch type: 0=unspecified, 1=Cartesian product
  M: number,  // Number of u segments
  N: number,  // Number of v segments
  tu: number[],  // M+1 u breakpoints
  tv: number[],  // N+1 v breakpoints
  patches: SplineSurfacePatch[]
};
```

### Type 116 — PointEntity

```ts
type PointData = {
  coords: Vec3,
  display_symbol: DEIndex,  // 0 = no display symbol
};
```

### Type 118 — RuledSurfaceEntity

```ts
type RuledSurfaceData = {
  de1: DEIndex,  // Pointer to first curve entity
  de2: DEIndex,  // Pointer to second curve entity
  dirflg: number,  // 0 = first-to-first, 1 = first-to-last
  devflg: number,  // 0 = possibly not developable, 1 = developable
};
```

### Type 120 — SurfaceOfRevolutionEntity

```ts
type SurfaceOfRevolutionData = {
  l: DEIndex,  // Pointer to Line Entity (axis of revolution)
  c: DEIndex,  // Pointer to generatrix entity
  sa: number,  // Start angle in radians
  ta: number,  // Terminate angle in radians
};
```

### Type 122 — TabulatedCylinderEntity

```ts
type TabulatedCylinderData = {
  de: DEIndex,  // Pointer to directrix curve entity
  terminate_point: Vec3,  // (LX, LY, LZ) terminate point of generatrix
};
```

### Type 123 — DirectionEntity

```ts
type DirectionData = {
  x: number,  // Direction ratio w.r.t. X axis
  y: number,  // Direction ratio w.r.t. Y axis
  z: number,  // Direction ratio w.r.t. Z axis
};
```

### Type 124 — TransformationMatrixEntity

```ts
type TransformationMatrixData = {
  rotation: Matrix3x3,
  translation: Vec3
};
```

### Type 125 — FlashEntity

```ts
type FlashData = {
  x: number,  // X reference of flash
  y: number,  // Y reference of flash
  dim1: number,  // First flash sizing parameter
  dim2: number,  // Second flash sizing parameter
  rot: number,  // Rotation about reference point in radians
  de: DEIndex,  // Pointer to DE of referenced entity or zero
};
```

### Type 126 — RationalBSplineCurveEntity

```ts
type RationalBSplineCurveData = {
  K: number,  // Upper index of sum (number of control points = K+1)
  M: number,  // Degree of basis functions
  prop1: number,  // 0 = nonplanar, 1 = planar
  prop2: number,  // 0 = open, 1 = closed
  prop3: number,  // 0 = rational, 1 = polynomial
  prop4: number,  // 0 = nonperiodic, 1 = periodic
  knots: number[],  // length = A+1 where A = N+2*M, N = 1+K-M
  weights: number[],  // length = K+1
  control_points: Vec3[],  // length = K+1
  v0: number,  // Starting parameter value
  v1: number,  // Ending parameter value
  plane_normal: Vec3,  // Always present; unit normal if planar (PROP1=1), else zero vector
};
```

### Type 128 — RationalBSplineSurfaceEntity

```ts
type RationalBSplineSurfaceData = {
  K1: number,  // Upper index of first sum
  K2: number,  // Upper index of second sum
  M1: number,  // Degree of first set of basis functions
  M2: number,  // Degree of second set of basis functions
  prop1: number,  // 1 = closed in first parametric direction
  prop2: number,  // 1 = closed in second parametric direction
  prop3: number,  // 0 = rational, 1 = polynomial
  prop4: number,  // 1 = periodic in first parametric direction
  prop5: number,  // 1 = periodic in second parametric direction
  knots_u: number[],  // first knot vector, length A+1
  knots_v: number[],  // second knot vector, length B+1
  weights: number[],  // C values, stored (K1+1)*(K2+1)
  control_points: Vec3[],  // C triples, stored (K1+1)*(K2+1)
  u0: number,  // parameter range in U
  u1: number,  // parameter range in U
  v0: number,  // parameter range in V
  v1: number,  // parameter range in V
};
```

### Type 130 — OffsetCurveEntity

```ts
type OffsetCurveData = {
  de1: DEIndex,  // Pointer to base curve to be offset
  flag: number,  // 1=uniform, 2=linear, 3=function
  de2: DEIndex,  // Pointer to function curve (FLAG=3), else 0
  ndim: number,  // Coordinate of DE2 for offset (FLAG=3)
  ptype: number,  // 1=arc length, 2=parameter
  d1: number,  // First offset distance
  td1: number,  // Arc length or param of first offset (FLAG=2)
  d2: number,  // Second offset distance
  td2: number,  // Arc length or param of second offset (FLAG=2)
  vx: number,  // Normal vector X component
  vy: number,  // Normal vector Y component
  vz: number,  // Normal vector Z component
  tt1: number,  // Starting parameter value
  tt2: number,  // Ending parameter value
};
```

### Type 132 — ConnectPointEntity

```ts
type ConnectPointData = {
  location: Vec3,  // 1-3: X, Y, Z
  display_symbol: DEIndex,  // 4: PTR — display symbol geometry DE
  tf: number,  // 5: TF — Type flag
  ff: number,  // 6: FF — Function flag (0/1/2)
  cid: string,  // 7: CID — Function identifier
  pttcid: DEIndex,  // 8: PTTCID — Text Display Template for CID
  cfn: string,  // 9: CFN — Connection Point Function Name
  pttcfn: DEIndex,  // 10: PTTCFN — Text Display Template for CFN
  cpid: number,  // 11: CPID — Unique Connect Point Identifier
  fc: number,  // 12: FC — Connect Point Function Code
  sf: number,  // 13: SF — Swap Flag (0=may swap, 1=may not)
  psfi: DEIndex,  // 14: PSFI — Pointer to owner
};
```

### Type 134 — NodeEntity (§4.27)

> A geometric point used in the definition of a finite element.

```ts
type NodeData = {
  x: number,  // First nodal coordinate
  y: number,  // Second nodal coordinate
  z: number,  // Third nodal coordinate
  ndcsp: DEIndex,  // Pointer to Transformation Matrix Entity (Form 10/11/12); 0 = Global Cartesian
};
```

### Type 136 — FiniteElementEntity

```ts
type FiniteElementData = {
  itop: number,  // Topology type (1-38, 5001=implementor-defined)
  n: number,  // Number of nodes defining element
  nodes: DEIndex[],  // Pointers to Node entities (Type 134)
  etyp: string,  // Element type name (e.g., "BEAM", "LTRIA")
};
```

### Type 138 — NodalDisplacementEntity

```ts
type NodalDisplacementValues = {
  x: number,  // X-Incr. translation
  y: number,  // Y-Incr. translation
  z: number,  // Z-Incr. translation
  rx: number,  // RX-Incr. rotation
  ry: number,  // RY-Incr. rotation
  rz: number,  // RZ-Incr. rotation
};

type NodalDisplacementNode = {
  node_id: number,  // Node number identifier
  np: DEIndex,  // Pointer to the Node Entity
  cases: NodalDisplacementValues[],  // One per analysis case (NC values)
};

type NodalDisplacementData = {
  nc: number,  // Number of analysis cases
  gp: DEIndex[],  // Pointers to General Note entities (NC)
  nn: number,  // Number of nodes
  nodes: NodalDisplacementNode[]
};
```

### Type 140 — OffsetSurfaceEntity

```ts
type OffsetSurfaceData = {
  nx: number,  // Offset indicator X component
  ny: number,  // Offset indicator Y component
  nz: number,  // Offset indicator Z component
  d: number,  // Offset distance
  de: DEIndex,  // Pointer to surface entity to be offset
};
```

### Type 141 — BoundaryEntity

```ts
type BoundaryCurve = {
  crvpt: DEIndex,  // Model space curve pointer
  sense: number,  // 1=no reversal, 2=reversed
  k: number,  // Number of param space curves
  pscpt: DEIndex[],  // Parameter space curve pointers
};

type BoundaryData = {
  type: number,  // 0=model space only, 1=model+param
  pref: number,  // Preferred representation
  sptr: DEIndex,  // Pointer to untrimmed surface
  n: number,  // Number of curves
  curves: BoundaryCurve[]
};
```

### Type 142 — CurveOnParametricSurfaceEntity

```ts
type CurveOnParametricSurfaceData = {
  crtn: number,  // Creation method: 0=unspecified, 1=projection,
  sptr: DEIndex,  // Pointer to surface S
  bptr: DEIndex,  // Pointer to curve B in (u,v) parameter space
  cptr: DEIndex,  // Pointer to curve C in model space
  pref: number  // Preferred representation: 0=unspecified,
};
```

### Type 143 — BoundedSurfaceEntity

```ts
type BoundedSurfaceData = {
  type: number,  // 0 = model space only, 1 = model + parameter space
  sptr: DEIndex,  // Pointer to untrimmed surface
  n: number,  // Number of boundary entities
  bdpt: DEIndex[],  // Pointers to Boundary entities (Type 141)
};
```

### Type 144 — TrimmedSurfaceEntity

```ts
type TrimmedSurfaceData = {
  pts: DEIndex,  // Pointer to surface being trimmed
  n1: number,  // 0 = outer boundary is boundary of D
  n2: number,  // Number of inner boundary curves
  pto: DEIndex,  // Outer boundary (Type 142) or zero
  pti: DEIndex[],  // Inner boundary pointers (Type 142)
};
```

### Type 146 — NodalResultsEntity

```ts
type NodalResultsNode = {
  node_id: number,  // FEM node number identifier
  np: DEIndex,  // Pointer to the DE of the Node Entity
  values: number[],  // NV data values for this node
};

type NodalResultsData = {
  gnote: DEIndex,  // Pointer to General Note Entity
  scn: number,  // Analysis subcase number (0 = no subcase)
  time: number,  // Analysis time value
  nv: number,  // Number of real values per node
  nn: number,  // Number of FEM nodes
  nodes: NodalResultsNode[]
};
```

### Type 148 — ElementResultsEntity

```ts
type ElementResultsElement = {
  en: number,  // FEM element number identifier
  ep: DEIndex,  // Pointer to the DE of the FEM Element Entity
  itop: number,  // Element Topology type
  nl: number,  // Number of layers per results data report location
  dlf: number,  // Data Layer Flag (0..4)
  nrl: number,  // Number of results data report locations
  rdrl: number[],  // Results data report locations (NRL values)
  numv: number,  // Total number of result values (NV*NL*NRL)
  values: number[],  // Result values V(J,K,L) in column-major order
};

type ElementResultsData = {
  gnote: DEIndex,  // Pointer to General Note Entity
  scn: number,  // Analysis subcase number (0 = no subcase)
  time: number,  // Analysis time value
  nv: number,  // Number of results values per report location
  rrf: number,  // Results Reporting Flag (0..3)
  ne: number,  // Number of FEM elements
  elements: ElementResultsElement[]
};
```

### Type 150 — BlockEntity

```ts
type BlockData = {
  lx: number,  // Edge lengths
  ly: number,  // Edge lengths
  lz: number,  // Edge lengths
  corner: Vec3,  // Corner point
  x_axis: Vec3,  // Local X-axis
  z_axis: Vec3,  // Local Z-axis
};
```

### Type 152 — WedgeEntity

```ts
type WedgeData = {
  lx: number,  // Edge lengths
  ly: number,  // Edge lengths
  lz: number,  // Edge lengths
  ltx: number,  // X-length at distance LY
  corner: Vec3,
  x_axis: Vec3,
  z_axis: Vec3
};
```

### Type 154 — RightCircularCylinderEntity

```ts
type RightCircularCylinderData = {
  h: number,  // Height
  r: number,  // Radius
  face_center: Vec3,  // First face center
  axis: Vec3,  // Axis direction
};
```

### Type 156 — ConeFrustumEntity

```ts
type ConeFrustumData = {
  h: number,  // Height
  r1: number,  // Larger face radius
  r2: number,  // Smaller face radius (0 for apex)
  face_center: Vec3,  // Larger face center
  axis: Vec3,  // Axis direction
};
```

### Type 158 — SphereEntity

```ts
type SphereData = {
  radius: number,
  center: Vec3
};
```

### Type 160 — TorusEntity

```ts
type TorusData = {
  r1: number,  // Major radius (axis to disc center)
  r2: number,  // Minor radius (disc radius)
  center: Vec3,
  axis: Vec3
};
```

### Type 162 — SolidOfRevolutionEntity

```ts
type SolidOfRevolutionData = {
  ptr: DEIndex,  // Pointer to curve to be revolved
  f: number,  // Fraction of full rotation
  axis_point: Vec3,  // Point on axis
  axis_dir: Vec3,  // Axis direction
};
```

### Type 164 — SolidOfLinearExtrusionEntity

```ts
type SolidOfLinearExtrusionData = {
  ptr: DEIndex,  // Pointer to closed curve
  length: number,  // Extrusion length
  direction: Vec3,  // Extrusion direction
};
```

### Type 168 — EllipsoidEntity

```ts
type EllipsoidData = {
  lx: number,  // Semi-axis lengths
  ly: number,  // Semi-axis lengths
  lz: number,  // Semi-axis lengths
  center: Vec3,
  x_axis: Vec3,  // Local X (major)
  z_axis: Vec3,  // Local Z (minor)
};
```

### Type 180 — BooleanTreeEntity

```ts
type BooleanTreeData = {
  n: number,  // Length of post-order notation
  entries: number[],  // Positive = operation, negative = pointer
};
```

### Type 182 — SelectedComponentEntity

```ts
type SelectedComponentData = {
  btree: DEIndex,  // Pointer to Boolean Tree Entity
  sel_point: Vec3,  // Point in or on desired component
};
```

### Type 184 — SolidAssemblyEntity

```ts
type SolidAssemblyData = {
  n: number,  // Number of items
  items: DEIndex[],  // Item pointers
  transforms: DEIndex[],  // Transform matrix pointers (0=identity)
};
```

### Type 186 — MSBOEntity (§4.49)

> The MSBO defines a manifold solid by enumerating its boundary.

```ts
type VoidShell = {
  shell: DEIndex,
  orientation: boolean
};

type MSBOData = {
  shell: DEIndex,  // Outer shell pointer
  sof: boolean,  // Shell orientation flag
  n: number,  // Number of void shells
  voids: VoidShell[]
};
```

### Type 190 — PlaneSurfaceEntity — form-dependent

```ts
type PlaneSurfaceData = {
  deloc: DEIndex,  // Point on surface
  denrml: DEIndex,  // Surface normal direction
  derefd: DEIndex,  // Reference direction (Form 1 only)
};
```

### Type 192 — CylindricalSurfaceEntity — form-dependent

```ts
type CylindricalSurfaceData = {
  deloc: DEIndex,  // Point on axis
  deaxis: DEIndex,  // Axis direction
  radius: number,
  derefd: DEIndex,  // Reference direction (Form 1 only)
};
```

### Type 194 — ConicalSurfaceEntity — form-dependent

```ts
type ConicalSurfaceData = {
  deloc: DEIndex,
  deaxis: DEIndex,
  radius: number,
  sangle: number,  // Semi-angle in degrees
  derefd: DEIndex,  // Reference direction (Form 1 only)
};
```

### Type 196 — SphericalSurfaceEntity — form-dependent

```ts
type SphericalSurfaceData = {
  deloc: DEIndex,  // Center point
  radius: number,
  deaxis: DEIndex,  // Axis direction (Form 1 only)
  derefd: DEIndex,  // Reference direction (Form 1 only)
};
```

### Type 198 — ToroidalSurfaceEntity — form-dependent

```ts
type ToroidalSurfaceData = {
  deloc: DEIndex,
  deaxis: DEIndex,
  majrad: number,
  minrad: number,
  derefd: DEIndex,  // Reference direction (Form 1 only)
};
```

### Type 202 — AngularDimensionEntity

```ts
type AngularDimensionData = {
  denote: DEIndex,
  dewit1: DEIndex,
  dewit2: DEIndex,
  xt: number,
  yt: number,
  radius: number,
  dearrw1: DEIndex,
  dearrw2: DEIndex
};
```

### Type 204 — CurveDimensionEntity

```ts
type CurveDimensionData = {
  denote: DEIndex,  // Pointer to DE of General Note Entity
  decurv1: DEIndex,  // Pointer to DE of first curve
  decurv2: DEIndex,  // Pointer to DE of second curve
  dearr1: DEIndex,  // Pointer to DE of first leader (arrow)
  dearr2: DEIndex,  // Pointer to DE of second leader (arrow)
  dewit1: DEIndex,  // Pointer to DE of first witness line
  dewit2: DEIndex,  // Pointer to DE of second witness line
};
```

### Type 206 — DiameterDimensionEntity

```ts
type DiameterDimensionData = {
  denote: DEIndex,
  dearrw1: DEIndex,
  dearrw2: DEIndex,
  xt: number,
  yt: number
};
```

### Type 208 — FlagNoteEntity

```ts
type FlagNoteData = {
  xt: number,  // X coordinate of lower left corner
  yt: number,  // Y coordinate of lower left corner
  zt: number,  // Z coordinate of lower left corner
  angle: number,  // Rotation angle in radians
  denote: DEIndex,  // Pointer to DE of General Note Entity
  n: number,  // Number of associated leader arrows
  leaders: DEIndex[],  // Pointers to DE of leader arrows
};
```

### Type 210 — GeneralLabelEntity

```ts
type GeneralLabelData = {
  denote: DEIndex,
  n: number,
  leaders: DEIndex[]
};
```

### Type 212 — GeneralNoteEntity (§4.58)

> A General Note Entity consists of one or more text strings.

```ts
type NoteString = {
  nc: number,
  wc: number,
  hc: number,
  fc: number,
  slant: number,
  angle: number,
  mirror: number,
  vh: number,
  start: Vec3,
  text: string
};

type GeneralNoteData = {
  ns: number,
  strings: NoteString[]
};
```

### Type 213 — NewGeneralNoteEntity

```ts
type NewNoteString = {
  fixvar: number,  // Fixed/Variable width character display
  chrwid: number,  // Character width
  chrhgt: number,  // Character height
  cspace: number,  // Inter-character spacing
  lspace: number,  // Interline spacing
  font: number,  // Font style
  chrang: number,  // Character angle
  cctext: string,  // Control code string
  nc: number,  // Number of characters in TEXT
  wt: number,  // Box width
  ht: number,  // Box height
  chrset: number,  // Character set interpretation
  sl: number,  // Slant angle
  a: number,  // Rotation angle
  m: number,  // Mirror flag (0, 1, 2)
  vh: number,  // Rotate internal text flag (0, 1)
  xs: number,  // Text start point X
  ys: number,  // Text start point Y
  zs: number,  // Text start point Z depth
  text: string,  // Text string
};

type NewGeneralNoteData = {
  txtcw: number,  // Text containment area width
  txtch: number,  // Text containment area height
  justcd: number,  // Justification code (0-3)
  txtcx: number,  // Text containment area location X
  txtcy: number,  // Text containment area location Y
  txtcz: number,  // Z depth from TXTCX,TXTCY plane
  txtag: number,  // Rotation angle of text containment area
  baselx: number,  // Position of first base line X
  basely: number,  // Position of first base line Y
  baselz: number,  // Z depth from BASELX,BASELY plane
  nils: number,  // Normal interline spacing
  ns: number,  // Number of text strings
  strings: NewNoteString[]
};
```

### Type 214 — LeaderArrowEntity

```ts
type LeaderSegment = {
  x: number,
  y: number
};

type LeaderArrowData = {
  n: number,
  ad1: number,  // Arrowhead height
  ad2: number,  // Arrowhead width
  zt: number,  // Z depth
  xh: number,  // Arrowhead coordinate X
  yh: number,  // Arrowhead coordinate Y
  segments: LeaderSegment[]
};
```

### Type 216 — LinearDimensionEntity

```ts
type LinearDimensionData = {
  denote: DEIndex,
  dearrw1: DEIndex,
  dearrw2: DEIndex,
  dewit1: DEIndex,
  dewit2: DEIndex
};
```

### Type 218 — OrdinateDimensionEntity — form-dependent

```ts
type OrdinateDimensionData = {
  form: number,
  denote: DEIndex,  // 1: Pointer to General Note DE
  dewit: DEIndex,  // 2 (Form 0): Pointer to Witness Line or Leader DE
  deord: DEIndex,  // 2 (Form 1): Pointer to Leader (ordinate) DE
  desupp: DEIndex,  // 3 (Form 1): Pointer to Leader (supplementary) DE
};
```

### Type 220 — PointDimensionEntity

```ts
type PointDimensionData = {
  denote: DEIndex,  // Pointer to DE of General Note Entity
  dearrw: DEIndex,  // Pointer to DE of leader (arrow)
  degeom: DEIndex,  // Pointer to DE of the enclosing geometric entity
};
```

### Type 222 — RadiusDimensionEntity — form-dependent

```ts
type RadiusDimensionData = {
  form: number,
  denote: DEIndex,  // 1: Pointer to General Note DE
  dearrw: DEIndex,  // 2: Pointer to Leader (arrow) DE
  xt: number,  // 3: Arc center X
  yt: number,  // 4: Arc center Y
  dearrw2: DEIndex,  // 5 (Form 1 only): Pointer to second Leader DE
};
```

### Type 228 — GeneralSymbolEntity

```ts
type GeneralSymbolData = {
  denote: DEIndex,  // Pointer to DE of General Note Entity
  n: number,  // Number of geometric entities
  geometries: DEIndex[],  // Pointers to DE of geometric entities
  l: number,  // Number of leader (arrow) entities
  leaders: DEIndex[],  // Pointers to DE of leader entities
};
```

### Type 230 — SectionedAreaEntity

```ts
type SectionedAreaData = {
  bndp: DEIndex,  // Pointer to DE of exterior definition curve
  patrn: number,  // Fill pattern code (0-19 standard, 20+ extended)
  xt: number,  // X coordinate through which a line shall pass
  yt: number,  // Y coordinate through which a line shall pass
  zt: number,  // Z depth of lines
  dist: number,  // Normal distance between adjacent lines
  angle: number,  // Angle in radians from XT axis to section lines
  n: number,  // Number of island curves or zero
  islands: DEIndex[],  // Pointers to DE of interior island curves
};
```

### Type 302 — AssociativityDefinitionEntity

```ts
type AssociativityClass = {
  bp: number,  // 1 = back pointers required, 2 = not required
  order: number,  // 1 = ordered class, 2 = unordered class
  n: number,  // Number of items per entry
  item_types: number[],  // Type of each item (1=pointer, 2=value, 3=either)
};

type AssociativityDefinitionData = {
  k: number,  // Number of class definitions
  classes: AssociativityClass[]
};
```

### Type 304 — LineFontDefinitionEntity — form-dependent

```ts
type LineFontDefinitionData = {
  form: number,
  m: number,  // Display flag (0=align with axes, 1=align with tangent)
  l1: DEIndex,  // Pointer to Subfigure Definition Entity
  l2: number,  // Common arc length distance between displays
  l3: number,  // Scale factor
  segments: number[],  // M segment lengths
  bitmask: string,  // Hex bitmask: which segments are visible/blank
};
```

### Type 308 — SubfigureDefinitionEntity

```ts
type SubfigureDefinitionData = {
  depth: number,
  name: string,
  n: number,
  entities: DEIndex[]
};
```

### Type 310 — TextFontDefinitionEntity

```ts
type PenMotion = {
  pf: number,  // Pen up/down flag: 0 = down, 1 = up
  x: number,  // Grid X location
  y: number,  // Grid Y location
};

type CharacterDefinition = {
  ac: number,  // ASCII code
  nx: number,  // Grid X of next character origin
  ny: number,  // Grid Y of next character origin
  nm: number,  // Number of pen motions
  motions: PenMotion[]
};

type TextFontDefinitionData = {
  fc: number,  // Font Code
  fname: string,  // Font Name
  sf: number,  // Supersedes Font (number or negated DE pointer)
  scale: number,  // Grid units per text height unit
  n: number,  // Number of characters
  characters: CharacterDefinition[]
};
```

### Type 312 — TextDisplayTemplateEntity

```ts
type TextDisplayTemplateData = {
  cbw: number,  // Character box width
  cbh: number,  // Character box height
  fc: number,  // Font code (or negative pointer to Type 310)
  sl: number,  // Slant angle of text in radians (pi/2 = no slant)
  a: number,  // Rotation angle in radians
  m: number,  // Mirror flag: 0=none, 1=perpendicular to base, 2=about base
  vh: number,  // Rotate internal text flag: 0=horizontal, 1=vertical
  xs: number,  // X of start (Form 0) or X increment (Form 1)
  ys: number,  // Y of start (Form 0) or Y increment (Form 1)
  zs: number,  // Z of start (Form 0) or Z increment (Form 1)
};
```

### Type 314 — ColorDefinitionEntity

```ts
type ColorDefinitionData = {
  red: number,
  green: number,
  blue: number,
  name: string
};
```

### Type 316 — UnitsDataEntity

```ts
type UnitEntry = {
  typ: string,  // Unit type name (e.g. "LENGTH")
  val: string,  // Unit value (e.g. "MM")
  sf: number,  // Scale factor
};

type UnitsDataData = {
  np: number,  // Number of units
  units: UnitEntry[]
};
```

### Type 320 — NetworkSubfigureDefinitionEntity

```ts
type NetworkSubfigureDefinitionData = {
  depth: number,  // Depth of subfigure nesting
  name: string,  // Subfigure name
  na: number,  // Number of associated entities
  associated: DEIndex[],  // Associated entity pointers
  tf: number,  // Type flag: 0=not specified, 1=logical, 2=physical
  prd: string,  // Primary reference designator
  dptr: DEIndex,  // Pointer to Text Display Template DE
  nc: number,  // Number of connect points
  connects: DEIndex[],  // Connect point pointers (or zero)
};
```

### Type 322 — AttributeTableDefinitionEntity — form-dependent

```ts
type AttributeEntry = {
  at: number,  // Attribute type number
  avdt: number,  // Attribute value data type (0-6)
  avc: number,  // Attribute value count
  values: FieldValue[],  // AVC values (Forms 1, 2 only)
  display_ptrs: DEIndex[],  // AVC display template pointers (Form 2 only)
};

type AttributeTableDefinitionData = {
  name: string,  // NAME — table name
  alt: number,  // ALT — attribute list type
  na: number,  // NA — number of attributes
  attributes: AttributeEntry[]
};
```

### Type 402 — AssociativityInstanceEntity

```ts
type AssociativityInstanceData = {
  n: number,
  entries: DEIndex[]
};
```

### Type 404 — DrawingEntity — form-dependent

```ts
type DrawingView = {
  view: DEIndex,
  x_origin: number,
  y_origin: number,
  angle: number,  // Form 1 only: orientation angle in radians
};

type DrawingData = {
  n: number,
  views: DrawingView[],
  m: number,
  annotations: DEIndex[]
};
```

### Type 406 — PropertyEntity

```ts
type PropertyData = {
  np: number,
  values: FieldValue[]
};
```

#### `FieldValue` — tagged-union value carrier

`FieldValue` is a discriminated union used wherever a parameter's data
type varies by context (Property values, AttributeTableDefinition
values, and any future entity that stores heterogeneous values).

```ts
type FieldValue =
  | { kind: "int",       value: number }    // Integer (§2.2.2.1)
  | { kind: "real",      value: number }    // Real (§2.2.2.2)
  | { kind: "string",    value: string }    // Language String (§2.2.2.4)
  | { kind: "bool",      value: boolean }   // Logical (§2.2.2.6)
  | { kind: "pointer",   value: DEIndex }   // Pointer (§2.2.2.7)
  | { kind: "defaulted", value: null };     // defaulted (§2.2.2.8)
```

Wire-format notes:

- `kind: "bool"` is serialized using the Logical wire form (§2.2.2.6):
  the literal integers `1` (true) or `0` (false). It is an error to
  emit `1.0` / `0.0` or any other encoding for a bool-kind FieldValue.
- `kind: "defaulted"` writes an empty field (nothing between
  delimiters) per §2.2.2.8.
- `kind: "pointer"` writes the DE index as an Integer per §2.2.2.7 and
  is subject to DE cross-reference validation.

Per-context kind restrictions:

- `PropertyData.values` (Type 406) accepts the full union except
  `pointer`. A property value carrying `kind: "pointer"` is an error.
- `AttributeEntry.values` (Type 322 Forms 1/2) accepts only `int`,
  `real`, `string`, and `pointer` — one kind per entry selected by the
  entry's `avdt`. `bool` and `defaulted` do not appear here.

### Type 408 — SubfigureInstanceEntity

```ts
type SubfigureInstanceData = {
  de: DEIndex,
  translation: Vec3,
  scale: number
};
```

### Type 410 — ViewEntity — form-dependent

Form 0 and Form 1 have **mutually exclusive** parameter-data layouts.
The canonical JSON merges both field sets into a single `ViewData`
object for uniformity, but only the form-appropriate subset is
carried on the wire:

- **Form 0** (orthographic): serializes `view_number`, `scale`, and a
  variable-length list of 6 `clip_planes` pointers. The perspective
  fields (`view_plane_normal`, `view_reference_point`,
  `center_of_projection`, `view_up_vector`, `view_plane_distance`,
  `umin`/`umax`/`vmin`/`vmax`, `depth_clipping`, `wmin`/`wmax`) are
  not written and are not read; they may be defaulted in
  canonical JSON and will not round-trip for Form 0.
- **Form 1** (perspective, §4.135): serializes `view_number`, `scale`,
  and the perspective fields listed above. `clip_planes` is not
  written and not read for Form 1.

```ts
type ViewData = {
  form: number,
  view_number: number,
  scale: number,
  clip_planes: DEIndex[],  // Form 0 only; defaulted/ignored for Form 1
  view_plane_normal: Vec3,  // 3-5: VPNX, VPNY, VPNZ (Form 1 only)
  view_reference_point: Vec3,  // 6-8: VRPX, VRPY, VRPZ (Form 1 only)
  center_of_projection: Vec3,  // 9-11: CPX, CPY, CPZ (Form 1 only)
  view_up_vector: Vec3,  // 12-14: VUPX, VUPY, VUPZ (Form 1 only)
  view_plane_distance: number,  // 15: VPD (Form 1 only)
  umin: number,  // 16: UMIN (Form 1 only)
  umax: number,  // 17: UMAX (Form 1 only)
  vmin: number,  // 18: VMIN (Form 1 only)
  vmax: number,  // 19: VMAX (Form 1 only)
  depth_clipping: number,  // 20: DCI (Form 1 only)
  wmin: number,  // 21: WMIN (Form 1 only)
  wmax: number,  // 22: WMAX (Form 1 only)
};
```

### Type 412 — RectangularArrayEntity

```ts
type RectangularArrayData = {
  de: DEIndex,  // 1: Pointer to base entity DE
  s: number,  // 2: Scale factor (default 1.0)
  position: Vec3,  // 3-5: Lower left corner X, Y, Z
  nc: number,  // 6: Number of columns
  nr: number,  // 7: Number of rows
  dx: number,  // 8: Horizontal distance between columns
  dy: number,  // 9: Vertical distance between rows
  ax: number,  // 10: Rotation angle in radians
  lc: number,  // 11: DO-DON'T list count (0=display all)
  ddf: number,  // 12: DO-DON'T flag (0=DO, 1=DON'T)
  positions: number[],  // 13..12+LC: Position numbers
};
```

### Type 414 — CircularArrayEntity

```ts
type CircularArrayData = {
  de: DEIndex,  // 1: Pointer to base entity DE
  ne: number,  // 2: Total number of possible instance locations
  center: Vec3,  // 3-5: Center of imaginary circle X, Y, Z
  r: number,  // 6: Radius of imaginary circle
  as: number,  // 7: Start angle in radians
  ad: number,  // 8: Delta angle in radians
  lc: number,  // 9: DO-DON'T list count (0=display all)
  ddf: number,  // 10: DO-DON'T flag (0=DO, 1=DON'T)
  positions: number[],  // 11..10+LC: Position numbers
};
```

### Type 416 — ExternalReferenceEntity — form-dependent

```ts
type ExternalReferenceData = {
  filename: string,
  entity_name: string
};
```

### Type 418 — NodalLoadConstraintEntity

```ts
type NodalLoadConstraintData = {
  nc: number,  // Total number of cases
  type: number,  // 1 = Loads, 2 = Constraints
  de: DEIndex,  // Pointer to Node
  ptrs: DEIndex[],  // Pointers to Tabular Data Properties
};
```

### Type 420 — NetworkSubfigureInstanceEntity

```ts
type NetworkSubfigureInstanceData = {
  de: DEIndex,  // Pointer to Network Subfigure Definition
  x: number,  // Translation X
  y: number,  // Translation Y
  z: number,  // Translation Z
  xs: number,  // Scale factor X (default 1.0)
  ys: number,  // Scale factor Y (default XS)
  zs: number,  // Scale factor Z (default XS)
  tf: number,  // Type flag: 0=not specified, 1=logical, 2=physical
  prd: string,  // Primary reference designator
  dptr: DEIndex,  // Pointer to Text Display Template DE
  nc: number,  // Number of connect points
  cptrs: DEIndex[],  // Connect point pointers (or zero)
};
```

### Type 430 — SolidInstanceEntity

```ts
type SolidInstanceData = {
  ptr: DEIndex,  // Pointer to the solid
};
```

### Type 502 — VertexListEntity (§4.143.1)

> The Vertex List Entity contains one or more vertices.

```ts
type VertexListData = {
  n: number,
  vertices: Vec3[]
};
```

### Type 504 — EdgeListEntity (§4.144.1)

> The Edge List Entity models an edge or a list of edges.

```ts
type EdgeTuple = {
  curve: DEIndex,  // Model space curve pointer
  svp: DEIndex,  // Start vertex list pointer
  sv: number,  // Start vertex index
  tvp: DEIndex,  // Terminate vertex list pointer
  tv: number,  // Terminate vertex index
};

type EdgeListData = {
  n: number,
  edges: EdgeTuple[]
};
```

### Type 508 — LoopEntity (§4.145)

> The Loop Entity specifies a bound of a face.

```ts
type ParamSpaceCurve = {
  isoparametric: boolean,
  curve: DEIndex
};

type EdgeUse = {
  type: number,  // 0=Edge, 1=Vertex
  edge: DEIndex,  // Pointer to Edge/Vertex List
  ndx: number,  // List index
  orientation: boolean,  // Orientation flag
  k: number,  // Number of param space curves
  param_curves: ParamSpaceCurve[]
};

type LoopData = {
  n: number,
  edge_uses: EdgeUse[]
};
```

### Type 510 — FaceEntity

```ts
type FaceData = {
  surf: DEIndex,  // Underlying surface pointer
  n: number,  // Number of loops
  outer_loop_flag: boolean,
  loops: DEIndex[]
};
```

### Type 514 — ShellEntity

```ts
type FaceUse = {
  face: DEIndex,
  orientation: boolean
};

type ShellData = {
  n: number,
  faces: FaceUse[]
};
```
