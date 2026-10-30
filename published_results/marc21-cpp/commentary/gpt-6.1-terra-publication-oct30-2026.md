# Reviewed GPT-6.1 Terra collection, October 29, 2026 — marc21-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `c02c7e39-2703-4229-ba7e-f4764d83fa61`

- Score 2900/2900; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 65 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 98 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's build directory (most of the 244 files).
- Perfect score; same as published GPT-6.1 Sol max (2900/2900); above GPT-5.6 Terra and GPT-6 Sol max (2876/2900) and every Claude 5.5 MARC21 run (best 2882/2900).

### GPT-6.1 Terra high — `b325e08d-2360-48d1-9f75-ecf977b55e9a`

- Score 2857/2900; status Incomplete.
- Failures: 43, all in 006/007/008 fixed-field validation, matching the gap the last message names.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 2900/2900, GPT-6 Sol 2896/2900.

### GPT-6.1 Terra low — `c63dbb17-1b2d-4e27-8dbc-8922873b96ef`

- Score 2351/2900; status Incomplete.
- Failures: 549, mostly fields defined only on shared documentation pages and fixed fields, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
