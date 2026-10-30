# Reviewed GPT-6.1 Terra collection, October 29, 2026 — ical-py

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `3ed80fd6-9154-4d03-bbfd-91dff2c58850`

- Score 461/467; status Complete.
- Failures: 6: the same two EXRULE cases, iTIP CANCEL STATUS and ADD RECURRENCE-ID rules and RDATE end-before-start warning as Terra ICal JS, plus an event before any VTIMEZONE observance DTSTART should use the earliest observance. Not mentioned.
- Network: One attempted curl of a Hong Kong Observatory calendar conversion table (www.hko.gov.hk, T2013e.txt) to check Chinese-calendar dates, denied by the API-only proxy; nothing was retrieved. Audit otherwise: chatgpt.com 128 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted fetch.
- Session turn context shows only gpt-6.1-terra; 1 turn; 99 commands; files written through shell commands; non-partial token accounting.
- Compared with published max runs: GPT-6.1 Sol 467/467, GPT-6 Sol 459/467, GPT-5.6 Terra 448/467.

### GPT-6.1 Terra high — `5f6ec874-2631-44d1-a978-cf261f0a0299`

- Score 460/467; status Incomplete.
- Failures: 7, in areas the last message lists (RSCALE, TZUNTIL, extension components, recurrence and iTIP edge cases).
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 463/467, GPT-6 Sol 459/467.

### GPT-6.1 Terra low — `c2094f07-251a-4b50-a942-919864de9940`

- Score 453/467; status Incomplete.
- Failures: 14, in RSCALE, historical timezones and iTIP, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 464/467, GPT-6 Sol 397/467.
