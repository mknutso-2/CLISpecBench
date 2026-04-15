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

For curve entities (Types 100, 102, 104, 106 forms 11-13, 110, 112, 126,
130), `--s` is rejected as invalid input. For surface entities (Types 114,
118, 120, 122, 128, 140, 190-198), both `--t` and `--s` are required and
`tangent` is null.

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

*This appendix contains the TypeScript-style `data` schema for each of
the 87 IGES 5.3 entity types covered by this eval, in spec-section order.*

**[TO BE FILLED IN — tracked in `Evals/IGES/PLAN.md` §2. Stage 2 of the
technical-requirements-prompt.md draft will populate this appendix by
extracting struct field lists from the reference implementation.]**
