# Reviewed GPT-6.1 Terra collection, October 29, 2026 — wordcount-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `e5852864-00de-4271-b395-eed8ca55d678`

- Score 46/46; status Complete.
- Failures: None.
- Network: One attempted Python urlopen of the Unicode Character Database ReadMe (www.unicode.org), denied by the API-only proxy (403); nothing was retrieved. The agent built its lowercasing tables from the local Python unicodedata module instead. Audit otherwise: chatgpt.com 49 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted fetch.
- Session turn context shows only gpt-6.1-terra; 1 turn; 39 commands and 6 file changes; non-partial token accounting.
- Same score as published GPT-6.1 Sol, GPT-5.6 Terra and GPT-6 Sol max runs (46/46).

### GPT-6.1 Terra high — `b078f5d2-1aca-40b2-9910-fbf5a6627f85`

- Score 46/46; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Same score as published GPT-6.1 Sol and GPT-6 Sol high (46/46).

### GPT-6.1 Terra low — `68959c29-0c86-403e-8253-119bd44acf76`

- Score 46/46; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Same score as published GPT-6.1 Sol and GPT-6 Sol low (46/46).
