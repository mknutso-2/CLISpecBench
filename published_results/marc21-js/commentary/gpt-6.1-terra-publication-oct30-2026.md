# Reviewed GPT-6.1 Terra collection, October 29, 2026 — marc21-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `c511de55-5584-4008-afff-f6ee90838501`

- Score 2900/2900; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 62 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 90 commands and 4 file changes; non-partial token accounting.
- Perfect score; above published GPT-6.1 Sol max 2896/2900, GPT-6 Sol 2876/2900 and GPT-5.6 Terra 2848/2900.

### GPT-6.1 Terra high — `1da6dfd7-d29e-4c75-8ed9-31e340e67eeb`

- Score 2857/2900; status Incomplete.
- Failures: 43, all in 006/007/008 fixed-field validation, matching the limitation the last message names.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 2900/2900, GPT-6 Sol 2876/2900.

### GPT-6.1 Terra low — `f11496de-2a79-4122-88e3-82c28b8b88ef`

- Score 2857/2900; status Complete.
- Failures: 43, in 006/007/008 fixed-field validation. Not mentioned.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
