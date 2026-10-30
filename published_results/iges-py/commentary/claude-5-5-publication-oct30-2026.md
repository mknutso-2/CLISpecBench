# Reviewed Claude 5.5 collection, October 13-29, 2026 — iges-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `d1735207-f7f8-4382-a775-9ac5ead16ae8`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith after a defaulted string control should be rejected (same as C++ and JS).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `df1cc2be-9d97-4423-93b1-d7d08a5f973c`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith after a defaulted string control should be rejected.
- Network: none

### Sonnet 5.5 max — `59b211f4-7cc5-4a6d-9258-8a331fc2f372`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control (the same single failure as Sonnet IGES C++ and JS max). Not mentioned.
- Network: WebSearch x3 and WebFetch x28 (Eclipse wiki, STEPtools igeslib schema pages, OCCT IGES reader sources on GitHub), plus curl downloads (web-enabled condition; disclose).
- Harness 0.2.1: the heaviest web-tool use so far, yet modelUsage lists only claude-sonnet-5-5. This confirms the helper-model fix in a real run.
- Retry of sonnet-iges-py-max-interrupted1 (infra_other: Docker unreachable at launch, never started).
- Five same-model Agent subagents, 12 ListAgents, 13 Monitor and 1 TaskStop. One malformed tool call, harmless.
- $90.77 in 166 min; started at 23:43 at 2% of the five-hour window and ended at 83%.

### Opus 5.5 max — `44cc01f6-f4a1-42b0-9234-5986c1cdcff2`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control. Not mentioned.
- Network: Downloaded public IGES CAD files from GitHub repos (pyiges, OpenCASCADE, pythonocc, FreeCAD-library and others) (9 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; no subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- Same score as Opus IGES Python high (248/249).
