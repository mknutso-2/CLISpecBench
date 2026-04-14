# Official results for CNCSim eval version 2.0.2

v2.0.2 adds a shared one-shot prompt (`Evals/_shared/require-one-shot.md`) appended
to all agent prompts. Only runs against the v2.0.2 prompt + 542-test suite are
included.

**Only runs where the agent completed successfully (`exit_reason: "completed"`)
appear in the tables.** Runs that errored, timed out, or were rate-limited are
excluded and noted as needing reruns. Best/Mean are computed only over completed runs.

Cost is `reported_cost_usd` from the agent CLI when available, otherwise
`estimated_cost_usd` computed by the harness (marked with ~). Copilot CLI does
not report input tokens or cost.

## C++

### claude-code

No v2.0.2 runs yet. See `results-2_0_1.md` for v2.0.1 results.

---

### codex-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| gpt-5.2-codex | xhigh | 419/542 (77.3%) | 58.0% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 321/542 (59.2%) | 40.5% | 3/3 | Complete |
| gpt-5.1-codex-mini | - | 132/542 (24.4%) | 8.1% | 3/3 | Complete; run 1 refused task, run 3 build failed |

#### gpt-5.2-codex / xhigh

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 266/542 (49.1%) | 130.2 min | 22.9M | 286K | ~$8.62 | 117 | 2 | 3255 | [result](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run1/transcript.jsonl) | Claims complete. |
| 2 | 419/542 (77.3%) | 64.2 min | 18.9M | 184K | ~$6.56 | 152 | 3 | 4332 | [result](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run2/transcript.jsonl) | Claims complete; noted corrections to G10/G92 motion suppression, cutter-comp arc position, and trace step validation. |
| 3 | 258/542 (47.6%) | 92.5 min | 35.3M | 226K | ~$10.65 | 178 | 3 | 3565 | [result](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run3/transcript.jsonl) | Claims complete. |

Prior eval (eval2): 1/3 completed (run 1: 420/542), run 2 timed out at 458/542, run 3 errored — rerun as eval3.

#### gpt-5.1-codex-max / xhigh

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 203/542 (37.5%) | 16.1 min | 3.8M | 56K | ~$2.13 | 41 | 3 | 2225 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run1/transcript.jsonl) | Claims complete. |
| 2 | 321/542 (59.2%) | 21.0 min | 9.3M | 70K | ~$3.23 | 55 | 3 | 2122 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run2/transcript.jsonl) | Claims complete; noted simplifications in canned cycles and cutter-radius compensation. |
| 3 | 134/542 (24.7%) | 15.6 min | 4.3M | 54K | ~$2.02 | 48 | 3 | 988 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run3/transcript.jsonl) | Claims complete. |

Prior eval (eval1): all 3 runs failed with `no_output` in 5s (startup issue).

#### gpt-5.1-codex-mini

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0/542 (0.0%) | 1.1 min | 298K | 6K | ~$0.03 | 6 | 0 | 0 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run1/transcript.jsonl) | Incomplete; wrote no code. Declined the task as "far beyond what I can deliver in a single response." Asked user to "break the problem into narrower slices." |
| 2 | 132/542 (24.4%) | 12.5 min | 5.6M | 88K | ~$0.41 | 34 | 3 | 1735 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run2/transcript.jsonl) | Claims complete. |
| 3 | 0/542 (0.0%) | 6.2 min | 2.1M | 40K | ~$0.19 | 35 | 2 | 428 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run3/transcript.jsonl) | Incomplete; build failed. Acknowledged incomplete — listed 3 "Remaining work" items and noted "build and runtime logic are still pending." Spent 69% of tool calls reading the spec; only wrote an expression parser (no main, no simulation). |

---

### gemini-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 238/542 (43.9%) | 37.9% | 3/3 | Complete |
| gemini-2.5-flash | - | 18/542 (3.3%) | 1.1% | 3/3 | Complete; runs 1-2 build failures, run 3 built |
| gemini-2.5-flash-lite | - | 0/542 (0.0%) | 0.0% | 3/3 | Complete; all builds failed |

#### gemini-3-flash-preview

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 196/542 (36.2%) | 4.8 min | 2.3M | 37K | ~$0.45 | 33 | 10 | 2483 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run1/transcript.jsonl) | Claims complete. |
| 2 | 182/542 (33.6%) | 7.4 min | 4.9M | 50K | ~$0.67 | 47 | 10 | 916 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run2/transcript.jsonl) | Claims complete. |
| 3 | 238/542 (43.9%) | 13.3 min | 10.9M | 81K | ~$1.25 | 83 | 14 | 1043 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run3/transcript.jsonl) | Claims complete. |

#### gemini-2.5-flash

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0/542 (0.0%) | 14.6 min | 5.6M | 86K | ~$0.92 | 54 | 2 | 509 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run1/transcript.jsonl) | Incomplete; build failed. Acknowledged limitations and stopped. |
| 2 | 0/542 (0.0%) | 33.2 min | 17.6M | 68K | ~$2.71 | 116 | 9 | 1762 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run2/transcript.jsonl) | Incomplete; build failed. Claimed blocked by persistent string literal compilation errors. |
| 3 | 18/542 (3.3%) | 10.0 min | 8.6M | 35K | ~$0.44 | 89 | 3 | 1168 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run3/transcript.jsonl) | Incomplete; was still iterating when session ended. Built successfully. |

#### gemini-2.5-flash-lite

All 3 runs scored 0/542. Model capability issues: missing tool parameters, hallucinated
filenames, builds that don't compile. See transcript investigation in prior session notes.

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0/542 (0.0%) | 1.3 min | 258K | 17K | ~$0.02 | 2 | 0 | 0 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run1/transcript.jsonl) | Incomplete; wrote no code. Laid out a plan but stopped after reading the spec. |
| 2 | 0/542 (0.0%) | 11.1 min | 6.4M | 110K | ~$0.27 | 48 | 16 | 2121 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run2/transcript.jsonl) | Incomplete; build failed. Encountered repeated `write_file` tool errors (missing `file_path` parameter). |
| 3 | 0/542 (0.0%) | 1.9 min | 888K | 12K | ~$0.02 | 10 | 2 | 399 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run3/transcript.jsonl) | Incomplete; scaffolded only. Set up project structure but wrote no implementation logic. |

---

### copilot-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| claude-haiku-4.5 | - | 90/542 (16.6%) | 14.2% | 3/3 | Complete (across eval1+eval2); eval2 run 3 rate limited |
| gpt-4.1 | - | 20/542 (3.7%) | 1.4% | 3/3 | Complete |
| gpt-5-mini | high | 145/542 (26.8%) | 24.1% | 3/3 | Complete |

#### claude-haiku-4.5

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| eval1/1 | 90/542 (16.6%) | 7.8 min | 0 | 49K | - | 0 | 3 | 1276 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval1/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval1/run1/transcript.jsonl) | Claims complete. |
| eval2/1 | 55/542 (10.1%) | 8.8 min | 0 | 41K | - | 0 | 3 | 1328 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run1/transcript.jsonl) | Claims complete. |
| eval2/2 | 86/542 (15.9%) | 13.1 min | 0 | 58K | - | 0 | 10 | 1996 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run2/transcript.jsonl) | Claims complete. |

Excluded: eval1 runs 2-3 (error + rate limited), eval2 run 3 (rate limited mid-execution at 75/542, 3231 LOC).

#### gpt-4.1

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1/542 (0.2%) | 3.3 min | 0 | 9K | - | 0 | 18 | 350 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run1/transcript.jsonl) | Incomplete; scaffolded only. Acknowledged "core logic... will be implemented" next. |
| 2 | 20/542 (3.7%) | 3.9 min | 0 | 10K | - | 0 | 18 | 506 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run2/transcript.jsonl) | Incomplete; scaffolded only. Asked "Let me know if you want to proceed with the execution engine." |
| 3 | 1/542 (0.2%) | 5.2 min | 0 | 14K | - | 0 | 2 | 207 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run3/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run3/transcript.jsonl) | Incomplete; scaffolded only. Asked "Let me know if you want to proceed with a specific part." |

#### gpt-5-mini / high

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 145/542 (26.8%) | 11.7 min | 0 | 43K | - | 0 | 2 | 709 | [result](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run1/transcript.jsonl) | Claims complete. |
| 2 | 113/542 (20.8%) | 8.7 min | 0 | 36K | - | 0 | 3 | 1527 | [result](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run2/transcript.jsonl) | Claims complete. |
| 3 | 134/542 (24.7%) | 8.3 min | 0 | 31K | - | 0 | 4 | 2335 | [result](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run3/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run3/transcript.jsonl) | Claims complete. |

Prior eval (eval1): all 3 runs rate limited (free-tier quota exhaustion). These results are from eval3 after cooldown.

---

## js

### codex-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| gpt-5.1-codex-mini | - | 166/542 (30.6%) | 11.4% | 3/3 | Complete; runs 1-2 scaffolded only |

#### gpt-5.1-codex-mini

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 18/542 (3.3%) | 5.3 min | 1.5M | 33K | ~$0.15 | 26 | 1 | 532 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run1/transcript.jsonl) | Incomplete; acknowledged "interpreter and trace generation are still missing" and listed outstanding work. |
| 2 | 1/542 (0.2%) | 8.4 min | 1.8M | 55K | ~$0.17 | 29 | 1 | 253 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run2/transcript.jsonl) | Incomplete; only CLI/state scaffolded. Wrote "so the simulator can later execute G-code blocks" — execution never implemented. |
| 3 | 166/542 (30.6%) | 13.0 min | 4.7M | 89K | ~$0.36 | 38 | 1 | 1089 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run3/transcript.jsonl) | Claims complete; implemented full CLI, expression evaluator, tokenizer, and trace recorder. |

## py

### codex-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| gpt-5.1-codex-mini | - | 179/542 (33.0%) | 16.5% | 3/3 | Complete; run 2 scaffolded only, run 3 had syntax errors |

#### gpt-5.1-codex-mini

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 179/542 (33.0%) | 13.1 min | 4.1M | 94K | ~$0.33 | 36 | 1 | 975 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run1/transcript.jsonl) | Claims complete; built full interpreter entry point with expression grammar, modal state, tool/parameter handling. |
| 2 | 15/542 (2.8%) | 5.5 min | 1.2M | 38K | ~$0.12 | 22 | 1 | 240 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run2/transcript.jsonl) | Incomplete; acknowledged "core interpreter is not built yet" — scaffolding only (CLI, readers, data model, stub `Simulator.run`). |
| 3 | 74/542 (13.6%) | 6.2 min | 1.5M | 44K | ~$0.14 | 28 | 1 | 664 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run3/transcript.jsonl) | Incomplete; opened with "Status Unknown" and acknowledged file "contains syntactic mistakes... will not run yet." |

## rs

No runs yet.
