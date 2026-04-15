# Technical Requirements

For technical compatibility with the evaluation harness, please build the tool
as a single command-line program and emit results in the canonical JSON
format defined below. The binary should be named `iges`.

---

## 1. CLI Contract

The `iges` binary supports five subcommands. All subcommands take a final
`--output <path>` flag and write a JSON file to that path on both success
and error. No subcommand prints anything meaningful to stdout or stderr
that the harness depends on; the output file is the sole result channel.

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
  JSON, any reference to a nonexistent DE index, any evaluation on a
  non-parametric entity, any semantic validation failure described in the
  IGES spec.
- `2` — internal error in the tool itself (panic, out-of-memory,
  unexpected exception).

### 1.3 Success output

On success, the output JSON for `parse`, `query`, `eval`, and `write`'s
JSON echo (if any) conforms to the schemas in §2 / §1.5. For `write` and
`roundtrip`, the primary output is the `.iges` file; the JSON at `--output`
is a terse status object:

```ts
{
  "ok": true,
  "entity_count": number,    // number of entities written
  "bytes_written": number,   // size of the output .iges file in bytes
  "error": null
}
```

### 1.4 Error output

On failure, every subcommand writes a diagnostic JSON object to `--output`:

```ts
{
  "ok": false,
  "error": string,             // human-readable error message
  "spec_ref": string | null,   // e.g. "§2.2.2.1", or null if not attributable
  "line": number | null,       // 1-based input file line number, or null
  "section": "S" | "G" | "D" | "P" | "T" | null,  // IGES section kind
  "diagnostics": Diagnostic[]  // full diagnostic list (may be empty)
}

type Diagnostic = {
  severity: "info" | "warning" | "error",
  message: string,
  spec_ref: string | null,
  line: number | null,
  section: "S" | "G" | "D" | "P" | "T" | null
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
  native parameter domain per §4.25.

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
  parameter domain, `s ∈ [0, 1]` along the generatrix direction per §4.19.
- Type `128` Rational B-Spline Surface: `(t, s)` lie in the native
  `(u, v)` parameter domain declared by the entity's `u0/u1/v0/v1` and
  its two knot vectors (§4.24).
- Type `140` Offset Surface: `(t, s)` in the base surface's native
  `(u, v)` parameter domain per §4.30.
- Types `190`/`192`/`194`/`196`/`198` Analytic Surfaces: `(t, s)` follow
  the native `(u, v)` parameterizations documented in §§4.50–4.54
  (e.g. Cylindrical `u ∈ [0°, 360°]` and `v ∈ (−∞, ∞)`). The CLI uses
  degrees for `u` where the spec uses degrees; radians otherwise.

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

// IGES variant fields (DE fields 4, 5, 13): a positive integer encodes
// a direct value, a negative integer encodes a DE pointer to the
// absolute value.
type LineFontVariant = { kind: "pattern", value: LineFontPattern }
                     | { kind: "pointer", de: DEIndex };
type LevelVariant    = { kind: "level",   value: number }
                     | { kind: "pointer", de: DEIndex };
type ColorVariant    = { kind: "color",   value: Color }
                     | { kind: "pointer", de: DEIndex };

type LineFontPattern = 0 | 1 | 2 | 3 | 4 | 5;  // §2.2.4.4 field 4
type Color           = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;  // §2.2.4.4 field 13
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
  spec_version:         SpecVersion,     // field 23 (default 3)
  drafting_standard:    DraftingStandard, // field 24 (default 0)
  model_timestamp:      Timestamp | null, // field 25 (null = absent)
  app_protocol:         string   // field 26 (default "")
};

type Units = "inches" | "mm" | "see-field-15" | "feet" | "miles"
           | "meters" | "kilometers" | "mils" | "microns"
           | "centimeters" | "microinches";

type SpecVersion = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;
type DraftingStandard = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
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
  color:            ColorVariant,     // field 13
  param_line_count: number,           // field 14 (number of P-section lines)
  form:             number,           // field 15 (form number)
  entity_label:     string,           // field 18 (up to 8 chars)
  entity_subscript: number            // field 19
};

type StatusNumber = {
  blank:       0 | 1,              // 0=visible, 1=blanked
  subordinate: 0 | 1 | 2 | 3,      // 0=indep, 1=physical-dep, 2=logical-dep, 3=both
  entity_use:  0 | 1 | 2 | 3 | 4 | 5 | 6,
  hierarchy:   0 | 1 | 2           // 0=global top-down, 1=global defer, 2=use property
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
catalog, emit a diagnostic at severity `warning` and preserve the raw
PD string in `data.raw_pd: string` so round-trip is still possible.

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
- Fields the writer may re-derive (DE sequence numbers, param_data_ptr,
  param_line_count) are not marked optional in these types — the schemas
  describe the fully-resolved post-parse shape per §2.3 and §2.4.

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
  zt: number,  // common z displacement (IP=1 only)
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
  ay: number,
  az: number
};

type ParametricSplineCurveData = {
  ctype: number,  // Spline type: 1=Linear,2=Quadratic,3=Cubic,4=WF,5=MWF,6=B-spline
  H: number,  // Degree of continuity w.r.t. arc length
  ndim: number,  // Number of dimensions: 2=planar, 3=nonplanar
  breakpoints: number[],  // N+1 breakpoints: T(1)..T(N+1)
  segments: SplineCurveSegment[],  // N segments
  tpx0: number,
  tpy0: number,
  tpz0: number
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
  v0: number,  // parameter range in V
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
  values: number[],  // NV data values for this node
};

type NodalResultsData = {
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
  itop: number,  // Element Topology type
  nl: number,  // Number of layers per results data report location
  dlf: number,  // Data Layer Flag (0..4)
  nrl: number,  // Number of results data report locations
  rdrl: number[],  // Results data report locations (NRL values)
  numv: number,  // Total number of result values (NV*NL*NRL)
  values: number[],  // Result values V(J,K,L) in column-major order
};

type ElementResultsData = {
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
};
```

### Type 152 — WedgeEntity

```ts
type WedgeData = {
  lx: number,  // Edge lengths
  ltx: number,  // X-length at distance LY
};
```

### Type 154 — RightCircularCylinderEntity

```ts
type RightCircularCylinderData = {
  h: number,  // Height
  r: number,  // Radius
};
```

### Type 156 — ConeFrustumEntity

```ts
type ConeFrustumData = {
  h: number,  // Height
  r1: number,  // Larger face radius
  r2: number,  // Smaller face radius (0 for apex)
};
```

### Type 158 — SphereEntity

```ts
type SphereData = {
  radius: number
};
```

### Type 160 — TorusEntity

```ts
type TorusData = {
  r1: number,  // Major radius (axis to disc center)
  r2: number,  // Minor radius (disc radius)
};
```

### Type 162 — SolidOfRevolutionEntity

```ts
type SolidOfRevolutionData = {
  ptr: DEIndex,  // Pointer to curve to be revolved
  f: number,  // Fraction of full rotation
};
```

### Type 164 — SolidOfLinearExtrusionEntity

```ts
type SolidOfLinearExtrusionData = {
  ptr: DEIndex,  // Pointer to closed curve
  length: number,  // Extrusion length
};
```

### Type 168 — EllipsoidEntity

```ts
type EllipsoidData = {
  lx: number,  // Semi-axis lengths
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
  values: (number | string | DEIndex)[],  // AVC values (Forms 1, 2 only)
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

### Type 408 — SubfigureInstanceEntity

```ts
type SubfigureInstanceData = {
  de: DEIndex,
  translation: Vec3,
  scale: number
};
```

### Type 410 — ViewEntity — form-dependent

```ts
type ViewData = {
  form: number,
  view_number: number,
  scale: number,
  clip_planes: DEIndex[],
  view_plane_normal: Vec3,  // 3-5: VPNX, VPNY, VPNZ
  view_reference_point: Vec3,  // 6-8: VRPX, VRPY, VRPZ
  center_of_projection: Vec3,  // 9-11: CPX, CPY, CPZ
  view_up_vector: Vec3,  // 12-14: VUPX, VUPY, VUPZ
  view_plane_distance: number,  // 15: VPD
  umin: number,  // 16: UMIN
  umax: number,  // 17: UMAX
  vmin: number,  // 18: VMIN
  vmax: number,  // 19: VMAX
  depth_clipping: number,  // 20: DCI
  wmin: number,  // 21: WMIN
  wmax: number,  // 22: WMAX
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
  ptrs: DEIndex[],  // Pointers to Tabular Data Properties
};
```

### Type 420 — NetworkSubfigureInstanceEntity

```ts
type NetworkSubfigureInstanceData = {
  x: number,  // Translation X
  y: number,  // Translation Y
  z: number,  // Translation Z
  xs: number,  // Scale factor X (default 1.0)
  ys: number,  // Scale factor Y (default XS)
  zs: number,  // Scale factor Z (default XS)
  tf: number,  // Type flag: 0=not specified, 1=logical, 2=physical
  prd: string,  // Primary reference designator
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
