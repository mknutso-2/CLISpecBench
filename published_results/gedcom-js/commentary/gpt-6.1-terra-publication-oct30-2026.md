# Reviewed GPT-6.1 Terra collection, October 29, 2026 — gedcom-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `176204dd-f46e-4297-ab87-70651183f787`

- Score 212/212; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 87 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 92 commands; files written through shell commands; non-partial token accounting.
- Perfect score. Same as published GPT-6.1 Sol and GPT-6 Sol max (212/212); far above GPT-5.6 Terra max (118/212).

### GPT-6.1 Terra high — `e88d38a3-aaa8-420e-8f63-81790e9ced37`

- Score 134/212; status Incomplete.
- Failures: 78, mostly context-specific structure and datatype validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 212/212, GPT-6 Sol 180/212.

### GPT-6.1 Terra low — `24fdd19e-5808-4956-af49-5f3c5502ebcc`

- Score 113/212; status Incomplete.
- Failures: 99, mostly structure and datatype validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 206/212, GPT-6 Sol 109/212.
