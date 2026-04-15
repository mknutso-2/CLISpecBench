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

- [ ] `iges parse --input <file.iges> --output <file.json>` — full parse to
      canonical IGES-JSON.
- [ ] `iges write --input <file.json> --output <file.iges>` — inverse.
- [ ] `iges query --input <file.iges> --de <n> --output <entity.json>` —
      single-entity extract by DE sequence number.
- [ ] `iges eval --input <file.iges> --de <n> --t <f> --output <point.json>` —
      geometric evaluation for parametric entities.
- [ ] `iges roundtrip --input <file.iges> --output <out.iges>` — one-shot
      parse+write for idempotence testing.
- [ ] Diagnostic JSON shape defined:
      `{"error": "...", "spec_ref": "§X.Y", "line": N, "section": "..."}`.

## 2. Canonical IGES-JSON Schema

Lives in `prompt/technical-requirements-prompt.md`. Machine-extracted from
`IGES-SDK/src/entities/*.hpp` structs, then hand-edited for clarity.

- [ ] Top-level shape: `{start_lines, global, entities[]}`.
- [ ] `global` — all 26 named fields with spec-defined defaults.
- [ ] `directory_entry` — all 20 named fields per entity.
- [ ] `entity.data` schema for each of the 87 entity types.
- [ ] Decide schema format: prose vs. JSON Schema vs. TypeScript-style. Pick
      one and apply uniformly.
- [ ] Form-dependent entity schemas (Drawing/External Ref/Line Font Def/
      Ordinate Dim/Radius Dim/View/Surfaces 190-198/Attr Table Def) call out
      per-form field lists.
- [ ] Numerical tolerance for `eval` picked and documented (initial target:
      relative `1e-9`).

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

- [ ] Copy `IGES-SDK/src/{types.hpp,types.cpp,entities/,model/,parser/,writer/}`
      verbatim into `reference-implementation-cpp/src/`.
- [ ] New `src/main.cpp` implementing subcommand dispatch for all five
      subcommands.
- [ ] Add `nlohmann/json` as a header-only dep (fetched via CMake
      FetchContent or vendored).
- [ ] Per-entity JSON serialization: `to_json` / `from_json` free functions
      mirroring the existing `parse_*_entity` / `write_*_entity` pattern —
      87 small functions in a new `src/json/entity_json.{hpp,cpp}`.
- [ ] `CMakeLists.txt` producing a single `iges` executable target (no
      Catch2, no library target). Mirror `Evals/CNCSim/reference-implementation-cpp/CMakeLists.txt`
      shape.
- [ ] Executable name matches `EVAL_CONFIG.preferred_executable_name="iges"`.
- [ ] Ref-impl passes the full Python test suite.

## 5. Tests (Catch2 → Python CLI)

`Evals/IGES/tests/`.

- [ ] `conftest.py` — copy CNCSim's, repoint `EVAL_CONFIG` to `iges`.
- [ ] `iges_support.py` — test helpers:
  - [ ] `run_iges(submission_command, subcommand, **kwargs) -> dict`
  - [ ] `build_iges_file(start_lines, global_overrides, entities) -> str`
  - [ ] `parse_iges_string(s) -> dict` (CLI round-trip helper)
- [ ] `data/ex1.iges`, `data/ex2.iges`, `data/ex3.iges` — copy unchanged.
- [ ] `test_build.py` — smoke test that the `iges` binary builds and is
      invokable (mirror CNCSim's).
- [ ] **Pilot port: Line entity end-to-end**
  - [ ] Port `test_4_13_line_entity.cpp` → `test_entity_line.py`.
  - [ ] Validate with the ref-impl that both parse + round-trip tests pass.
  - [ ] Treat this as the template for all remaining entity ports.
- [ ] **File format / data type tests** (higher value — port first)
  - [ ] `test_2_2_2_*.cpp` → `test_data_types.py` (integer, real, string,
        pointer, logical).
  - [ ] `test_2_2_3_*.cpp` → `test_free_format.py` (delimiters, free format).
  - [ ] `test_2_2_4_*.cpp` → `test_sections.py` (Start/Global/DE/PD/Terminate).
- [ ] **Per-entity tests** — 87 entity-level ports. Track individually:
  - [ ] §4.1 Null (0)
  - [ ] §4.3 Circular Arc (100)
  - [ ] §4.4 Composite Curve (102)
  - [ ] §4.5 Conic Arc / Copious Data (104 / 106)
  - [ ] §4.12 Plane (108)
  - [ ] §4.13 Line (110) — **pilot, see above**
  - [ ] §4.14 Parametric Spline Curve (112)
  - [ ] §4.15 Parametric Spline Surface (114)
  - [ ] §4.16 Point (116)
  - [ ] §4.17 Ruled Surface (118)
  - [ ] §4.18 Surface of Revolution (120)
  - [ ] §4.19 Tabulated Cylinder (122)
  - [ ] §4.20 Direction (123)
  - [ ] §4.21 Transformation Matrix (124)
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
  - [ ] §4.92 Subfigure Definition (308)
  - [ ] §4.93 Color Definition (314)
  - [ ] §4.97 Property (406)
  - [ ] §4.131 Drawing (404)
  - [ ] §4.133 Subfigure Instance (408)
  - [ ] §4.134 View (410)
  - [ ] §4.135 External Reference (416)
  - [ ] §4.136 Rectangular Array (412)
  - [ ] §4.137 Circular Array (414)
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
  - [ ] `test_writer_roundtrip*.cpp` → `test_writer_roundtrip.py`.
- [ ] **Geometric evaluation**
  - [ ] `test_geometric_evaluation.cpp` → `test_geometric_eval.py` (drives
        `iges eval` with known inputs).
- [ ] **Malformed input**
  - [ ] `test_malformed.cpp` → `test_malformed.py` (exit 1 + `spec_ref`).
- [ ] **Validation**
  - [ ] `test_validate.cpp` → `test_validation.py`.
- [ ] **Reference fixtures**
  - [ ] `test_reference_files.cpp` → `test_reference_fixtures.py`
        (round-trip `ex1`/`ex2`/`ex3`, assert entity counts + key fields).

## 6. Eval Design Doc

- [ ] `Evals/IGES/IGES-Design.md` — capture:
  - [ ] Why this eval exists (CNCSim saturation, harder spec-comprehension).
  - [ ] CLI contract rationale (why 5 subcommands).
  - [ ] IGES-JSON schema design choices.
  - [ ] Scoping: entities in scope, explicit non-goals (Binary Format,
        MACRO, drafting-only, Compressed Format).
  - [ ] Known spec ambiguities the tests deliberately do not assert.

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

- [ ] Schema encoding in the prompt: prose tables vs. JSON Schema vs.
      TypeScript-style type aliases.
- [ ] Whether to include `IGES5-3.pdf` in `docs/` (license review needed).
- [ ] Final `eval` subcommand surface — just `{x,y,z}`, or also first/second
      derivatives?
- [ ] Tolerance policy — single global tolerance, or per-entity-type?
- [ ] Whether `query --de <n>` on an out-of-range index is exit 1
      (malformed input) or a distinct error class.
