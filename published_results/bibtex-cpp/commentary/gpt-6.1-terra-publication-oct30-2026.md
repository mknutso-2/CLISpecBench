# Reviewed GPT-6.1 Terra collection, October 29, 2026 — bibtex-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `ffa474ce-e643-4f5f-9923-1d24eae48432`

- Score 384/386; status Complete.
- Failures: 2: format.name$ with an out-of-range index (test_builtins_exhaustive.py) and a macro concatenated with itself (test_concat_and_macros.py). Not mentioned.
- Network: Searched for a reference BibTeX: 'pip index versions' for bibtex, bibtex-tidy and tectonic (pypi.org, 18 denials) and curl HEAD probes of deb.debian.org and github.com, all denied by the API-only proxy; nothing was retrieved or installed. Audit otherwise: chatgpt.com 85 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted lookups.
- Session turn context shows only gpt-6.1-terra; 1 turn; 97 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's build directory (most of the 250 files).
- Best published-max comparison: above GPT-6.1 Sol 382/386, GPT-5.6 Terra 362/386 and GPT-6 Sol 362/386.

### GPT-6.1 Terra high — `fa3dabd4-9e6c-4387-9ae8-1feab42b98fa`

- Score 356/386; status Incomplete.
- Failures: 30, in name formatting, special characters, warnings and other edge cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- One 13-line egress-proxy traceback in the network audit (tracked separately).
- Model-side early stop at high effort; the same model at max scored 384/386 in 14.2 min.
- Compared with published high runs: GPT-6.1 Sol 377/386, GPT-6 Sol 361/386.

### GPT-6.1 Terra low — `0ee276dd-eb70-4170-808f-4a1bfa3e6203`

- Score 339/386; status Incomplete.
- Failures: 47, in name formatting, width$, special characters, crossrefs and load-time validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- One 13-line egress-proxy traceback in the network audit (tracked separately).
- Compared with published low runs: GPT-6.1 Sol 375/386, GPT-6 Sol 348/386.
