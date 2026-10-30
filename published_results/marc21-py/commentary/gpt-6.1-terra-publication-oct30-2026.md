# Reviewed GPT-6.1 Terra collection, October 29, 2026 — marc21-py

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `cb80939a-6b17-4a41-ba76-eba57c64ef2d`

- Score 2900/2900; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 63 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 87 commands; files written through shell commands; non-partial token accounting.
- Perfect score; same as published GPT-6.1 Sol max (2900/2900); above GPT-6 Sol 2882/2900 and GPT-5.6 Terra 2841/2900.

### GPT-6.1 Terra high — `88348f7d-8ba2-4265-bf46-50903b5490fe`

- Score 2861/2900; status Complete.
- Failures: 39, in 006/007/008 fixed-field validation. Not mentioned.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 2900/2900, GPT-6 Sol 2856/2900.

### GPT-6.1 Terra low — `f23a58e3-91e5-4758-9b5f-6896eb9db989`

- Score 2394/2900; status Complete.
- Failures: 506, in field-rule coverage and fixed fields. Not mentioned.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
