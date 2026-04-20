# Variance commentary: `cncsim-js` on claude-code / claude-sonnet-4-6 high

Three runs of the same prompt produced scores of **0.793 / 0.749 / 0.417** (range 0.376, mean 0.653). Run 3 wrote the most code and scored the worst — an over-engineering pattern similar to the [gpt-5.2-codex rs case](cncsim-rs-gpt-5.2-codex-high-variance.md), but concentrated in the parser rather than the execution engine.

Back-link: [`results-2_1_1.md` → js section → claude-code → claude-sonnet-4-6 / high](../results-2_1_1.md).

## High-level metrics

| Run | Score | Wall | Files | Total LOC | Output tokens | Tool calls | Cost |
|-----|-------|------|-------|-----------|---------------|------------|------|
| 1 | 0.793 (430/542) | 38.6 min | 6 | 3427 | 144K | 94 | $5.02 |
| 2 | 0.749 (406/542) | 53.0 min | 6 | **2050** | 212K | 73 | $6.34 |
| 3 | 0.417 (226/542) | 65.2 min | 6 | **3770** | 203K | 115 | $8.47 |

All three runs chose the same 6-file architecture — no architectural variance. Run 2 wrote the *least* code (2050 LOC) for a middle score; run 3 wrote the *most* code (3770 LOC) for the worst score. The "more code = better" intuition is again inverted.

## Where the code went

Per-file LOC for each run:

| File | Run 1 | Run 2 | Run 3 |
|------|-----:|-----:|-----:|
| `main.js` | 384 | 340 | 415 |
| `parser.js` | 530 | 368 | **783** |
| `executor.js` / `interpreter.js` | 1660 | 888 | 1358 |
| `machine.js` | 438 | 281 | 606 |
| `trace.js` / `tracer.js` | 458 | 293 | 643 |
| `geometry.js` / `arcmath.js` | 388 | 143 | 441 |
| **Total** | **3427** | **2050** | **3770** |

Two things stand out:

- **Run 2 is compact everywhere.** Half the tracer, half the geometry, ~half the parser and executor. Yet it still scored 0.749 — close to run 1's 0.793. More efficient encoding of the same functionality.
- **Run 3 has an oversized parser.** 783 LOC is 2× run 2's and 1.5× run 1's. The executor is smaller than run 1's (1358 vs 1660) but machine.js, tracer.js, and arcmath.js are all larger than either other run.

A structural probe across `.js` files (no `node_modules`):

| Probe | Run 1 | Run 2 | Run 3 |
|-------|-----:|-----:|-----:|
| Motion G0-G3 literals | 6 | 18 | 21 |
| M-code literals | 36 | 50 | **85** |
| CRC/cutter-comp tokens | 16 | 10 | **35** |
| trace/probe tokens | 17 | 19 | 19 |
| function definitions | 35 | 30 | **69** |
| class definitions | 4 | 6 | 3 |

Run 3 has ~2× the function granularity, ~2× the M-code coverage, and ~2-3× the CRC surface area of the other two runs. It expanded in every direction — and it lost.

## What actually failed

Per-run failure classification:

| Run | `returncode != 0` failures | Other failures |
|-----|---:|---:|
| 1 | 93 | 19 |
| 2 | 122 | 14 |
| 3 | **267** | 52 |

Run 3's binary exits non-zero ~3× as often as the others. Per-test-file pass breakdown shows where:

| Test file | Run 1 | Run 2 | Run 3 |
|-----------|------:|------:|------:|
| `test_canned_cycle_errors` | 23/27 | 19/27 | **0/27** |
| `test_parameter_errors` | 15/21 | 13/21 | **0/21** |
| `test_word_repeat_errors` | 17/17 | 6/17 | **0/17** |
| `test_gcode_group_errors` | 10/11 | 10/11 | **0/11** |
| `test_mcode_group_errors` | 4/6 | 4/6 | **0/6** |
| `test_probing_errors` | 12/13 | 10/13 | **0/13** |
| `test_tool_length_compensation_errors` | 3/3 | 3/3 | **0/3** |
| `test_tool_selection_errors` | 3/3 | 2/3 | **0/3** |
| `test_cutter_radius_compensation_errors` | 30/47 | 44/47 | **2/47** |
| `test_comment_errors` | 3/3 | 2/3 | **0/3** |
| `test_arc_errors` | 4/5 | 5/5 | **0/5** |
| `test_g28_g30` | 4/8 | 8/8 | **0/8** |
| `test_cutter_radius_compensation` | 15/24 | 0/24 | 0/24 |
| `test_position_tracking` | 30/35 | 16/35 | 17/35 |

The most striking row is the near-total collapse on error-handling suites: `test_canned_cycle_errors`, `test_parameter_errors`, `test_word_repeat_errors`, `test_gcode_group_errors`, `test_mcode_group_errors`, `test_probing_errors`, `test_tool_*_errors`, `test_arc_errors`, `test_comment_errors` — all zero in run 3, all well-passed in runs 1-2. These are tests that exercise *invalid* inputs and expect specific error behavior (exit code 1, error field populated, etc.).

The fact that run 3 fails *error*-suites at the `returncode == 0` assertion suggests its parser is rejecting too many inputs. The test expects the simulator to run, detect a specific error condition, and exit 1 with a specific error message. Run 3's oversized parser apparently rejects these inputs earlier (wrong exit code, wrong error path, or a `throw` not caught), failing the expected-error pattern.

## Run 1 vs Run 2 (both passing, different strengths)

Run 1 and run 2 are close in score but have visibly different strengths:

- Run 1 wins on: `test_cutter_radius_compensation` (15 vs 0), `test_parameter_expressions` (30 vs 21), `test_position_tracking` (30 vs 16), `test_word_repeat_errors` (17 vs 6), `test_probing_errors` (12 vs 10).
- Run 2 wins on: `test_canned_cycles` (23 vs 20), `test_cutter_radius_compensation_errors` (44 vs 30), `test_parameter_file_cli` (10 vs 7), `test_g28_g30` (8 vs 4), `test_trace_format` (36 vs 30).

Run 1 went deeper on *core* behavior (motion tracking, expressions, CRC actual execution). Run 2 went deeper on *error paths* (cutter-comp errors, g28/g30 validation, canned cycle errors). Two different prioritizations that net out to similar totals.

## The pattern

Three distinct strategies on the same task:

1. **Run 1 — "core-heavy, sufficient error handling."** 3427 LOC concentrated in the executor (1660) and parser (530). Best at the behavioral tests that require tracking state through real programs. Score: 0.793.
2. **Run 2 — "compact, error-path-heavy."** 2050 LOC — 60% of run 1's size. Less core, more validation; wins error-handling suites. Score: 0.749.
3. **Run 3 — "over-built parser, permissions misaligned."** 3770 LOC (most of any run) with a 783-LOC parser (2× run 2's). Apparently rejects too many inputs — exits non-zero on ~267 tests that runs 1-2 execute successfully. Score: 0.417.

The common thread with [the other commentaries](./): at long-horizon agentic scale, **where the agent invests its code budget is more predictive than how much it writes**. Run 2 proves you can get 0.749 with 2050 LOC if the budget is well-allocated; run 3 proves you can get 0.417 with 3770 LOC if it isn't. The gap between run 2 and run 3 is not code quantity but rather where the code applies pressure — run 3's parser treats inputs more strictly than the test suite expects, and the rest of the project can't recover from that.
