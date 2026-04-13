# Official results for CNCSim eval version 2.0.2

v2.0.2 adds a shared one-shot prompt (`Evals/_shared/require-one-shot.md`) appended
to all agent prompts. Only runs against the v2.0.2 prompt + 542-test suite are
included.

**Only runs where the agent completed successfully (`exit_reason: "completed"`)
appear in the tables.** Runs that errored, timed out, or were rate-limited are
excluded and noted as needing reruns. Best/Mean are computed only over completed runs.

Cost is `reported_cost_usd` from the agent CLI when available. Copilot CLI does
not report input tokens or cost.

## C++

### claude-code

No v2.0.2 runs yet. See `results-2_0_1.md` for v2.0.1 results.

---

### codex-cli

No v2.0.2 runs yet. See `results-2_0_1.md` for v2.0.1 results.

---

### gemini-cli

No v2.0.2 runs yet. See `results-2_0_1.md` for v2.0.1 results.

---

### copilot-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| claude-haiku-4.5 | - | 90/542 (16.6%) | 16.6% | 1/3 | Run 2 errored; run 3 rate limited; needs rerun |
| gpt-4.1 | - | 20/542 (3.7%) | 1.4% | 3/3 | Complete |
| gpt-5-mini | high | - | - | 0/3 | All rate limited (free-tier quota); needs rerun |

#### claude-haiku-4.5

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 90/542 (16.6%) | 7.8 min | 0 | 49K | - | 0 | 3 | 1276 | [result](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval1/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/claude-haiku-4.5/eval1/run1/transcript.jsonl) | Claims complete; built and tested. |

Excluded: run 2 (exit_reason=error, scored 86/542), run 3 (rate limited, 369 tokens).

#### gpt-4.1

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Last Message |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1/542 (0.2%) | 3.3 min | 0 | 9K | - | 0 | 18 | 350 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run1/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run1/transcript.jsonl) | Incomplete; scaffolded only. Acknowledged "core logic... will be implemented" next. |
| 2 | 20/542 (3.7%) | 3.9 min | 0 | 10K | - | 0 | 18 | 506 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run2/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run2/transcript.jsonl) | Incomplete; scaffolded only. Asked "Let me know if you want to proceed with the execution engine." |
| 3 | 1/542 (0.2%) | 5.2 min | 0 | 14K | - | 0 | 2 | 207 | [result](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run3/result.json) [transcript](../../results/cncsim-full/copilot-cli/gpt-4.1/eval1/run3/transcript.jsonl) | Incomplete; scaffolded only. Asked "Let me know if you want to proceed with a specific part." |

#### gpt-5-mini / high

All 3 runs rate limited (free-tier quota exhaustion). Run 1 hit 429 mid-implementation
after 17 min; runs 2-3 failed immediately (6-hour cooldown). Needs rerun.

---

## js

No runs yet.

## py

No runs yet.

## rs

No runs yet.
