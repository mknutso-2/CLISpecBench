# Reviewed GPT-6.1 Terra collection, October 29, 2026 — ical-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `d9c09f79-3c8a-4d27-b89b-08d9d3daddc0`

- Score 462/467; status Complete.
- Failures: 5: two EXRULE cases (monthly second Friday; combined with EXDATE), calendar IMAGE DISPLAY comma-list values, iTIP ADD forbids RECURRENCE-ID, and an RDATE period ending before its start should warn. Four overlap with Terra ICal JS. Not mentioned.
- Network: One attempted 'pip install clang-format' into /tmp, denied by the API-only proxy (pypi.org, 4 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 123 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs; one 13-line egress-proxy traceback (tracked separately). Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 125 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's build directory (most of the 205 files).
- Compared with published max runs: GPT-6.1 Sol 464/467, GPT-6 Sol 458/467, GPT-5.6 Terra 456/467.

### GPT-6.1 Terra high — `d01bdb75-6d8f-4e81-86f7-5dce23cb452c`

- Score 450/467; status Incomplete.
- Failures: 17, including RSCALE, historical TZUNTIL and recurrence/timezone edge cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 464/467, GPT-6 Sol 456/467.

### GPT-6.1 Terra low — `50cfb034-e375-4b54-a078-543da4d55652`

- Score 400/467; status Incomplete.
- Failures: 67, across recurrence rule parts, RSCALE, timezone history and iTIP, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 463/467, GPT-6 Sol 373/467.
