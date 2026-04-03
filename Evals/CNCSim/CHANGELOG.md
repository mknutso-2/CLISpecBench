# CNCSim Changelog

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
