# Official results for IGES eval version 1.0.13

First run of the IGES eval. All 12 runs so far are gemini-cli / gemini-3-flash-preview (gemini-cli v0.36.0), 3 runs × 4 language variants.

**Task registration.** `iges-py` and `iges-rs` were added to `_KNOWN_TASKS` at the start of this sweep. The task registration does not require a reference implementation — only `prompt/`, `prompt/docs/`, `tests/`, and the shared `Evals/_shared/language-requirements-<lang>.md` file. A Python reference exists; no Rust reference exists yet.

**Inclusion rule.** Same as CNCSim: a run is included in the per-run detail table and in Best/Mean when it either completed normally or failed on its own accord. Self-inflicted zero-score runs (`context_exhausted`, `agent_error`, `build_failure`, `no_code_written`) count as 0 and are annotated. A run is excluded only on a harness- or environment-level failure. All 12 runs in this sweep have `exit_reason: completed` and are included.

Cost is `reported_cost_usd` from the agent CLI when available, otherwise `estimated_cost_usd` from the harness (marked with ~). Gemini CLI does not report its own cost, so all entries are `~`.

Test total: **258**. No extensions; `task_score` == `correctness` == passed / 258.

Commentary:
- [Why the high scorers won (js r3 0.585, rs r3 0.589, rs r2 0.527)](commentary/iges-gemini-3-flash-preview-high-scorers.md)
- [What went wrong in the sub-10% runs (cpp r2/r3, py r2/r3, rs r1)](commentary/iges-gemini-3-flash-preview-sub-10pct.md)
- [Postmortem: why `iges-rs` run 1 terminated at 0/258 with `status: success`](commentary/iges-rs-gemini-3-flash-preview-run1-postmortem.md)

## C++

### gemini-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 1.0.13 | 48/258 (18.6%) | 9.3% | 3/3 | Complete; all three run-binary invocations are cpp r1's (17/2/0) — r3 never ran its binary, r2 never ran it either |

#### gemini-3-flash-preview / -

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0.13 | 48/258 (18.6%) | 18.8 min | 14.9M | 105.6K | ~$2.208 | 166 |  9 | 2786 | [result](../../results/iges-cpp/gemini-cli/gemini-3-flash-preview/eval1/run1/result.json) [transcript](../../results/iges-cpp/gemini-cli/gemini-3-flash-preview/eval1/run1/transcript.jsonl) | Claims complete; single-file C++20 tool plus CMakeLists; lists parsing, writing, parametric evaluation for curves 100/102/104/106/110/112/126/130 and surfaces 114/118/120/122/128/140/190–198, and "all 87 entity types". Ran its own binary 17× through the session. |
| 2 | 1.0.13 | 19/258 (7.4%) | 13.3 min |  6.0M |  75.3K | ~$1.113 | 101 | 16 | 2845 | [result](../../results/iges-cpp/gemini-cli/gemini-3-flash-preview/eval1/run2/result.json) [transcript](../../results/iges-cpp/gemini-cli/gemini-3-flash-preview/eval1/run2/transcript.jsonl) | Claims complete with a terse "I'm done.". Built 5× but never invoked the binary. Categories needing round-trip fidelity all score 0; malformed-input / error-envelope paths partially work. |
| 3 | 1.0.13 |  5/258 (1.9%) |  5.0 min |  2.4M |  34.0K | ~$0.462 |  40 | 17 | 1496 | [result](../../results/iges-cpp/gemini-cli/gemini-3-flash-preview/eval1/run3/result.json) [transcript](../../results/iges-cpp/gemini-cli/gemini-3-flash-preview/eval1/run3/transcript.jsonl) | Claims complete with a confident multi-paragraph summary. Built 4× but never ran the binary. Every round-trip test fails with `terminate called after throwing an instance of 'std::invalid_argument' / what(): stoi` — parser crashes on the first non-integer parameter-data field. One unchecked `stoi` wipes out the largest category. |

---

## JavaScript

### gemini-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 1.0.13 | 151/258 (58.5%) | 32.9% | 3/3 | Complete; r3 is the highest JS scorer despite making 1 shell call and 0 binary invocations — wins on entity-dispatch breadth, not self-testing |

#### gemini-3-flash-preview / -

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0.13 |  62/258 (24.0%) |  5.1 min |  4.2M |  39.3K | ~$0.614 |  40 | 6 | 1680 | [result](../../results/iges-js/gemini-cli/gemini-3-flash-preview/eval1/run1/result.json) [transcript](../../results/iges-js/gemini-cli/gemini-3-flash-preview/eval1/run1/transcript.jsonl) | Claims complete with an effusive 1315-char feature list (parser/writer/evaluator/CLI/diagnostics). 6-file Node.js tree, 6 binary invocations. Dispatches ~20 entity types; strong on `line_entity` 9/9 and `reference_fixtures` 6/6 but 0/15 on `annotation_entities` and 3/44 on `entity_roundtrips`. |
| 2 | 1.0.13 |  42/258 (16.3%) | 10.7 min |  4.3M |  91.3K | ~$1.076 |  71 | 5 | 1021 | [result](../../results/iges-js/gemini-cli/gemini-3-flash-preview/eval1/run2/result.json) [transcript](../../results/iges-js/gemini-cli/gemini-3-flash-preview/eval1/run2/transcript.jsonl) | Claims complete with a one-word "Done." Most tool calls of the three JS runs (71) but the least code (1021 LOC) — spent the turn budget re-scaffolding rather than enumerating entities. Dispatches ~15 entity types. 1 binary invocation. |
| 3 | 1.0.13 | **151/258 (58.5%)** | 11.2 min |  8.2M |  75.7K | ~$1.412 |  59 | 4 | 1853 | [result](../../results/iges-js/gemini-cli/gemini-3-flash-preview/eval1/run3/result.json) [transcript](../../results/iges-js/gemini-cli/gemini-3-flash-preview/eval1/run3/transcript.jsonl) | Claims complete in one paragraph. **Zero shell calls**, zero binary invocations — a pure one-shot. 4-file Node.js tree whose `entities.js` dispatches 40+ IGES entity type numbers (0, 100–180). Wins on breadth: 15/15 annotation, 12/12 solid, 9/10 surface_boundary, 40/44 entity_roundtrips. Trades depth — only 6/51 geometric_eval vs r1's 12/51. |

---

## Python

### gemini-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 1.0.13 | 103/258 (39.9%) | 16.4% | 3/3 | Complete; r2 shipped a `SyntaxError` and claimed success without ever running the file |

#### gemini-3-flash-preview / -

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0.13 | 103/258 (39.9%) | 7.9 min | 4.2M | 48.6K | ~$0.792 | 52 | 4 | 1551 | [result](../../results/iges-py/gemini-cli/gemini-3-flash-preview/eval1/run1/result.json) [transcript](../../results/iges-py/gemini-cli/gemini-3-flash-preview/eval1/run1/transcript.jsonl) | Claims complete; modular `iges_schema.py` / `iges_io.py` / `iges_eval.py` / `main.py` split. Enumerates "all 87 entity types" and implements curves/surfaces 100–198. Ran its own binary 13× through the session — most-tested py run. |
| 2 | 1.0.13 |   6/258 (2.3%)  | 4.0 min | 1.1M | 43.4K | ~$0.370 | 13 | 2 |  336 | [result](../../results/iges-py/gemini-cli/gemini-3-flash-preview/eval1/run2/result.json) [transcript](../../results/iges-py/gemini-cli/gemini-3-flash-preview/eval1/run2/transcript.jsonl) | **False completion claim.** Agent asserts "the `iges` wrapper script is ready for use" but `main.py:199` has a literal `SyntaxError` — a broken f-string mixing `{{dict}[key]}` inside the format spec. Every test that invokes the CLI fails immediately. The agent never executed the file once (no `python3 main.py` call in the transcript) so the syntax error was never surfaced. |
| 3 | 1.0.13 |  18/258 (7.0%)  | 4.4 min | 2.9M | 40.6K | ~$0.580 | 28 | 6 |  988 | [result](../../results/iges-py/gemini-cli/gemini-3-flash-preview/eval1/run3/result.json) [transcript](../../results/iges-py/gemini-cli/gemini-3-flash-preview/eval1/run3/transcript.jsonl) | Claims complete. Binary runs (3 `--help` invocations). 6-file split; covers writer basics (`writer_param` 2/2, `writer_format` 2/4) and `data_types` 3/7 but zero on every entity-content category (annotation/solid/line/metadata/entity_roundtrips). Scope is roughly 10% of what the suite exercises. |

---

## Rust

### gemini-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 1.0.13 | 152/258 (58.9%) | 37.2% | 3/3 | Complete; r1 is a `build_failure` but self-inflicted (one late `cargo build` attempt, no recovery) — counted as 0 and included. r2 and r3 both clear ~0.5 |

#### gemini-3-flash-preview / -

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0.13 |   0/258 (0.0%)  | 15.5 min |  8.3M | 161.9K | ~$1.915 |  73 | 1 |  490 | [result](../../results/iges-rs/gemini-cli/gemini-3-flash-preview/eval1/run1/result.json) [transcript](../../results/iges-rs/gemini-cli/gemini-3-flash-preview/eval1/run1/transcript.jsonl) | **Incomplete and not acknowledged; closer to `agent_error` than a plain `build_failure`.** Last agent message is a forward-looking plan. Single-file `main.rs` (510 LOC). Self-entered `enter_plan_mode` and denied its own `write_file` 4× before exiting; later thrashed on main.rs with three full rewrites in ~2 min between one failed `cargo build` and the session end. Session terminated with `status: success` after 11 s of empty model output. Full reconstruction: [run 1 postmortem](commentary/iges-rs-gemini-3-flash-preview-run1-postmortem.md). |
| 2 | 1.0.13 | 136/258 (52.7%) | 14.9 min |  9.1M | 121.3K | ~$1.867 | 118 | 8 | 4808 | [result](../../results/iges-rs/gemini-cli/gemini-3-flash-preview/eval1/run2/result.json) [transcript](../../results/iges-rs/gemini-cli/gemini-3-flash-preview/eval1/run2/transcript.jsonl) | Claims complete in one short line. 8-file modular tree: `parser.rs`, `writer.rs`, `entities.rs` (2408 lines, ~110 struct/enum defs, 50+ entity type dispatch), `eval.rs` (696 lines, parametric evaluator for 19 entity types), `json_parser.rs`, `model.rs`, `error.rs`, `main.rs`. Ran 7× `cargo build` through the session. Distinctive win: `test_geometric_eval` 45/51 — more than 3× any other run in the sweep. |
| 3 | 1.0.13 | **152/258 (58.9%)** | 19.7 min | 14.5M | 132.1K | ~$2.955 | 132 | 8 | 4765 | [result](../../results/iges-rs/gemini-cli/gemini-3-flash-preview/eval1/run3/result.json) [transcript](../../results/iges-rs/gemini-cli/gemini-3-flash-preview/eval1/run3/transcript.jsonl) | Claims complete; explicitly asserts "all 87 entity types defined in the spec." 8-file modular tree, comparable layout to r2 but runs longer and produces more balanced coverage. Highest-scoring run of the entire IGES sweep. |
