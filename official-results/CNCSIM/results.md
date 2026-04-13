# Official results for CNCSim eval version 2.0.1

Only runs against the current 542-test suite are included. Runs invalidated by
infrastructure failures (auth errors, rate limits, insufficient timeout, data
corruption) are excluded and noted as needing reruns. Empty cells = data not yet
collected.

## C++

### claude-code

| Model | Effort | Run 1 | Run 2 | Run 3 | Best | Mean | Notes |
|---|---|---|---|---|---|---|---|
| claude-opus-4-6 | max | [430/542 (79.3%)](../../results/cncsim-full/claude-code/claude-opus-4-6_max/eval1/run1/result.json) | [399/542 (73.6%)](../../results/cncsim-full/claude-code/claude-opus-4-6_max/eval1/run2/result.json) | | 430 | 76.5% | Run 3 timed out (old 30m limit); needs rerun |
| claude-opus-4-5-20251101 | high | [331/542 (61.1%)](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run1/result.json) | [376/542 (69.4%)](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run2/result.json) | [382/542 (70.5%)](../../results/cncsim-full/claude-code/claude-opus-4-5-20251101_high/eval1/run3/result.json) | 382 | 67.0% | All completed cleanly |
| claude-sonnet-4-6 | high | | | | | | All 3 timed out (old 30m limit); needs full rerun |
| claude-sonnet-4-5-20250929 | high | [184/542 (33.9%)](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run1/result.json) | [179/542 (33.0%)](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run2/result.json) | [167/542 (30.8%)](../../results/cncsim-full/claude-code/claude-sonnet-4-5-20250929_high/eval1/run3/result.json) | 184 | 32.6% | All completed cleanly |
| claude-haiku-4-5-20251001 | high | [104/542 (19.2%)](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run1/result.json) | [0/542 (0.0%)](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run2/result.json) | [0/542 (0.0%)](../../results/cncsim-full/claude-code/claude-haiku-4-5-20251001_high/eval1/run3/result.json) | 104 | 6.4% | Runs 2-3: agent completed but never wrote code |

### codex-cli

| Model | Effort | Run 1 | Run 2 | Run 3 | Best | Mean | Notes |
|---|---|---|---|---|---|---|---|
| gpt-5.4 | xhigh | [380/542 (70.1%)](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run1/result.json) | [262/542 (48.3%)](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run2/result.json) | [262/542 (48.3%)](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval4/run3/result.json) | 380 | 55.6% | All completed cleanly; additional clean run: [408/542 (75.3%)](../../results/cncsim-full/codex-cli/gpt-5.4_xhigh/eval3/run1/result.json) |
| gpt-5.4-mini | xhigh | | | | | | 0/542 x3 (old 30m limit); needs rerun with 4hr timeout |
| gpt-5.3-codex | xhigh | | | | | | All timed out (old 30m limit); needs rerun |
| gpt-5.2-codex | xhigh | | | | | | Auth failure (stale refresh token); needs rerun |
| gpt-5.2 | high | | | | | | Auth failure (stale refresh token); needs rerun |
| gpt-5.1-codex-max | xhigh | | | | | | Auth failure (stale refresh token); needs rerun |
| gpt-5.1-codex-mini | high | | | | | | Auth failure (stale refresh token); needs rerun |

### gemini-cli

| Model | Effort | Run 1 | Run 2 | Run 3 | Best | Mean | Notes |
|---|---|---|---|---|---|---|---|
| gemini-3-flash-preview | - | [211/542 (38.9%)](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run1/result.json) | [186/542 (34.3%)](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run2/result.json) | [184/542 (33.9%)](../../results/cncsim-full/gemini-cli/gemini-3-flash-preview/eval1/run3/result.json) | 211 | 35.7% | All completed cleanly |
| gemini-3.1-pro-preview | - | [123/542 (22.7%)](../../results/cncsim-full/gemini-cli/gemini-3.1-pro-preview/eval4/run1/result.json) | | | 123 | 22.7% | Runs 2-3 hit rate limit (429); needs rerun |
| gemini-2.5-pro | - | | | | | | Rate limit 429 ("exhausted quota"); needs rerun |
| gemini-2.5-flash | - | | | | | | Error/timeout; needs rerun |
| gemini-2.5-flash-lite | - | | | | | | Incomplete code / timeout; needs rerun |

## js

*(No runs yet)*

## py

*(No runs yet)*

## rs

*(No runs yet)*
