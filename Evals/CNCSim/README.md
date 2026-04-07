# CNCSim

CNC G-code interpreter eval for SWE-BuildBench. Agents receive the RS274/NGC
specification and must produce a working simulator that parses G-code programs
and outputs machine state.

> **Status note (planned rename).** What currently lives in this directory is
> expected to be renamed to **CNCSim-Lite**. It evaluates RS274 interpretation
> against *final* machine state — given a program, produce the correct end
> state. A future second eval, tentatively **CNCSim-Heavy** (working name),
> will extend the CLI contract with **inter-line state semantics**: the agent
> must report machine state at intermediate points in the program, not just
> the final state. CNCSim-Heavy will be a strict superset of CNCSim-Lite —
> every Lite spec-correctness assertion will still apply, plus new
> trajectory/interpolation tests against an extended CLI surface (e.g.
> `--state-trace`, `--query-at-block`, or similar; not yet pinned down).
>
> Until that work happens, both `cncsim-lite` and `cncsim-full` task IDs in
> `_KNOWN_TASKS` resolve to this directory and run the same tests. Treat the
> two IDs as aliases for now; they will diverge once CNCSim-Heavy lands.

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
  cncsim_support.py                 # Test helpers (run simulator, parse output)
  cncsim_target.py                  # Implementation target resolution
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
```

## Task Variants

### CNCSim-Lite (current eval — what this directory implements)

Provides the complete RS274/NGC specification as context and asks for a full
implementation. The hidden test suite asserts **final machine state only**:
given a G-code program, the simulator's reported end state must match the
expected end state. No intermediate state is queried and no time-based
interpolation is required.

This is the primary *comparison* eval — designed to produce differentiating
scores between current frontier models on dense-spec comprehension and
correct RS274 interpretation.

> Earlier versions of this README described CNCSim-Lite as a *scoped subset*
> of RS274. That framing is being retired: the eval as actually implemented
> tests against the full spec, with the "Lite" qualifier instead reflecting
> the fact that it scores only final state, not trajectory.

### CNCSim-Heavy (planned, not yet implemented)

A future eval that adds **inter-line state semantics** to the CLI contract.
The agent will need to report machine state at intermediate points during
program execution — at minimum after each block, and possibly at fixed
time intervals (requiring genuine kinematic simulation rather than just
endpoint computation).

CNCSim-Heavy will be a *strict superset* of CNCSim-Lite: every Lite
spec-correctness test must still pass, plus new tests exercising the
extended CLI surface. CLI shape, prompt structure, and reference
implementation strategy are all TBD. See the rename discussion in the
project history for the design tradeoffs (full duplication vs shared test
module vs single-eval-with-markers).

## Running Tests

Against the reference implementation:

```bash
pytest Evals/CNCSim/tests -v
```

Against a different implementation:

```bash
pytest Evals/CNCSim/tests --implementation-root /path/to/submission
```

The `--build-timeout-seconds` option (default 300) controls the CMake build
timeout.

## Prompt Structure

- [prompt/base-prompt.md](prompt/base-prompt.md) -- Domain expert persona
  describing what the simulator should do, without engineering guidance.
- [prompt/technical-requirements-prompt.md](prompt/technical-requirements-prompt.md)
  -- Harness contract: C++20/CMake, CLI flags (`--input`, `--output`,
  `--tool-table`, `--block-delete`, `--carousel-slots`, `--parameter-input`,
  `--parameter-output`, `--probe-box`, `--probe-tool`), exit codes, output
  schema.
- [prompt/docs/](prompt/docs/) -- RS274/NGC specification and figures provided
  to the agent.

## Design Decisions

### Single-document corpus

CNCSim uses only the RS274/NGC specification as its documentation corpus. The
spec is self-contained, and the single-document constraint makes CNCSim a clean
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

## Extension Tasks

Hidden prompts injected after the base implementation is scored. The agent does
not know they are coming. Extension prompts use the same non-developer persona
as the base prompt, written as natural follow-up requests.

**CNCSim-Lite extensions (current eval):**

- **ext-01: Arc plane selection (G17/G18/G19)** -- Tests whether arc math is
  parameterized by plane or hardcoded to XY.
- **ext-02: Coordinate system offsets (G54-G59)** -- Tests whether position
  tracking was abstracted beyond a single coordinate frame.

**CNCSim-Heavy extensions (planned, alongside the Heavy eval itself):**

- **ext-01: Stock removal simulation** -- Adds volumetric material tracking.
  Tests architectural extensibility.
- **ext-02: Haas dialect support** -- Adds Haas-specific G-code conventions.
  Tests parser/interpreter extensibility.
