# Reviewed GPT-6.1 Terra collection, October 29, 2026 — ical-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `2f8fd44f-0096-4b80-bfcb-d2b46abb9657`

- Score 461/467; status Complete.
- Failures: 6: the same two EXRULE cases, iTIP ADD forbids RECURRENCE-ID and RDATE end-before-start warning as Terra ICal JS/C++, plus a warning should include the UID when applicable and a malformed GEO should warn. Not mentioned.
- Network: One attempted 'pip install python-dateutil' into /tmp for cross-checking, denied by the API-only proxy (pypi.org, 6 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 92 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 87 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's target/ build directory (most of the 558 files).
- Compared with published max runs: GPT-6.1 Sol 466/467, GPT-6 Sol 461/467, GPT-5.6 Terra 454/467.

### GPT-6.1 Terra high — `158e8333-d1cd-4b85-a7e7-ec77cd37718f`

- Score 450/467; status Incomplete.
- Failures: 17, in RSCALE, historical timezone rules and UNTIL comparisons, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 463/467, GPT-6 Sol 450/467.

### GPT-6.1 Terra low — `af17afa0-1a9b-446d-8348-36c585dcece2`

- Score 346/467; status Incomplete.
- Failures: 121, across BYxxx rules, overrides, VTIMEZONE resolution and validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 462/467, GPT-6 Sol 442/467.
