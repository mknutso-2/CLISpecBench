# Reviewed GPT-6.1 Terra collection, October 29, 2026 — las-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `5d2de615-d896-4153-8a68-9795da686eef`

- Score 223/223; status Complete.
- Failures: None.
- Network: One attempted 'rustup component add rustfmt', denied by the API-only proxy (static.rust-lang.org, 2 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 60 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 68 commands; files written through shell commands; non-partial token accounting.
- Perfect score; same as published GPT-6.1 Sol, GPT-5.6 Terra and GPT-6 Sol max (223/223). Terra is 223/223 in all four LAS languages.

### GPT-6.1 Terra high — `499c3d6f-d775-4a9b-86ef-d3e0d91fa9ec`

- Score 218/223; status Incomplete.
- Failures: 5, including WKT grammar and metadata cross-check edge cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6 Sol 218/223, GPT-6.1 Sol 217/223.

### GPT-6.1 Terra low — `558802d1-32e0-40ee-8dcc-099fdf4f817a`

- Score 207/223; status Incomplete.
- Failures: 16, in CRS, waveform and extra-bytes validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
