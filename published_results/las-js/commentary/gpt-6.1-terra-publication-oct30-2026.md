# Reviewed GPT-6.1 Terra collection, October 29, 2026 — las-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `cfb8f09b-20d1-4761-bbde-ba01495e789e`

- Score 223/223; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 52 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs; one 13-line egress-proxy traceback (tracked separately).
- Session turn context shows only gpt-6.1-terra; 1 turn; 58 commands; files written through shell commands; non-partial token accounting.
- Perfect score; same as published GPT-6.1 Sol, GPT-5.6 Terra and GPT-6 Sol max (223/223).

### GPT-6.1 Terra high — `11711881-3bf3-4f7c-99e5-68c9420a607c`

- Score 222/223; status Complete.
- Failures: 1. Not mentioned.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 223/223, GPT-6 Sol 222/223.

### GPT-6.1 Terra low — `37e75591-f4d1-4312-b077-6a59f5cd4795`

- Score 219/223; status Incomplete.
- Failures: 4, in WKT and cross-record validation, matching the caveat the last message gives.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
