# Reviewed GPT-6.1 Terra collection, October 29, 2026 — bibtex-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `f36b8bda-0206-4733-aeb7-41cf9fad7669`

- Score 380/386; status Complete.
- Failures: 6: format.name$ out-of-range index, a redeclared crossref field should be rejected, extra commas in name form 3 should be discarded, and the same three output-buffer rules as Terra BibTeX JS. Not mentioned.
- Network: Searched for a reference BibTeX and tools: 'apt-get update && apt-get install texlive-binaries' (deb.nodesource.com denied, exit 100), a curl probe of deb.debian.org, 'npm view bibtex' (registry.npmjs.org denied), 'pip index versions' for several BibTeX packages (pypi.org, 22 denials) and 'rustup component add rustfmt' (static.rust-lang.org denied); nothing was retrieved or installed. Audit also logged 4 malformed denied requests and 11 denied startup requests to oaiusercontent.com content CDNs; chatgpt.com 81 allowed. Disclose the attempted installs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 84 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's target/ build directory (most of the 612 files).
- Compared with published max runs: GPT-6.1 Sol 382/386, GPT-5.6 Terra 382/386, GPT-6 Sol 372/386.

### GPT-6.1 Terra high — `ca386e92-05b0-4ad1-a844-178ed782ee71`

- Score 349/386; status Incomplete.
- Failures: 37, in name formatting, cross-reference handling, character operations and error locations, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 378/386, GPT-6 Sol 365/386.

### GPT-6.1 Terra low — `fe2b0221-5b02-49ed-ad7a-21884e32001a`

- Score 326/386; status Incomplete.
- Failures: 60, in name formatting, special characters, width$, crossrefs, error locations and warnings, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- One 13-line egress-proxy traceback in the network audit (tracked separately).
- Compared with published low runs: GPT-6.1 Sol 373/386, GPT-6 Sol 324/386.
