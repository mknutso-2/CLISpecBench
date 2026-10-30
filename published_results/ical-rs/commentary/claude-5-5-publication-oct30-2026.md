# Reviewed Claude 5.5 collection, October 13-29, 2026 — ical-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `01e80b13-770c-43a9-9d0e-f26b56cb000c`

- Score 461/467; status Complete.
- Failures: 6: DST gap / half-hour gap pre-transition offset (2; it openly chose the post-transition offset), iTIP CANCEL STATUS and ADD RECURRENCE-ID (2), EXDATE before override (1), RDATE PERIOD end-before-start warning (1).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `28c33aaf-e211-49b0-b3d4-f6d4fdd50e6b`

- Score 464/467; status Complete.
- Failures: 3: iTIP ADD RECURRENCE-ID (1), EXDATE before override (1), RDATE PERIOD end-before-start warning (1).
- Network: pip-installed python-dateutil into /tmp as a cross-check oracle (web-enabled condition); not part of the submission.
- Two same-model subagents (calendar module, spec review) both completed; follow-up results processed normally (turns 53, 2, 6). No ScheduleWakeup.

### Sonnet 5.5 max — `1993477b-bcfa-4bff-ab34-0e8be754d9af`

- Score 464/467; status Complete.
- Failures: 3, the same as Sonnet ICal Python max: iTIP CANCEL STATUS must be CANCELLED, iTIP ADD forbids RECURRENCE-ID, RDATE PERIOD end-before-start warning. Not specifically disclosed.
- Network: pip-installed python-dateutil, icalendar and recurring-ical-events as test oracles (web-enabled condition; disclose).
- Harness 0.2.0 conditions; cargo on PATH: 26 cargo invocations, no cargo-not-found errors.
- Five result events (turns 203, 1, 1, 1, 1): the follow-ups are Monitor completions re-invoking the agent, not ScheduleWakeup. The graded source is from the end of the session.
- One same-model Agent subagent; stream, native and modelUsage all claude-sonnet-5-5.

### Opus 5.5 max — `c5bf08bb-21c1-4f87-950d-1a5f12d54071`

- Score 465/467; status Complete.
- Failures: 2, the same as Opus ICal C++ and JS max: iTIP ADD forbids RECURRENCE-ID, and the RDATE PERIOD end-before-start warning. Not specifically mentioned.
- Network: pip-installed python-dateutil into a venv as an oracle (2 network commands) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; cargo on PATH (38 invocations, none not found); no subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- Started under the weekly final-stretch rule at 81% weekly; ended with the weekly window at 86%.
- Above Opus ICal Rust high (464/467).
