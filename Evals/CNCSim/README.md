# CNCSim

CNC G-code interpreter eval for SWE-BuildBench. Agents receive the RS274/NGC
specification and must produce a working C++ simulator that parses G-code
programs and outputs machine state.

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

### CNCSim-Lite

Uses a predefined subset of the RS274/NGC standard focused on core motion and
modal control. The prompt provides only the relevant sections. This is the
primary *comparison* eval -- designed to produce differentiating scores between
current frontier models. The hidden test suite covers in-scope features
exhaustively.

In scope:
- Linear motion: G0 (rapid), G1 (linear feed)
- Arc motion: G2 (clockwise arc), G3 (counter-clockwise arc), both radius and IJ/K offset forms
- Coordinate systems: G90 (absolute), G91 (incremental), with correct modal persistence
- Feed rate: F word, interaction with G0 vs G1
- Spindle: S word, M3/M4/M5
- Modal group state: correct persistence, reset behavior, and interaction between groups
- Basic program structure: N-words, end-of-program M2/M30

Out of scope: tool radius compensation (G41/G42), canned cycles (G80-G89),
coordinate system offsets (G54-G59), tool length compensation.

### CNCSim-Full

Provides the complete RS274/NGC specification as context. The prompt asks for a
full implementation without predefined scope. This is the primary *longitudinal
progress* eval -- designed to measure how much of the spec models can implement
as capabilities improve. The primary metric is **feature coverage**: what
percentage of the spec's distinct feature categories did the model attempt, and
what was the correctness rate within attempted features.

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

**CNCSim-Lite extensions:**

- **ext-01: Arc plane selection (G17/G18/G19)** -- Tests whether arc math is
  parameterized by plane or hardcoded to XY.
- **ext-02: Coordinate system offsets (G54-G59)** -- Tests whether position
  tracking was abstracted beyond a single coordinate frame.

**CNCSim-Full extensions:**

- **ext-01: Stock removal simulation** -- Adds volumetric material tracking.
  Tests architectural extensibility.
- **ext-02: Haas dialect support** -- Adds Haas-specific G-code conventions.
  Tests parser/interpreter extensibility.
