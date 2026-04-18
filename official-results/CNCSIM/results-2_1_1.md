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
column. v2.1.1 rows appear under py and rs for the newer codex-cli models (gpt-5.3-codex,
gpt-5.4, gpt-5.4-mini).

**Inclusion rule.** A run is *included* in the per-run detail table and
in Best/Mean when it either completed normally or failed on its own
accord — i.e. the failure mode tells us something about the agent.
Agent-self-inflicted zero-score runs (`context_exhausted`, `agent_error`,
`build_failure`, `no_code_written`) count as 0 and are annotated so a
reader sees what happened. A run is *excluded* (and flagged as needing
a rerun) only when it hit a harness- or environment-level failure
unrelated to the agent: Docker/daemon issues, auth failures, scorer
container glitches (e.g. pytest exit 4 with missing `report.json`),
rate limits imposed on the harness, or completed runs with invalid
`0/0` scorer artifacts.

Cost is `reported_cost_usd` from the agent CLI when available, otherwise
`estimated_cost_usd` computed by the harness (marked with ~). Copilot CLI does
not report input tokens or cost.

## C++

### claude-code

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| claude-sonnet-4-6 | high | 2.1.1 | 375/542 (69.2%) | 38.9% | 3/3 | Complete; wide single-prompt variance (375/191/67) |

#### claude-sonnet-4-6 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 375/542 (69.2%) | 65.6 min | 10.9M | 155K | $11.50 | 268 | 9 | 4392 | [result](../../results/cncsim-full/claude-code/claude-sonnet-4-6_high/eval2/run1/result.json) [transcript](../../results/cncsim-full/claude-code/claude-sonnet-4-6_high/eval2/run1/transcript.jsonl) | Claims complete; multi-file C++20 tree with `CMakeLists.txt` + simulator/parser/executor split; session-end summary of G28/G30 + nonmodal-G fixes. |
| 2 | 2.1.1 | 191/542 (35.2%) | 39.8 min | 6.7M | 156K | $5.41 | 95 | 12 | 3665 | [result](../../results/cncsim-full/claude-code/claude-sonnet-4-6_high/eval2/run2/result.json) [transcript](../../results/cncsim-full/claude-code/claude-sonnet-4-6_high/eval2/run2/transcript.jsonl) | Claims complete; 12-file `output/` with a clean CMake build. |
| 3 | 2.1.1 | 67/542 (12.4%) | 60.3 min | 3.2M | 221K | $5.27 | 46 | 10 | 3303 | [result](../../results/cncsim-full/claude-code/claude-sonnet-4-6_high/eval2/run3/result.json) [transcript](../../results/cncsim-full/claude-code/claude-sonnet-4-6_high/eval2/run3/transcript.jsonl) | Builds cleanly; claims complete but fails a single spec-interpretation point that cascades. Spec requires `error` always present (null on success); agent wrote `if (!res.error.empty()) { jw.key("error"); ... }` — so the key is absent on success and 259 of 475 failures are `KeyError: 'error'` (~55% of all fails). Same conditional-emit pattern costs another 4 failures on `error_line_number` / `error_block_segment_index`. |

Runs 1-3 executed under the old `cncsim-full` task id (before the 2026-04-17 rename to `cncsim-cpp`); content hashes are identical.

---

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.4 | xhigh | 2.1.1 | 423/542 (78.0%) | 57.5% | 3/3 | Complete (eval7); earlier evals 1-4 superseded by harness/timeout changes |
| gpt-5.4-mini | xhigh | 2.1.1 | 248/542 (45.8%) | 27.9% | 3/3 | Complete (eval4); run 3 context-exhausted mid-scaffold (0/542) |
| gpt-5.3-codex | xhigh | 2.1.0 | 265/542 (48.9%) | 48.3% | 2/3 | Run 1 scorer-timeout artifact (`0/0`) excluded |
| gpt-5.3-codex-spark | xhigh | 2.1.1 | 0/542 (0.0%) | 0.0% | 3/3 | Complete; all 3 runs context-exhausted before any file written |
| gpt-5.2-codex | xhigh | 2.0.2 | 419/542 (77.3%) | 58.0% | 3/3 | Complete |
| gpt-5.2 | high | 2.1.0 | 412/542 (76.0%) | 65.4% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 2.0.2 | 321/542 (59.2%) | 40.5% | 3/3 | Complete |
| gpt-5.1 | high | 2.1.0 | 278/542 (51.3%) | 31.7% | 3/3 | Complete |
| gpt-5 | high | 2.1.0 | 197/542 (36.3%) | 12.2% | 3/3 | Complete; runs 1+3 self-acknowledged incomplete (stub only) |
| gpt-5.1-codex-mini | - | 2.0.2 | 132/542 (24.4%) | 8.1% | 3/3 | Complete; run 1 refused task, run 3 build failed |

#### gpt-5.4 / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 423/542 (78.0%) | 52.9 min | 8.7M | 155K | ~$5.39 | 82 | 9 | 4276 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval7/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval7/run1/transcript.jsonl) | Claims complete; multi-file C++20 project under `output/` with `CMakeLists.txt` + `simulator.cpp`. |
| 2 | 2.1.1 | 249/542 (45.9%) | 36.1 min | 14.7M | 97K | ~$5.87 | 83 | 2 | 3068 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval7/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval7/run2/transcript.jsonl) | Claims complete; single-file `main.cpp` + `CMakeLists.txt`. |
| 3 | 2.1.1 | 263/542 (48.5%) | 56.6 min | 13.6M | 111K | ~$6.20 | 66 | 4 | 3811 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval7/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval7/run3/transcript.jsonl) | Claims complete; `output/main.cpp` + `output/simulator.cpp` + `output/CMakeLists.txt`. |

Prior evals: eval1 all 3 runs hit the old 30-min wall cap (pre-v2.1.1); eval2 runs 1-3 `no_output`; eval3 only run 1 completed; eval4 was a 3/3 completed set (380/262/262) but superseded by eval7; eval5-6 startup errors.

#### gpt-5.4-mini / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 205/542 (37.8%) | 80.7 min | 26.7M | 400K | ~$4.40 | 238 | 5 | 2734 | [result](../../results/cncsim-full/codex-cli/gpt-5.4-mini_xhigh/eval4/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4-mini_xhigh/eval4/run1/transcript.jsonl) | Claims complete; C++20 project built with `cmake -B build && cmake --build build`. |
| 2 | 2.1.1 | 248/542 (45.8%) | 105.3 min | 38.2M | 690K | ~$7.23 | 416 | 3 | 4219 | [result](../../results/cncsim-full/codex-cli/gpt-5.4-mini_xhigh/eval4/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4-mini_xhigh/eval4/run2/transcript.jsonl) | Claims complete; 105-min run with 38M input tokens. |
| 3 | 2.1.1 | 0/542 (0.0%) | 35.2 min | ? | ? | - | ? | 3 | 234 | [result](../../results/cncsim-full/codex-cli/gpt-5.4-mini_xhigh/eval4/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4-mini_xhigh/eval4/run3/transcript.jsonl) | Incomplete; context-exhausted while still "fixing the scaffold before the real implementation lands." 3 scaffold files / 234 LOC, no working implementation. |

Run 3 token usage unavailable: context-exhausted during remote compact. Prior evals: eval1 all 3 runs scored 0/542 (two `completed`, one `timeout` on the 30-min cap); eval2-3 startup errors.

#### gpt-5.3-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 2.1.0 | 259/542 (47.8%) | 38.4 min | 4.9M | 122K | ~$2.81 | 54 | 3 | 4027 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run2/transcript.jsonl) | Claims complete. |
| 3 | 2.1.0 | 265/542 (48.9%) | 36.0 min | 8.2M | 82K | ~$3.12 | 50 | 3 | 4088 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex_xhigh/eval2/run3/transcript.jsonl) | Claims complete; C++20 simulator in a three-file output tree. |

Excluded: eval2/run1 completed but the old scorer timed out before `report.json` was written, leaving an invalid `0/0` artifact; do not count it in Best/Mean.

#### gpt-5.3-codex-spark / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 0/542 (0.0%) | 3.6 min | ? | ? | - | 17 | 0 | 0 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/transcript.jsonl) | Incomplete; context-exhausted right after planning. Said "I'm now implementing the simulator in `output/`..." and ran `mkdir -p output`, then the next remote-compact call exceeded the model's context window. 0 files written. |
| 2 | 2.1.1 | 0/542 (0.0%) | 1.6 min | ? | ? | - | 29 | 0 | 0 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/transcript.jsonl) | Incomplete; context-exhausted while still reading the spec ("I'll read that part next..."). Compaction call exceeded the context window. 0 files written. |
| 3 | 2.1.1 | 0/542 (0.0%) | 5.2 min | ? | ? | - | 15 | 0 | 0 | [result](../../results/cncsim-full/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/transcript.jsonl) | Incomplete; context-exhausted mid-research ("Next I'm reading the canonical-motion and cycle sections..."). 0 files written. |

All 3 runs ended in `context_exhausted` before any code was written, so token usage / cost are unavailable. The model's context window is too small to hold the CNCSim prompt + a few research turns.

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

### claude-code

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| claude-sonnet-4-6 | high | 2.1.1 | 430/542 (79.3%) | 65.3% | 3/3 | Complete |

#### claude-sonnet-4-6 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 430/542 (79.3%) | 38.6 min | 5.3M | 144K | $5.02 | 94 | 6 | 3427 | [result](../../results/cncsim-js/claude-code/claude-sonnet-4-6_high/eval1/run1/result.json) [transcript](../../results/cncsim-js/claude-code/claude-sonnet-4-6_high/eval1/run1/transcript.jsonl) | Claims complete; Node.js simulator split across 6 files; end-of-session bug-fix note (`hasG80` variable). |
| 2 | 2.1.1 | 406/542 (74.9%) | 53.0 min | 5.9M | 212K | $6.34 | 73 | 6 | 2050 | [result](../../results/cncsim-js/claude-code/claude-sonnet-4-6_high/eval1/run2/result.json) [transcript](../../results/cncsim-js/claude-code/claude-sonnet-4-6_high/eval1/run2/transcript.jsonl) | Claims complete; 6-file output tree with block parser, tool/param file handling. |
| 3 | 2.1.1 | 226/542 (41.7%) | 65.2 min | 7.4M | 203K | $8.47 | 115 | 6 | 3770 | [result](../../results/cncsim-js/claude-code/claude-sonnet-4-6_high/eval1/run3/result.json) [transcript](../../results/cncsim-js/claude-code/claude-sonnet-4-6_high/eval1/run3/transcript.jsonl) | Claims complete; 6-file CLI simulator with full file table in the final report. |

---

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.4 | xhigh | 2.1.1 | 445/542 (82.1%) | 69.1% | 3/3 | Complete |
| gpt-5.3-codex | xhigh | 2.1.0 | 442/542 (81.5%) | 80.3% | 3/3 | Complete |
| gpt-5.3-codex-spark | xhigh | 2.1.1 | 0/542 (0.0%) | 0.0% | 3/3 | Complete; all 3 runs context-exhausted before any file written |
| gpt-5.4-mini | xhigh | 2.1.1 | 346/542 (63.8%) | 36.2% | 3/3 | Complete; runs 1-2 burned 90-130 min each, run 3 context-exhausted before writing code |
| gpt-5.2-codex | xhigh | 2.1.0 | 268/542 (49.4%) | 48.6% | 3/3 | Complete; runs 72-91 min each |
| gpt-5.2 | high | 2.1.0 | 257/542 (47.4%) | 31.4% | 3/3 | Complete; run 2 context-exhausted after partial implementation |
| gpt-5.1-codex-max | xhigh | 2.0.2 | 263/542 (48.5%) | 43.6% | 3/3 | Complete |
| gpt-5.1 | high | 2.1.0 | 218/542 (40.2%) | 38.3% | 3/3 | Complete |
| gpt-5 | high | 2.1.0 | 249/542 (45.9%) | 15.3% | 3/3 | Complete; runs 2+3 wrote zero files (self-reported terminal quoting issues) |
| gpt-5.1-codex-mini | - | 2.0.2 | 166/542 (30.6%) | 11.4% | 3/3 | Complete; runs 1-2 scaffolded only |

#### gpt-5.4 / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 255/542 (47.0%) | 63.8 min | 9.3M | 92K | ~$4.41 | 83 | 5 | 3107 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.4_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.4_xhigh/eval1/run1/transcript.jsonl) | Claims complete; multi-module CLI with parser/execution/trace in `output/interpreter.js`. |
| 2 | 2.1.1 | 424/542 (78.2%) | 33.5 min | 9.9M | 90K | ~$4.83 | 61 | 10 | 2881 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.4_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.4_xhigh/eval1/run2/transcript.jsonl) | Claims complete; 10-file module tree under `output/`. |
| 3 | 2.1.1 | 445/542 (82.1%) | 49.5 min | 6.3M | 95K | ~$3.74 | 74 | 7 | 3411 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.4_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.4_xhigh/eval1/run3/transcript.jsonl) | Claims complete; simulator + parser + runtime split across `main.js` / `simulator.js` / `parser.js`. |

#### gpt-5.3-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 442/542 (81.5%) | 30.0 min | 19.5M | 85K | ~$4.85 | 88 | 5 | 2614 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete; full CLI scaffold with RS274 parsing, state execution, and trace generation. |
| 2 | 2.1.0 | 433/542 (79.9%) | 29.3 min | 8.5M | 71K | ~$2.70 | 73 | 7 | 2651 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; Node.js 22+ simulator with a multi-file output tree. |
| 3 | 2.1.0 | 431/542 (79.5%) | 33.5 min | 11.3M | 86K | ~$3.42 | 71 | 1 | 2637 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; single-file Node.js CLI simulator. |

#### gpt-5.3-codex-spark / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 0/542 (0.0%) | 1.3 min | ? | ? | - | 19 | 0 | 0 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/transcript.jsonl) | Incomplete; context-exhausted while still mapping the spec ("I'm grabbing the error-condition section next..."). 0 files written. |
| 2 | 2.1.1 | 0/542 (0.0%) | 2.6 min | ? | ? | - | 26 | 0 | 0 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/transcript.jsonl) | Incomplete; context-exhausted while still validating spec edge cases. 0 files written. |
| 3 | 2.1.1 | 0/542 (0.0%) | 8.2 min | ? | ? | - | 31 | 0 | 0 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/transcript.jsonl) | Incomplete; context-exhausted via `max_output_tokens` mid-implementation. Said "I'm implementing the full CLI simulator now in `output/main.js`..." but never wrote the file. 0 files. |

All 3 runs ended in `context_exhausted` (runs 1-2 ran out of input window, run 3 hit `max_output_tokens` while emitting the implementation). Token usage / cost unavailable.

#### gpt-5.4-mini / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 346/542 (63.8%) | 92.2 min | 29.8M | 562K | ~$6.11 | 345 | 2 | 4230 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.4-mini_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.4-mini_xhigh/eval1/run1/transcript.jsonl) | Claims complete; simulator engine split across `output/main.js` and `output/simulator.js`. |
| 2 | 2.1.1 | 242/542 (44.6%) | 130.2 min | 33.6M | 764K | ~$6.62 | 381 | 4 | 3283 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.4-mini_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.4-mini_xhigh/eval1/run2/transcript.jsonl) | Claims complete; 130-min run with simulator core in `output/interpreter.js`. |
| 3 | 2.1.1 | 0/542 (0.0%) | 22.5 min | ? | ? | - | ? | 3 | 824 | [result](../../results/cncsim-full-js/codex-cli/gpt-5.4-mini_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-js/codex-cli/gpt-5.4-mini_xhigh/eval1/run3/transcript.jsonl) | Incomplete; context-exhausted while still describing what it was about to write ("starting with the shared primitives first"). 3 scaffolding files / 824 LOC but no working implementation. |

Run 3 token usage unavailable: context-window exhausted during remote compact, turn.failed carries no usage record.

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

### claude-code

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| claude-sonnet-4-6 | high | 2.1.1 | 388/542 (71.6%) | 59.0% | 3/3 | Complete; run 2 originally scored `0/0` due to a transient scorer-container failure and was re-scored against the saved submission (see note) |

#### claude-sonnet-4-6 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 346/542 (63.8%) | 56.5 min | 6.7M | 200K | $6.43 | 88 | 5 | 2998 | [result](../../results/cncsim-full-py/claude-code/claude-sonnet-4-6_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/claude-code/claude-sonnet-4-6_high/eval1/run1/transcript.jsonl) | Claims complete; "simulator is complete and working," summary of file-level breakdown. |
| 2 | 2.1.1 | 226/542 (41.7%) | 37.6 min | 7.1M | 145K | $5.67 | 83 | 7 | 3050 | [result](../../results/cncsim-full-py/claude-code/claude-sonnet-4-6_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/claude-code/claude-sonnet-4-6_high/eval1/run2/transcript.jsonl) | Claims complete; 7-file output with per-file size/purpose table. Originally scored `0/0` — see note below. |
| 3 | 2.1.1 | 388/542 (71.6%) | 48.4 min | 12.3M | 98K | $12.51 | 277 | 5 | 3228 | [result](../../results/cncsim-full-py/claude-code/claude-sonnet-4-6_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/claude-code/claude-sonnet-4-6_high/eval1/run3/transcript.jsonl) | Claims complete; session-end summary describes `motion_kind` plumbing and final-state reporting. |

Run 2 note: the original scorer container for run 2 exited with code 4 in 0.4s and never wrote `report.json`, yielding a transient `0/0` artifact. Pytest on the saved source on the host and in a fresh scorer container both collect and run all 542 tests cleanly. The score above (226/542) was produced by invoking `run_hidden_tests` against the preserved `source/` in the same Docker configuration the runner uses. Harness now retries once on this failure mode and persists `test-container.attempt<N>.log` for future diagnostics (see commit `78313e1`).

Runs 1-3 executed under the old `cncsim-full-py` task id (before the 2026-04-17 rename to `cncsim-py`); content hashes are identical.

---

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.4 | xhigh | 2.1.1 | 449/542 (82.8%) | 59.0% | 3/3 | Complete |
| gpt-5.3-codex | xhigh | 2.1.1 | 460/542 (84.9%) | 69.6% | 3/3 | Complete |
| gpt-5.3-codex-spark | xhigh | 2.1.1 | 0/542 (0.0%) | 0.0% | 3/3 | Complete; all 3 runs context-exhausted before any file written |
| gpt-5.4-mini | xhigh | 2.1.1 | 402/542 (74.2%) | 24.7% | 3/3 | Complete; runs 1-2 context-exhausted before writing code (0/542 each); run 3 delivered |
| gpt-5.2-codex | xhigh | 2.1.0 | 461/542 (85.1%) | 82.8% | 3/3 | Complete; runs 82-91 min each |
| gpt-5.2 | high | 2.1.0 | 448/542 (82.7%) | 69.1% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 2.0.2 | 339/542 (62.5%) | 57.6% | 3/3 | Complete |
| gpt-5 | high | 2.1.0 | 335/542 (61.8%) | 21.5% | 3/3 | Complete; runs 1+3 self-acknowledged incomplete (stubs) |
| gpt-5.1 | high | 2.1.0 | 205/542 (37.8%) | 25.0% | 3/3 | Complete; run 2 self-acknowledged partial coverage |
| gpt-5.1-codex-mini | - | 2.0.2 | 179/542 (33.0%) | 16.5% | 3/3 | Complete; run 2 scaffolded only, run 3 had syntax errors |

#### gpt-5.4 / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 253/542 (46.7%) | 28.6 min | 8.4M | 83K | ~$4.09 | 55 | 2 | 2758 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.4_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.4_xhigh/eval1/run1/transcript.jsonl) | Claims complete; `main.py` + `simulator.py`; flagged cutter-radius compensation and a few rare behaviors as "pragmatically" implemented. |
| 2 | 2.1.1 | 258/542 (47.6%) | 40.2 min | 11.3M | 115K | ~$5.72 | 107 | 1 | 2289 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.4_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.4_xhigh/eval1/run2/transcript.jsonl) | Claims complete; single-file `output/main.py`. |
| 3 | 2.1.1 | 449/542 (82.8%) | 31.4 min | 4.6M | 97K | ~$2.90 | 59 | 2 | 2588 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.4_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.4_xhigh/eval1/run3/transcript.jsonl) | Claims complete; thin `main.py` wrapper + core in `rs274_sim.py`. |

#### gpt-5.3-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 409/542 (75.5%) | 52.8 min | 9.6M | 67K | ~$3.53 | 57 | 2 | 2519 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete ("Implemented."). |
| 2 | 2.1.1 | 262/542 (48.3%) | 40.6 min | 12.7M | 89K | ~$3.73 | 82 | 1 | 2540 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; full CLI simulator in `output/main.py`. |
| 3 | 2.1.1 | 460/542 (84.9%) | 23.7 min | 6.7M | 45K | ~$2.28 | 49 | 1 | 2231 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; single-file `main.py`. |

#### gpt-5.3-codex-spark / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 0/542 (0.0%) | 3.9 min | ? | ? | - | 49 | 0 | 0 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/transcript.jsonl) | Incomplete; context-exhausted before producing any meaningful agent message (last message truncated to "I'm"). 0 files written. |
| 2 | 2.1.1 | 0/542 (0.0%) | 1.5 min | ? | ? | - | 22 | 0 | 0 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/transcript.jsonl) | Incomplete; context-exhausted just as it announced the implementation phase ("I've mapped the RS274 semantics and will now implement a"). 0 files written. |
| 3 | 2.1.1 | 0/542 (0.0%) | 2.7 min | ? | ? | - | 20 | 0 | 0 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/transcript.jsonl) | Incomplete; context-exhausted while still tightening defaults/diagnostics ("doing one more pass for default machine-mode values..."). 0 files written. |

All 3 runs ended in `context_exhausted` before any code was written. Token usage / cost unavailable.

#### gpt-5.4-mini / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 0/542 (0.0%) | 32.9 min | ? | ? | - | ? | 0 | 0 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.4-mini_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.4-mini_xhigh/eval1/run1/transcript.jsonl) | Incomplete; context-exhausted mid-spec-review ("a few cycle details are underspecified..."); wrote no code. |
| 2 | 2.1.1 | 0/542 (0.0%) | 24.1 min | ? | ? | - | ? | 0 | 0 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.4-mini_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.4-mini_xhigh/eval1/run2/transcript.jsonl) | Incomplete; context-exhausted mid-implementation ("I'm implementing the interpreter now: parser, modal state machine, motion/cycle expansion..."); wrote no code. |
| 3 | 2.1.1 | 402/542 (74.2%) | 62.5 min | 29.1M | 436K | ~$5.05 | 290 | 1 | 2946 | [result](../../results/cncsim-full-py/codex-cli/gpt-5.4-mini_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-py/codex-cli/gpt-5.4-mini_xhigh/eval1/run3/transcript.jsonl) | Claims complete; `output/main.py` plus thin wrapper at `main.py`. |

Runs 1-2 token usage unavailable: both context-exhausted during remote compact, turn.failed carries no usage record. Run 3 completed cleanly.

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

Rust ref impl and the `cncsim-full-rs` variant were added in v2.1.0. Existing rows are
eval_version=2.1.0; newer codex-cli entries (gpt-5.3-codex, gpt-5.4, gpt-5.4-mini) are 2.1.1.

### claude-code

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| claude-sonnet-4-6 | high | 2.1.1 | 376/542 (69.4%) | 41.0% | 3/3 | Complete; run 2 agent_error — hit Claude Code's 32K-output-token-per-response cap mid-`Write`, counted as 0/542 (see note) |

#### claude-sonnet-4-6 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 376/542 (69.4%) | 53.3 min | 11.2M | 202K | $7.75 | 102 | 7 | 4775 | [result](../../results/cncsim-rs/claude-code/claude-sonnet-4-6_high/eval1/run1/result.json) [transcript](../../results/cncsim-rs/claude-code/claude-sonnet-4-6_high/eval1/run1/transcript.jsonl) | Claims complete; 7-file Cargo project; session-end summary of `src/interp.rs` use-path fixes. |
| 2 | 2.1.1 | 0/542 (0.0%) | 29.7 min | 1.7M | 152K | $3.25 | 23 | 4 | 1115 | [result](../../results/cncsim-rs/claude-code/claude-sonnet-4-6_high/eval1/run2/result.json) [transcript](../../results/cncsim-rs/claude-code/claude-sonnet-4-6_high/eval1/run2/transcript.jsonl) | `agent_error`: Claude Code's API rejected the response with `"exceeded the 32000 output token maximum"`. Agent was mid-way through a single `Write` of the interpreter file (thinking log: _"This is a very large file. I'll write it in sections."_ — but tried to emit it monolithically). 4 files / 1115 LOC persisted before the crash; nothing builds. |
| 3 | 2.1.1 | 290/542 (53.5%) | 45.4 min | 6.2M | 172K | $5.63 | 83 | 7 | 2943 | [result](../../results/cncsim-rs/claude-code/claude-sonnet-4-6_high/eval1/run3/result.json) [transcript](../../results/cncsim-rs/claude-code/claude-sonnet-4-6_high/eval1/run3/transcript.jsonl) | Claims complete; 7-file Cargo project; session-end verifies exit-code contract (0 success / 1 G-code error / 2 internal). |

Run 2 note: this is the first observed occurrence of the Claude Code `CLAUDE_CODE_MAX_OUTPUT_TOKENS=32000` default cap across the entire dataset (grep over all `results/` confirms no prior hits). Other models break large files into smaller `Write` chunks (typically 3-5K chars each); sonnet-4-6 on Rust attempted a single monolithic `Write` of the interpreter and its own CLI's per-response cap rejected it. Counted as `0/542` per the inclusion rule: the failure is sonnet-4-6's own output-chunking strategy, not a harness issue. The cap was NOT raised for comparability with the other 11 sonnet-4-6 runs in this session and the rest of the dataset (all runs use Claude Code's default).

### codex-cli

| Model | Effort | Version | Best | Mean | Runs | Status |
|---|---|---|---|---|---|---|
| gpt-5.3-codex | xhigh | 2.1.1 | 447/542 (82.5%) | 81.4% | 3/3 | Complete; all 3 runs within 2 points (80.1-82.5%) |
| gpt-5.3-codex-spark | xhigh | 2.1.1 | 0/542 (0.0%) | 0.0% | 3/3 | Complete; all 3 runs context-exhausted before any file written |
| gpt-5.4 | xhigh | 2.1.1 | 424/542 (78.2%) | 58.4% | 3/3 | Complete; run 2 best; runs 1+3 hovered near 48% despite longer wall |
| gpt-5.4-mini | xhigh | 2.1.1 | 369/542 (68.1%) | 53.2% | 3/3 | Complete; tool-heavy (176-329 tool calls/run); runs 2+3 burned 35M+ input tokens each |
| gpt-5.2-codex | xhigh | 2.1.0 | 438/542 (80.8%) | 56.6% | 3/3 | Complete; run 2 best; runs 1+3 spent 60-92 min each |
| gpt-5.2 | high | 2.1.0 | 268/542 (49.4%) | 49.0% | 3/3 | Complete |
| gpt-5.1 | high | 2.1.0 | 302/542 (55.7%) | 40.2% | 3/3 | Complete |
| gpt-5.1-codex-max | xhigh | 2.1.0 | 299/542 (55.2%) | 39.6% | 3/3 | Complete; run 3 took 86 min after "rebuild from scratch" |
| gpt-5.1-codex-mini | high | 2.1.0 | 4/542 (0.7%) | 0.5% | 3/3 | Complete; all 3 runs scaffolded/stubbed — model gave up on Rust implementation |
| gpt-5 | high | 2.1.0 | 4/542 (0.7%) | 0.2% | 3/3 | Complete; runs 1+3 self-acknowledged quote-mangling failures (0 or stub output) |

#### gpt-5.3-codex / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 434/542 (80.1%) | 65.7 min | 6.3M | 162K | ~$3.81 | 61 | 1 | 3932 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex_xhigh/eval1/run1/transcript.jsonl) | Claims complete; standard Cargo Rust project. |
| 2 | 2.1.1 | 447/542 (82.5%) | 61.1 min | 9.0M | 123K | ~$3.65 | 94 | 1 | 3416 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex_xhigh/eval1/run2/transcript.jsonl) | Claims complete; standard Rust Cargo project under `output/`. |
| 3 | 2.1.1 | 443/542 (81.7%) | 34.6 min | 6.4M | 71K | ~$2.54 | 41 | 1 | 3655 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex_xhigh/eval1/run3/transcript.jsonl) | Claims complete; standard Cargo project. |

#### gpt-5.3-codex-spark / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 0/542 (0.0%) | 5.1 min | ? | ? | - | 23 | 0 | 0 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run1/transcript.jsonl) | Incomplete; context-exhausted while still mining the spec appendices ("checking the remaining appendices..."). 0 files written. |
| 2 | 2.1.1 | 0/542 (0.0%) | 5.6 min | ? | ? | - | 54 | 0 | 0 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run2/transcript.jsonl) | Incomplete; context-exhausted via `max_output_tokens` while emitting the simulator. Said "I've finished toolchain bootstrap and am now writing the full simulator implementation in `output/src/main.rs`..." but the response truncated. 0 files persisted. |
| 3 | 2.1.1 | 0/542 (0.0%) | 3.0 min | ? | ? | - | 35 | 0 | 0 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.3-codex-spark_xhigh/eval1/run3/transcript.jsonl) | Incomplete; context-exhausted as the implementation pass started ("now I'm implementing the Rust simulator in `output/src/main.rs` in one pass..."). 0 files written. |

All 3 runs ended in `context_exhausted` (run 1+3 ran out of input window, run 2 hit `max_output_tokens` mid-emission). Token usage / cost unavailable.

#### gpt-5.4 / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 261/542 (48.2%) | 50.1 min | 18.5M | 134K | ~$7.88 | 141 | 7 | 4111 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.4_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.4_xhigh/eval1/run1/transcript.jsonl) | Claims complete; Rust CLI simulator with 7-file module layout. |
| 2 | 2.1.1 | 424/542 (78.2%) | 45.7 min | 14.1M | 133K | ~$6.17 | 111 | 5 | 4160 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.4_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.4_xhigh/eval1/run2/transcript.jsonl) | Claims complete; Rust CLI simulator; noted `cargo build --release --manifest-…`. |
| 3 | 2.1.1 | 264/542 (48.7%) | 69.1 min | 10.5M | 100K | ~$4.75 | 91 | 1 | 3707 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.4_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.4_xhigh/eval1/run3/transcript.jsonl) | Claims complete; single-file `src/main.rs`. |

#### gpt-5.4-mini / xhigh

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.1 | 369/542 (68.1%) | 38.9 min | 24.5M | 267K | ~$3.93 | 176 | 7 | 4221 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.4-mini_xhigh/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.4-mini_xhigh/eval1/run1/transcript.jsonl) | Claims complete; Rust simulator with 7-file module layout under `output/Cargo.toml`. |
| 2 | 2.1.1 | 249/542 (45.9%) | 99.0 min | 36.0M | 684K | ~$7.05 | 329 | 3 | 4105 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.4-mini_xhigh/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.4-mini_xhigh/eval1/run2/transcript.jsonl) | Claims complete; std-only Rust 2021 Cargo project with cycle engine in `output/src/sim.rs`. |
| 3 | 2.1.1 | 247/542 (45.6%) | 73.5 min | 35.6M | 519K | ~$6.09 | 315 | 11 | 4692 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.4-mini_xhigh/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.4-mini_xhigh/eval1/run3/transcript.jsonl) | Claims complete; 11-file Rust 2021 Cargo binary. |

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
| 1 | 2.1.0 | 4/542 (0.7%) | 16.6 min | 7.0M | 111K | ~$0.50 | 49 | 1 | 77 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run1/transcript.jsonl) | Incomplete; no implementation — "Progress so far: None yet; the filesystem hasn't been inspected, and no implementation work has started." Left 77-LOC placeholder. |
| 2 | 2.1.0 | 1/542 (0.2%) | 7.2 min | 2.3M | 46K | ~$0.18 | 35 | 1 | 3 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run2/transcript.jsonl) | Incomplete; acknowledged — "implementing that full specification would take far more time than this session allows, so I left output/src/main.rs as a placeholder that simply reports the simulator is not implemented." |
| 3 | 2.1.0 | 3/542 (0.6%) | 7.2 min | 1.7M | 54K | ~$0.16 | 26 | 1 | 403 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5.1-codex-mini_high/eval1/run3/transcript.jsonl) | Incomplete; CLI skeleton and "foundational runtime plumbing" only — interpreter, motion, and trace not implemented. |

Note: run 1 token counts/cost were backfilled from the archived `codex-events.jsonl` after the adapter parser was hardened against non-dict JSON lines (commit 7e75622).

#### gpt-5 / high

| Run | Version | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.1.0 | 0/542 (0.0%) | 9.9 min | 4.1M | 59K | ~$1.21 | 55 | 0 | 0 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run1/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run1/transcript.jsonl) | Incomplete; wrote no code. Blamed "CLI's shell-quoting mangles embedded quotes and braces in long here-documents." Presented design plan only. |
| 2 | 2.1.0 | 4/542 (0.7%) | 11.1 min | 4.0M | 58K | ~$1.18 | 37 | 1 | 1491 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run2/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run2/transcript.jsonl) | Claims complete; std-only Cargo project — but 538/542 tests failed. |
| 3 | 2.1.0 | 0/542 (0.0%) | 10.6 min | 1.9M | 57K | ~$0.89 | 29 | 1 | 396 | [result](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run3/result.json) [transcript](../../results/cncsim-full-rs/codex-cli/gpt-5_high/eval1/run3/transcript.jsonl) | Incomplete; acknowledged — "wasn't able to create files in output/ because the terminal is mangling multi-line writes." Wrote design doc in response only (396 LOC is partial stub). |

Note: ChatGPT-auth codex-cli does not emit `reported_cost_usd` for non-codex models (gpt-5, gpt-5.1, gpt-5.2); costs shown are `estimated_cost_usd` from token counts × published per-MTok pricing. Captured before OpenAI deprecated these models.
