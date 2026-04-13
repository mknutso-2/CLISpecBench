# Official results for CNCSim eval version 2.0.1

Only runs against the current 542-test suite are included. Runs invalidated by
infrastructure failures (auth errors, rate limits, insufficient timeout, data
corruption) are excluded and noted as needing reruns.

Cost is `reported_cost_usd` from the agent CLI when available, otherwise
`estimated_cost_usd` computed by the harness (marked with ~).

## C++

### claude-code

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| claude-opus-4-6 | max | 430/542 (79.3%) | 76.5% | 2/3 | Run 3 timed out (old 30m limit); needs rerun |
| claude-opus-4-5-20251101 | high | 382/542 (70.5%) | 67.0% | 3/3 | Complete |
| claude-sonnet-4-6 | high | - | - | 0/3 | All timed out (old 30m limit); needs full rerun |
| claude-sonnet-4-5-20250929 | high | 184/542 (33.9%) | 32.6% | 3/3 | Complete |
| claude-haiku-4-5-20251001 | high | 104/542 (19.2%) | 6.4% | 3/3 | Complete |

#### claude-opus-4-6 / max

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 430/542 (79.3%) | 16.8 min | 3.4M | 59K | $4.70 | 51 | 10 | 3751 | [result](../../results/cncsim-full/claude-code/claude-opus-4-6_max/eval1/run1/result.json) [transcript](../../results/cncsim-full/claude-code/claude-opus-4-6_max/eval1/run1/transcript.jsonl) | Completed cleanly |
| 2 | 399/542 (73.6%) | 24.9 min | 5.4M | 79K | $6.25 | 114 | 5 | 3308 | [result](../../results/cncsim-full/claude-code/claude-opus-4-6_max/eval1/run2/result.json) [transcript](../../results/cncsim-full/claude-code/claude-opus-4-6_max/eval1/run2/transcript.jsonl) | Completed cleanly |
| 3 | | | | | | | | | | Timed out (old 30m limit); needs rerun |

#### claude-opus-4-5-20251101 / high

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 331/542 (61.1%) | 17.4 min | 10.6M | 67K | $8.23 | 109 | 17 | 4521 | [result](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run1/result.json) [transcript](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run1/transcript.jsonl) | Completed cleanly |
| 2 | 376/542 (69.4%) | 21.1 min | 10.7M | 86K | $9.00 | 134 | 12 | 4326 | [result](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run2/result.json) [transcript](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run2/transcript.jsonl) | Completed cleanly |
| 3 | 382/542 (70.5%) | 19.1 min | 8.8M | 76K | $7.72 | 104 | 18 | 4370 | [result](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run3/result.json) [transcript](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run3/transcript.jsonl) | Completed cleanly |

#### claude-sonnet-4-6 / high

All 3 runs timed out at the old 30-minute limit. Needs full rerun with 4-hour timeout.

#### claude-sonnet-4-5-20250929 / high

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 184/542 (33.9%) | 11.1 min | 2.7M | 46K | $1.82 | 48 | 13 | 3164 | [result](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run1/result.json) [transcript](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run1/transcript.jsonl) | Completed cleanly |
| 2 | 179/542 (33.0%) | 16.6 min | 3.4M | 58K | $2.71 | 78 | 30 | 4110 | [result](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run2/result.json) [transcript](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run2/transcript.jsonl) | Completed cleanly |
| 3 | 167/542 (30.8%) | 16.1 min | 2.4M | 25K | $3.05 | 101 | 3 | 2899 | [result](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run3/result.json) [transcript](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run3/transcript.jsonl) | Completed cleanly |

#### claude-haiku-4-5-20251001 / high

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 104/542 (19.2%) | 8.0 min | 6.9M | 52K | $1.07 | 83 | 26 | 3093 | [result](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run1/result.json) [transcript](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run1/transcript.jsonl) | Completed cleanly |
| 2 | 0/542 (0.0%) | 3.0 min | 0.5M | 5K | $0.29 | 38 | 0 | 0 | [result](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run2/result.json) [transcript](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run2/transcript.jsonl) | Agent planned but never wrote code |
| 3 | 0/542 (0.0%) | 3.1 min | 0.4M | 6K | $0.26 | 34 | 0 | 0 | [result](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run3/result.json) [transcript](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run3/transcript.jsonl) | Agent planned but never wrote code |

---

### codex-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| gpt-5.4 | xhigh | 408/542 (75.3%) | 55.6% | 4/3 | Complete (4 clean runs across two batches) |
| gpt-5.4-mini | xhigh | - | - | 0/3 | 0/542 x3 (old 30m limit); needs rerun |
| gpt-5.3-codex | xhigh | - | - | 0/3 | All timed out (old 30m limit); needs rerun |
| gpt-5.2-codex | xhigh | - | - | 0/3 | Auth failure (stale refresh token); needs rerun |
| gpt-5.2 | high | - | - | 0/3 | Auth failure (stale refresh token); needs rerun |
| gpt-5.1-codex-max | xhigh | - | - | 0/3 | Auth failure (stale refresh token); needs rerun |
| gpt-5.1-codex-mini | high | - | - | 0/3 | Auth failure (stale refresh token); needs rerun |

#### gpt-5.4 / xhigh

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 408/542 (75.3%) | 51.7 min | 10.2M | 85K | ~$4.17 | 72 | 5 | 4217 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval3/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval3/run1/transcript.jsonl) | Completed cleanly (eval3) |
| 2 | 380/542 (70.1%) | 44.9 min | 11.2M | 120K | ~$5.00 | 62 | 4 | 3591 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run1/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run1/transcript.jsonl) | Completed cleanly (eval4/run1) |
| 3 | 262/542 (48.3%) | 38.2 min | 9.8M | 89K | ~$4.23 | 55 | 3 | 3528 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run2/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run2/transcript.jsonl) | Completed cleanly (eval4/run2) |
| 4 | 262/542 (48.3%) | 34.4 min | 12.0M | 67K | ~$4.56 | 65 | 4 | 3398 | [result](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run3/result.json) [transcript](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run3/transcript.jsonl) | Completed cleanly (eval4/run3) |

---

### gemini-cli

| Model | Effort | Best | Mean | Runs | Status |
|---|---|---|---|---|---|
| gemini-3-flash-preview | - | 211/542 (38.9%) | 35.7% | 3/3 | Complete |
| gemini-3.1-pro-preview | - | 123/542 (22.7%) | 22.7% | 1/3 | Runs 2-3 hit rate limit (429); needs rerun |
| gemini-2.5-pro | - | - | - | 0/3 | Rate limit 429; needs rerun |
| gemini-2.5-flash | - | - | - | 0/3 | Error/timeout; needs rerun |
| gemini-2.5-flash-lite | - | - | - | 0/3 | Incomplete code / timeout; needs rerun |

#### gemini-3-flash-preview

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 211/542 (38.9%) | 4.6 min | 2.5M | 37K | ~$0.49 | 28 | 11 | 1300 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run1/transcript.jsonl) | Completed cleanly |
| 2 | 186/542 (34.3%) | 7.8 min | 6.1M | 48K | ~$0.94 | 75 | 10 | 2606 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run2/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run2/transcript.jsonl) | Completed cleanly |
| 3 | 184/542 (33.9%) | 8.2 min | 3.7M | 46K | ~$0.66 | 37 | 10 | 953 | [result](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run3/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run3/transcript.jsonl) | Completed cleanly |

#### gemini-3.1-pro-preview

| Run | Score | Wall | Input | Output | Cost | Tools | Files | LOC | Links | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 123/542 (22.7%) | 5.4 min | 0.9M | 12K | ~$1.00 | 24 | 12 | 1449 | [result](../../results/cncsim-full/gemini-cli/gemini-3.1-pro-preview/eval4/run1/result.json) [transcript](../../results/cncsim-full/gemini-cli/gemini-3.1-pro-preview/eval4/run1/transcript.jsonl) | Completed cleanly |
| 2 | | | | | | | | | | Rate limit 429; needs rerun |
| 3 | | | | | | | | | | Rate limit 429; needs rerun |

---

### copilot-cli

No runs yet.

## js

No runs yet.

## py

No runs yet.

## rs

No runs yet.
