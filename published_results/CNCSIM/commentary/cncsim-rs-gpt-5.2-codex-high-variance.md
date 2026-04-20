# Variance commentary: `cncsim-rs` on codex-cli / gpt-5.2-codex xhigh

Three runs of the same prompt produced scores of **0.480 / 0.808 / 0.411** (range 0.397, mean 0.566). Unlike the [gpt-5.1 cpp case](cncsim-cpp-gpt-5.1-high-variance.md) — where variance came from *how decomposed* the architecture got — here all three runs made the same architectural choice (single-file `src/main.rs` monolith around 3000 LOC). The variance is about **how the agent budgeted feature coverage across the RS274 spec**.

Back-link: [`results-2_1_1.md` → rs section → codex-cli → gpt-5.2-codex / xhigh](../results-2_1_1.md).

## High-level metrics

| Run | Score | Wall | `main.rs` LOC | Tool calls | Output tokens |
|-----|-------|------|---------------|------------|---------------|
| 1 | 0.480 (260/542) | 64.8 min | 2929 | 104 | 192K |
| 2 | 0.808 (438/542) | 78.3 min | 3125 | 112 | 202K |
| 3 | 0.411 (223/542) | 92.1 min | **3751** | **138** | **262K** |

Run 3 wrote the *most code*, spent the *most time*, and made the *most tool calls* — and scored the lowest. "More code = better" is straightforwardly wrong here.

## Where the code actually went

Structural probe of each `src/main.rs`:

| Probe | Run 1 | Run 2 | Run 3 |
|-------|-----:|-----:|-----:|
| Motion literals (`"G0"`/`"G1"`/`"G2"`/`"G3"`) | 2 | 17 | 16 |
| Coordinate/tool literals (G10/G28/G54/G92/G43/…) | 3 | **35** | 20 |
| Canned cycle literals (G81-G89) | **0** | **31** | 10 |
| M-code literals | 1 | **21** | 8 |
| Cutter radius compensation tokens | 29 | 55 | **90** |
| Trace-related tokens | 80 | **138** | 67 |
| `match` blocks | **58** | 36 | 33 |
| Enum definitions | 9 | 8 | 15 |
| Function definitions | 80 | 75 | **100** |

Three very different budget allocations are visible:

- **Run 1.** Heavy structured dispatch (58 `match`, 9 enums), light on literal-match breadth. Likely dispatches G-codes via a `GCode::G0 => …, GCode::G1 => …` enum rather than string literals. But **0 canned-cycle literals** — that whole feature class is missing. Clean architecture masks narrow coverage.
- **Run 2.** Breadth-first. Highest counts across every feature category — motion, coordinates, canned cycles, M-codes, trace. Nothing especially deep; just thoroughly implemented.
- **Run 3.** **Over-invested in cutter radius compensation** (90 CRC tokens — 1.6× run 2, 3× run 1) and granular helper functions (100 `fn` defs). Under-invested in breadth — third as many canned-cycle literals as run 2, less than half the M-code coverage.

## What actually failed, per category

| Test file | Run 1 | Run 2 | Run 3 |
|-----------|------:|------:|------:|
| `test_active_gcode_groups` | 0/34 | **34/34** | 0/34 |
| `test_active_mcode_groups` | 0/10 | **10/10** | 0/10 |
| `test_canned_cycles` | 0/23 | **17/23** | 0/23 |
| `test_parameter_expressions` | 0/37 | **37/37** | 0/37 |
| `test_position_tracking` | 0/35 | **15/35** | 0/35 |
| `test_g92_offsets` | 0/11 | **11/11** | 0/11 |
| `test_g28_g30` | 0/8 | **8/8** | 0/8 |
| `test_tooling_state` | 0/15 | **14/15** | 0/15 |
| `test_cutter_radius_compensation_errors` | 45/47 | 36/47 | 45/47 |
| `test_parameter_errors` | 19/21 | 13/21 | **21/21** |

Run 2 dominates most behavioral categories; runs 1 and 3 both score zero on ~15 categories. Note the mirror at the bottom: run 3 *beats* run 2 on `test_cutter_radius_compensation_errors` (45 vs 36) and `test_parameter_errors` (21 vs 13) — the CRC over-investment paid off in those specific categories, but at a massive breadth cost.

## Why the "zero" categories are actually zero for runs 1 and 3

The failure mode is `assert completed.returncode == 0` — the agent's binary exits non-zero on test inputs it doesn't fully handle. Breakdown:

| Run | `returncode != 0` failures | Other failures |
|-----|---:|---:|
| 1 | **260** | 22 |
| 2 | 90 | 14 |
| 3 | **267** | 52 |

Runs 1 and 3 have ~260 tests each where the simulator crashed or returned `Err(…)` on test inputs that hit an unimplemented code path. The tests never reached their real assertions — `output_path.is_file()` or `returncode == 0` fails first — and the assertion message shows whatever happened to be in stderr (cargo build warnings from `cargo run` recompiling the binary). **Those stderr warnings are a red herring; the real issue is unimplemented behavior.**

## The pattern

Three different strategies on the same task, same model, same prompt:

1. **Run 1 — "architecture over coverage."** Nicest Rust (enum-driven dispatch, most match blocks), but skipped canned cycles entirely and kept coordinate/modal handling shallow. Clean code, narrow functionality.
2. **Run 2 — "pragmatic breadth."** Touched every major feature category. Less structured than run 1 but broader. Winning strategy for a test suite that rewards coverage.
3. **Run 3 — "over-specialize a niche."** Spent ~800 extra LOC on cutter radius compensation and granular helper functions. CRC is legitimately hard (RS274 Appendix B), but the test suite has far more weight in the breadth categories (modal tracking, parameter expressions, canned cycles) — all of which run 3 skipped or stubbed.

The common thread with the gpt-5.1 cpp finding: **at long-horizon agentic scale, the agent's early scope decision (*"how deep on CRC?"* / *"how decomposed?"*) determines where the remaining budget gets spent, and small differences in that decision produce large score swings on a broad suite.** The 0.397 range between 0.808 and 0.411 isn't sampling noise — it's three viable strategies playing out differently against a test suite that has its own weightings.
