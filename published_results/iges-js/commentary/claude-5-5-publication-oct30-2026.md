# Reviewed Claude 5.5 collection, October 13-29, 2026 — iges-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `125b859b-0406-4e1f-9131-d2266e46bacf`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith after a defaulted string control should be rejected (same as the C++ run).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `a4891cb0-1ed9-408b-9d1f-f1187b32f189`

- Score 249/249; status Complete.
- Failures: none
- Network: none
- Called ScheduleWakeup twice while a same-model review subagent ran, but the subagent completed before the session ended, so the CLI delivered its notification and the agent fixed three issues it found (mirrored normals, clip_planes, terminate-count handling) in a follow-up turn.

### Sonnet 5.5 max — `11333887-1340-4761-afd9-b4d602e26b39`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control (the same single failure as Sonnet IGES C++ max). Not mentioned; the agent said Hollerith counts are enforced.
- Network: Downloaded public IGES sample files from many GitHub repos, pip-installed cadquery-ocp (OpenCascade) as an oracle and npm-installed eslint for linting; no WebFetch/WebSearch (web-enabled condition; disclose).
- First run under harness 0.2.1: container had ANTHROPIC_SMALL_FAST_MODEL and ANTHROPIC_DEFAULT_HAIKU_MODEL set to claude-sonnet-5-5; modelUsage lists only claude-sonnet-5-5.
- Two same-model Agent subagents and 14 ListAgents calls. One malformed tool call, harmless.

### Opus 5.5 max — `b412e95e-3bcb-43f2-8173-a6183c26ae37`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control. Not mentioned.
- Network: Downloaded public IGES CAD files from GitHub repos (OpenCASCADE, pythonocc and others) (10 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; no subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- Started at 08:23 under the weekly straddle rule, 37 minutes before the 09:00 weekly reset; the weekly window then reset to 1%.
- 1 below Opus IGES JS high (249/249).
