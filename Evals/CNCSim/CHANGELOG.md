# CNCSim Changelog

## Proposed (not yet applied)

### Clarify cutter-radius-compensation (CRC) arc and first-move semantics

Pass-rate analysis across ~255 runs (every model, every language variant,
run via `scripts/per-test-pass-rate.py`) shows that 21 of the 23
`test_cutter_radius_compensation.py` cases passed ≤5 times and 6 passed
never:

- **Arc endpoints (8 cases, 0 or 1 passes each)**: all of
  `test_application_tracks_cutter_radius_compensated_arc_endpoints`
  (g41/g42 × first-arc / subsequent-arc × center-format / radius-format).
- **Entry-move straight line (4 cases, 1–4 passes)**:
  `test_application_tracks_cutter_radius_compensated_spindle_center`
  parametrizations `g41-first-straight-move-left`,
  `g42-first-straight-move-right`, `g41-omitted-d-uses-tool-in-spindle`,
  `g41-first-rapid-move-left`.
- **Continuation / transition (9 cases, 1–2 passes each)**: the colinear-
  follow-on, convex-corner, convex-90-degree, g40-follow-on,
  g40-then-g42-restarts, and tool-change-while-comp-on parametrizations
  of the same spindle-center test.

The continuation failures are a cascade: every continuation test depends
on the agent first computing the entry-move endpoint correctly, so a
single side-selection flip (or first-move geometry mistake) scores N
times across tests named for independent behaviors. This is the cascade
pattern warned against in `skills/eval-authoring/SKILL.md`.

Review of `RS274NGC.md` §B.6 and §3.5.3 against the test inputs identified
four interpretive leaps that are required to reach the expected answers
but are **not stated in the prose spec**:

1. **§B.6 silently overrides §3.5.3.2's distance-mismatch error.** The
   first-arc inputs place the tool at (7, 0) with the programmed arc
   center at (0, 0) and end at (0, ±4) — current-to-center distance 7,
   end-to-center distance 4. §3.5.3.2 says such a mismatch is a hard
   error; §B.6 never says it's waived under CRC.
2. **Radius-format first-arc is geometrically impossible under normal R
   rules.** `G42 D1 G3 X0 Y4 R4` from (7, 0) has chord √65 ≈ 8.06 > 2r =
   8, so no center exists. The tests assume R becomes the *auxiliary*
   arc radius; §B.6 says "actual computations differ ... see 3.5.3" and
   §3.5.3.1 says nothing about CRC.
3. **"Current location" for I/J under CRC is undefined.** §3.5.3.2 says
   I/J are offsets from "the current location." Under CRC the tool
   center and programmed contour diverge. The continuation tests only
   pass if I/J are read relative to the programmed contour.
4. **G41/G42 side selection on a CCW arc is not stated.** Deciding that
   G42 on CCW puts the tool on the outside (tool-center radius =
   programmed + tool) requires reasoning from the tangent-direction
   convention. §B.6 only says "on the appropriate side."

Plus a chain cascade: continuation tests named for independent behaviors
(convex corner, colinear follow-on, G40 transition) all fail when the
agent gets the first move wrong, violating the independent-failure-modes
rule in `skills/eval-authoring/SKILL.md`.

Proposed options (not yet chosen):

- **Option A — expand `technical-requirements-prompt.md` / `base-prompt.md`.**
  Add a short "CRC arc entry and continuation rules" paragraph that spells
  out (1)–(4) above, without editing `RS274NGC.md`. This preserves the
  tests and measures implementation skill against a specified contract.
- **Option B — remove or weaken the arc-endpoint tests.** Keep only the
  straight-move first-move and continuation tests; drop the 8 arc cases.
  Accept a lower suite size in exchange for tests that are derivable from
  the spec alone.
- **Option C — keep as-is.** Accept that these probe inference beyond the
  prose spec and treat the eval's practical ceiling as ≈98.9% rather
  than 100%.

None of these is applied yet; VERSION, content hashes, and test behavior
are unchanged. See the PASS-RATE NOTE comment blocks in
`Evals/CNCSim/tests/test_cutter_radius_compensation.py` (above
`CRC_ARC_CASES` and above the straight-move `@pytest.mark.parametrize`)
for the in-code version of the same analysis.

### Resolve full-circle arc inconsistency with §3.5.3.2

`test_trace_stepping.py::test_full_circle_arc_no_axis_words` passed 25 /
243 times across all models. The test runs `G2 I-1 J0` with no X or Y
word and expects a full circle (endpoint = start point). RS274
§3.5.3.2 explicitly lists "X and Y are both omitted" as a hard error
for G17 center-format arcs (`RS274NGC.md` lines 1659–1660). The test's
prior docstring cited "§3.5.17.3," but §3.5.17 is "Set Distance Mode —
G90 and G91" and has no bearing on arcs. A spec-conformant agent
rejects this input as an error and fails this test.

Proposed options (not yet chosen):

- **Option A — remove the test.** Drop `test_full_circle_arc_no_axis_words`.
  Agents cannot be asked to rederive full-circle-when-axes-omitted from
  the spec as given.
- **Option B — document the simulator convention.** Add a sentence to
  `base-prompt.md` or `technical-requirements-prompt.md` that under this
  simulator, when both in-plane axis words are omitted on a center-format
  arc, the endpoint equals the current point (full circle). This would
  justify the test without editing `RS274NGC.md`.
- **Option C — change the test input.** Replace `G2 I-1 J0` with
  `G2 X1 Y0 I-1 J0` so it exercises full-circle timing/stepping with
  explicit axes.

Documentation-only under Options B and C; a test removal under Option A.
Not applied yet.

### Clarify G87 back-boring behavior when I/J/K are omitted

`test_trace_stepping.py::test_g87_back_boring_sub_motions` passed 16 /
243 times. The input `G87 X1 Z-1 R0 F60` omits I, J, and K. RS274
§3.5.16.8 lists `I… J… K…` in the G87 prototype but specifies no
defaults and does not explicitly say omission is an error.

CHANGELOG v1.0.1 already acknowledged this ambiguity by removing the
"error when I/J/K omitted" tests on the same grounds, but no
clarification was added telling agents what G87 does in that case. This
success test requires the agent to assume I = J = K = 0 (or some other
simulator-chosen default) without any prompt guidance.

Proposed clarification: add a sentence to `base-prompt.md` or
`technical-requirements-prompt.md` specifying the default for omitted
I/J/K on G87 (e.g., "I, J, and K default to 0 when omitted"). A clean
patch bump; the reference implementation already encodes whatever
default the test assumes.

### Clarify G88 retract behavior in a non-interactive simulator

`test_trace_stepping.py::test_g88_boring_rapid_retract` passed 21 / 243
times. RS274 §3.5.16.9 step 4 says G88 must "Stop the program so the
operator can retract the spindle manually" — incompatible with this
simulator, which runs to completion without operator interaction. The
test adopts a specific simulator convention (G88 behaves like G86 with
the spindle left on: rapid retract to initial Z at the end), but no
prompt file states this convention.

Proposed clarification: add a sentence to
`technical-requirements-prompt.md` saying that since this simulator is
non-interactive, G88's "manual retract" step is performed as a rapid
retract to initial Z (G98) or R (G99) — matching whatever convention
the reference implementation encodes. Documentation-only.

### Clarify `cutter_radius_compensation_number` semantics for D0

Four tests share this issue:

- `test_cutter_radius_compensation.py::test_application_tracks_cutter_radius_compensated_spindle_center[g41-d0-keeps-spindle-center-on-programmed-path]` (33 / 255)
- `test_cutter_radius_compensation.py::test_application_tracks_cutter_radius_compensated_spindle_center[g42-d0-keeps-spindle-center-on-programmed-path]` (33 / 255)
- `test_program_end_reset.py::test_application_turns_cutter_compensation_off_on_m2_and_m30[M2]` (26 / 255)
- `test_program_end_reset.py::test_application_turns_cutter_compensation_off_on_m2_and_m30[M30]` (26 / 255)

The D0 cases expect `cutter_radius_compensation_number == 0` (explicit
zero) when `G41 D0` or `G42 D0` is active.
`technical-requirements-prompt.md` says the field is "the active D
number, or null if no explicit cutter radius compensation number is
active." D0 fits both readings — "D=0 is explicit" and "D0 deactivates
the CRC number" — and the prompt does not disambiguate. The two M2/M30
tests use `G41 D0` as setup, so a model that picks the null reading
fails both D0-in-CRC tests AND the program-end-reset cascade tests —
the program-end-reset tests then score the upstream D0 interpretation
mistake rather than M2/M30 behavior, violating the independent-failure-
mode rule in `skills/eval-authoring/SKILL.md`.

Secondary ambiguity: §B.6's first-move tangent-circle construction
degenerates at radius 0 (the circle collapses to a point). The spec
does not say whether D0 skips the construction and places the tool on
the programmed contour, or applies the degenerate construction.

Proposed clarification: amend the
`technical-requirements-prompt.md` line defining
`cutter_radius_compensation_number` to say explicitly that D0 is
treated as an explicit zero and serializes as 0 (not null), and that
the null value is reserved for "no active CRC" (i.e., G40 mode or
never turned on). Documentation-only; a patch bump.

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

### Clarify python `output/` contract (shared language requirements)

`Evals/_shared/language-requirements-py.md` currently tells the agent:

> The program must be runnable as: `python main.py <arguments>`
>
> Place all source files in the `output/` directory relative to your current
> working directory. The entry point must be `output/main.py`.

The two sentences together are satisfied by any code that runs when `main.py`
is invoked from inside `output/`. They do not tell the agent that the harness
extracts the **contents** of `output/` into a flat submission directory and
then invokes `python3 <that-dir>/main.py`, with cwd set elsewhere. Code that
depends on the wrapping directory being literally named `output/` (e.g.
`from output.errors import ...` with `sys.path` including the parent, or
package-style relative imports across sibling files with a populated
`__init__.py`) passes the agent's own smoke test and then fails at test time
with `ModuleNotFoundError`.

Observed in a 2026-04-18 claude-opus-4-7 run: `cncsim-py` run 1 built
successfully, claimed complete, and scored 4/542 because every test failed
at `main.py` import. Fixing 6 relative imports, 3 `from output.xxx`
imports, and removing an empty `__init__.py` brought the same source to
354/542 (counterfactual 0.653, in family with runs 2–3 at 0.806 / 0.747).

Proposed clarification: add a sentence to `language-requirements-py.md`
(and the js/rs analogues if applicable) telling the agent that the `output/`
directory is a submission convention only — at test time its contents are
relocated and its name does not survive — so code must resolve imports
from the script's own directory, not from a parent named `output`.

This is documentation-only: no test behavior, harness contract, or
reference implementation changes. When applied it is a patch bump
(2.1.2 → 2.1.3). It is not applied yet; VERSION and content hashes are
unchanged.

## v2.1.2 — unreleased

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
  `/usr/bin/python3` (see `src/swe_buildbench/build/backends.py:254`).

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
  a new Rust task variant so agents can be evaluated on their ability to
  implement the CNCSim spec in Rust. Uses `serde`/`serde_json` only
  (agents remain std-only per `Evals/_shared/language-requirements-rs.md`).
- **Rust task registration** in `src/swe_buildbench/harness/task.py`,
  plus the Rust reference implementation wired into
  `Evals/CNCSim/tests/conftest.py` so `--language=rs` runs the Rust ref.

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
