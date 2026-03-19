# CNCSim Design

This document captures the CNCSim-specific task design extracted from the main SWE-BuildBench design document.

## 1. Background

CNC machines execute programs written in G-code, a language standardized by NIST in the RS274NGC specification. A G-code program is a sequence of blocks, each specifying motion commands, spindle control, and modal state changes. A simulator reads a G-code program and produces the resulting machine state — tool positions, active modal codes, feed rate, spindle speed — after each block or at program end.

This is an ideal SWE-BuildBench task because:

- Simulation output is fully deterministic: given a G-code program and initial state, there is exactly one correct final state
- The domain is narrow enough that current training data contains few complete implementations
- Domain expertise in CNC machining (held by this project's author) enables authoritative, adversarial test case design

**Corpus design choice — single document.** CNCSim uses only the RS274/NGC specification PDF as its documentation corpus. This is an intentional decision: the spec is genuinely self-contained and comprehensive, and the single-document constraint makes CNCSim a clean test of dense specification comprehension specifically. Future tasks may use richer multi-document corpora to test a different capability profile — document synthesis across sources, handling of contradictions between documents, navigating sparse or poorly organized reference material. CNCSim deliberately does not test those things.

## 2. Dual Eval Structure

CNCSim ships as two separate tasks.

**CNCSim-Lite** uses a predefined subset of the RS274/NGC standard focused on core motion and modal control. The prompt provides only the relevant sections, not the full PDF. This is the primary *comparison* eval — designed to produce differentiating scores between current frontier models. The hidden test suite covers the in-scope features exhaustively.

In-scope for CNCSim-Lite:
- Linear motion: G0 (rapid), G1 (linear feed)
- Arc motion: G2 (clockwise arc), G3 (counter-clockwise arc), with both radius and IJ/K offset forms
- Coordinate systems: G90 (absolute), G91 (incremental), with correct modal persistence
- Feed rate: F word, interaction with G0 vs G1
- Spindle: S word, M3/M4/M5
- Modal group state: correct persistence, reset behavior, and interaction between groups
- Basic program structure: N-words, end-of-program M2/M30

Out of scope for CNCSim-Lite: tool radius compensation (G41/G42), canned cycles (G80–G89), coordinate system offsets (G54–G59), tool length compensation.

**CNCSim-Full** provides the complete RS274/NGC PDF as context. The prompt asks for a full implementation without predefined scope. This is the primary *longitudinal progress* eval — designed to measure how much of the spec models can implement as capabilities improve. The hidden test suite covers the full standard, including features that no current model is expected to implement correctly.

The primary metric for CNCSim-Full is not raw pass rate but **feature coverage**: what percentage of the spec's distinct feature categories did the model attempt an implementation for, and what was the correctness rate within attempted features.

## 3. Prompt Template

```
I work with CNC machines and I need software that can simulate the execution of G-code
programs — the language CNC machines use to describe tool paths and machining operations.

The complete specification for the G-code language I use is in the docs/ directory.
Please read it and build a simulator that correctly executes G-code programs according
to that specification.

The simulator should be a command-line program. When I run it, I want to give it a
G-code file and get back a description of the machine's final state after the program
runs — where the tool ended up, what the feed rate was, spindle status, and so on.

---
Technical note (required for compatibility with the test system):

- Please implement this in C++20, buildable with: cmake -B build && cmake --build build
- The program must accept: --input <gcode_file> --output <result_file>
- The output file must be JSON in this format:
  {
    "final_position": {"x": float, "y": float, "z": float},
    "feed_rate": float,
    "spindle_speed": float,
    "spindle_direction": "CW" | "CCW" | "OFF",
    "active_modal_codes": {"motion": string, "coordinate_mode": string},
    "error": string | null
  }
- Exit 0 on success, 1 for invalid input, 2 for internal errors
---

The specification document is in docs/. Everything else is up to you.
```

## 4. Test Case Design

Test cases are stored as JSONL in the private repository. Each record:

```json
{
  "id": "arc-ij-endpoint-tolerance-001",
  "category": "arc_motion",
  "difficulty": "hard",
  "tags": ["G2", "IJ_form", "endpoint_tolerance", "adversarial"],
  "input_gcode": "G17 G90\nG0 X0 Y0\nG2 X1.0 Y0 I0.5 J0 F100\nM2\n",
  "expected_output": {
    "final_position": {"x": 1.0, "y": 0.0, "z": 0.0},
    "feed_rate": 100.0,
    "spindle_direction": "OFF"
  },
  "tolerance": {"position": 0.0001},
  "timeout_seconds": 10,
  "weight": 2.0,
  "notes": "Arc endpoint must match start point within spec-defined tolerance. Common failure: accumulated floating point error causes endpoint mismatch rejection."
}
```

Test categories for CNCSim-Lite:
- Basic motion (G0, G1): simple positioning, correct feed vs rapid behavior
- Arc motion (G2, G3): both forms, endpoint tolerance, full-circle arcs, quadrant crossing
- Modal state: persistence across blocks, reset on M2/M30, interaction between modal groups
- Coordinate mode: G90/G91 switching mid-program, correct relative reference point
- Edge cases: zero-length moves, redundant modal codes, block-order sensitivity
- Adversarial: cases designed to catch common misreadings of the spec
- Performance: large input files (e.g., 100MB NC programs) with a domain-meaningful `timeout_seconds`; catches O(n²) or worse parsing

## 5. Extension Tasks

CNCSim includes extension tasks for both the Lite and Full variants. These are hidden prompts injected after the base implementation is scored — the agent does not know they are coming.

**CNCSim-Lite extensions:**

- **ext-01: Arc plane selection (G17/G18/G19).** The base CNCSim-Lite scope assumes G17 (XY plane) only. This extension asks the agent to add support for G18 (XZ plane) and G19 (YZ plane) arc interpolation. A well-structured implementation with a clean separation between G-code parsing and motion geometry will absorb this by parameterizing the arc plane. A tightly coupled implementation will require rewriting the arc math.

- **ext-02: Coordinate system offsets (G54–G59).** Adds work coordinate system support — the agent must extend its coordinate handling to support multiple named offsets. This tests whether the position tracking logic was abstracted or hardcoded to a single coordinate frame.

**CNCSim-Full extensions:**

- **ext-01: Stock removal simulation.** Asks the agent to add volumetric stock tracking — given a workpiece bounding box and material, track material removal as the tool moves through cutting paths. This is a substantial architectural extension: it requires adding a spatial model (voxel grid or mesh) alongside the existing motion simulation. The extension prompt is written in machinist voice: "I'd also like the simulator to track what material gets removed from the workpiece as the tool cuts, so I can verify my programs aren't leaving extra stock or gouging."

- **ext-02: Haas dialect support.** Asks the agent to extend the simulator to handle Haas-specific G-code conventions (e.g., Haas macro variable syntax, Haas-specific canned cycle behavior). The extension provides a short Haas reference document in `extensions/ext-02/docs/`. This tests whether the parser and interpreter were designed with extensibility in mind or whether the RS274/NGC behavior is hardcoded throughout.

**Extension prompt style.** Extension prompts follow the same non-developer persona as the base prompt. They are written as natural follow-up requests from the same domain expert: "This is working well — now I'd also like it to..." The technical compatibility note (language, CLI contract, output schema additions) is appended identically to the base prompt.
