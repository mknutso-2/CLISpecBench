# Reviewed GPT-6.1 Terra collection, October 29, 2026 — marc21-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `ca795823-9afe-47c5-845d-d7883339f088`

- Score 2900/2900; status Complete.
- Failures: None.
- Network: One attempted 'rustup component add rustfmt', denied by the API-only proxy (static.rust-lang.org, 2 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 105 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs; one 13-line egress-proxy traceback (tracked separately). Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 104 commands and 8 file changes; non-partial token accounting.
- The saved source includes the agent's target/ build directory (most of the 536 files).
- Perfect score; above published GPT-6.1 Sol max 2897/2900, GPT-6 Sol 2880/2900 and GPT-5.6 Terra 2857/2900. Terra is 2900/2900 in all four MARC21 languages.

### GPT-6.1 Terra high — `2a4cfa81-38eb-4454-92bd-b2941ea916f2`

- Score 2359/2900; status Incomplete.
- Failures: 541, in fixed-field positions and undefined data-field tags, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 2900/2900, GPT-6 Sol 2861/2900.

### GPT-6.1 Terra low — `00c6ec57-86c8-42d1-81a4-75bc715d8e2e`

- Score 2837/2900; status Incomplete.
- Failures: 63, in fixed-field positions and unextracted field definitions, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
