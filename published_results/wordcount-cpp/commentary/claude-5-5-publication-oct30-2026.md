# Reviewed Claude 5.5 collection, October 13-29, 2026 — wordcount-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `8d1c1b4c-901d-4a38-a6e8-9bd06ffe46a3`

- Score 46/46; status Complete.
- Failures: none
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `1a41c898-9648-4d0e-a324-e1b9439d8af4`

- Score 46/46; status Complete.
- Failures: none
- Network: none

### Sonnet 5.5 max — `cad7560f-a91a-446f-9e7f-aa778fa0cee8`

- Score 46/46; status Complete.
- Failures: 0.
- Network: None detected.
- Harness 0.2.1 conditions; no subagents; modelUsage only claude-sonnet-5-5.

### Opus 5.5 max — `63866933-2957-4774-9912-4733a3c60b96`

- Score 46/46; status Complete.
- Failures: None.
- Network: None (no network commands; no WebFetch/WebSearch).
- Harness 0.2.2 conditions; no subagents; modelUsage only claude-opus-5-5; 1 result event. 32 task notifications completed, 3 failed (background shell tasks for unit tests, corpus generation and a sanitizer rerun, which the agent redid); none stopped.
- Same score as Sonnet WordCount C++ max (46/46), taking 74.4 min vs 31.8; most of the extra time went to performance work (prefetching, sharded tables, cgroup-aware threading).
