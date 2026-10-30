# Reviewed GPT-6.1 Terra collection, October 29, 2026 — wordcount-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `89d151a5-266c-4889-8533-d0ccdb3fafd5`

- Score 46/46; status Complete.
- Failures: None.
- Network: None by the agent ('rustup component list --installed' and 'rustup toolchain list' are local queries). API-only audit: chatgpt.com 29 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 26 commands and 4 file changes; non-partial token accounting.
- The saved source includes the agent's target/ build directory (most of the 666 files).
- Same score as published GPT-6.1 Sol, GPT-5.6 Terra and GPT-6 Sol max runs (46/46).

### GPT-6.1 Terra high — `b0a4dda7-9143-487d-8f86-e4b58070f064`

- Score 46/46; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Same score as published GPT-6.1 Sol and GPT-6 Sol high (46/46).

### GPT-6.1 Terra low — `1b21472c-086b-4d73-83ce-9e6baa7e5516`

- Score 46/46; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Same score as published GPT-6.1 Sol and GPT-6 Sol low (46/46).
