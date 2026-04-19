# High-scoring runs: `iges-js` run 3 and `iges-rs` run 2 on gemini-cli / gemini-3-flash-preview

The two best results in the 2026-04-18 IGES sweep: `iges-js` run 3 at **0.585** and `iges-rs` run 2 at **0.527**. Both came from sibling-run cohorts where other runs scored much lower (js r2 = 0.163, rs r1 = 0.000). This note explains what those two runs did differently.

Back-link: [`iges-gemini-3-flash-preview-sub-10pct.md`](iges-gemini-3-flash-preview-sub-10pct.md) covers the sub-10% runs.

## Aggregate metrics side-by-side

| Run | Score | Wall | Files | LOC | Tool calls | Output tokens | Build |
|-----|------:|-----:|------:|----:|-----------:|--------------:|:-----:|
| js r1 | 0.240 |  5.1 min | 6 | 1680 |  40 |  39K | ok |
| js r2 | 0.163 | 10.7 min | 5 | 1021 |  71 |  91K | ok |
| **js r3** | **0.585** | 11.2 min | **4** | 1853 | 59 | 76K | ok |
| **rs r1** | 0.000 | 15.5 min | 1 | 490 | 73 | **162K** | **fail** |
| **rs r2** | **0.527** | 14.9 min | **8** | **4808** | **118** | 121K | ok |

Two notable shapes:

- **js r3** is *not* the biggest js implementation by LOC (r1 has 1680 vs r3's 1853 — close), nor the longest-running. It wrote the *fewest files* but packed a richer payload into them.
- **rs r2** dwarfs every other run in the entire IGES sweep on LOC (4808) and tool calls (118). It is by far the most thorough implementation attempted.

## js run 3 — wins on breadth via a much wider entity table

js r1 / r2 / r3 are the *same agent* (gemini-3-flash-preview) running the *same prompt* three times. All three produced a modular Node.js layout with `entities.js`, `parser.js`, `writer.js`, etc. The single structural difference that drives the 0.240 / 0.163 / 0.585 spread is **how many IGES entity types each implementation enumerates in its dispatch table**.

Counting `case <n>:` / `<n>: (f) => ...` dispatch entries in each run's `entities.js`:

| Run | Entity types dispatched in `entities.js` |
|-----|:----------------------------------------:|
| js r1 | ~20 (100–132 range) |
| js r2 | ~15 (100–125 range) |
| **js r3** | **40+ (0, 100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 123, 124, 125, 126, 128, 130, 132, 134, 136, 138, 140, 141, 142, 143, 144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 168, 180)** |

That doubled dispatch table is exactly what the scorecard rewards. Categories where js r3 dominates over r1 and r2:

| Category | Total | r1 | r2 | **r3** |
|----------|------:|---:|---:|-------:|
| `annotation_entities` | 15 | 0 | 0 | **15** |
| `entity_roundtrips` | 44 | 3 | 1 | **40** |
| `solid_entities` | 12 | 0 | 0 | **12** |
| `surface_boundary_entities` | 10 | 0 | 0 | **9** |
| `metadata_entities` | 9 | 0 | 0 | **7** |
| `pointer_backed_fields` | 8 | 0 | 0 | **7** |
| `structure_and_view_entities` | 4 | 0 | 0 | **4** |
| `defaulted_fields` | 3 | 0 | 0 | **3** |

Those eight categories alone yield +97 tests for r3 that r1 and r2 both leave on the table.

Interestingly, js r3 is actually *weaker* than js r1 in curve-math depth:

| Category | Total | r1 | r2 | **r3** |
|----------|------:|---:|---:|-------:|
| `geometric_eval` | 51 | 12 | 3 | **6** |
| `line_entity` | 9 | 9 | 0 | **4** |
| `reference_fixtures` | 6 | 6 | 6 | **3** |

r3 traded some per-entity math correctness for entity-kind breadth, and the trade paid off because the suite has more breadth tests than depth tests. The three sessions look like three different bets by the same model about where to spend its 11-minute budget; only one bet matched the test distribution.

### Why js r2 lost despite more tool calls

js r2 used 71 tool calls (most of the three) but produced only 1021 LOC (least) and dispatched the narrowest entity set (~15 types). Its `entity_roundtrips` score is **1/44**. The agent spent most of its turn budget iterating on the parser scaffolding rather than enumerating entities. Its `agent_last_message` is a terse "Done." — consistent with the agent having no clear signal that its implementation was incomplete.

## rs run 2 — wins on architectural scope + a dedicated evaluator module

Only two rs runs have completed so far (r3 is still in progress), so the contrast is rs r1 (0.000, build failed) vs rs r2 (0.527). The delta is almost purely architectural:

**rs r1 layout** — one file:
```
src/main.rs         510 lines   (fn main at line 39, rest inline)
```
Monolithic, never compiled, session exited mid-plan.

**rs r2 layout** — eight files, 5180 total lines:
```
src/main.rs          185 lines   CLI dispatch
src/parser.rs        267 lines   IGES section parsing
src/writer.rs        425 lines   IGES emission
src/entities.rs     2408 lines   ~110 struct/enum definitions, 50+ type dispatch
src/eval.rs          696 lines   parametric evaluator for 19 entity types
src/json_parser.rs   889 lines   canonical JSON handling
src/model.rs         220 lines   shared types
src/error.rs          92 lines   diagnostic envelope
```

The rs r2 agent actually split the problem into the right modules *before* writing 4800 lines; rs r1 tried to inline everything into `main.rs`, blew its turn budget, and never got to a state that compiled.

### rs r2's distinctive win: `geometric_eval`

The single biggest test category is `test_geometric_eval` (51 tests). Across all 11 completed runs, rs r2 scored **45/51 (88%)** on it — more than 3× any other run. The runner-up is js r1 at 12/51.

`src/eval.rs` (696 lines) explicitly implements parametric evaluation for entity types `100, 102, 104, 106, 110, 112, 114, 118, 120, 122, 126, 128, 130, 140, 190, 192, 194, 196, 198` — that's the core curve/surface set (Circular Arc, Composite Curve, Conic Arc, Copious Data, Line, Parametric Spline Curve, Parametric Spline Surface, Curve on Parametric Surface, Boundary, Composite Curve on Parametric Surface, Rational B-Spline Curve, Rational B-Spline Surface, Offset Curve, Offset Surface, plus several plane/sphere/torus/cylinder analytics). rs r1 never wrote any eval logic at all.

### Where rs r2 still fails

rs r2 is near-zero on several small categories: `data_types` 0/7, `metadata_entities` 0/9, `solid_entities` 0/12, `writer_global` 0/2, `writer_param` 0/2. Those 32 unfilled tests are the ceiling between 0.527 and what a more balanced implementation would score. rs r2's strategy was "go deep on the parametric stack," and it did not allocate tokens to the bookkeeping-style categories.

## Shell activity across the sweep

A pattern that looked obvious ("winners self-test, losers don't") turns out to be language-dependent once you count the actual `run_shell_command` invocations in each transcript:

| Run | Score | Shell cmds | Builds | Binary invocations |
|-----|------:|-----------:|-------:|-------------------:|
| cpp r1 | 0.186 | 33 | 7 | **17** |
| cpp r2 | 0.074 | 10 | 5 | 2 |
| cpp r3 | 0.019 |  6 | 4 | 0 |
| js r1 | 0.240 | 13 | 0 | 6 |
| js r2 | 0.163 |  2 | 0 | 1 |
| **js r3** | **0.585** | **1** | **0** | **0** |
| py r1 | 0.399 | 19 | 0 | **13** |
| py r2 | 0.023 |  3 | 0 | 0 |
| py r3 | 0.070 |  7 | 0 | 3 |
| rs r1 | 0.000 |  3 | 1 (failed) | 0 |
| **rs r2** | **0.527** | 12 | **7** | 0 |

For cpp and py the pattern is clean: binary invocations correlate with score. cpp r1 (17 runs) tops its cohort at 0.186. py r1 (13 runs) tops its cohort at 0.399.

For rs the analog is `cargo build` iterations: rs r2 built seven times through its session and cleared 0.527; rs r1 built **once** — 12.5 minutes into the session, against a format-string error it then patched once more before the gemini-cli session terminated with `status: success`. (No harness-imposed time cap; durations across the eleven runs range 3.9–18.7 min. The most likely explanation is a CLI-internal turn/token ceiling, inferred from rs r1 being the heaviest session of the eleven at 8.34M input tokens.)

**For js the pattern inverts.** The highest-scoring run in the entire sweep — js r3 at 0.585 — made exactly one shell call and zero binary invocations. It wrote 4 files across 1853 LOC in one pass and declared done. The lower-scoring js r1 (6 binary runs) and js r2 (1) both spent more tool budget on self-testing but ended up with narrower entity tables.

The most defensible reading: for unforgiving languages (C++, Rust), every shell call that surfaces a real error recovers tests; for forgiving languages where this model's generation is already close to correct (Node.js with just `fs`/`path`), tool calls spent running the binary are tool calls *not* spent writing entity handlers — and entity handlers are what the IGES suite rewards most heavily.

## What the two winners actually share

What js r3 and rs r2 *do* share:

1. **Modular multi-file layout.** Both use ≥4 files with clear separation (`parser` / `writer` / `entities` / `eval`). The worst performers in each language went either too thin (py r2 = 2 files) or monolithic (rs r1 = 1 file).
2. **Rich entity dispatch.** Both winners enumerate 40+ IGES entity type numbers in their dispatch tables. Every run under 0.2 in this sweep has ≤20 dispatched types.
3. **Full turn budget used.** js r3 ran 11.2 min and rs r2 ran 14.9 min — both near the top of their cohorts.

What they do *not* share: self-testing behaviour. rs r2 hammered `cargo build`; js r3 ran nothing. The shared property that predicts score is the **size of the entity dispatch table**, not the amount of runtime validation.

## Takeaway

On the same model, same prompt, and comparable wall-clock budgets, the spread from 0.000 to 0.585 on IGES is driven more by *which parts of the spec the agent chose to implement* than by raw capability. The losers failed in four distinct ways: scaffolding without filling in entity tables (js r2), compiling but never running the binary (cpp r2, cpp r3), shipping code that never executed at all (py r2, with a literal SyntaxError), and writing 12 minutes before attempting to build (rs r1). None of those four failure modes reduce to "ran out of tokens" — they are all allocation failures inside a budget the successful sibling run completed with.
