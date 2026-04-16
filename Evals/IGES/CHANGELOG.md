# IGES Changelog

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
  (`107 passed`, 2026-04-16).
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
  (`107 passed`, 2026-04-16).
- `uv run ruff check` and `uv run pyright` pass repo-wide
  (2026-04-16).
- First real-agent smoke run completed cleanly:
  `iges / claude-code / claude-opus-4-6` scored `43/93`
  (`exit_reason: "completed"`). The agent voluntarily exited and
  claimed full success despite partial correctness, so the low score was
  model behavior rather than harness/auth/rate-limit failure.
