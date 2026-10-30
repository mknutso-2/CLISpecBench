# Reviewed GPT-6.1 Terra collection, October 29, 2026 — bibtex-py

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `9e153227-56b9-41bb-8276-2d72f16f64c8`

- Score 382/386; status Complete.
- Failures: 4: EXECUTE before READ should be rejected, format.name$ out-of-range index, extra commas in name form 3 should be discarded, and a pending write should be discarded at the end of the run. Not mentioned.
- Network: Searched for a reference BibTeX: apt-get update (deb.nodesource.com and archive.ubuntu.com denied), 'pip index versions' for texlive, pybtex, bibtex and tectonic (pypi.org, 25 denials) and curl HEAD probes of archive.ubuntu.com (one with --noproxy), all denied or failed; nothing was retrieved or installed. Audit also logged 4 malformed denied requests and 11 denied startup requests to oaiusercontent.com content CDNs; chatgpt.com 85 allowed. Disclose the attempted lookups.
- Session turn context shows only gpt-6.1-terra; 1 turn; 77 commands and 19 file changes; non-partial token accounting.
- Compared with published max runs: GPT-6.1 Sol 380/386, GPT-6 Sol 376/386, GPT-5.6 Terra 373/386.

### GPT-6.1 Terra high — `c2723239-a387-47ac-bf95-06850a071ade`

- Score 358/386; status Incomplete.
- Failures: 28, in name formatting, special characters and warning$ logging, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 382/386, GPT-6 Sol 364/386.

### GPT-6.1 Terra low — `69b06f69-d9f3-49fe-a5b1-89a055901f84`

- Score 345/386; status Incomplete.
- Failures: 41, in name formatting and special characters, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 378/386, GPT-6 Sol 347/386.
