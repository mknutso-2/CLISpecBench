# Reviewed Claude 5.5 collection, October 13-29, 2026 — iges-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `a2bbb8f9-3d8e-4dec-b7f6-6bc551a5befe`

- Score 248/249; status Complete.
- Failures: 1: a zero-count Hollerith string after a defaulted string control should be rejected.
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `4539bc92-5886-4782-9719-b92087a734d7`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith after a defaulted string control should be rejected (the same single failure as all four Sonnet IGES runs).
- Network: none

### Sonnet 5.5 max — `43d2fb1d-445e-4ea7-9a5c-05a159edf98f`

- Score 248/249; status not published.
- Not published: held: cross-model sidecar requests (Haiku helper before harness 0.2.1).
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control. Not mentioned.
- Network: WebSearch x2 and WebFetch x15 (steptools igeslib docs, OCCT IGES reader sources on diyhpl.us and GitHub), plus curl of OCCT sources and IGES sample files from many GitHub repos (web-enabled condition; disclose).
- First run in this collection to use WebFetch/WebSearch; no other reviewed cell has any non-Sonnet modelUsage.
- Highest-cost max run so far: $110.75, 172 min; ended at 94% of the five-hour window.
- Two same-model Agent subagents. Preserved as-is; no rerun without the user's decision.

### Opus 5.5 max — `926b7214-e0ef-49d3-8459-80f9df02858f`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control (the same single failure as every Sonnet IGES run). Not mentioned.
- Network: None detected.
- Harness 0.2.1 conditions; no subagents, no web tools and no stopped background tasks; modelUsage only claude-opus-5-5.
- Equal to Opus IGES C++ high (248/249).
