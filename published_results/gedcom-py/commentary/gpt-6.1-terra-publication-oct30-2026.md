# Reviewed GPT-6.1 Terra collection, October 29, 2026 — gedcom-py

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `b360f3a0-d5d6-425b-838e-5c6bd7a3d17f`

- Score 212/212; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 87 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 63 commands and 19 file changes; non-partial token accounting.
- Perfect score. Same as published GPT-6.1 Sol and GPT-6 Sol max (212/212); above GPT-5.6 Terra max (205/212) and every Claude 5.5 GEDCOM run so far.

### GPT-6.1 Terra high — `aa6728e1-b860-4e44-bd8e-8310cbcee786`

- Score 124/212; status Incomplete.
- Failures: 88, mostly structure, cardinality, payload-type and pointer-target validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 212/212, GPT-6 Sol 195/212.

### GPT-6.1 Terra low — `030c757b-dbc9-418a-ba08-9ecc6cd06318`

- Score 124/212; status Incomplete.
- Failures: 88, mostly structure, cardinality and datatype validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- One 13-line egress-proxy traceback in the network audit (tracked separately).
- Compared with published low runs: GPT-6.1 Sol 212/212, GPT-6 Sol 117/212.
