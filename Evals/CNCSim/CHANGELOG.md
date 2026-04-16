# CNCSim Changelog

## v2.1.1 — 2026-04-15

### Fixed

- **Hidden-test timing metadata**: `parse_json_report()` now reads the
  per-phase durations emitted by `pytest-json-report` instead of recording
  every test as `0.0s`.

### Changed

- **Per-test simulator timeout**: reduced the CNCSim test helper timeout from
  30 seconds to 5 seconds so hanging submissions consume less scorer wall
  clock per failing test.
- **Outer hidden-test timeout**: increased the harness-level hidden-test cap
  from 600 seconds to 1200 seconds so runs with repeated per-test timeouts can
  still produce more complete scoring signal before the scorer is killed.

## v2.1.0 — 2026-04-13

### Added

- **Rust reference implementation** (`reference-implementation-rs/`), a
  single-file port of the Python ref that passes all 542 tests. Enables
  a new task variant `cncsim-full-rs` (and `cncsim-lite-rs`) so agents
  can be evaluated on their ability to implement the CNCSim spec in
  Rust. Uses `serde`/`serde_json` only (agents remain std-only per
  `Evals/_shared/language-requirements-rs.md`).
- **`cncsim-full-rs` / `cncsim-lite-rs` task registration** in
  `src/swe_buildbench/harness/task.py`, plus `rs_reference_impl_subdir`
  wired into `Evals/CNCSim/tests/conftest.py` so `--language=rs` runs
  the Rust ref.

## v2.0.2 — 2026-04-12

### Changed

- **Prompt: non-interactive instruction**: appended shared
  `Evals/_shared/require-one-shot.md` to the assembled prompt, telling agents
  this is a non-interactive task — implement the full solution without asking
  questions or waiting for confirmation. Addresses haiku-4.5 runs that asked
  "Should I proceed?" and stopped.

## v2.0.1 — 2026-04-11

RS274 spec-compliance fixes found during adversarial subagent review of
the trace implementation.

### Fixed

- **G93 inverse-time convention**: changed `1/F seconds` to `60/F seconds`
  in `technical-requirements-prompt.md` and the Python ref to match
  RS274 §3.5.19.1, where F is in inverse minutes.
- **RS274 §2.1.2.5 Case A path length**: `_linear_path_length_inches`
  now uses XYZ-only Euclidean distance (was incorrectly including rotary
  axes, conflating inches and degrees).
- **RS274 §2.1.2.5 Case B/C rotary-only feed rate**: `_feed_duration`
  no longer applies mm→in conversion under G21 for rotary-only moves
  (feed rate is in deg/min regardless of G20/G21).

### Added

- 8 new trace tests from review rounds (unit switch, G21 arc stepping,
  linear+rotary duration, rotary-only G21, G88 boring, G28 per-SM
  stepping, M2 parameter delta, CS offset units).
- 4 test improvements (canned cycle modal delta, G84 trailing entry,
  block-delete position, tool table M6).

## v2.0.0 — 2026-04-09

Added motion trace: a time-ordered record of inter-line machine state
evolution during program execution, enabling GUI replay and per-line scoring.

### Added

- **`--trace-output <path>`** CLI flag writing a JSON trace file alongside the
  existing `--output` end-of-program snapshot. Requires exactly one stepping
  mode flag: `--trace-time-step`, `--trace-distance-step`, or
  `--trace-position-tolerance`.
- **Trace file schema**: `initial_state` header (full end-snapshot shape) plus
  `entries` array of sparse deltas, each with `line_number`, per-line `time`,
  and any state fields that changed since the prior entry. `motion_kind`
  labels canned-cycle sub-motions; `nonmodal_g_codes` labels blocks executing
  RS274 group-0 codes (G4/G10/G28/G30/G53/G92/G92.1/G92.2/G92.3).
- **Baked time constants**: rapid feed rate 1000 in/min, state-only block
  duration 0.0001 s. Not configurable (rationale in README).
- **Two-axis trace test parameterization**: every trace test runs under both
  `--trace-time-step` and `--trace-distance-step`, decoupling timing bugs from
  geometry bugs for localized failure signal.
- **`@pytest.mark.trace`** marker partitioning the test suite. `pytest -m
  "not trace"` reproduces the 1.x-era scoring profile.

### Preserved

- The `--output` end-of-program snapshot contract from 1.x is unchanged. A
  submission that implements only the end-snapshot still passes every 1.x
  test. The git tag `cncsim-pre-trace` marks the last 1.x baseline commit.

## v1.0.1 — 2026-04-03

Test review after first round of multi-model evaluation (Opus 4.6, GPT-5.4,
Sonnet 4.6, Opus 4.5, Sonnet 4.5, GPT-5.4-mini, Gemini 3 Flash, Haiku 4.5).
Cross-referenced all 31 never-passed tests against the RS274 specification.

### Removed (commented out with rationale)

- **G87 I/J/K requirement tests** (`test_canned_cycle_errors.py`): Section
  3.5.16.8 lists I, J, K in the G87 prototype but never explicitly says
  omitting them is an error. I and J are incremental offsets where 0 is a valid
  default; K in absolute mode specifies a Z-axis target that could also default
  to 0. (3 tests)
- **Non-printable comment character test** (`test_comment_errors.py`): Appendix
  E defines `comment_character` but neither section 3.3.4 nor the grammar
  explicitly says non-`comment_character` values inside parentheses are an
  error. (1 test)

### Changed

- **G92.x CRC error tests** (`test_cutter_radius_compensation_errors.py`):
  Replaced bare G92.1/G92.2/G92.3 entries with versions that establish a
  nonzero G92 offset before enabling cutter radius compensation, making the
  test intent unambiguous per Appendix B.5 error 1. (3 tests replaced)
- **Parameter file range test** (`test_parameter_file_cli.py`): Changed
  out-of-range index from 5400 to 5401. Section 3.2.1 says "range 1 to 5400"
  (inclusive upper bound), so 5400 is valid.

### Added

- Standardized spec-reference comments on all 27 remaining never-passed tests,
  citing the specific RS274 section that mandates the tested behavior.

### Net effect

438 → 434 tests (removed 4, replaced 3 with 3 strengthened equivalents).

## v1.0.0

Initial test suite.
