# Variance commentary: `cncsim-py` on codex-cli / gpt-5.2 high

Three runs of the same prompt produced scores of **0.450 / 0.797 / 0.827** (range 0.376, mean 0.691). Runs 2 and 3 are essentially tied; run 1 is the outlier, and the cause is surprisingly narrow — a single strict spec interpretation that cascades into 260+ test failures.

Back-link: [`results-2_1_1.md` → py section → codex-cli → gpt-5.2 / high](../results-2_1_1.md).

## High-level metrics

| Run | Score | Wall | Files | Total LOC | Output tokens | Tool calls |
|-----|-------|------|-------|-----------|---------------|------------|
| 1 | 0.450 (244/542) | 35.7 min | 11 | 2661 | 102K | 63 |
| 2 | 0.797 (432/542) | 46.8 min | 13 | 2889 | 133K | 63 |
| 3 | 0.827 (448/542) | 58.4 min | 11 | 2822 | 157K | 74 |

All three runs share the same top-level architecture: one big core module (`simulator.py` / `interpreter.py` / `executor.py` at 1572-1716 LOC) plus ~10 small helpers for parsing, state, geometry, expressions, trace, and I/O. Totals are within ~10% of each other. LOC is not the differentiator.

## Where the code went

Structural probe across the full source tree (`.py` files, `__pycache__` excluded):

| Probe | Run 1 | Run 2 | Run 3 |
|-------|-----:|-----:|-----:|
| Motion G0-G3 literals | 19 | 22 | 32 |
| Coordinate G10/G28/G54/G92/G43 | 40 | 39 | 48 |
| Canned cycles G81-G89 | **46** | **50** | 27 |
| M-codes | 39 | 33 | 45 |
| CRC/cutter-comp tokens | **63** | **61** | 23 |
| trace/probe tokens | 121 | 125 | 115 |

Coverage is similar across runs — no obvious gap. Counterintuitively, the *highest-scoring* run (3) has the *fewest* cutter-comp and canned-cycle tokens. The differentiator is elsewhere.

## The actual cause: strict F-rate validation in run 1

Per-run failure classification:

| Run | `returncode != 0` failures | Other failures |
|-----|---:|---:|
| 1 | **270** | 12 |
| 2 | 92 | 18 |
| 3 | 84 | 10 |

Run 1's binary exits with code 1 roughly 3× as often as the others. To find out why, I ran it directly on the first parametrized case of `test_active_gcode_groups`:

```
input:  G94
        G0 X0
        G1 X0
```

Run 1 produces a valid output JSON — `active_modal_g_codes["1"] = "G1"` is correctly tracked — and then sets the output's `error` field to `"feed rate not set"` and exits 1. The test expects exit code 0.

This is run 1 taking the spec literally: RS274 §3.5.2 says "It is an error if the feed rate is 0 when linear motion at the current feed rate is programmed." No F is set in this program, so the feed rate is 0 (the default), so G1 is an error in the strictest reading. Runs 2 and 3 either defer F validation, default F to a non-error value, or don't error when F is absent — a more permissive reading of the same spec.

The cascade: every test that exercises G1/G2/G3 motion without explicitly setting F hits this error. Looking at per-test-file passes:

| Test file | Run 1 | Run 2 | Run 3 |
|-----------|------:|------:|------:|
| `test_active_gcode_groups` | 0/34 | 33/34 | 34/34 |
| `test_canned_cycles` | 0/23 | 16/23 | 19/23 |
| `test_comment_parsing` | 0/5 | 5/5 | 5/5 |
| `test_feed_and_spindle_state` | 0/6 | 6/6 | 6/6 |
| `test_g92_offsets` | 0/11 | 10/11 | 11/11 |
| `test_parameter_expressions` | 0/37 | 37/37 | 37/37 |
| `test_parameter_values` | 0/5 | 5/5 | 5/5 |
| `test_position_tracking` | 0/35 | 16/35 | 15/35 |
| `test_tooling_state` | 0/15 | 13/15 | 14/15 |
| `test_canned_cycle_errors` | 27/27 | 22/27 | 27/27 |
| `test_cutter_radius_compensation_errors` | 45/47 | 47/47 | 36/47 |
| `test_trace_stepping` | 41/50 | 43/50 | 46/50 |

Run 1 scores zero on every behavioral suite whose inputs exercise motion without F. Where it *does* pass, the test either deliberately provides F (trace suites, error suites) or exercises parsing/validation paths that don't require F to be set first (canned_cycle_errors, cutter_radius_compensation_errors).

## The pattern

Unlike the [gpt-5.1 cpp case](cncsim-cpp-gpt-5.1-high-variance.md) (architectural variance) or the [gpt-5.2-codex rs case](cncsim-rs-gpt-5.2-codex-high-variance.md) (coverage variance), this is **spec-interpretation variance**. All three runs wrote comparable code with comparable coverage; they just disagreed on one edge case in how to handle a missing F rate. Run 1 took the literal reading and rejected the program as invalid; runs 2 and 3 deferred or relaxed the check and ran the program to completion.

This is the most fragile variance type to measure: the agent made a plausible, defensible choice early in implementation (strict F validation seems *more* correct by the spec, not less), and the test suite penalized it heavily because most tests don't explicitly set F before each motion. It's a one-line difference — `raise ProgramError("feed rate not set")` vs. a quiet default — producing a 0.38 score swing.

The takeaway for test-suite design: specs have degenerate corners where a strict reading and a permissive reading both defensibly pass, and the test suite effectively picks one via the inputs it uses. Authors of tests that don't care about F (modal-group tracking, coordinate-system offsets, expression evaluation) still need to set F, or the test will over-reward whichever permissive interpretation the other agents happened to pick.
