# Reviewed Claude 5.5 collection, October 13-29, 2026 — wordcount-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `bbf58146-f0c1-45b0-b22a-101f41e0898e`

- Score 46/46; status Complete.
- Failures: none
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `31c8a9cf-83bb-4740-8b05-f89256b51791`

- Score 46/46; status Complete.
- Failures: none
- Network: none

### Sonnet 5.5 max — `65b10098-5b4d-4950-a344-c1f3a05a2c59`

- Score 46/46; status Complete.
- Failures: 0.
- Network: None detected.
- Harness 0.2.1 conditions; no subagents; modelUsage only claude-sonnet-5-5.

### Opus 5.5 max — `89624237-c4b3-456b-867c-b7f1a2361bb9`

- Score 46/46; status Incomplete.
- Failures: None.
- Network: None (no network commands; no WebFetch/WebSearch).
- Harness 0.2.2 conditions; one background review subagent on claude-opus-5-5; modelUsage only claude-opus-5-5; 1 result event. 30 task notifications completed, 2 stopped.
- Queued for one rerun at the end under the 2026-10-24 'Keep, rerun at end' decision for background-stop runs, keeping both attempts.
- Same score as Sonnet WordCount JS max (46/46).

### Opus 5.5 max (rerun) — `e6d33b8d-d846-45ad-b494-52461102c105`

- Score 46/46; status Complete.
- Failures: None.
- Network: None (no network commands; no WebFetch/WebSearch).
- Rerun of opus-wordcount-js-max (46/46, Incomplete, background subagent stopped) under the 2026-10-24 'Keep, rerun at end' decision; both attempts kept. Same score as the first attempt.
- Harness 0.2.2 conditions; no subagents this time; modelUsage only claude-opus-5-5; 1 result event. 7 task notifications, all completed; none stopped.
