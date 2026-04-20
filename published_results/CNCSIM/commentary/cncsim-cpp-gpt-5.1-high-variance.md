# Variance commentary: `cncsim-cpp` on codex-cli / gpt-5.1 high

Three runs of the same prompt produced scores of **0.513 / 0.076 / 0.363** (range 0.437, mean 0.317). This page documents what drove the spread.

Back-link: [`results-2_1_1.md` → C++ section → codex-cli → gpt-5.1 / high](../results-2_1_1.md).

## High-level metrics

| Run | Score | Wall | Files | Total LOC | Output tokens | Tool calls |
|-----|-------|------|-------|-----------|---------------|------------|
| 1 | 0.513 (278/542) | 16.4 min | 2 | 2117 | 87K | 52 |
| 2 | 0.076 (41/542) | 12.8 min | **8** | **1256** | 71K | 43 |
| 3 | 0.363 (197/542) | 16.9 min | 7 | 2015 | 92K | 48 |

Run 2 has the *most files* but the *least code* and the *shortest wall time* — it scaffolded more aggressively but finished generating earlier.

## Where the code actually lives

| Run | Architecture | Interpreter LOC | Parser LOC |
|-----|-------------|-----------------|------------|
| 1 | Monolithic `main.cpp` (2107 LOC) | ~1500 inline | ~600 inline |
| 2 | 8 files: parser/interpreter/json_writer/main | **249** (`interpreter.cpp`) | 428 |
| 3 | 4 units: common/parser/simulator/main | 1159 (`simulator.cpp`) | 461 |

Run 2's `interpreter.cpp` is only **249 LOC** for the entire RS274 execution engine. A quick structural probe counting motion/modal tokens (`"G0"`, `"G1"`, `"G17"`, `"G90"`, `execute_`, `handle_g`, `case G[0-9]`, etc.) returns:

- Run 1: 50 hits
- Run 2: **5 hits**
- Run 3: 43 hits

Run 2 has roughly **1/10th** the actual execution logic of the other two runs. Its 249 LOC of interpreter is almost entirely modal-state initialization — setting the default to G0/G17/G20/G54/G90 etc. — with no handlers for any of the subsequent codes.

## Where the scores diverge, per test file

Categories where run 2 collapses while runs 1/3 succeed:

| Test file | run 1 | run 2 | run 3 |
|-----------|------:|------:|------:|
| `test_canned_cycle_errors` | 27/27 | **0/27** | 27/27 |
| `test_feed_and_spindle_state` | 6/6 | **0/6** | 6/6 |
| `test_gcode_group_errors` | 10/11 | **0/11** | 11/11 |
| `test_parameter_expressions` | 33/37 | **1/37** | 0/37 |
| `test_position_tracking` | 17/35 | **0/35** | 0/35 |
| `test_probing_errors` | 12/13 | **0/13** | 0/13 |
| `test_word_repeat_errors` | 4/17 | 0/17 | 17/17 |
| `test_active_gcode_groups` | 24/34 | **6/34** | 25/34 |
| `test_tooling_state` | 14/15 | 2/15 | 14/15 |

Run 2 fails every category that requires *execution-after-parse*. Error-detection tests fail because the interpreter never runs far enough to detect the error. Modal-state tracking fails because execution doesn't happen. Parameter expressions fail because they parse but are never evaluated and stored.

## Why run 3 is weaker than run 1 (secondary question)

Different architectural blind spot: run 3 drops every `test_parameter_expressions` test (0/37) and `test_comment_parsing` (0/5) — its parser/simulator split apparently didn't implement expression evaluation — but it *beats* run 1 on `test_word_repeat_errors` (17/17 vs 4/17), `test_active_mcode_groups` (10/10 vs 6/10), and most error-detection categories. Run 3 spent its code budget on cleaner error handling at the cost of expression semantics; run 1 did the opposite.

## The pattern

This is **budget-allocation** variance, not random-sampling-noise variance. Given ~16 minutes and ~90K output tokens, gpt-5.1's behavior split three ways:

1. **Monolithic brute force (run 1, best).** One file, write-until-time-runs-out. Covers motion + expressions + errors partially.
2. **Architecture-first scaffolding (run 2, worst).** Committed to decomposition early, spent the bulk of the budget laying out 8 files and their interfaces, ran out before implementing the interpreter. Agent confidently declared complete because the *project structure* matched its plan, even though half the files are boilerplate.
3. **Selective decomposition (run 3, middle).** Split parser from simulator, implemented motion thoroughly, skipped expression/parameter semantics entirely.

The test suite penalizes (2) most heavily because the over-scaffolded run has no fallback — a monolithic partial implementation at least passes the surface-level tests, while a clean 8-file skeleton with only 249 LOC of interpreter passes almost nothing. This is the long-horizon agentic variance in practice: an early architectural decision (*how ambitious should decomposition be?*) locks in what the rest of the budget gets spent on, and the test suite's distribution of rewards determines which choice wins.
