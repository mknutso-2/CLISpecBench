# Reviewed GPT-6.1 Terra collection, October 29, 2026 — bibtex-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `86c2b26d-483c-474d-a45d-267812053263`

- Score 382/386; status Complete.
- Failures: 4: format.name$ out-of-range index, and three output-buffer rules (trailing whitespace removed on a short line, pending write discarded at the end of the run, whitespace-only line discarded on flush). Not mentioned.
- Network: Searched for a reference BibTeX: apt-get update (archive.ubuntu.com and deb.nodesource.com denied), npm view/search for tectonic and bibtex (registry.npmjs.org denied), 'pip index versions' for tectonic, texlive and bibtex (pypi.org, 18 denials) and a curl --noproxy probe of registry.npmjs.org (failed, exit 6); nothing was retrieved or installed. Audit also logged 4 malformed denied requests and 11 denied startup requests to oaiusercontent.com content CDNs; chatgpt.com 76 allowed. Disclose the attempted lookups.
- Session turn context shows only gpt-6.1-terra; 1 turn; 85 commands; files written through shell commands; non-partial token accounting.
- Compared with published max runs: GPT-6 Sol 381/386, GPT-6.1 Sol 380/386, GPT-5.6 Terra 372/386.

### GPT-6.1 Terra high — `30827195-8007-4c82-9cf2-bfa7ed40bc5f`

- Score 353/386; status Incomplete.
- Failures: 33, in name formatting, special characters, warnings and output-buffer edge cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 380/386, GPT-6 Sol 358/386.

### GPT-6.1 Terra low — `495bbc55-e7b9-4346-9954-3be7b0e78b7d`

- Score 352/386; status Incomplete.
- Failures: 34, in name formatting, special characters, warnings and error cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 377/386, GPT-6 Sol 336/386.
