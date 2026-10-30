# Reviewed GPT-6.1 Terra collection, October 29, 2026 — gedcom-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `d7fb8ebd-14e4-4bb9-83ce-607a53909c8d`

- Score 212/212; status Complete.
- Failures: None.
- Network: One attempted 'rustup component add rustfmt', denied by the API-only proxy (static.rust-lang.org, 2 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 95 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 80 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's target/ build directory (most of the 859 files).
- Perfect score. Same as published GPT-6.1 Sol max (212/212); above GPT-6 Sol 167/212 and GPT-5.6 Terra 128/212.

### GPT-6.1 Terra high — `da943336-6d6d-409d-b129-a00e785733b3`

- Score 125/212; status Incomplete.
- Failures: 87, mostly structure-specific cardinality, payload-type and semantic validation, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 212/212, GPT-6 Sol 166/212.

### GPT-6.1 Terra low — `31ab8af1-1e0c-4b1e-8732-2effe99071ae`

- Score 121/212; status Incomplete.
- Failures: 91, mostly context-specific structure, datatype, cardinality and media-reference validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 212/212, GPT-6 Sol 96/212.
