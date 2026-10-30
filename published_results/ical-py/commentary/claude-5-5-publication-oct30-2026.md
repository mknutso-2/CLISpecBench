# Reviewed Claude 5.5 collection, October 13-29, 2026 — ical-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `73fa2c81-d289-4f0c-ae2c-0e7962e52f0e`

- Score 460/467; status Complete.
- Failures: 7: DST gap / half-hour gap pre-transition offset (2), iTIP CANCEL STATUS and ADD RECURRENCE-ID (2), EXDATE before override (1), RDATE PERIOD end-before-start warning (1), calendar IMAGE DISPLAY comma list (1).
- Network: Network commands: Bash: ls; rm -f *.whl; mkdir -p /tmp/dep && pip install --target /tmp/dep python-dateutil 2>&1 | tail -1; ls /workspace; web tool requests: 0.
- Installed python-dateutil outside output/ (web-enabled condition) purely to cross-check its RRULE engine on ~3,000 random rules; the submission itself uses only the standard library.

### Opus 5.5 high — `55aa38de-d177-4f58-9fda-c6d5490259a0`

- Score 463/467; status Complete.
- Failures: 4: iTIP CANCEL STATUS and ADD RECURRENCE-ID (2), EXDATE before override (1), RDATE PERIOD end-before-start warning (1).
- Network: pip-installed python-dateutil into /tmp as a cross-check oracle (web-enabled condition); not part of the submission.
- Delegated the non-Gregorian calendar module to a same-model subagent that completed normally; no ScheduleWakeup.

### Sonnet 5.5 max — `f4b3b61e-ec78-4dde-994d-8b73f5832533`

- Score 464/467; status Complete.
- Failures: 3 of the four seen in the C++ and JS runs (iTIP CANCEL STATUS must be CANCELLED, iTIP ADD forbids RECURRENCE-ID, RDATE PERIOD end-before-start warning); it passed the EXDATE-before-override ordering test. Not specifically disclosed.
- Network: pip-installed python-dateutil, convertdate, lunardate, icalendar, recurring-ical-events, ephem, sxtwl, lunar-python, uv and pyflakes into a throwaway venv, and used uv to download CPython 3.11 for testing (web-enabled condition; disclose).
- Harness 0.2.0 conditions. No subagents; stream, native and modelUsage all claude-sonnet-5-5.
- Cheapest ICal max run so far ($23.15).

### Opus 5.5 max — `d6d651a3-4225-4166-b677-e31692eac6af`

- Score 466/467; status Complete.
- Failures: 1: iTIP ADD forbids RECURRENCE-ID. Not specifically mentioned.
- Network: pip-installed python-dateutil and pyflakes into a target directory (2 network commands) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; no subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- Best ICal score in this collection: 466/467, above Opus ICal Python high (463/467). Only $24.61 in 71 min.
