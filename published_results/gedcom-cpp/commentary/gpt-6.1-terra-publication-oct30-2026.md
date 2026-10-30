# Reviewed GPT-6.1 Terra collection, October 29, 2026 — gedcom-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `21af76e1-a313-44f9-b8f5-9b6ae92feb48`

- Score 212/212; status Complete.
- Failures: None.
- Network: One attempted 'pip install clang-format' into /tmp, denied by the API-only proxy (pypi.org, 4 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 123 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 88 commands; files written through shell commands; non-partial token accounting.
- Perfect score. Same as published GPT-6.1 Sol max (212/212); above GPT-6 Sol 205/212 and GPT-5.6 Terra 169/212.

### GPT-6.1 Terra high — `5747e987-00ae-4cc2-a586-d5b6453ed2c0`

- Score 114/212; status Incomplete.
- Failures: 98, mostly structure, cardinality and datatype validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 212/212, GPT-6 Sol 143/212.

### GPT-6.1 Terra low — `7dd26b60-788d-4dac-b152-9d11b51d72e9`

- Score 125/212; status Incomplete.
- Failures: 87, mostly structure, cardinality and datatype validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 210/212, GPT-6 Sol 93/212.
