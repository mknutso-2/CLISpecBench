# Official results for CNCSim eval versions 2.0.2, 2.1.0, and 2.1.1

v2.0.2 adds a shared one-shot prompt (`Evals/_shared/require-one-shot.md`) appended
to all agent prompts.

v2.1.0 adds the Rust reference implementation and the `cncsim-full-rs` / `cncsim-lite-rs`
task variants. The agent-facing `cpp` / `py` / `js` prompt SHAs are **identical** to v2.0.2;
the test-suite SHA changed only because `conftest.py` now supports `--language=rs` (no test
behaviors changed — still 542 tests). Runs from multiple versions appear together here because
the cpp/py/js agent contracts are comparable; `rs` runs are v2.1.0-only by construction.

v2.1.1 keeps the same agent-facing prompts but changes scoring/reporting and the CNCSim timeout
behavior. This file is copied forward from `results-2_0_2.md` and adds an explicit `Version`
column; no v2.1.1 rows are listed yet.

**Only runs where the agent completed successfully (`exit_reason: "completed"`)
appear in the tables.** Runs that errored, timed out, or were rate-limited are
excluded and noted as needing reruns. Completed runs with invalid scorer artifacts
are also excluded and called out inline. Best/Mean are computed only over the
listed runs.

Cost is `reported_cost_usd` from the agent CLI when available, otherwise
`estimated_cost_usd` computed by the harness (marked with ~). Copilot CLI does
not report input tokens or cost.

## C++

### claude-code

No v2.0.2 runs yet. See `results-2_0_1.md` for v2.0.1 results.

---

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.3-codex | xhigh | 2.1.0 | 265/542 (48.9%) | 48.3% | 2/3 | Run 1 scorer-timeout artifact (`0/0`) excluded |
| gpt-5.2-codex | xhigh | 2.0.2 | 419/542 (77.3%) | 58.0% | 3/3 | Complete |
| gpt-5.2 | high | 2.1.0 | 412/542 (76.0%) | 65.4% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 2.0.2 | 321/542 (59.2%) | 40.5% | 3/3 | Complete |
| gpt-5.1 | high | 2.1.0 | 278/542 (51.3%) | 31.7% | 3/3 | Complete |
| gpt-5 | high | 2.1.0 | 197/542 (36.3%) | 12.2% | 3/3 | Complete; runs 1+3 self-acknowledged incomplete (stub only) |
| gpt-5.1-codex-mini | - | 2.0.2 | 132/542 (24.4%) | 8.1% | 3/3 | Complete; run 1 refused task, run 3 build failed |

#### gpt-5.3-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 2.1.0 | 259/542 (47.8%) | 38.4 min | 4.9M | 122K | ~$2.81 | 54 | 3 | 4027 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run2/transcript.jsonl) | Claims complete. |
| 3 | 2.1.0 | 265/542 (48.9%) | 36.0 min | 8.2M | 82K | ~$3.12 | 50 | 3 | 4088 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run3/transcript.jsonl) | Claims complete; C++20 simulator in a three-file output tree. |

Excluded: eval2/run1 completed but the old scorer timed out before `report.json` was written, leaving an invalid `0/0` artifact; do not count it in Best/Mean.

#### gpt-5.2-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 266/542 (49.1%) | 130.2 min | 22.9M | 286K | ~$8.62 | 117 | 2 | 3255 | [result](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run1/transcript.jsonl) | Claims complete. |
| 2 | 2.0.2 | 419/542 (77.3%) | 64.2 min | 18.9M | 184K | ~$6.56 | 152 | 3 | 4332 | [result](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run2/transcript.jsonl) | Claims complete; noted corrections to G10/G92 motion suppression, cutter-comp arc position, and trace step validation. |
| 3 | 2.0.2 | 258/542 (47.6%) | 92.5 min | 35.3M | 226K | ~$10.65 | 178 | 3 | 3565 | [result](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2-codex_xhigh/eval3/run3/transcript.jsonl) | Claims complete. |

Prior eval (eval2): 1/3 completed (run 1: 420/542), run 2 timed out at 458/542, run 3 errored — rerun as eval3.

#### gpt-5.2 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 412/542 (76.0%) | 44.5 min | 11.8M | 128K | ~$4.07 | 47 | 17 | 3590 | [result](../../results/cncsim-full/codex-cli/gpt-5.2_high/eval2/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2_high/eval2/run1/transcript.jsonl) | Claims complete; C++20 RS274/NGC simulator with no third-party deps. |
| 2 | 2.1.0 | 393/542 (72.5%) | 45.5 min | 16.2M | 130K | ~$4.77 | 65 | 20 | 3746 | [result](../../results/cncsim-full/codex-cli/gpt-5.2_high/eval2/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2_high/eval2/run2/transcript.jsonl) | Claims complete; multi-file C++20 simulator with broader project structure. |
| 3 | 2.1.0 | 259/542 (47.8%) | 67.9 min | 31.1M | 162K | ~$8.31 | 178 | 18 | 3355 | [result](../../results/cncsim-full/codex-cli/gpt-5.2_high/eval2/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.2_high/eval2/run3/transcript.jsonl) | Claims complete. |

#### gpt-5.1-codex-max / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 203/542 (37.5%) | 16.1 min | 3.8M | 56K | ~$2.13 | 41 | 3 | 2225 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run1/transcript.jsonl) | Claims complete. |
| 2 | 2.0.2 | 321/542 (59.2%) | 21.0 min | 9.3M | 70K | ~$3.23 | 55 | 3 | 2122 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run2/transcript.jsonl) | Claims complete; noted simplifications in canned cycles and cutter-radius compensation. |
| 3 | 2.0.2 | 134/542 (24.7%) | 15.6 min | 4.3M | 54K | ~$2.02 | 48 | 3 | 988 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-max_xhigh/eval2/run3/transcript.jsonl) | Claims complete. |

Prior eval (eval1): all 3 runs failed with `no_output` in 5s (startup issue).

#### gpt-5.1 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 278/542 (51.3%) | 16.4 min | 6.6M | 87K | ~$1.94 | 52 | 2 | 2117 | [result](../../results/cncsim-full/codex-cli/gpt-5.1_high/eval1/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1_high/eval1/run1/transcript.jsonl) | Claims complete; full CLI with modal state, expressions, motion, probing, trace stepping in single `main.cpp`. |
| 2 | 2.1.0 | 41/542 (7.6%) | 12.8 min | 4.6M | 71K | ~$1.41 | 43 | 8 | 1431 | [result](../../results/cncsim-full/codex-cli/gpt-5.1_high/eval1/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1_high/eval1/run2/transcript.jsonl) | Claims complete despite low score; "syntactically correct RS274/NGC parser" but runtime behavior mostly broken (41/542). |
| 3 | 2.1.0 | 197/542 (36.3%) | 16.9 min | 4.3M | 92K | ~$1.50 | 48 | 7 | 2015 | [result](../../results/cncsim-full/codex-cli/gpt-5.1_high/eval1/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1_high/eval1/run3/transcript.jsonl) | Claims complete; modular parser/simulator split across multiple files. |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models.

#### gpt-5 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 1/542 (0.2%) | 12.1 min | 3.5M | 69K | ~$1.22 | 44 | 4 | 12 | [result](../../results/cncsim-full/codex-cli/gpt-5_high/eval1/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5_high/eval1/run1/transcript.jsonl) | Incomplete; acknowledged — agent gave up citing "hard technical limitation in the current execution environment: the terminal tool mangles quotes and backslashes in long multi-line file writes." Wrote stub only (12 LOC). |
| 2 | 2.1.0 | 197/542 (36.3%) | 8.7 min | 3.6M | 42K | ~$0.96 | 27 | 10 | 1282 | [result](../../results/cncsim-full/codex-cli/gpt-5_high/eval1/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5_high/eval1/run2/transcript.jsonl) | Claims complete; standalone RS274/NGC simulator in C++20. |
| 3 | 2.1.0 | 1/542 (0.2%) | 13.1 min | 2.6M | 88K | ~$1.30 | 30 | 3 | 9 | [result](../../results/cncsim-full/codex-cli/gpt-5_high/eval1/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5_high/eval1/run3/transcript.jsonl) | Incomplete; acknowledged — "stub doesn't yet execute or trace G‑code; it only compiles successfully." Listed 8 remaining work items. Asked "If you want, I'll proceed now." |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models.

#### gpt-5.1-codex-mini

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 0/542 (0.0%) | 1.1 min | 298K | 6K | ~$0.03 | 6 | 0 | 0 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run1/transcript.jsonl) | Incomplete; wrote no code. Declined the task as "far beyond what I can deliver in a single response." Asked user to "break the problem into narrower slices." |
| 2 | 2.0.2 | 132/542 (24.4%) | 12.5 min | 5.6M | 88K | ~$0.41 | 34 | 3 | 1735 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run2/transcript.jsonl) | Claims complete. |
| 3 | 2.0.2 | 0/542 (0.0%) | 6.2 min | 2.1M | 40K | ~$0.19 | 35 | 2 | 428 | [result](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.1-codex-mini/eval1/run3/transcript.jsonl) | Incomplete; build failed. Acknowledged incomplete — listed 3 "Remaining work" items and noted "build and runtime logic are still pending." Spent 69% of tool calls reading the spec; only wrote an expression parser (no main, no simulation). |

---

### gemini-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 2.0.2 | 238/542 (43.9%) | 37.9% | 3/3 | Complete |
| gemini-2.5-flash | - | 2.0.2 | 18/542 (3.3%) | 1.1% | 3/3 | Complete; runs 1-2 build failures, run 3 built |
| gemini-2.5-flash-lite | - | 2.0.2 | 0/542 (0.0%) | 0.0% | 3/3 | Complete; all builds failed |

#### gemini-3-flash-preview

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 196/542 (36.2%) | 4.8 min | 2.3M | 37K | ~$0.45 | 33 | 10 | 2483 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run1/transcript.jsonl) | Claims complete. |
| 2 | 2.0.2 | 182/542 (33.6%) | 7.4 min | 4.9M | 50K | ~$0.67 | 47 | 10 | 916 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run2/transcript.jsonl) | Claims complete. |
| 3 | 2.0.2 | 238/542 (43.9%) | 13.3 min | 10.9M | 81K | ~$1.25 | 83 | 14 | 1043 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval2/run3/transcript.jsonl) | Claims complete. |

#### gemini-2.5-flash

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 0/542 (0.0%) | 14.6 min | 5.6M | 86K | ~$0.92 | 54 | 2 | 509 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run1/transcript.jsonl) | Incomplete; build failed. Acknowledged limitations and stopped. |
| 2 | 2.0.2 | 0/542 (0.0%) | 33.2 min | 17.6M | 68K | ~$2.71 | 116 | 9 | 1762 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run2/transcript.jsonl) | Incomplete; build failed. Claimed blocked by persistent string literal compilation errors. |
| 3 | 2.0.2 | 18/542 (3.3%) | 10.0 min | 8.6M | 35K | ~$0.44 | 89 | 3 | 1168 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash/eval2/run3/transcript.jsonl) | Incomplete; was still iterating when session ended. Built successfully. |

#### gemini-2.5-flash-lite

All 3 runs scored 0/542. Model capability issues: missing tool parameters, hallucinated
filenames, builds that don't compile. See transcript investigation in prior session notes.

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 0/542 (0.0%) | 1.3 min | 258K | 17K | ~$0.02 | 2 | 0 | 0 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run1/transcript.jsonl) | Incomplete; wrote no code. Laid out a plan but stopped after reading the spec. |
| 2 | 2.0.2 | 0/542 (0.0%) | 11.1 min | 6.4M | 110K | ~$0.27 | 48 | 16 | 2121 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run2/transcript.jsonl) | Incomplete; build failed. Encountered repeated `write_file` tool errors (missing `file_path` parameter). |
| 3 | 2.0.2 | 0/542 (0.0%) | 1.9 min | 888K | 12K | ~$0.02 | 10 | 2 | 399 | [result](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-2.5-flash-lite/eval2/run3/transcript.jsonl) | Incomplete; scaffolded only. Set up project structure but wrote no implementation logic. |

---

### copilot-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| claude-haiku-4.5 | - | 2.0.2 | 90/542 (16.6%) | 14.2% | 3/3 | Complete (across eval1+eval2); eval2 run 3 rate limited |
| gpt-4.1 | - | 2.0.2 | 20/542 (3.7%) | 1.4% | 3/3 | Complete |
| gpt-5-mini | high | 2.0.2 | 145/542 (26.8%) | 24.1% | 3/3 | Complete |

#### claude-haiku-4.5

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| eval1/1 | 2.0.2 | 90/542 (16.6%) | 7.8 min | 0 | 49K | - | 0 | 3 | 1276 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval1/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval1/run1/transcript.jsonl) | Claims complete. |
| eval2/1 | 2.0.2 | 55/542 (10.1%) | 8.8 min | 0 | 41K | - | 0 | 3 | 1328 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run1/transcript.jsonl) | Claims complete. |
| eval2/2 | 2.0.2 | 86/542 (15.9%) | 13.1 min | 0 | 58K | - | 0 | 10 | 1996 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval2/run2/transcript.jsonl) | Claims complete. |

Excluded: eval1 runs 2-3 (error + rate limited), eval2 run 3 (rate limited mid-execution at 75/542, 3231 LOC).

#### gpt-4.1

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 1/542 (0.2%) | 3.3 min | 0 | 9K | - | 0 | 18 | 350 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run1/transcript.jsonl) | Incomplete; scaffolded only. Acknowledged "core logic... will be implemented" next. |
| 2 | 2.0.2 | 20/542 (3.7%) | 3.9 min | 0 | 10K | - | 0 | 18 | 506 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run2/transcript.jsonl) | Incomplete; scaffolded only. Asked "Let me know if you want to proceed with the execution engine." |
| 3 | 2.0.2 | 1/542 (0.2%) | 5.2 min | 0 | 14K | - | 0 | 2 | 207 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run3/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run3/transcript.jsonl) | Incomplete; scaffolded only. Asked "Let me know if you want to proceed with a specific part." |

#### gpt-5-mini / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 145/542 (26.8%) | 11.7 min | 0 | 43K | - | 0 | 2 | 709 | [result](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run1/transcript.jsonl) | Claims complete. |
| 2 | 2.0.2 | 113/542 (20.8%) | 8.7 min | 0 | 36K | - | 0 | 3 | 1527 | [result](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run2/transcript.jsonl) | Claims complete. |
| 3 | 2.0.2 | 134/542 (24.7%) | 8.3 min | 0 | 31K | - | 0 | 4 | 2335 | [result](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run3/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-5-mini_high/eval3/run3/transcript.jsonl) | Claims complete. |

Prior eval (eval1): all 3 runs rate limited (free-tier quota exhaustion). These results are from eval3 after cooldown.

---

## js

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.3-codex | xhigh | 2.1.0 | 442/542 (81.5%) | 80.3% | 3/3 | Complete |
| gpt-5.2-codex | xhigh | 2.1.0 | 268/542 (49.4%) | 48.6% | 3/3 | Complete; runs 72-91 min each |
| gpt-5.2 | high | 2.1.0 | 257/542 (47.4%) | 31.4% | 3/3 | Complete; run 2 context-exhausted after partial implementation |
| gpt-5.1-codex-max | xhigh | 2.0.2 | 263/542 (48.5%) | 43.6% | 3/3 | Complete |
| gpt-5.1 | high | 2.1.0 | 218/542 (40.2%) | 38.3% | 3/3 | Complete |
| gpt-5 | high | 2.1.0 | 249/542 (45.9%) | 15.3% | 3/3 | Complete; runs 2+3 wrote zero files (self-reported terminal quoting issues) |
| gpt-5.1-codex-mini | - | 2.0.2 | 166/542 (30.6%) | 11.4% | 3/3 | Complete; runs 1-2 scaffolded only |

#### gpt-5.3-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 442/542 (81.5%) | 30.0 min | 19.5M | 85K | ~$4.85 | 88 | 5 | 2614 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete; full CLI scaffold with RS274 parsing, state execution, and trace generation. |
| 2 | 2.1.0 | 433/542 (79.9%) | 29.3 min | 8.5M | 71K | ~$2.70 | 73 | 7 | 2651 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; Node.js 22+ simulator with a multi-file output tree. |
| 3 | 2.1.0 | 431/542 (79.5%) | 33.5 min | 11.3M | 86K | ~$3.42 | 71 | 1 | 2637 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; single-file Node.js CLI simulator. |

#### gpt-5.2-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 268/542 (49.4%) | 91.1 min | 28.9M | 261K | ~$9.20 | 204 | 1 | 2132 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.2-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.2-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete; full RS274/NGC interpreter with motion, trace, parameter/tool I/O; noted parse/exec edge-case hardening (line numbers, M-code limit, G53 rules, arc R unit conversion). |
| 2 | 2.1.0 | 264/542 (48.7%) | 85.1 min | 28.0M | 247K | ~$8.74 | 194 | 1 | 2566 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.2-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.2-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; reworked modal motion + post-motion spindle for canned cycles (G84/G86/G87/G88); G38.2 feed validation; cutter-comp radius unit scaling. |
| 3 | 2.1.0 | 258/542 (47.6%) | 72.0 min | 18.4M | 198K | ~$6.74 | 111 | 9 | 2211 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.2-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.2-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; multi-file RS274/NGC parser/executor with runtime expression eval, motion (G0/G1/G2/G3/G38.2, canned cycles), tool/parameter I/O. |

#### gpt-5.2 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 254/542 (46.9%) | 44.2 min | 10.2M | 133K | ~$3.98 | 52 | 9 | 2772 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.2_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.2_high/eval1/run1/transcript.jsonl) | Claims complete; Node.js 22+ simulator driven by the RS274 docs. |
| 2 | 2.1.0 | 0/542 (0.0%) | 69.0 min | ? | ? | - | ? | 11 | 2530 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.2_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.2_high/eval1/run2/transcript.jsonl) | Incomplete; context window exhausted after partial implementation work. |
| 3 | 2.1.0 | 257/542 (47.4%) | 39.2 min | 12.6M | 112K | ~$4.18 | 64 | 10 | 2300 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.2_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.2_high/eval1/run3/transcript.jsonl) | Claims complete; dependency-free Node.js CLI with optional motion trace sampling. |

#### gpt-5.1-codex-max / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 263/542 (48.5%) | 17.2 min | 5.2M | 60K | ~$1.98 | 43 | 1 | 1437 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run1/transcript.jsonl) | Claims complete; covers G0-G3, G38.2 probing, G10, G28/G30, G92, basic canned cycles G81/G82, trace stepping. |
| 2 | 2.0.2 | 253/542 (46.7%) | 17.1 min | 5.0M | 60K | ~$1.81 | 53 | 1 | 1525 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run2/transcript.jsonl) | Claims complete; full RS274/NGC simulator including cycles, arcs, probing, G92, G10, G28/30, trace stepping modes. |
| 3 | 2.0.2 | 193/542 (35.6%) | 12.9 min | 3.3M | 44K | ~$1.69 | 50 | 1 | 1566 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run3/transcript.jsonl) | Claims complete; noted simplifications — cutter radius comp path geometry not implemented; rotary motion in arcs not modeled. |

#### gpt-5.1 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 203/542 (37.5%) | 16.5 min | 5.8M | 97K | ~$1.81 | 52 | 7 | 1658 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1_high/eval1/run1/transcript.jsonl) | Claims complete; modular multi-file Node.js implementation; acknowledged "important limitations" inline. |
| 2 | 2.1.0 | 218/542 (40.2%) | 15.5 min | 8.2M | 91K | ~$2.07 | 53 | 7 | 2701 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1_high/eval1/run2/transcript.jsonl) | Claims complete; modular simulator with convenience `main.js` wrapper. |
| 3 | 2.1.0 | 201/542 (37.1%) | 16.5 min | 7.9M | 78K | ~$1.93 | 70 | 7 | 2817 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1_high/eval1/run3/transcript.jsonl) | Claims complete; seven-file modular Node.js simulator. |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models. eval_version=2.1.0 (prompt SHA identical to v2.0.2).

#### gpt-5 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 249/542 (45.9%) | 9.2 min | 4.7M | 48K | ~$1.17 | 48 | 1 | 1495 | [result](../../results/cncsim-full-js/codex-cli/gpt-5_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5_high/eval1/run1/transcript.jsonl) | Claims complete; self-contained Node.js 22+ simulator with no dependencies. |
| 2 | 2.1.0 | 0/542 (0.0%) | 5.8 min | 2.7M | 29K | ~$0.71 | 43 | 0 | 0 | [result](../../results/cncsim-full-js/codex-cli/gpt-5_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5_high/eval1/run2/transcript.jsonl) | Incomplete; wrote no code. Blamed "command-quoting issue while writing multi-line JS files via the terminal tool." Offered to retry with "base64 → decode" pipeline. |
| 3 | 2.1.0 | 0/542 (0.0%) | 10.4 min | 2.2M | 66K | ~$1.08 | 31 | 0 | 0 | [result](../../results/cncsim-full-js/codex-cli/gpt-5_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5_high/eval1/run3/transcript.jsonl) | Incomplete; wrote no code. Acknowledged "writing the Node.js source file(s) into output/ from this environment failed repeatedly due to quoting/truncation issues." |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models. eval_version=2.1.0 (prompt SHA identical to v2.0.2).

#### gpt-5.1-codex-mini

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 18/542 (3.3%) | 5.3 min | 1.5M | 33K | ~$0.15 | 26 | 1 | 532 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run1/transcript.jsonl) | Incomplete; acknowledged "interpreter and trace generation are still missing" and listed outstanding work. |
| 2 | 2.0.2 | 1/542 (0.2%) | 8.4 min | 1.8M | 55K | ~$0.17 | 29 | 1 | 253 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run2/transcript.jsonl) | Incomplete; only CLI/state scaffolded. Wrote "so the simulator can later execute G-code blocks" — execution never implemented. |
| 3 | 2.0.2 | 166/542 (30.6%) | 13.0 min | 4.7M | 89K | ~$0.36 | 38 | 1 | 1089 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.1-codex-mini/eval1/run3/transcript.jsonl) | Claims complete; implemented full CLI, expression evaluator, tokenizer, and trace recorder. |

## py

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.2-codex | xhigh | 2.1.0 | 461/542 (85.1%) | 82.8% | 3/3 | Complete; runs 82-91 min each |
| gpt-5.2 | high | 2.1.0 | 448/542 (82.7%) | 69.1% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 2.0.2 | 339/542 (62.5%) | 57.6% | 3/3 | Complete |
| gpt-5 | high | 2.1.0 | 335/542 (61.8%) | 21.5% | 3/3 | Complete; runs 1+3 self-acknowledged incomplete (stubs) |
| gpt-5.1 | high | 2.1.0 | 205/542 (37.8%) | 25.0% | 3/3 | Complete; run 2 self-acknowledged partial coverage |
| gpt-5.1-codex-mini | - | 2.0.2 | 179/542 (33.0%) | 16.5% | 3/3 | Complete; run 2 scaffolded only, run 3 had syntax errors |

#### gpt-5.2-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 450/542 (83.0%) | 84.5 min | 23.7M | 228K | ~$8.43 | 153 | 1 | 2610 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.2-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.2-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete; full RS274/NGC simulator in single `main.py` with parsing, modal state, motion, canned cycles, probing, tool/param I/O, and trace stepping. |
| 2 | 2.1.0 | 461/542 (85.1%) | 91.1 min | 29.2M | 229K | ~$8.97 | 184 | 1 | 2388 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.2-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.2-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; noted percent-delimited files, optional carousel slots, G93 inverse-time feed, probe box/tool rules, unit scaling for length state, per-submotion error indices, spindle state transitions in canned cycles. |
| 3 | 2.1.0 | 436/542 (80.4%) | 81.6 min | 16.2M | 244K | ~$6.99 | 103 | 8 | 2250 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.2-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.2-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; multi-file Python implementation with state model, trace engine, tool/parameter file handling, canned cycles. |

#### gpt-5.2 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 244/542 (45.0%) | 35.7 min | 11.2M | 102K | ~$3.49 | 63 | 11 | 2661 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.2_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.2_high/eval1/run1/transcript.jsonl) | Claims complete; stdlib-only Python 3.11+ simulator. |
| 2 | 2.1.0 | 432/542 (79.7%) | 46.8 min | 12.9M | 133K | ~$4.48 | 63 | 13 | 2889 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.2_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.2_high/eval1/run2/transcript.jsonl) | Claims complete; stdlib-only Python simulator with `output/main.py` entrypoint. |
| 3 | 2.1.0 | 448/542 (82.7%) | 58.4 min | 17.6M | 157K | ~$5.67 | 74 | 11 | 2822 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.2_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.2_high/eval1/run3/transcript.jsonl) | Claims complete; stdlib-only RS274/NGC simulator CLI. |

#### gpt-5.1-codex-max / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 284/542 (52.4%) | 12.3 min | 3.3M | 42K | ~$1.35 | 51 | 1 | 1504 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run1/transcript.jsonl) | Claims complete. |
| 2 | 2.0.2 | 339/542 (62.5%) | 28.7 min | 10.5M | 99K | ~$3.68 | 82 | 1 | 1894 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run2/transcript.jsonl) | Claims complete. |
| 3 | 2.0.2 | 314/542 (57.9%) | 19.2 min | 5.4M | 68K | ~$2.03 | 46 | 1 | 1723 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run3/transcript.jsonl) | Claims complete. |

#### gpt-5 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 4/542 (0.7%) | 11.2 min | 3.2M | 77K | ~$1.28 | 45 | 1 | 133 | [result](../../results/cncsim-full-py/codex-cli/gpt-5_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5_high/eval1/run1/transcript.jsonl) | Incomplete; acknowledged — "didn't finish implementing the full RS274 execution engine... interpreter and motion engine are not fully implemented." Wrote CLI shell only (133 LOC). |
| 2 | 2.1.0 | 335/542 (61.8%) | 16.3 min | 6.5M | 77K | ~$1.81 | 56 | 1 | 1783 | [result](../../results/cncsim-full-py/codex-cli/gpt-5_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5_high/eval1/run2/transcript.jsonl) | Claims complete; self-contained pure-Python RS274/NGC simulator. |
| 3 | 2.1.0 | 10/542 (1.8%) | 10.0 min | 4.7M | 57K | ~$1.24 | 41 | 2 | 648 | [result](../../results/cncsim-full-py/codex-cli/gpt-5_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5_high/eval1/run3/transcript.jsonl) | Claims complete but failed 532/542; built CLI with partial motion/canned-cycle coverage that runtime-broke on most programs. |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models. eval_version=2.1.0 (prompt SHA identical to v2.0.2).

#### gpt-5.1 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 205/542 (37.8%) | 11.3 min | 3.4M | 69K | ~$1.20 | 40 | 1 | 1557 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1_high/eval1/run1/transcript.jsonl) | Claims complete; stdlib-only standalone simulator with required CLI. |
| 2 | 2.1.0 | 4/542 (0.7%) | 12.3 min | 4.6M | 63K | ~$1.31 | 57 | 2 | 1155 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1_high/eval1/run2/transcript.jsonl) | Incomplete; acknowledged — "currently supports only a subset of the full specification." Wrote simulator that runs but fails 538/542. |
| 3 | 2.1.0 | 198/542 (36.5%) | 13.8 min | 5.9M | 78K | ~$1.61 | 44 | 9 | 1938 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1_high/eval1/run3/transcript.jsonl) | Claims complete; multi-file stdlib-only Python implementation. |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models. eval_version=2.1.0 (prompt SHA identical to v2.0.2).

#### gpt-5.1-codex-mini

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.0.2 | 179/542 (33.0%) | 13.1 min | 4.1M | 94K | ~$0.33 | 36 | 1 | 975 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run1/transcript.jsonl) | Claims complete; built full interpreter entry point with expression grammar, modal state, tool/parameter handling. |
| 2 | 2.0.2 | 15/542 (2.8%) | 5.5 min | 1.2M | 38K | ~$0.12 | 22 | 1 | 240 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run2/transcript.jsonl) | Incomplete; acknowledged "core interpreter is not built yet" — scaffolding only (CLI, readers, data model, stub `Simulator.run`). |
| 3 | 2.0.2 | 74/542 (13.6%) | 6.2 min | 1.5M | 44K | ~$0.14 | 28 | 1 | 664 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.1-codex-mini/eval1/run3/transcript.jsonl) | Incomplete; opened with "Status Unknown" and acknowledged file "contains syntactic mistakes... will not run yet." |

---

### copilot-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| claude-haiku-4.5 | - | 2.1.0 | 212/542 (39.1%) | 39.1% | 1/6 | Complete; 5 of 6 runs rate-limited (Free-tier per-period quota) |

#### claude-haiku-4.5

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| eval2/1 | 2.1.0 | 212/542 (39.1%) | 11.8 min | 5.6M | 66K | - | 0 | 6 | 1835 | [result](../../results/cncsim-full-py/copilot-cli/claude-haiku-4.5/eval2/run1/result.json) [transcript](../../results/cncsim-full-py/copilot-cli/claude-haiku-4.5/eval2/run1/transcript.jsonl) | Claims complete. |

Excluded: eval1 runs 1-3 (all rate-limited — run 1 partial with 109/542 before quota hit); eval2/2 (rate_limit mid-execution at 142/542), eval2/3 (rate_limit on first request). Single clean run in eval2/1 exhausted the per-period Free-tier quota for subsequent runs.

## rs

All Rust runs are eval_version=2.1.0 (Rust ref impl and `cncsim-full-rs` variant were added in v2.1.0).

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.2-codex | xhigh | 2.1.0 | 438/542 (80.8%) | 56.6% | 3/3 | Complete; run 2 best; runs 1+3 spent 60-92 min each |
| gpt-5.2 | high | 2.1.0 | 268/542 (49.4%) | 49.0% | 3/3 | Complete |
| gpt-5.1 | high | 2.1.0 | 302/542 (55.7%) | 40.2% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 2.1.0 | 299/542 (55.2%) | 39.6% | 3/3 | Complete; run 3 took 86 min after "rebuild from scratch" |
| gpt-5.1-codex-mini | high | 2.1.0 | 4/542 (0.7%) | 0.5% | 3/3 | Complete; all 3 runs scaffolded/stubbed — model gave up on Rust implementation |
| gpt-5 | high | 2.1.0 | 4/542 (0.7%) | 0.2% | 3/3 | Complete; runs 1+3 self-acknowledged quote-mangling failures (0 or stub output) |

#### gpt-5.2-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 260/542 (48.0%) | 64.8 min | 13.4M | 192K | ~$5.52 | 104 | 1 | 2690 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.2-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.2-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete; full CLI with RS274 modal handling, motion, probing, parameter/tool-table I/O. |
| 2 | 2.1.0 | 438/542 (80.8%) | 78.3 min | 18.4M | 202K | ~$6.62 | 112 | 1 | 2929 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.2-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.2-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; noted RS274 alignment — G53 axis-word enforcement, coord-system-under-CRC blocking, G38.2 probe constraints, G87 XY-plane requirement, per-submotion error-segment indexing for G28/G30. |
| 3 | 2.1.0 | 223/542 (41.1%) | 92.1 min | 25.4M | 262K | ~$8.83 | 138 | 1 | 3509 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.2-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.2-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; standalone Rust std-only Cargo project with full CLI, parsing, motion (G0/G1/G2/G3), probing, G28/G30, G10/G92, canned cycles (G81–G89). |

#### gpt-5.2 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 268/542 (49.4%) | 104.4 min | 40.7M | 285K | ~$11.92 | 255 | 10 | 6040 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.2_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.2_high/eval1/run1/transcript.jsonl) | Claims complete; dependency-free Cargo project with stable Rust 2021 tooling. |
| 2 | 2.1.0 | 262/542 (48.3%) | 72.8 min | 22.7M | 199K | ~$7.30 | 138 | 9 | 4480 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.2_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.2_high/eval1/run2/transcript.jsonl) | Claims complete; dependency-free Rust simulator. |
| 3 | 2.1.0 | 266/542 (49.1%) | 72.7 min | 20.7M | 211K | ~$7.16 | 112 | 8 | 5169 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.2_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.2_high/eval1/run3/transcript.jsonl) | Claims complete; dependency-free Rust RS274/NGC simulator. |

#### gpt-5.1 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 165/542 (30.4%) | 12.4 min | 4.3M | 76K | ~$1.37 | 38 | 1 | 1969 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1_high/eval1/run1/transcript.jsonl) | Claims complete; std-only Cargo project, single-file `main.rs`. |
| 2 | 2.1.0 | 302/542 (55.7%) | 20.6 min | 14.5M | 106K | ~$3.01 | 72 | 1 | 2838 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1_high/eval1/run2/transcript.jsonl) | Claims complete; single-file Cargo project building with `cargo build --release`. |
| 3 | 2.1.0 | 186/542 (34.3%) | 13.2 min | 4.5M | 90K | ~$1.53 | 29 | 5 | 2140 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1_high/eval1/run3/transcript.jsonl) | Claims complete; multi-file Cargo project with module layout. |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models.

#### gpt-5.1-codex-max / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 165/542 (30.4%) | 19.5 min | 4.0M | 71K | ~$1.95 | 49 | 1 | 364 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run1/transcript.jsonl) | Claims complete but acknowledged limitations — "Arcs, canned cycles, probing, cutter compensation, tool tables, and most non-modal" features not implemented. Minimal 364-LOC scaffold. |
| 2 | 2.1.0 | 299/542 (55.2%) | 12.2 min | 3.0M | 45K | ~$1.21 | 37 | 1 | 1705 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run2/transcript.jsonl) | Claims complete; standalone std-only RS274/NGC simulator. |
| 3 | 2.1.0 | 180/542 (33.2%) | 86.2 min | 7.4M | 114K | ~$3.23 | 73 | 1 | 2776 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-max_xhigh/eval1/run3/transcript.jsonl) | Claims complete after "I had to rebuild the entire simulator from scratch" — compiled single-file output with full modal/coord/unit/expression coverage but scored lower than faster run 2. |

#### gpt-5.1-codex-mini / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 4/542 (0.7%) | 16.6 min | ? | ? | - | ? | 1 | 77 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run1/transcript.jsonl) | Incomplete; no implementation — "Progress so far: None yet; the filesystem hasn't been inspected, and no implementation work has started." Left 77-LOC placeholder. |
| 2 | 2.1.0 | 1/542 (0.2%) | 7.2 min | 2.3M | 46K | ~$0.18 | 35 | 1 | 3 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run2/transcript.jsonl) | Incomplete; acknowledged — "implementing that full specification would take far more time than this session allows, so I left output/src/main.rs as a placeholder that simply reports the simulator is not implemented." |
| 3 | 2.1.0 | 3/542 (0.6%) | 7.2 min | 1.7M | 54K | ~$0.16 | 26 | 1 | 403 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run3/transcript.jsonl) | Incomplete; CLI skeleton and "foundational runtime plumbing" only — interpreter, motion, and trace not implemented. |

Note: run 1 token usage failed to parse (`'str' object has no attribute 'get'` in `codex_cli.py`), so input/output/tool-call counts are unavailable for that run. Runs 2+3 parsed cleanly.

#### gpt-5 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 0/542 (0.0%) | 9.9 min | 4.1M | 59K | ~$1.21 | 55 | 0 | 0 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run1/transcript.jsonl) | Incomplete; wrote no code. Blamed "CLI's shell-quoting mangles embedded quotes and braces in long here-documents." Presented design plan only. |
| 2 | 2.1.0 | 4/542 (0.7%) | 11.1 min | 4.0M | 58K | ~$1.18 | 37 | 1 | 1491 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run2/transcript.jsonl) | Claims complete; std-only Cargo project — but 538/542 tests failed. |
| 3 | 2.1.0 | 0/542 (0.0%) | 10.6 min | 1.9M | 57K | ~$0.89 | 29 | 1 | 396 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run3/transcript.jsonl) | Incomplete; acknowledged — "wasn't able to create files in output/ because the terminal is mangling multi-line writes." Wrote design doc in response only (396 LOC is partial stub). |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models.
