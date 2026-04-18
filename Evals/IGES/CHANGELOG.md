# IGES Changelog

## v1.0.13 — unreleased

### Added

- `tests/test_validation.py`, porting the SDK's structural-validation
  surface to the CLI by asserting `iges parse` rejects:
  - invalid `xform_matrix` and `view` DE references
  - negative entity types
  - zero `param_line_count` on non-null entities
  - non-positive `model_space_scale`
- `tests/test_error_envelope.py`, verifying the shipped diagnostic JSON
  shape for `parse` / `query` / `eval` failures.
- `tests/test_directory_entry.py`, covering the `DirectoryEntry`
  contract directly rather than only `entity.data`.
- `tests/test_entity_roundtrips.py` Form 0 roundtrips for analytic
  surfaces `190 / 192 / 194 / 196 / 198`.
- `tests/test_entity_roundtrips.py` roundtrips for Type `110` Forms 1
  (semi-bounded line) and 2 (unbounded line), Type `106` Form 11
  (2D planar linear path), and Type `322` Forms 0 and 1 (Attribute
  Table Definition without values, and with values but without display
  pointers).
- `tests/test_geometric_eval.py` Line Form 1 / Form 2 eval tests
  covering the extended parameter domains (t > 1 and t < 0) documented
  in TR §1.6.
- `tests/test_validation.py` parameterized non-positive rejection for
  Global fields 8 / 9 / 10 / 11 / 16 / 19, plus a dedicated rejection
  test for degenerate zero-length Line entities (spec §3.2.5).

### Changed

- `reference-implementation-cpp/src/main.cpp` now runs structural
  validation after parsing and before `parse` / `query` / `eval` /
  `roundtrip` proceed on invalid files.
- `reference-implementation-cpp/src/model/validate.cpp` now emits
  error-severity diagnostics for failing structural checks.
- `prompt/technical-requirements-prompt.md` now describes the shipped
  structural-validation surface precisely instead of overclaiming that
  every entity-data DE pointer is validated at parse time.
- `prompt/technical-requirements-prompt.md` now matches the shipped CLI
  behavior for `write` / `roundtrip` outputs, error-envelope shape, the
  byte-idempotence fixed-point rule, unsupported-entity handling, and
  the documented Type `122` / `130` / `140` evaluation conventions.
- Type `126` `plane_normal` is now documented as always-present, with a
  zero vector for non-planar curves.
- Tightened the new dedicated entity tests so Circular Arc uses a real
  quarter-arc fixture and Composite Curve uses a spec-legal non-empty
  constituent list.
- Tightened malformed-input assertions to require exit code `1` for
  invalid user input and added missing coverage for `label_display`,
  even-DE rejection, Type `106` Form `63`, and the `eval` CLI shape
  rules.
- Removed duplicate or non-independent checks from overlapping suites,
  including the line arc-length-from-endpoints assertion and the weaker
  subset overlaps between the dedicated roundtrip files and the generic
  entity roundtrip coverage.
- `reference-implementation-cpp/src/model/validate.cpp` now rejects
  non-positive values for Global fields 8 / 9 / 10 / 11 / 16 / 19
  (`sp_magnitude`, `sp_significance`, `dp_magnitude`, `dp_significance`,
  `max_line_weight_grads`, `min_resolution`). Previously only fields
  7 and 13 were validated; TR §1.2 calls for the same treatment across
  all required positive Global numeric fields.
- `reference-implementation-cpp/src/entities/line_entity.cpp` now
  rejects degenerate Line entities whose start and terminate points
  are coincident, enforcing spec §3.2.5 "All curves shall have non-zero
  arc length."
- Test `test_line_entity.py::test_line_at_origin` renamed to
  `test_line_starting_at_origin` and updated to use a non-degenerate
  Line; the prior version relied on the (invalid) zero-length-Line
  behavior the ref-impl now rejects.

### Validated

- `py -3 -m pytest Evals/IGES/tests --language=cpp` passes locally
  (`252 passed`, 2026-04-18).
- `py -3 -m pytest Evals/IGES/tests --language=cpp` passes locally
  (`228 passed`, 2026-04-17).
- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`219 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.12 — unreleased

### Added

- Dedicated CLI coverage in `tests/test_core_entities.py` for:
  - Null / Circular Arc / Composite Curve (0 / 100 / 102)
  - Point / Direction / Transformation Matrix (116 / 123 / 124)
- Dedicated CLI coverage in `tests/test_structure_and_view_entities.py`
  for:
  - Subfigure Definition / Property / Drawing (308 / 406 / 404)
  - Subfigure Instance / View (408 / 410)
  - Rectangular Array / Circular Array (412 / 414)

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`211 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.11 — unreleased

### Added

- CLI-level spline/NURBS/FEA coverage in
  `tests/test_spline_and_fea_entities.py` for:
  - Parametric Spline Curve / Surface (112 / 114)
  - Rational B-Spline Curve / Surface (126 / 128)
  - Connect Point / Finite Element (132 / 136)

### Changed

- `prompt/technical-requirements-prompt.md` now includes Type `126`
  `plane_normal`, matching the shipped canonical JSON schema.

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`198 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.10 — unreleased

### Added

- CLI-level surface-boundary/reference coverage in
  `tests/test_surface_boundary_entities.py` for:
  - Boundary / Curve on Parametric Surface / Bounded Surface /
    Trimmed Surface (141 / 142 / 143 / 144)
  - Associativity Instance (402)
  - External Reference (416, Forms 0 / 1 / 2)

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`192 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.9 — unreleased

### Added

- CLI-level solid/CSG coverage in `tests/test_solid_entities.py` for:
  - Block / Right Angular Wedge (150 / 152)
  - Right Circular Cylinder / Cone Frustum / Sphere / Torus
    (154 / 156 / 158 / 160)
  - Solid of Revolution / Solid of Linear Extrusion / Ellipsoid
    (162 / 164 / 168)
  - Boolean Tree / Selected Component / Solid Assembly
    (180 / 182 / 184)

### Changed

- `Evals/IGES-SDK/scripts/generate_entity_json.py` and
  `extract_entity_schemas.py` now expand comma-separated member
  declarations such as `Real lx = 0.0, ly = 0.0, lz = 0.0;` instead of
  silently serializing only the first field.
- Regenerated `reference-implementation-cpp/src/json/entity_json.hpp`
  so the canonical JSON now includes the missing multi-field members on
  compact entity structs, including:
  - solid primitives `150 / 152 / 154 / 156 / 158 / 160 / 168`
  - `112` Parametric Spline Curve coefficients / terminal derivatives
  - `128` Rational B-Spline Surface parameter-range endpoints
  - `162 / 164` solid axis/direction vectors
- `prompt/technical-requirements-prompt.md` now matches the corrected
  canonical JSON for those entities.

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`182 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.8 — unreleased

### Added

- CLI-level metadata/reference coverage in
  `tests/test_metadata_entities.py` for:
  - Associativity Definition (302)
  - Line Font Definition (304, Forms 1 and 2)
  - Text Font Definition (310)
  - Text Display Template (312)
  - Color Definition (314)
  - Units Data (316)
  - Attribute Table Definition (322, Form 2)
  - Solid Instance (430)

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`170 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.7 — unreleased

### Added

- Regression coverage in `tests/test_pointer_backed_fields.py` for
  brace-default-initialized DE-pointer fields on:
  - Plane (108)
  - Node (134)
  - Nodal Displacement / Results / Element Results (138 / 146 / 148)
  - Network Subfigure Definition / Instance (320 / 420)
  - Nodal Load/Constraint (418)

### Changed

- `Evals/IGES-SDK/scripts/generate_entity_json.py` and
  `extract_entity_schemas.py` now preserve brace-default-initialized
  fields such as `DEIndex ptr{0};` instead of silently dropping them.
- Regenerated `reference-implementation-cpp/src/json/entity_json.hpp`
  so the ref-impl's canonical JSON includes the previously omitted
  pointer fields.
- `prompt/technical-requirements-prompt.md` now matches the corrected
  canonical JSON for Types `108`, `134`, `138`, `146`, `148`, `320`,
  `418`, and `420`.
- Existing tests that depended on the buggy omission now pass explicit
  default values (`ptr: 0`, `dptr: 0`) in their canonical JSON payloads.

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`161 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.6 — unreleased

### Added

- CLI-level annotation/dimension coverage in
  `tests/test_annotation_entities.py` for:
  - Angular Dimension (202)
  - Curve / Diameter Dimension (204 / 206)
  - Flag Note / General Note (208 / 212)
  - General Label (210)
  - Leader Arrow (214)
  - Linear Dimension (216)
  - New General Note / Ordinate Dimension (213 / 218)
  - Point / Radius Dimension (220 / 222)
  - General Symbol (228)
  - Sectioned Area (230)

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`153 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.5 — unreleased

### Changed

- `prompt/technical-requirements-prompt.md` now matches the shipped JSON
  schema for:
  - `GlobalSection.units`, `spec_version`, and `drafting_std`
  - `DirectoryEntry.status`
  - raw signed-integer `line_font`, `level`, and `color` fields
- `Evals/IGES-SDK/src/writer/file_writer.cpp` now mirrors the ref-impl's
  custom-delimiter PD prefix handling.
- The empty-start-lines writer test now asserts the spec-level contract
  ("one or more blank Start records") instead of pinning the current
  ref-impl's exact choice of one line.

### Validated

- Prompt/schema review reconciled against the C++ ref-impl and hidden
  test expectations on 2026-04-16.

## v1.0.4 — unreleased

### Added

- Additional topology/boundary round-trip coverage in
  `tests/test_entity_roundtrips.py` for:
  - MSBO (186)
  - Vertex List (502)
  - Edge List (504)
  - Loop (508)
  - Face (510)
  - Shell (514)

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`138 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.3 — unreleased

### Added

- Additional per-entity round-trip coverage in `tests/test_entity_roundtrips.py`
  for:
  - Conic Arc (104)
  - Copious Data (106)
  - Ruled Surface (118)
  - Surface of Revolution (120)
  - Tabulated Cylinder (122)
  - Flash (125)
  - Offset Curve (130)
  - Offset Surface (140)
  - Plane / Cylindrical / Conical / Spherical / Toroidal Surfaces
    (190 / 192 / 194 / 196 / 198)

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`138 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.2 — unreleased

### Added

- Writer-focused hidden coverage:
  - `tests/test_writer_global.py`
  - `tests/test_writer_format.py`
  - `tests/test_writer_param.py`
  - `tests/test_writer_file.py`

### Changed

- `write_global_section()` now emits Global field 26
  (`app_protocol`) instead of silently dropping non-empty values.

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`138 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.1 — unreleased

### Added

- CLI-level ports of the IGES-SDK's spec-backed file-format coverage:
  - `tests/test_data_types.py`
  - `tests/test_free_format.py`
  - `tests/test_sections.py`
- `tests/raw_iges_support.py` for constructing and inspecting raw
  physical IGES records in section-format tests.

### Changed

- The C++ reference implementation now honors non-default Global
  parameter/record delimiters when writing and re-reading PD records,
  including the entity-type prefix on each PD record.
- Global-section parsing now surfaces invalid field diagnostics instead
  of silently defaulting malformed tokens.
- `test_malformed.py`'s minimal-valid fixture now encodes `"site"` with
  the correct Hollerith count.

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`138 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).

## v1.0.0 — unreleased

Initial IGES eval release. The task is now functional end-to-end with a
buildable C++ reference implementation, prompt/docs bundle, and full
Python CLI test suite.

### Added

- `iges` task registration in `src/swe_buildbench/harness/task.py`.
- Full IGES prompt bundle:
  - `prompt/base-prompt.md`
  - `prompt/technical-requirements-prompt.md`
  - `prompt/docs/iges-5-3-specification.md`
  - `prompt/docs/figures/` (86 copied figures)
- C++ reference implementation under
  `reference-implementation-cpp/` with all five CLI subcommands:
  `parse`, `write`, `query`, `eval`, and `roundtrip`.
- Python CLI test suite under `Evals/IGES/tests/` covering build,
  malformed input, line/entity round-trips, fixture parsing,
  roundtrip behavior, defaulted fields, and geometric evaluation.
- Parametric evaluation coverage for the contract's curve/surface types,
  including Composite Curve, Offset Curve, Ruled Surface, Surface of
  Revolution, Tabulated Cylinder, Offset Surface, Conic Arc, and
  analytic surfaces `190/192/194/196/198`.

### Changed

- Evaluation dispatch now threads referenced-entity resolution and DE
  transformation matrices through nested curve/surface sampling.
- `dispatch.cpp` is regenerated via a binary-safe workflow to avoid the
  accidental embedded-NUL corruption seen during development.
- IGES-SDK helper scripts touched during the port are now Ruff- and
  Pyright-clean.

### Validated

- `uv run pytest Evals/IGES/tests --language=cpp -q` passes locally
  (`138 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).
- First real-agent smoke run completed cleanly:
  `iges / claude-code / claude-opus-4-6` scored `43/93`
  (`exit_reason: "completed"`). The agent voluntarily exited and
  claimed full success despite partial correctness, so the low score was
  model behavior rather than harness/auth/rate-limit failure.
