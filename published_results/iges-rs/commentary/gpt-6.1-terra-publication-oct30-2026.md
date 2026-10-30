# Reviewed GPT-6.1 Terra collection, October 29, 2026 — iges-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `3659f14a-edab-489d-8ae5-e55776d8cd78`

- Score 248/249; status Complete.
- Failures: 1: test_zero_count_hollerith_is_rejected_after_defaulted_string_control, the same single failure as Terra IGES C++ and the Claude 5.5 IGES runs. Not mentioned.
- Network: One curl of the FreeCAD GitHub tree (api.github.com) looking for IGES sample files, denied by the API-only proxy (exit 56); nothing was retrieved. 'rustup toolchain list' is a local query. Audit otherwise: chatgpt.com 93 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted fetch.
- Session turn context shows only gpt-6.1-terra; 1 turn; 104 commands; files written through shell commands; non-partial token accounting.
- Compared with published max runs: GPT-5.6 Terra 248/249, GPT-6.1 Sol 247/249, GPT-6 Sol 243/249.

### GPT-6.1 Terra high — `e07d7893-a753-4a36-bdcb-06c6b2a0990b`

- Score 149/249; status Incomplete.
- Failures: 100, across the uncovered entity catalog and evaluators, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 249/249, GPT-6 Sol 243/249.

### GPT-6.1 Terra low — `40b09b6e-d5b9-48d5-bb5c-dc4eb26a25ef`

- Score 75/249; status Incomplete.
- Failures: 174, across JSON writing, most schemas, surface and spline evaluation and round-trip normalization, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
