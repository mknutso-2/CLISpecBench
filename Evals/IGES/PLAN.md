# IGES Eval — Port Plan

Checklist for porting [IGES-SDK](../IGES-SDK) into a full SWE-BuildBench eval.
Mark items off (`[x]`) as they land. Keep section numbering stable so commits
can reference section IDs.

---

## 0. Naming & Registration

- [x] Create `Evals/IGES/` directory.
- [x] `Evals/IGES/README.md` — initial README.
- [x] `Evals/IGES/PLAN.md` — this file.
- [x] `Evals/IGES/VERSION` = `1.0.0`.
- [x] `Evals/IGES/CHANGELOG.md` — initial `1.0.0 — initial release` entry.
- [x] Register task IDs in `src/swe_buildbench/harness/task.py` `_KNOWN_TASKS`:
  - [x] `"iges": _RegisteredTask("Evals/IGES")`
  - [ ] (later) `iges-py`, `iges-js`, `iges-rs` once those ref-impls exist.
- [ ] Decide disposition of the original `Evals/IGES-SDK/` directory once the
      port completes (keep as snapshot vs. delete). Leave in place until the
      port is green end-to-end.

## 1. CLI Contract

Five subcommands on a single `iges` binary. All write JSON on both success
and error. Exit codes: `0` success, `1` invalid input, `2` internal error.

- [x] `iges parse --input <file.iges> --output <file.json>` — full parse to
      canonical IGES-JSON.
- [x] `iges write --input <file.json> --output <file.iges>` — inverse.
- [x] `iges query --input <file.iges> --de <n> --output <entity.json>` —
      single-entity extract by DE sequence number.
- [x] `iges eval --input <file.iges> --de <n> --t <f> --output <point.json>` —
      geometric evaluation for parametric entities.
- [x] `iges roundtrip --input <file.iges> --output <out.iges>` — one-shot
      parse+write for idempotence testing.
- [x] Diagnostic JSON shape defined:
      `{"error": "...", "spec_ref": "§X.Y", "line": N, "section": "..."}`
      + full `diagnostics[]` list.

## 2. Canonical IGES-JSON Schema

Lives in `prompt/technical-requirements-prompt.md`. Machine-extracted from
`IGES-SDK/src/entities/*.hpp` structs, then hand-edited for clarity.

- [x] Top-level shape: `{start_lines, global, entities[]}`.
- [x] `global` — all 26 named fields with spec-defined defaults.
- [x] `directory_entry` — all 20 named fields per entity.
- [x] `entity.data` schema for each of the 87 entity types. **Mechanically
      extracted via `Evals/IGES-SDK/scripts/extract_entity_schemas.py` into
      `prompt/technical-requirements-prompt.md` appendix A.** Spot-fix
      needed: `SplineSurfacePatch` fixed-size `Real[16]` arrays patched
      manually; all other 86 entities extracted cleanly. Iterative
      hand-polish of per-entity comments may follow.
- [x] Schema format decided: TypeScript-style for `data` payloads, prose
      for the envelope and CLI contract.
- [x] Form-dependent entity schemas (Drawing/External Ref/Line Font Def/
      Ordinate Dim/Radius Dim/View/Surfaces 190-198/Attr Table Def) called
      out. Current approach: each form-dependent entity is marked
      `— form-dependent` in its section heading and emits the union of all
      fields; the agent is pointed at the spec sections for form-to-field
      mapping (appendix A preamble). Consider per-form literal-union
      narrowing as a follow-up if agents conflate forms in practice.
- [x] Numerical tolerance for `eval` picked and documented:
      relative `1e-9`, absolute `1e-12` near zero.

## 3. Prompt Authoring

```
prompt/
  base-prompt.md
  technical-requirements-prompt.md
  docs/
    iges-5-3-specification.md
    figures/
```

- [x] `docs/iges-5-3-specification.md` — moved from `IGES-SDK/` unchanged.
- [x] `docs/figures/` — copied 86 PNGs from `IGES-SDK/figures/` unchanged
      (counts 036a/036b as separate files).
- [x] `base-prompt.md` — domain-expert prompt drafted.
- [ ] `technical-requirements-prompt.md` — CLI contract + full JSON schema
      (§1 + §2 above).
- [ ] Confirm total prompt token count fits within a baseline agent's
      single-turn context (test with claude-opus-4-6).
- [ ] Decide whether to ship `IGES5-3.pdf` in `docs/` (license check) or
      rely on the transcribed `.md` alone. Default: `.md` only.

## 4. Reference Implementation (C++)

`Evals/IGES/reference-implementation-cpp/`.

- [x] Copy `IGES-SDK/src/{types.hpp,types.cpp,entities/,model/,parser/,writer/}`
      verbatim into `reference-implementation-cpp/src/`.
- [x] New `src/main.cpp` implementing subcommand dispatch for all five
      subcommands.
- [x] Add `nlohmann/json` as a header-only dep (fetched via CMake
      FetchContent or vendored).
- [x] Per-entity JSON serialization: `to_json` / `from_json` free functions
      mirroring the existing `parse_*_entity` / `write_*_entity` pattern —
      87 small functions in a new `src/json/entity_json.{hpp,cpp}`.
- [x] `CMakeLists.txt` producing a single `iges` executable target (no
      Catch2, no library target). Mirror `Evals/CNCSim/reference-implementation-cpp/CMakeLists.txt`
      shape.
- [x] Executable name matches `EVAL_CONFIG.preferred_executable_name="iges"`.
- [x] Ref-impl passes the full Python test suite (54 tests, 2026-04-14).

## 5. Tests (Catch2 → Python CLI)

`Evals/IGES/tests/`.

- [x] `conftest.py` — copy CNCSim's, repoint `EVAL_CONFIG` to `iges`.
- [x] `iges_support.py` — test helpers. Shape landed: canonical-JSON
      builders (`default_global`, `default_directory_entry`,
      `make_entity`, `wrap_entities`, `single_line_document`) + CLI
      drivers (`write_iges_from_json`, `parse_iges_to_json`,
      `query_entity`, `evaluate_entity`, `roundtrip_iges`,
      `semantic_roundtrip_json`).
- [x] `data/ex1.iges`, `data/ex2.iges`, `data/ex3.iges` — copied from
      `Evals/IGES-SDK/tests/data/` unchanged.
- [x] `test_build.py` — smoke test that the `iges` binary builds and is
      invokable (mirror CNCSim's).
- [x] **Pilot port: Line entity end-to-end** — `test_line_entity.py`,
      10 tests, all passing against the C++ ref-impl.
- [ ] **File format / data type tests** (higher value — port first)
  - [ ] `test_2_2_2_*.cpp` → `test_data_types.py` (integer, real, string,
        pointer, logical).
  - [ ] `test_2_2_3_*.cpp` → `test_free_format.py` (delimiters, free format).
  - [ ] `test_2_2_4_*.cpp` → `test_sections.py` (Start/Global/DE/PD/Terminate).
- [ ] **Per-entity tests** — 87 entity-level ports. Broad coverage
      (round-trip of `entity.data` for 14 entity types) now lives in
      `test_entity_roundtrips.py`; per-entity `§4.X` files below are still
      desirable for behavioural assertions beyond JSON round-tripping.
  - [ ] §4.1 Null (0) — covered in `test_entity_roundtrips.py`
  - [ ] §4.3 Circular Arc (100) — covered in `test_entity_roundtrips.py`
        + `test_geometric_eval.py`
  - [ ] §4.4 Composite Curve (102) — covered in `test_entity_roundtrips.py`
  - [ ] §4.5 Conic Arc / Copious Data (104 / 106)
  - [ ] §4.12 Plane (108) — covered in `test_entity_roundtrips.py`
  - [x] §4.13 Line (110) — pilot, `test_line_entity.py`
  - [ ] §4.14 Parametric Spline Curve (112)
  - [ ] §4.15 Parametric Spline Surface (114)
  - [ ] §4.16 Point (116) — covered in `test_entity_roundtrips.py`
  - [ ] §4.17 Ruled Surface (118)
  - [ ] §4.18 Surface of Revolution (120)
  - [ ] §4.19 Tabulated Cylinder (122)
  - [ ] §4.20 Direction (123) — covered in `test_entity_roundtrips.py`
  - [ ] §4.21 Transformation Matrix (124) — covered in `test_entity_roundtrips.py`
  - [ ] §4.22 Flash (125)
  - [ ] §4.23 Rational B-Spline Curve (126)
  - [ ] §4.24 Rational B-Spline Surface (128)
  - [ ] §4.25 Offset Curve (130)
  - [ ] §4.26 Connect Point (132)
  - [ ] §4.27 Node (134)
  - [ ] §4.28 Finite Element (136)
  - [ ] §4.29 Nodal Displacement (138)
  - [ ] §4.30 Offset Surface (140)
  - [ ] §4.31 Boundary (141)
  - [ ] §4.32 Curve on Parametric Surface (142)
  - [ ] §4.33 Bounded Surface (143)
  - [ ] §4.34 Trimmed Surface (144)
  - [ ] §4.35 Nodal Results (146)
  - [ ] §4.36 Element Results (148)
  - [ ] §4.37 Block (150)
  - [ ] §4.38 Right Angular Wedge (152)
  - [ ] §4.39 Right Circular Cylinder (154)
  - [ ] §4.40 Right Circular Cone Frustum (156)
  - [ ] §4.41 Sphere (158)
  - [ ] §4.42 Torus (160)
  - [ ] §4.43 Solid of Revolution (162)
  - [ ] §4.44 Solid of Linear Extrusion (164)
  - [ ] §4.45 Ellipsoid (168)
  - [ ] §4.46 Boolean Tree (180)
  - [ ] §4.47 Selected Component (182)
  - [ ] §4.48 Solid Assembly (184)
  - [ ] §4.49 MSBO (186)
  - [ ] §4.50 Plane Surface (190)
  - [ ] §4.51 Cylindrical Surface (192)
  - [ ] §4.52 Conical Surface (194)
  - [ ] §4.53 Spherical Surface (196)
  - [ ] §4.54 Toroidal Surface (198)
  - [ ] §4.55 Angular Dimension (202)
  - [ ] §4.56 Curve / Diameter Dimension (204 / 206)
  - [ ] §4.57 General Label (210)
  - [ ] §4.58 Flag Note / General Note (208 / 212)
  - [ ] §4.59 Leader Arrow (214)
  - [ ] §4.60 Linear Dimension (216)
  - [ ] §4.61 New General Note / Ordinate Dimension (213 / 218)
  - [ ] §4.63 Radius Dimension (222)
  - [ ] §4.65 Point Dimension (220)
  - [ ] §4.67 General Symbol (228)
  - [ ] §4.68 Sectioned Area (230)
  - [ ] §4.69 Associativity Definition (302)
  - [ ] §4.74 Text Font Definition (310)
  - [ ] §4.75 Text Display Template (312)
  - [ ] §4.77 Units Data (316)
  - [ ] §4.78 Network Subfigure Definition (320)
  - [ ] §4.79 Attribute Table Definition (322)
  - [ ] §4.90 Associativity Instance (402)
  - [ ] §4.91 Line Font Definition (304)
  - [ ] §4.92 Subfigure Definition (308) — covered in `test_entity_roundtrips.py`
  - [ ] §4.93 Color Definition (314)
  - [ ] §4.97 Property (406) — covered in `test_entity_roundtrips.py`
  - [ ] §4.131 Drawing (404) — covered in `test_entity_roundtrips.py`
  - [ ] §4.133 Subfigure Instance (408) — covered in `test_entity_roundtrips.py`
  - [ ] §4.134 View (410) — covered in `test_entity_roundtrips.py`
  - [ ] §4.135 External Reference (416)
  - [ ] §4.136 Rectangular Array (412) — covered in `test_defaulted_fields.py`
  - [ ] §4.137 Circular Array (414) — covered in `test_entity_roundtrips.py`
  - [ ] §4.139 Nodal Load/Constraint (418)
  - [ ] §4.140 Network Subfigure Instance (420)
  - [ ] §4.142 Solid Instance (430)
  - [ ] §4.143 Vertex List (502)
  - [ ] §4.144 Edge List (504)
  - [ ] §4.145 Loop (508)
  - [ ] §4.146 Face (510)
  - [ ] §4.147 Shell (514)
- [ ] **Writer-specific tests**
  - [ ] `test_writer_format.cpp` → `test_writer_format.py` (Hollerith,
        integer, real, column packing).
  - [ ] `test_writer_global.cpp` → `test_writer_global.py`.
  - [ ] `test_writer_param.cpp` → `test_writer_param.py`.
  - [ ] `test_writer_file.cpp` → `test_writer_file.py`.
  - [x] `test_writer_roundtrip*.cpp` → `test_roundtrip_cli.py` —
        parametrized over ex1/ex2/ex3: entity-count + per-entity data
        preservation + byte-level idempotence after one normalization
        pass. Library-internal `test_writer_roundtrip*.cpp` per-entity
        cases are covered by `test_entity_roundtrips.py`.
- [x] **Geometric evaluation** — `test_geometric_eval.py`, 5 tests:
      Circular Arc evaluation at start/end/mid-angle, z-plane respect,
      eval-on-non-parametric rejected. Ports the CLI-observable subset
      of `test_geometric_evaluation.cpp`; B-spline / surface / block /
      sphere / cylinder evaluation is a follow-up once the Arc contract
      is settled (see Open Questions).
- [x] **Malformed input** — `test_malformed.py`, 6 tests covering
      MAL-1/MAL-2/MAL-10/MAL-12 plus query-on-nonexistent-DE and
      random-bytes-input. Asserts `ok:false` + `error` field on the
      diagnostic envelope (spec_ref / line exact values left
      implementation-dependent).
- [ ] **Validation**
  - [ ] `test_validate.cpp` → `test_validation.py`.
- [x] **Reference fixtures** — `test_reference_fixtures.py`, 6 tests,
      parses ex1/ex2/ex3 via `iges parse` and asserts entity counts +
      globals + per-type mix. Ported from
      `Evals/IGES-SDK/tests/integration/test_reference_files.cpp`.
- [x] **Defaulted-field regression coverage** (from Known Issues
      2026-04-14) — `test_defaulted_fields.py`, 3 tests:
  - [x] Connect Point (§4.26) with empty `cid` / `cfn` round-trips to `""`.
  - [x] Network Subfigure Definition (§4.22) with empty `prd` round-trips
        to `""`.
  - [x] Rectangular Array (§4.41) with omitted `ddf` round-trips to `0`.
  - [x] `ex1.iges` parses with 21 entities (asserted in
        `test_reference_fixtures.py::test_ex1_parses_with_expected_global_and_entity_count`).

## 6. Eval Design Doc

- [x] `Evals/IGES/IGES-Design.md` — 6 sections:
  - [x] Why this eval exists (CNCSim saturation, harder spec-comprehension).
  - [x] CLI contract rationale (why 5 subcommands).
  - [x] IGES-JSON schema design choices.
  - [x] Scoping: entities in scope, explicit non-goals (Binary Format,
        MACRO, drafting-only, Compressed Format).
  - [x] Known spec ambiguities the tests deliberately do not assert
        (includes the CircularArc `t`-parameterization finding — see
        Open Questions below).
  - [x] Reference implementation roles.

## 7. End-to-End Validation

- [ ] `pytest Evals/IGES/tests --language=cpp` passes against the ref-impl.
- [ ] `uv run ruff check` clean.
- [ ] `uv run pyright` clean.
- [ ] Smoke-test with one real agent run (baseline: `swe-buildbench run
      --task iges --agent claude-code --model claude-opus-4-6 --runs 1`) —
      confirm the agent builds something, the harness scores it, and the
      result JSON is sensible.
- [ ] Record baseline pass rates before declaring 1.0.0 ready.

## 8. Follow-up (post-1.0.0)

- [ ] `reference-implementation-py/` — Python ref-impl, register `iges-py`.
- [ ] `reference-implementation-js/` — JavaScript ref-impl, register
      `iges-js`.
- [ ] `reference-implementation-rs/` — Rust ref-impl, register `iges-rs`.
- [ ] Decide whether to split `iges-lite` back out if agents are scoring
      near-zero on full (fallback plan only).

---

## Open Questions

Decisions that need to be made before or during the port. Remove each item
once resolved (and capture the decision in `IGES-Design.md`).

<!-- Resolved: TypeScript-style for per-entity data, prose for CLI
     contract and envelope. See technical-requirements-prompt.md. -->

- [ ] Whether to include `IGES5-3.pdf` in `docs/` (license review needed).
- [ ] Final `eval` subcommand surface — just `{x,y,z}`, or also first/second
      derivatives?
- [ ] Tolerance policy — single global tolerance, or per-entity-type?
- [ ] Whether `query --de <n>` on an out-of-range index is exit 1
      (malformed input) or a distinct error class.
<!-- Resolved 2026-04-15: chose (b) — native per-entity parameters,
     documented in technical-requirements-prompt.md §1.6. See Codex
     review transcript codex-conversations/2026-04-15-08-47-iges-arc-t-convention.md
     and IGES-Design.md §5. Decisive evidence: Line Forms 1/2 have
     infinite native domains (spec §4.13 lines 2628-2629) so [0,1]
     normalization is literally undefined for them; the spec itself
     gives per-entity "default parameterization if required" rather
     than a global one. -->

## `iges eval` expansion (in-progress 2026-04-15)

The contract in `technical-requirements-prompt.md` §1.5 lists curves
`100, 102, 104, 106/11/12/63, 110, 112, 126, 130` and surfaces
`114, 118, 120, 122, 128, 140, 190/192/194/196/198` as parametric.
The C++ ref-impl + SDK only implement `evaluate()` for 6 of those
(`100, 110, 112, 114, 126, 128`). Broadening both to match, using an
**11-commit staging plan**. Commits land incrementally; each is
self-contained (ref-impl change + dispatch regen + tests + green full
suite). No `VERSION` / `CHANGELOG.md` bumps until after first agent
run — per user rule, eval is still in active pre-first-run dev.

### Architecture of the expansion

Self-contained curves/surfaces (those whose evaluation depends only on
their own PD fields) get member `Vec3 evaluate(Real t)` / `evaluate(Real
t, Real s)` methods in `Evals/IGES-SDK/src/entities/*.hpp`. The
generator `Evals/IGES-SDK/scripts/generate_dispatch.py` auto-detects
these via regex (`EVAL_CURVE_RE` / `EVAL_SURFACE_RE`) and emits switch
cases into `Evals/IGES/reference-implementation-cpp/src/json/dispatch.cpp`.

Resolver-using entities (those that reference other entities by DE
pointer — Composite Curve 102, Ruled Surface 118, Surface of Revolution
120, Offset Curve 130) get hand-written free functions in
`Evals/IGES/reference-implementation-cpp/src/json/eval_helpers.{hpp,cpp}`
and are registered in the generator's `RESOLVER_USING` map with kind
`"curve"` / `"surface"` / `"surface_form"`.

Shared helper `curve_native_span(type, form, data) → (v0, v1)` in
`eval_helpers.cpp` returns the native parameter domain of a curve
referenced by DE pointer — used by composite/offset/ruled/SoR
constructions that need to know their constituent curves' parameter
ranges without fully evaluating them.

### Regeneration + Windows CRLF quirk

After editing either a `RESOLVER_USING` entry or an entity's header,
regenerate dispatch with:

```bash
python Evals/IGES-SDK/scripts/generate_dispatch.py \
    > Evals/IGES/reference-implementation-cpp/src/json/dispatch.cpp
```

**Then normalize line endings** — Python's stdout redirection on
Windows inserts `\r\n` and breaks the build's cross-platform line
endings. Run immediately after:

```python
from pathlib import Path
p = Path("Evals/IGES/reference-implementation-cpp/src/json/dispatch.cpp")
p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
```

### Landed commits

- [x] §1.5 reverted to broad type list (2026-04-15, `eec0219`).
- [x] §1.6 expanded to cover all contract types' native `t` / `(t, s)`.
- [x] §1.6 sweep-convention note: forward sweep `0 < Δ ≤ 2π` for
      Type 100 and Type 120 angle ranges, full turn encoded as
      `ta = sa + 2π`, hidden tests do not probe complementary arc
      (commit `4bcc2d9`).
- [x] **Commit 1** `5f5aaa4` — Thread `EntityResolver` through
      `evaluate_entity_dispatch`.
- [x] **Commit 2** `d1b472e` — Copious Data (106) forms 11/12/63
      polyline evaluator.
- [x] **Commit 3** `3c484e6` — Composite Curve (102) evaluator.
- [x] **Commit 4** `8dfae4d` — Offset Curve (130) `FLAG=1` evaluator
      (FLAG 2/3 out of scope, documented in §1.6).
- [x] **Commit 5** `5b00097` — Ruled Surface (118) evaluator with
      `surface_form` kind to thread `form` for Form-0 vs Form-1
      normalization.
- [x] **Commit 6** (was rolled into commit 1 — resolver threading).
- [x] **Commit 7** `4bcc2d9` — Surface of Revolution (120) evaluator
      using Rodrigues' rotation formula; axis entity must be Type 110
      Line. Test angle range padded to `sa=-0.1, ta=π+0.1` to
      sidestep `%.15g` last-bit rounding of π.

### Remaining commits

- [ ] **Commit 8** — Tabulated Cylinder (122). Self-contained
      directrix-dependent surface per §4.19: evaluates the directrix
      entity at native parameter `t` and translates by
      `s · (LX-DX, LY-DY, LZ-DZ)` where `(LX, LY, LZ)` is the
      generatrix terminate point and `(DX, DY, DZ)` is the directrix
      start point (implicitly the first point of the directrix).
      Resolver-using — add entry `122: ("tabulated_cylinder", "surface")`
      to `RESOLVER_USING` and write `evaluate_tabulated_cylinder(ent,
      t, s, resolver)` in `eval_helpers.cpp`. `s ∈ [0, 1]` per §1.6.
      Tests: cylinder over a Line directrix (trivial check), cylinder
      over a Circular Arc directrix (check rotation preserved along
      the sweep direction).

- [ ] **Commit 9** — Offset Surface (140). Resolver-using per §4.30:
      evaluates base surface at `(t, s)`, computes the surface normal
      there, and offsets by the entity's `D` distance along the
      normal. Tricky: normal computation may need numeric
      differentiation on the base surface, or analytic normals for
      known base surface types. Check ref-impl SDK for existing
      surface-normal code; if none, simplest approach is central-
      difference around `(t, s)` with a small epsilon
      (`1e-6 · span_size` on each axis). Register
      `140: ("offset_surface", "surface")`. Tests: offset of a
      Plane Surface (190) — should yield parallel plane at distance
      D along the plane normal; offset of a Cylindrical Surface (192)
      — should yield concentric cylinder with radius increased by D.

- [ ] **Commit 10** — Conic Arc (104). Form-dependent, self-contained
      (no resolver). §4.5 gives three canonical forms:
      Form 1 Ellipse `C(t) = (a cos t, b sin t, zT)`,
      Form 2 Hyperbola `(a sec t, b tan t, zT)`,
      Form 3 Parabola `(t, −(A/E)t², zT)`. The entity's `A`..`F`
      coefficients define the general conic `Ax² + Bxy + Cy² + Dx +
      Ey + F = 0`, and the implementation must canonicalize to
      definition space (rotation + translation) before applying the
      form's default parameterization. Transformation Matrix pointer
      also applies. This is the most math-heavy of the remaining
      commits. SDK `conic_arc_entity.hpp` already parses A..F but
      probably has no `evaluate()` — add as a member function. Tests:
      one arc per form, evaluated at mid-range `t`.

- [ ] **Commit 11** — Analytic Surfaces (190/192/194/196/198).
      Self-contained, parametric per §§4.50–4.54. All have explicit
      closed-form `(u, v) → (x, y, z)` mappings. Member `evaluate()`
      on each entity. §1.6 says "The CLI uses degrees for `u` where
      the spec uses degrees; radians otherwise." — double-check each
      spec section and reflect in the implementation. Five entities
      in one commit is reasonable since each is ~10 lines. Tests:
      one surface per type at a mid-range `(t, s)`.

### Workflow per commit

1. Edit SDK entity header (`Evals/IGES-SDK/src/entities/<stem>.hpp`)
   or write helper in `eval_helpers.{hpp,cpp}`. For resolver-using
   entities, also add `RESOLVER_USING[type] = (stem, kind)` in
   `generate_dispatch.py`.
2. Sync SDK → ref-impl: copy the edited entity file to
   `Evals/IGES/reference-implementation-cpp/src/entities/`.
3. Regenerate dispatch (see CRLF quirk above).
4. Add CLI-level hidden tests in
   `Evals/IGES/tests/test_geometric_eval.py`.
5. Run `uv run pytest Evals/IGES/tests -q` and confirm all tests pass.
6. `uv run ruff check` + `uv run pyright` on changed Python files.
7. Stage only the IGES-related files (the working tree has
   unrelated AGENTS.md/CLAUDE.md env-notes edits — leave those
   uncommitted). Commit with a descriptive message following the
   pattern of commits 1-7.

### Gotchas picked up along the way

- **`curve_native_span` supports types 100, 106, 110 form 0, 126**.
  Other curve types (104 conic arc, 112 parametric spline, offset
  curve 130) return an error because their domains are either
  resolver-dependent (130) or not yet implemented (104/112). If a
  new composite curve constituent hits this, extend the switch in
  `eval_helpers.cpp::curve_native_span`.
- **IGES writer uses `%.15g`** (see `writer/` in the SDK) — precisely
  15 significant decimals. `math.pi` round-trips with its last bit
  changed, so test ranges that touch `π` exactly (SoR angle limits)
  must be padded. Do NOT switch the writer to `%.17g`; that breaks
  unrelated round-trip comparisons.
- **Vec3 lives in `entities/entity.hpp`**, not in `types.hpp`. New
  entity `.cpp` files that use `Vec3` in free functions must include
  `"entity.hpp"` (not `"../types.hpp"`).
- **Clang LSP diagnostics may be stale** (docker `compile_commands.json`
  lags the local tree). Trust the `pytest` run, not the editor squiggles.
- **Pre-existing ruff errors** in `generate_dispatch.py` (36 E501 +
  F541 issues) are not new work — fixing them is a separate concern
  from this expansion.

### Design-decision audit trail

Codex critique 2026-04-15 on the arc `t`-parameter convention
concluded Option B (native per-entity parameters, documented in §1.6)
is the right call for a doc-comprehension benchmark. Transcript:
`codex-conversations/2026-04-15-08-47-iges-arc-t-convention.md`.
Captured in IGES-Design.md §5 and in the Resolved open question
above.

---

## Known Issues / Investigations

Parked items to revisit — not blockers for shipping 1.0.0 but should not
be forgotten.

- [ ] **Docker build via `run_in_background` silently dropped output**
      (2026-04-14). Ran `wsl.exe -d Ubuntu -e bash -lc 'docker run ...'`
      as a backgrounded shell command; the container never appeared in
      `docker ps`, the redirected log file was zero bytes, and the agent
      had no signal the build had died. Re-running the same command
      foreground succeeded in ~1s configure + a couple minutes compile.
      Suspected cause: Windows→WSL→docker pipe handoff drops stdout
      when the outer shell exits immediately (backgrounded). Workarounds:
      always run WSL docker builds foreground, or have the wrapper write
      to a mounted file path instead of relying on stdout capture.
      Next step: reproduce deterministically; decide whether to patch
      the `Bash` tool wrapper or forbid backgrounding WSL commands.

- [x] ~~**Ref-impl parses `ex1.iges` with "expected string, got default"**~~
      Fixed 2026-04-14. Root cause was three entity parsers calling
      `next_string()` / `next_integer()` for optional fields that IGES
      §4 defines as defaultable:
      - `connect_point_entity.cpp`: `cid`, `cfn` (§4.26)
      - `network_subfigure_definition_entity.cpp`: `prd` (§4.22)
      - `rectangular_array_entity.cpp`: `ddf` (§4.41)
      Changed each to the `_or(default)` variant. `ex1.iges` now parses
      with 21 entities (matching the SDK Catch2 assertion). **Test debt**:
      when §5 pytest tests land, each of these defaulted-field paths
      needs a dedicated test — see §5 below.

- [ ] **Roundtrip is not byte-identical** on `ex2.iges`: writer
      normalizes defaulted Global delimiters (`,,` → `1H,,1H;`),
      expands 2-digit year timestamps (`900729` → `19900729`), and
      zero-pads status codes (`       0` → `000000000`). These are
      all spec-legal but surface as diffs. **Semantic** roundtrip
      (parse → write → parse, diff JSON) is clean on all 3 fixtures
      (ex1/ex2/ex3 = 21/90/109 entities, zero mismatches). Tests
      must use semantic comparison — see §5 fixture test.
