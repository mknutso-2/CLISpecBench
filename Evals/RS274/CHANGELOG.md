# RS274 Changelog

## Proposed (not yet applied)

### Two M-code modal-group issues in the prompt

Issue (a) and issue (b) are independent and have very different
expected impact.

**(a) Typo in `technical-requirements-prompt.md` Example 1 (line 292).**
The example shows:

    "active_modal_m_codes": {"4": "M5", "...": "other default groups"}

M5 is in modal group 7 (spindle turning) per RS274 Table 4
(`RS274NGC.md` lines 1452–1454). Group 4 is the stopping group
(M0/M1/M2/M30/M60). The fix is a three-character edit:
`"4"` → `"7"`. Low impact — see below — but still a real bug the
prompt should not ship with.

**(b) Ambiguity in "modal group" semantics for one-shot M-codes.**
RS274 Table 4 places M0/M1/M2/M30/M60 (stopping) in group 4 and M6
(tool-change) in group 6. In context, "modal group" means at most one
member may be active on a single line. For continuous-state codes
(M3/M4/M5 spindle, M7/M8/M9 coolant, M48/M49 override) the word
"modal" also reads naturally as persistent state: after M3 executes,
the machine remains in spindle-CW until M5. For instantaneous actions
(M0 stop, M6 tool-change), the spec never says whether the code
remains the "active" member of its group after the action completes.
The tests assume it does; models reasonably treat these as events
without a persistent modal slot.

Pass-rate signal across 255 runs, grouped by which modal group a test
exercises:

| Group          | M-codes covered   | Pass rate |
|----------------|-------------------|-----------|
| 4 (stopping)   | M0, M1, M60       | 18–22%    |
| 6 (tool-chg)   | M6                | 20%       |
| 7 (spindle)    | M5                | 42%       |
| 8 (coolant)    | M7, M8, M9        | 34–41%    |
| 9 (override)   | M49               | 36%       |

The typo alone would predict the opposite of what we see: if agents
followed `{"4": "M5"}` literally, `group-7-m5` would be the lowest
pass rate. It is the highest. The 20 pp gap between the continuous-
state groups (~40%) and the one-shot groups (~20%) is issue (b), not
issue (a).

17 tests directly assert on `active_modal_m_codes[<group>]`. About
half sit in the low band; most of those would lift by ~20 percentage
points if issue (b) were clarified.

Proposed:

- For (a): fix the typo. `"4": "M5"` → `"7": "M5"`.
- For (b): add a sentence to `base-prompt.md` or
  `technical-requirements-prompt.md` stating that every M-code from
  RS274 Table 4 that appears in the input program remains the active
  member of its modal group for the rest of the program (until
  replaced by another member of the same group or reset by M2/M30),
  including stopping codes and M6. This removes the ambiguity
  without editing `RS274NGC.md`.

Documentation-only; a patch bump. Not applied yet. Aggregate score
impact is small (~0.3 pp of overall suite score), but issue (b) is the
main driver of a persistent ~20 pp gap across ~8 tests.

### Clarify trace behavior when state-only transitions share a line with motion

`test_trace_format.py::test_motion_plus_m2_same_line_final_entry_time`
passed only 2 / 243 times across all models. Input: `G1 X1 F60 M2` on a
single line. The test requires the final trace entry's `time` to equal
the motion duration (1.0 s), with the M2 modal deltas folded into that
entry.

`technical-requirements-prompt.md` describes state-only blocks as
producing a single `time == 0.0001` epsilon entry and motion blocks as
being stepped into sub-motion entries, but does not specify what happens
when a state-only transition (M2 program-end) shares a line with a
motion block. Models reasonably emit either:

- A folded final entry whose `time` equals the motion duration and which
  carries the M2 modal deltas (the test's expected form), or
- A trailing `time == 0.0001` entry after the final motion step,
  carrying just the M2 deltas.

Both are defensible under the current prompt. Proposed clarification: add
a sentence to the trace rules that says when a block contains both
motion and state-only content, the state-only deltas fold into the
block's final stepping entry rather than producing a separate epsilon
entry. Documentation-only; would be a patch bump when applied.

## v3.1.9 — 2026-04-26

- Tightened `tests/test_output_schema.py` trace-entry validation:
  - optional trace delta maps/lists must be non-empty when present;
  - coordinate-system delta keys are restricted to `"1"` through `"9"`;
  - modal-code map keys must be decimal modal-group strings;
  - required `line_number` and `time` entry fields are asserted explicitly.

## v3.1.8 — 2026-04-26

- Added `tests/test_output_schema.py` as the central schema gate for
  `--output` and `--trace-output` payloads:
  - success payloads now get full nested schema checks for machine position,
    modal-code maps, coordinate-system offsets, parameters, and nullable state
    fields;
  - error payloads now gate top-level output shape and non-empty error fields
    without requiring every nested state snapshot to be complete on the error
    path.
- Made shared RS274 test runners tolerate missing or malformed JSON objects by
  returning `{}`; schema tests now own the hard schema failure, while behavioral
  tests can continue to report value mismatches.
- Swept behavioral tests from direct `payload[...]` and top-level
  `trace[...]` subscripts to `payload.get(...)`, `mapping_field(...)`,
  `trace_entries(...)`, and `trace_initial_state(...)` accessors.

## v3.1.7 — 2026-04-25

- Reduced independent-failure-mode cascades in the RS274 test suite:
  - collapsed the CRC+G92.x axis-offset error parametrization to one
    representative `G92.1` precondition test, with G92.2/G92.3 covered
    by the dedicated G92 tests;
  - combined parameter-file startup-state checks into one parser gate and
    moved G28/G30 home-motion tests to in-program parameter assignments so
    they no longer depend on `--parameter-input`;
  - split probing coverage into one 5061-5066 trip-parameter plumbing test
    plus per-case final-position behavior tests.
- Kept the canned-cycle spindle-restore and sticky-R/Z variants as separate
  tests because each still has distinct cycle endpoint/spindle expectations;
  updated comments to document the intentional shared preconditions.

## v3.1.6 — 2026-04-25

### Changed

- Clarified in `technical-requirements-prompt.md` that an explicit D0 is
  an active cutter radius compensation number and serializes as 0, not
  null.
- Added a `prompt/docs/Clarifications.md` section defining D0 as active
  zero-radius cutter radius compensation whose tool-center path coincides
  with the programmed contour.
- Changed the M2/M30 cutter-compensation reset test to establish active
  cutter compensation with an explicit zero-radius D1 tool-table entry
  instead of D0, reducing cascade from D0 serialization mistakes.
- Added an explicit feed rate to that reset test's setup move so the test
  is not dependent on default feed-rate behavior.

### Fixed

- Resolved the documentation gap behind the D0 cutter radius compensation
  cases and the related program-end reset cascade.

## v3.1.5 — 2026-04-25

### Changed

- Added a normative clarification in `prompt/docs/Clarifications.md`
  that G88's manual operator retract is modeled as an automatic rapid
  retract to the canned-cycle clear level in this non-interactive
  simulator.
- Updated G88-related test comments and docstrings to cite that
  clarification instead of treating the retract convention as unstated.

### Fixed

- Resolved the documentation gap behind
  `test_trace_stepping.py::test_g88_boring_rapid_retract`, which
  exercises a G88 rapid retract in trace output.

## v3.1.4 — 2026-04-25

### Changed

- Added a normative clarification in `prompt/docs/Clarifications.md`
  that omitted I, J, and K words on G87 default to 0 for this eval.
- Updated G87-related test comments and docstrings to cite the
  clarification instead of treating omitted I/J/K behavior as unresolved.

### Fixed

- Resolved the documentation gap behind
  `test_trace_stepping.py::test_g87_back_boring_sub_motions`, which
  exercises a G87 block with omitted I, J, and K words.

## v3.1.3 — 2026-04-25

### Changed

- Updated full-circle center-format arc success tests to name the
  start/end point explicitly with in-plane axis words, e.g.
  `G2 X1 Y0 I-1 J0`, instead of using `G2 I-1 J0` with both X and Y
  omitted.
- Applied the same correction to the position-tracking G2/G3 full-circle
  cases and renamed their IDs from `*-no-axis-words` to
  `*-explicit-endpoint`.

### Fixed

- Removed an inconsistency with RS274 §3.5.3.2, which allows a
  center-format arc endpoint to equal the current point but still requires
  at least one selected-plane axis word.

## v3.1.2 — 2026-04-25

### Changed

- Added explicit `F60` feed setup to
  `test_application_tracks_cutter_radius_compensated_spindle_center`
  inputs so these CRC geometry tests do not also depend on whether an
  implementation accepts feed motion before a feed rate is set in G94 mode.
- Kept the hard Appendix B.6 `(3.2, +/-2.4)` first-move geometry only in
  the cases that explicitly test that construction.
- Switched the omitted-D, first-rapid, continuation, G40, convex-corner,
  and tool-change cases to tangential CRC setup moves that land at obvious
  compensated centers `(5, 3)` or `(5, -3)`, reducing the number of
  downstream tests that fail from one first-entry geometry mistake.
- Clarified the test comments to state that G41/G42 left/right selection is
  not ambiguous for these left-to-right paths.

## v3.1.1 — 2026-04-25

### Added

- **`prompt/docs/Clarifications.md`** — a new document for normative
  disambiguations of `RS274NGC.md` where the spec admits multiple
  defensible readings. The first entry resolves CRC arc input
  semantics, applying to both the entry move (first compensated
  motion after G41 or G42) and continuation moves:
  - X, Y name the programmed contour endpoint (the auxiliary-arc
    endpoint per §B.6), not the position the tool tip will reach.
  - R names the radius of the path the tool tip actually traces
    (the "generated arc" per §B.6, which shares its center with the
    auxiliary arc).
  - I, J are offsets from the current tool-tip location (per §B.1.1's
    world-model convention) to that shared center — not from the
    previous programmed contour endpoint.

### Changed

- **`base-prompt.md`** updated to point agents at `docs/Clarifications.md`
  and to call out that its content is normative for this task.

  Background: §3.5.3 says "If cutter radius compensation is active,
  the motion will differ from what is described here. See Appendix B,"
  but §3.5.3 + §B.6 + §B.1.1 do not unambiguously settle which point
  serves as the I/J reference under CRC, nor whether R names the path-
  arc radius or the auxiliary-arc radius. Three readings are defensible
  (path-arc; contour-radius with tool-tip-relative I/J; contour-radius
  with tangent-point-relative I/J); this release picks the first
  (path-arc throughout) for the simplest semantic continuity with
  non-CRC arcs and uniform first/continuation handling. The full
  analysis is documented in the comment block above `CRC_ARC_CASES`
  in `tests/test_cutter_radius_compensation.py`.

### Notes

- The agent's prompt corpus changes (new `docs/Clarifications.md` file
  and updated `base-prompt.md`), so the contract is observably
  different. Test inputs and reference implementations are unchanged;
  the existing tests already align with the picked reading.

## v3.1.0 — 2026-04-25

### Changed

- **CRC arc tests — corrected geometry under the §3.5.3 path-arc reading.**
  `test_cutter_radius_compensation.py::test_application_tracks_cutter_radius_compensated_arc_endpoints`
  inputs were geometrically inconsistent under the only spec-consistent
  reading: §3.5.3 explicitly defers to Appendix B under CRC, so "the
  arc" of §3.5.3.1/§3.5.3.2 refers to the path the tool actually
  traces, not the input X/Y/I/J literally. R names the path-arc radius;
  I/J name the path-arc center offset from the tool-tip current
  position. Specifically:
  - Four radius-format first-arc cases changed `R4.0 → R7.0` (R = path
    arc radius 7, not auxiliary arc radius 4).
  - Two subsequent-arc cases changed `J±4.0 → J±7.0` (I/J = path arc
    center offset from tool-tip current, paralleling the R reading).
  - The §3.5.3.2 → §3.5.3.1 section reference on the
    radius-format-outside-tangent comment was a paste error in the
    prior version; corrected.

### Added

- **Four CRC inside-tangent arc test cases.** The prior suite covered
  only outside-tangent geometries (G42 CCW, G41 CW). Added the
  inside-tangent variants (G41 CCW, G42 CW) for both center-format and
  radius-format first arcs, with programmed endpoint at (0, ±10) and
  auxiliary arc radius 10, giving the same compensated tool-center
  endpoint (0, ±7). Total CRC arc cases now 12 (was 8); total
  `test_cutter_radius_compensation.py` cases now 28 (was 23).

- **Test ID renames for clarity.** Existing CRC arc test IDs gained
  explicit traversal direction and tangency descriptors:
  `g42-first-arc-move` →
  `g42-ccw-first-center-format-arc-move-tangent-outside-arc`, and
  similar for the other first-arc tests.

- **Per-test comment blocks** on all CRC arc test cases explaining the
  auxiliary arc geometry, the side-selection rule, and (for radius-
  format) the path-arc-radius reading of R. Comments mirror cleanly
  between CCW and CW, outside- and inside-tangent variants.

### Notes

- This release does **not** modify `RS274NGC.md`; the spec is consistent
  on these cases under careful reading of §3.5.3 + §3.5.10 + §4.3.11 +
  Appendix B.
- Reference implementations (`reference-implementation-py/main.py` and
  `reference-implementation-cpp/src/main.cpp`) were updated in this
  release to compute the CRC arc geometry under the path-arc reading.
  Both implementations:
  - Use the current tool-tip location (not the previous programmed
    contour endpoint) as the reference for I/J on every CRC arc
    (including continuation arcs).
  - For radius format, treat R as the path-arc radius and derive
    `aux_r = path_r -/+ tool_r` based on side selection, then locate
    the shared center via the same two-circle intersection used for
    first arcs (no separate continuation branch).
  - Reject geometrically degenerate inputs where the chord between
    tool-tip and programmed end falls at or below `|aux_r - path_r|`
    (the analogue of §3.5.3.1's "end point of the arc is the same as
    the current point" error under the path-arc reading).

## v3.0.0 — 2026-04-20

### Changed

- **Eval rename**: renamed the eval from `CNCSim` to `RS274` across the
  eval directory, docs, tests, reference implementations, and the preferred
  executable name. The canonical harness task IDs are now
  `rs274-{cpp,py,js,rs}`.
- **Compatibility aliases**: the historical `cncsim-{cpp,py,js,rs}` task IDs
  remain registered as compatibility aliases resolving to the renamed RS274
  eval so existing scripts and published-result tooling do not break
  immediately.
- **Behavior unchanged**: this is a taxonomy/documentation rename only. The
  prompt materials, hidden tests, and reference-implementation behavior are
  unchanged from v2.1.2.

## v2.1.2 — 2026-04-18

### Changed

- **Container `python` symlink**: added `python-is-python3` to
  `docker/base.Dockerfile` so the bare `python` command resolves to
  `/usr/bin/python3` inside both agent and test containers. The shared
  `Evals/_shared/language-requirements-py.md` prompt instructs agents
  that `python main.py <arguments>` must work, but Ubuntu 24.04 ships
  only `python3` by default — agents that smoke-tested with
  `python output/main.py --help` got `command not found / exit 127`
  even when their implementation was correct. Test scoring is
  unaffected because `submission_command` already hard-resolves
  `/usr/bin/python3` (see `src/clispecbench/build/backends.py:254`).
- **Harness: preserve `output/` wrapper at test-container staging.**
  The scorer now mounts the agent's `output/` contents at
  `/tmp/submission/output/` inside the test container instead of
  flattening them to `/tmp/submission/`, matching the `output/main.py`
  entry point promised by `Evals/_shared/language-requirements-py.md`.
  Observed in a 2026-04-18 claude-opus-4-7 `rs274-py` run: the agent
  structured its code as a Python package named `output`
  (`from output.errors import ...` with supporting modules using
  `from .common import ...`), succeeded in its own smoke test from
  `/workspace/`, and died at test-time import with `ModuleNotFoundError:
  No module named 'output'` — scoring 4/542. Harness-only change in
  `src/clispecbench/harness/scoring.py` (`_CONTAINER_SUBMISSION`) and
  `src/clispecbench/harness/docker.py` (`copy_in` now auto-creates
  intermediate dirs under `/tmp`); no eval files changed.

## v2.1.1 — 2026-04-15

### Fixed

- **Hidden-test timing metadata**: `parse_json_report()` now reads the
  per-phase durations emitted by `pytest-json-report` instead of recording
  every test as `0.0s`.

### Changed

- **Per-test simulator timeout**: reduced the RS274 test helper timeout from
  30 seconds to 5 seconds so hanging submissions consume less scorer wall
  clock per failing test.
- **Outer hidden-test timeout**: increased the harness-level hidden-test cap
  from 600 seconds to 1200 seconds so runs with repeated per-test timeouts can
  still produce more complete scoring signal before the scorer is killed.

## v2.1.0 — 2026-04-13

### Added

- **Rust reference implementation** (`reference-implementation-rs/`), a
  single-file port of the Python ref that passes all 542 tests. Enables
  a new Rust task variant so agents can be evaluated on their ability to
  implement the RS274 spec in Rust. Uses `serde`/`serde_json` only
  (agents remain std-only per `Evals/_shared/language-requirements-rs.md`).
- **Rust task registration** in `src/clispecbench/harness/task.py`,
  plus the Rust reference implementation wired into
  `Evals/RS274/tests/conftest.py` so `--language=rs` runs the Rust ref.

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
