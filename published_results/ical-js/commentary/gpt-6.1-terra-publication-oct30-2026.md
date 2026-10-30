# Reviewed GPT-6.1 Terra collection, October 29, 2026 — ical-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `0a5f0d7b-c2f8-49a7-bd2e-6dc3e37f4dee`

- Score 462/467; status Complete.
- Failures: 5: two EXRULE cases (monthly second Friday; combined with EXDATE), two iTIP method rules (CANCEL STATUS must be CANCELLED if present; ADD forbids RECURRENCE-ID), and an RDATE period ending before its start should warn. Not mentioned.
- Network: None by the agent. API-only audit: chatgpt.com 73 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 80 commands; files written through shell commands; non-partial token accounting.
- Known frozen-suite caveats for ICal 3.0.5 (raw-property projection and the invalid UNTIL fixture) apply; none of these five failures is one of them.
- Compared with published max runs: GPT-6.1 Sol 463/467, GPT-6 Sol 458/467, GPT-5.6 Terra 447/467.

### GPT-6.1 Terra high — `4eccb3a7-1723-4384-ba40-10e92a2414ab`

- Score 458/467; status Incomplete.
- Failures: 9, in RSCALE and advanced recurrence/historical timezone cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 463/467, GPT-6 Sol 448/467.

### GPT-6.1 Terra low — `e46bbecb-57ff-425e-8e24-a3f2d375de9f`

- Score 451/467; status Incomplete.
- Failures: 16, in RSCALE, recurrence, timezones, overrides and warnings, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 465/467, GPT-6 Sol 424/467.
