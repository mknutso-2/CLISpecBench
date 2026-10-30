# Reviewed Claude 5.5 collection, October 13-29, 2026 — ical-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `64ac5c67-e23a-4a88-aecb-724e3a41e970`

- Score 461/467; status Complete.
- Failures: 6: DST gap / one-off half-hour gap should use the pre-transition offset (2), iTIP CANCEL STATUS and ADD RECURRENCE-ID (2), EXDATE must remove before an override replaces (1), RDATE PERIOD end-before-start warning (1).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `17dcbe11-e008-4482-ac88-ec342ff25762`

- Score 464/467; status Incomplete.
- Failures: 3: iTIP CANCEL STATUS and ADD RECURRENCE-ID (2), RDATE PERIOD end-before-start warning (1).
- Network: pip-installed python-dateutil into /tmp for cross-checking (web-enabled condition); not part of the submission.
- The agent started a background same-model subagent, called ScheduleWakeup (delay 1200 s), and ended its turn. The CLI's tool result told it the harness would re-invoke it on the wakeup or task notification, but headless --print sessions end instead: the CLI killed the subagent and never resumed. Same trap as published Opus RS274 C++ high and four Haiku 5.5 max runs; treated consistently as a completed model run labeled Incomplete, with disclosure.

### Sonnet 5.5 max — `fc0361a7-37cd-4205-9165-3d2012d9e631`

- Score 463/467; status Complete.
- Failures: 4, the same four as Sonnet ICal C++ max: iTIP CANCEL STATUS must be CANCELLED, iTIP ADD forbids RECURRENCE-ID, EXDATE-before-override ordering, and an RDATE PERIOD with end before start should warn. Not specifically disclosed.
- Network: pip-installed python-dateutil, icalendar, recurring-ical-events, convertdate and lunardate as test oracles (web-enabled condition; disclose).
- Harness 0.2.0 conditions. Two same-model Agent subagents, 9 ListAgents and 2 SendMessage calls; stream, native and modelUsage all claude-sonnet-5-5. One malformed tool call, harmless.

### Opus 5.5 max — `c63bf483-ac70-4c12-b852-8aeb377dee9c`

- Score 465/467; status Complete.
- Failures: 2, the same as Opus ICal C++ max: iTIP ADD forbids RECURRENCE-ID, and the RDATE PERIOD end-before-start warning. Not specifically mentioned.
- Network: None detected.
- Harness 0.2.1 conditions; three same-model subagents; modelUsage only claude-opus-5-5.
- Eight result events (turns 128, 4, 3, 4, 56, 3, 3, 9) from background-task re-invocations; the final result is the full summary. Two background tasks were stopped by the agent itself (TaskStop x2) mid-run; no session-end cutoff.
- Above Opus ICal JS high (464/467, Incomplete); this max run completed normally.
