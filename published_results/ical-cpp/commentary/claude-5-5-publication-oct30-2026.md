# Reviewed Claude 5.5 collection, October 13-29, 2026 — ical-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `ab112967-97ba-4e2c-b06d-397320795e60`

- Score 462/467; status Complete.
- Failures: 5: iTIP CANCEL STATUS and ADD RECURRENCE-ID rules (2), RDATE PERIOD with end before start should warn (1), orphan RECURRENCE-ID overrides on VTODO/VJOURNAL should warn (2).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `848d6af5-ad88-43b4-aa40-b09541a3e92c`

- Score 465/467; status Incomplete.
- Failures: 2: iTIP ADD must forbid RECURRENCE-ID (1), RDATE PERIOD end-before-start warning (1).
- Network: none
- The agent started a background same-model subagent, called ScheduleWakeup (delay 1200 s), and ended its turn. The CLI's tool result told it the harness would re-invoke it on the wakeup or task notification, but headless --print sessions end instead: the CLI killed the subagent and never resumed. Same trap as published Opus RS274 C++ high and four Haiku 5.5 max runs; treated consistently as a completed model run labeled Incomplete, with disclosure.

### Sonnet 5.5 max — `9bdb926e-01fd-4487-a305-3242d23cb2ca`

- Score 463/467; status Complete.
- Failures: 4: iTIP CANCEL STATUS must be CANCELLED, iTIP ADD forbids RECURRENCE-ID, EXDATE-before-override ordering, and an RDATE PERIOD with end before start should warn. None was specifically disclosed; the agent did disclose iTIP table and RDATE/EXDATE/COUNT choices in general terms.
- Network: pip-installed python-dateutil, icalendar, recurring-ical-events, convertdate, lunardate and korean_lunar_calendar into a venv as test oracles, and fetched libical's icalrecur.c from GitHub (web-enabled condition; disclose).
- Harness 0.2.0 conditions. Five same-model Agent subagents, 29 ListAgents and 5 SendMessage calls; stream, native and modelUsage all claude-sonnet-5-5. Three malformed tool calls, harmless.
- Longest max run so far (195 min) and did not hit the five-hour cap. It started at 21:24, just after the 21:20 reset.
- Ended with C: at 24 GB free, so the 30 GB disk gate held the next cell; the space was mostly another project's temp files, not this run.

### Opus 5.5 max — `d58c38d5-b9c2-48ac-94af-d2d561f9595a`

- Score 465/467; status Complete.
- Failures: 2: iTIP ADD forbids RECURRENCE-ID, and an RDATE PERIOD with end before start should warn. Neither was specifically mentioned; it said its iTIP checks follow the RFC 5546 tables literally.
- Network: pip-installed oracle libraries (python-dateutil, ephem, convertdate and others) into a venv (4 network commands) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; two same-model subagents; modelUsage only claude-opus-5-5.
- One background Monitor ('adversarial tester activity') shows status 'stopped' mid-run, before the final result; it is the agent's own watcher, not a session-end cutoff. The final summary is complete.
- Equal to Opus ICal C++ high (465/467, Incomplete); this max run completed normally.
