# Reviewed GPT-6.1 Terra collection, October 29, 2026 — rs274-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `1aad4248-0dd0-42ee-93c2-458e0ba0ecc4`

- Score 555/555; status Complete.
- Failures: None.
- Network: None by the agent. API-only audit: chatgpt.com 127 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 102 commands; files were written through shell commands (no apply_patch file_change items); non-partial token accounting.
- Perfect score. Compared with published max runs: GPT-6.1 Sol 555/555, GPT-6 Sol 553/555, GPT-5.6 Terra 545/555.

### GPT-6.1 Terra high — `6625d3d5-14a4-4290-af99-75f7da4698a6`

- Score 393/555; status Incomplete.
- Failures: 162 across coordinate-system selection, block prefixes and block delete, canned cycles, comment parsing, cutter radius compensation and more; consistent with the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com 24 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 12 commands; files written through shell commands; non-partial token accounting.
- Model-side early stop at high effort: the same model at max scored 555/555 in 24.8 min. Counted as a completed run; status Incomplete because the agent acknowledged the gaps.
- Compared with published high runs: GPT-6 Sol 547/555, GPT-6.1 Sol 546/555, GPT-5.6 Terra 461/555.

### GPT-6.1 Terra low — `17db0624-f44c-4b45-ab82-298dce6de6c6`

- Score 308/555; status Incomplete.
- Failures: 247, across arcs, canned cycles, probing, G28/G30, cutter compensation and more, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 546/555, GPT-6 Sol 405/555.
