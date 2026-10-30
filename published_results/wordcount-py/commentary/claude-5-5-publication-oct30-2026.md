# Reviewed Claude 5.5 collection, October 13-29, 2026 — wordcount-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `2893f568-dab1-4dff-990d-e30a41745614`

- Score 46/46; status Complete.
- Failures: none
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `de09245f-2dca-47ce-b82f-f9b117cdb87a`

- Score 46/46; status Complete.
- Failures: none
- Network: none

### Sonnet 5.5 max — `4663093f-695e-452d-9a6e-b8028a120230`

- Score 46/46; status Complete.
- Failures: 0.
- Network: None detected.
- Harness 0.2.1 conditions; no subagents; modelUsage only claude-sonnet-5-5.

### Opus 5.5 max — `2c0ef1c6-d4d0-4889-b4b2-8a2612f7d8ba`

- Score 46/46; status Incomplete.
- Failures: None.
- Network: None (no network commands; no WebFetch/WebSearch).
- Harness 0.2.2 conditions; one background review subagent on claude-opus-5-5; modelUsage only claude-opus-5-5; 1 result event. 15 task notifications completed, 2 stopped.
- Queued for one rerun at the end under the 2026-10-24 'Keep, rerun at end' decision for background-stop runs, keeping both attempts.
- Same score as Sonnet WordCount Python max (46/46).

### Opus 5.5 max (rerun) — `38b424e2-cf70-42a5-85c7-ba4eb72eaa96`

- Score 46/46; status Complete.
- Failures: None.
- Network: None (no network commands; no WebFetch/WebSearch).
- Rerun of opus-wordcount-py-max (46/46, Incomplete, background subagent stopped) under the 2026-10-24 'Keep, rerun at end' decision; both attempts kept. Same score as the first attempt.
- Harness 0.2.2 conditions; no subagents this time (the 'final review' was the agent's own); modelUsage only claude-opus-5-5; 1 result event. 12 task notifications completed, 1 failed (a background timing and memory measurement task); none stopped.
