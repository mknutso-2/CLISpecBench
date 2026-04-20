# RS274

CNC G-code interpreter eval for CLISpecBench. Agents receive the RS274/NGC
specification and must produce a working simulator that parses G-code programs
and outputs machine state.

> **Status note.** Earlier drafts of this README described a possible split
> between the end-of-program snapshot surface and the inter-line trace surface.
> That split has been deferred. As of version 2.0.0, RS274 is a single eval
> that covers both: the `--output` end-of-program snapshot from the 1.x line
> *and* a new optional `--trace-output` motion trace that reports inter-line
> state evolution. The 1.x contract is preserved via the git tag
> `cncsim-pre-trace`; if a future fork is warranted, that tag marks the last
> commit of the 1.x baseline and can be copied into a new eval directory.

## Directory Structure

```
prompt/
  base-prompt.md                    # Domain expert persona prompt
  technical-requirements-prompt.md  # CLI contract, language, output schema
  docs/
    RS274NGC.md                     # Full RS274/NGC specification
    figure_*.png                    # Specification figures
tests/
  conftest.py                       # Build fixtures and executable discovery
  rs274_support.py                  # Test helpers (run simulator, parse output)
  modal_groups.py                   # G/M-code modal group definitions
  rs274_parameters.py               # RS274 parameter index constants
  test_build.py                     # Verifies cmake build succeeds
  test_*.py                         # Hidden test suite (~40 test modules)
reference-implementation-cpp/
  CMakeLists.txt                    # CMake project
  src/                              # C++ reference solution (passes all tests)
reference-implementation-py/
  main.py                           # Python reference solution (passes all tests)
reference-implementation-js/
  main.js                           # JavaScript reference solution (passes all tests)
reference-implementation-rs/
  Cargo.toml / src/                 # Rust reference solution (passes all tests)
```

## What RS274 Evaluates

RS274 provides the complete RS274/NGC specification as context and asks for a
full implementation. The hidden test suite scores the simulator along two
independent dimensions:

1. **Final machine state** (from 1.x). Given a G-code program, the
   `--output` end-of-program JSON must match the expected end state. This is
   the original RS274 scoring surface and it is preserved unchanged.
2. **Motion trace** (added in 2.0.0). When invoked with `--trace-output` and
   one of the three stepping flags, the simulator must also emit a
   time-ordered record of how machine state evolved *during* execution,
   sampled according to the stepping mode. See the
   [Motion Trace](#motion-trace) design section below for the full
   behavioral model.

These two dimensions are scored independently. An agent that correctly
implements the end-of-program snapshot but not the trace passes all the
1.x-style tests unchanged, which gives the eval a natural difficulty tier
built into the test suite: a strong implementation earns credit on both
dimensions, a partial implementation earns credit on whichever it got right.
This replaces the earlier planned Lite/Heavy split — the partition is now a
property of the test suite (via the `trace` pytest marker), not the eval
directory layout.

RS274 is the primary *comparison* eval — designed to produce differentiating
scores between current frontier models on dense-spec comprehension and
correct RS274 interpretation.

## Running Tests

Against the reference implementation:

```bash
pytest Evals/RS274/tests --language=cpp -v
```

Against a different implementation:

```bash
pytest Evals/RS274/tests --language=<lang> --implementation-root /path/to/submission
```

The `--build-timeout-seconds` option (default 300) controls the CMake build
timeout.

## Prompt Structure

- [prompt/base-prompt.md](prompt/base-prompt.md) -- Domain expert persona
  describing what the simulator should do, without engineering guidance.
- [prompt/technical-requirements-prompt.md](prompt/technical-requirements-prompt.md)
  -- Harness contract: C++20/CMake, CLI flags (`--input`, `--output`,
  `--tool-table`, `--block-delete`, `--carousel-slots`, `--parameter-input`,
  `--parameter-output`, `--probe-box`, `--probe-tool`, `--trace-output`,
  `--trace-time-step`, `--trace-distance-step`, `--trace-position-tolerance`),
  exit codes, output schema, trace schema.
- [prompt/docs/](prompt/docs/) -- RS274/NGC specification and figures provided
  to the agent.

## Design Decisions

### Single-document corpus

RS274 uses only the RS274/NGC specification as its documentation corpus. The
spec is self-contained, and the single-document constraint makes RS274 a clean
test of dense specification comprehension. Future tasks may use multi-document
corpora to test document synthesis across sources.

### Why this task

- Simulation output is fully deterministic: given a G-code program and initial
  state, there is exactly one correct final state
- The domain is narrow enough that current training data contains few complete
  implementations
- Domain expertise in CNC machining enables authoritative, adversarial test
  case design

### Requirement provenance

The RS274/NGC document is the sole behavioral source of truth. Tests only assert
behavior that is explicit and unambiguous in the spec. If a behavior requires
nontrivial inference across multiple clauses, it must be clarified in the prompt
or this document before becoming a test requirement.

### Motion Trace

Added in 2.0.0. The motion trace is a time-parameterized record of machine
state during program execution, suitable for driving a CNC simulation GUI that
replays tool motion or for scoring per-line simulator behavior against a
reference. The end-of-program `--output` payload from the 1.x contract is
unchanged; this feature adds a second, optional output file (`--trace-output`)
describing *how* state evolved to reach that end state.

The hard contract — CLI flags, file format, entry fields, delta rules, error
case — lives in `prompt/technical-requirements-prompt.md`. This section
captures the *design rationale* and the non-obvious behavioral rules that
informed that contract.

#### Purpose

Without the trace, a consumer of the end-snapshot cannot:

- Replay a G2/G3 arc as an arc (only the endpoint is visible — a naive
  consumer would draw it as a straight line).
- Replay a canned-cycle drill (G81/G82/G83) as its constituent rapid-to-XY,
  rapid-to-R, feed-to-Z, retract sub-motions (only the final position is
  visible; all the interior motion disappears).
- Distinguish `G53 G1 X1 Y2` from a plain `G1 X1 Y2` to the same absolute
  coordinates (both produce the same end state).
- Observe G92.2 / G92.3 transitions (the backing parameters 5211–5216 are
  identical across the toggle; only `nonmodal_g_codes` labels can expose it).

The trace closes all of these gaps.

#### Scoring locality: why per-line time

`time` in trace entries is scoped **per source line**: each entry reports
seconds elapsed since the start of its source line's execution, and the
clock resets on every new line. A natural alternative would be to report
global "seconds since program start," which is simpler for a GUI replay
consumer but worse for scoring: a bug in the agent's computation of line
5's duration would cascade wrong `time` values into every subsequent entry
on lines 6..N, and the test suite would report hundreds of failures for
one bug. Per-line scoping contains that damage: each line is independently
scorable, and a failing report localizes the actual bug. A GUI consumer
that needs a global timeline can trivially accumulate per-line durations.

Within a line, no entry is ever emitted at `time == 0.0` for a motion
block. The first emitted entry of a motion line lands at the first
interior stepped sample of its first non-zero sub-motion, or at that
sub-motion's final entry if no interior sample fits. Modal / parameter /
tool / label deltas declared by the block ride that first emitted entry.
An alternative would be to always emit a `time == 0.0` entry carrying the
block's opening deltas, but that entry's `machine_position` is by
definition identical to the prior entry's — it is redundant noise. Rolling
the deltas forward onto the first real entry preserves every bit of
information the `time == 0.0` entry would have carried, halves the entry
count on short motion lines, and simplifies consumers (they never have to
skip "empty-position" entries).

#### Baked constants, not CLI flags

Two fictional constants are baked into the contract rather than exposed as
CLI flags:

- **Rapid feed rate: 1000 inches/minute.** RS274 says nothing about rapid
  speed; it is machine-specific. Any value is equally unprincipled, and the
  benchmark only needs all implementations to agree on one. A
  `--rapid-feed-rate` flag would split the scoring surface (two runs with
  different flag values produce different traces) without improving any
  test's fidelity. Downstream consumers that want machine-specific rapid
  speeds can post-process: rapid sub-motions inside canned cycles are
  identified by `motion_kind: "rapid"`, and rapids elsewhere are identified
  by `active_modal_g_codes` group 1 being `G0`.
- **State-only block duration: 0.0001 seconds.** Blocks that change state
  without producing motion (e.g., `G90`, `#100=5`, `T1`) emit a single
  trace entry with `time = 0.0001`. This epsilon is also fictional, but it
  serves two real purposes: (1) it gives state-only blocks a non-zero
  contribution to accumulated program time, so a GUI's line-start
  accumulator advances on every executed block; and (2) it guarantees
  forward progress for programs that poll a timer parameter inside an
  O-word loop whose body contains only state mutations — without the
  epsilon, such a loop could never terminate in simulation because
  simulated time would never advance. Like the rapid rate, the epsilon is
  deliberately not configurable: tunability would only create a new axis
  for scoring disagreement.

#### Delta encoding, not full snapshots

Each trace entry is a sparse delta against the prior entry (folded against
`initial_state` for the first entry), not a full state snapshot. A full
snapshot per entry would multiply the trace file size by the size of the
end-snapshot payload — `parameters` alone can be hundreds of entries, and
`coordinate_system_offsets` is 9 systems × 6 axes — for traces that may
contain thousands of entries on a non-trivial program. Most fields don't
change per entry; delta encoding preserves the information at a small
fraction of the size.

The `initial_state` header is required (not implicit "RS274 defaults")
because G20/G21, loaded parameter files, and `--tool-table` all mutate
starting state in ways an implicit default cannot capture.

#### `motion_kind`: why it exists only inside canned cycles

The `motion_kind` field (`"rapid"` or `"feed"`) is present only on the
first emitted entry of each sub-motion inside a canned cycle expansion,
and is omitted everywhere else. The reason: for ordinary G0/G1/G2/G3/G38.2
motion, a consumer can already recover the motion kind from
`active_modal_g_codes` group 1. Inside a canned cycle, however, group 1 is
the cycle code itself (e.g., `G81`), so the consumer cannot distinguish
the cycle's rapid sub-motions (rapid-to-XY, rapid-to-R, retract) from its
feed sub-motions (feed-to-Z, peck feeds) from modal state alone.
`motion_kind` fills only that gap — it deliberately does not apply to
cutter-comp lead-in/lead-out (which is modeled as a single tool-tip
sub-motion that inherits the active G0/G1) or to G38.2 (which has its own
modal group 1 value).

The "first emitted entry of a sub-motion" is the earliest entry whose
cumulative `time` lies within the sub-motion's extent — its first interior
stepped sample when stepping produces any, otherwise its final entry. For
a canned cycle where every sub-motion fits inside a single step, every
sub-motion has only its final entry, so every emitted entry carries
`motion_kind`. Conversely, a long feed sub-motion with many interior
samples has `motion_kind` only on its first interior sample; subsequent
samples within the same sub-motion inherit it.

#### `nonmodal_g_codes`: exposing group-0 execution

Non-modal G-codes (RS274 group 0: G4, G10, G28, G30, G53, G92, G92.1,
G92.2, G92.3) execute on exactly one block and do not stick. The
end-snapshot's `active_modal_g_codes` does not report them — nothing is
"active" at end-of-program — but a trace consumer very much wants to know
which non-modal fired on which block. Without labeling, a trace consumer
cannot tell `G53 G1 X1 Y2` from a plain `G1 X1 Y2`, cannot see that
`G10 L2 P1 X0` was a G10, and cannot track G92.2 / G92.3 transitions at
all.

The `nonmodal_g_codes` field (array of strings, alphabetical order) is
present only on the first emitted entry of each sub-motion induced by a
non-modal. Subsequent stepped samples within a sub-motion inherit the
label. G28 and G30 each expand into two sub-motions (move to intermediate
point, then move to the parameterized destination), and the label appears
on the first emitted entry of **each sub-motion that produces any
entries** — a G28 whose block specifies no intermediate axis words has a
zero-duration SM1 that produces no entries, so the label appears only on
SM2's first emitted entry in that case. G92.1 / G92.2 / G92.3 must be
emitted as their exact variant strings, not canonicalized to `"G92"`.

#### G92 offset handling: no new layer

RS274 1.x already stores G92 offsets in the RS274 parameter layer at
parameters 5211–5216 (X/Y/Z/A/B/C), matching the spec's section 3.5.18.
The end-snapshot reports those parameters inside `parameters`; there is no
separate `g92_offsets` field in the schema. The trace inherits this
convention: G92 offset changes ride the existing `parameters` delta, and
`machine_position` in trace entries is post-G92-offset (absolute machine
coordinates, the same convention as the end-snapshot `machine_position`).
No new layer is introduced.

The one subtlety is G92.2 and G92.3, which suspend and restore the active
G92 offset *without* writing the backing parameters. Under the
`parameters`-delta-only view, those transitions are invisible: parameter
values are identical before and after. `nonmodal_g_codes` closes this gap —
a consumer can see which G92 variant fired on each entry and statefully
track active-vs-suspended across subsequent entries. This is the second
motivation for `nonmodal_g_codes` (beyond "which non-modal caused this
motion"), and is why a dedicated `g92_active` boolean would be redundant.

#### Testing strategy: two-axis parameterization

Trace tests parameterize each test case along **two independent axes**,
running the same input program twice:

1. **Time axis** (`--trace-time-step`): checks the simulator's timing
   algorithm. A bug in arc-length computation, feed-rate-mode handling,
   G84 reversal timing, or canned-cycle sub-motion counting fails the time
   axis but should *not* fail the distance axis.
2. **Distance axis** (`--trace-distance-step`): checks the simulator's
   path geometry. A bug in arc center computation, cutter-comp offsetting,
   canned-cycle trajectory, or G83 peck counting fails the distance axis
   but should *not* fail the time axis.

Decoupling these axes keeps failure signal local: an agent with a bad
timing algorithm but correct geometry still earns credit for the geometry,
and vice versa. The failure report points directly at the mis-implemented
dimension rather than reporting a generic "trace didn't match."

`--trace-position-tolerance` is intentionally **not** used as a test axis.
Tolerance mode is adaptive, so multiple different sampling strategies
satisfy the tolerance bound with different entry counts and different
positions — there is no canonical correct output to compare against.
Tolerance mode exists for GUI consumers that want adaptive sampling, not
for scoring. The test fixture rejects it with a clear error message so
future contributors do not attempt it as a third axis.

#### Test organization: colocation by domain, partition by marker

Trace tests are colocated into the existing domain test files whenever
they reuse scaffolding from the end-snapshot tests — `test_canned_cycles.py`
contains both end-state and trace assertions about G81, `test_arc_errors.py`
contains both for arcs, and so on. This avoids duplicating input programs
and commentary across separate files, and documents intent: the file name
is the domain, and everything in that file is "how we test this domain."

Partitioning between the 1.x baseline and the 2.0 trace additions is
handled by a pytest marker, `@pytest.mark.trace`, applied to every
trace-related test regardless of which file it lives in. `pytest -m "not
trace"` produces the 1.x-equivalent scoring profile and is the
recommended invocation for agents that have not yet implemented the trace
feature or for reproducing 1.x-era results.

Cross-cutting trace concerns that have no natural domain home live in
dedicated files:

- `test_trace_stepping.py` — the three stepping modes and their edge cases
  (missing flag, multiple flags, zero-duration lines, single-entry lines,
  the final-entry-at-T rule).
- `test_trace_nonmodal.py` — `nonmodal_g_codes` labeling rules as a
  cross-cutting piece of contract (alphabetical ordering, exact variant
  preservation, multi-non-modal arrays, the G28/G30 dual-sub-motion rule).
- `test_trace_format.py` — top-level trace file structure (`initial_state`
  presence, `entries` shape, error-case fields, empty-program handling).

#### Shared fixture

A helper in `Evals/RS274/tests/rs274_support.py` encapsulates the
two-axis fixture so individual tests do not repeat the scaffolding: it
runs the simulator twice (once per stepping mode), loads both traces, and
exposes a pair of views (`time_trace`, `distance_trace`) plus a
`reconstruct_state_after(trace, i)` fold helper that resolves sparse
deltas against `initial_state`. Individual tests then assert on whichever
view they care about.

## Test Categories

- **Basic motion** (G0, G1): positioning, feed vs rapid behavior
- **Arc motion** (G2, G3): radius and IJ/K forms, endpoint tolerance, quadrant crossing
- **Modal state**: persistence across blocks, reset on M2/M30, group interactions
- **Coordinate systems**: G90/G91 switching, G54-G59 offsets, G92 offsets, G10 setting
- **Parameters**: RS274 numbered parameters, expressions, file I/O
- **Tool management**: tool changes, length compensation, carousel
- **Probing**: G38.x probe cycles with bounding box simulation
- **Canned cycles**: G80-G89 drilling cycles
- **Cutter radius compensation**: G41/G42 offset paths
- **Error handling**: invalid inputs produce structured error output with exit code 1
- **Motion trace** (2.0.0, marker `trace`): `--trace-output` file structure,
  delta encoding, per-line time, final-entry-at-T rule, time model constants,
  canned-cycle sub-motion enumeration, `motion_kind` labeling inside canned
  cycles, `nonmodal_g_codes` labeling across G4/G10/G28/G30/G53/G92.x, G92.2
  / G92.3 state tracking via non-modal labels, two-axis time/distance
  parameterization, error-case `error_line_number` and
  `error_block_segment_index`

## Extension Tasks

Hidden prompts injected after the base implementation is scored. The agent does
not know they are coming. Extension prompts use the same non-developer persona
as the base prompt, written as natural follow-up requests.

**Current extensions:**

- **ext-01: Arc plane selection (G17/G18/G19)** -- Tests whether arc math is
  parameterized by plane or hardcoded to XY.
- **ext-02: Coordinate system offsets (G54-G59)** -- Tests whether position
  tracking was abstracted beyond a single coordinate frame.

**Possible future extensions:**

- **ext-01: Stock removal simulation** -- Adds volumetric material tracking.
  Tests architectural extensibility.
- **ext-02: Haas dialect support** -- Adds Haas-specific G-code conventions.
  Tests parser/interpreter extensibility.
