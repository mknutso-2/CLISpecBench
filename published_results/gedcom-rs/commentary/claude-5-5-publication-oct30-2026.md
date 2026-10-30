# Reviewed Claude 5.5 collection, October 13-29, 2026 — gedcom-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `64340df7-b95e-455c-82fe-81d73f7ca083`

- Score 189/212; status Complete.
- Failures: 23, mostly render-time validation (same profile as the JS run): wrong-record-type pointers (5), family back-links (6), empty individual (2), lat/long and datatype payloads (3), duplicate xref, shared note payload, NAME TRAN without LANG, multimedia FILE/FORM and TITL, submitter NAME, plus a GEDZIP reserved-entry check.
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `db8006dc-27f8-4b42-a0a5-52d55e8e6e16`

- Score 210/212; status Complete.
- Failures: 2: latitude/longitude payload validation.
- Network: none

### Sonnet 5.5 max — `4e74884c-8ac2-43cf-8fff-e245fa307337`

- Score 212/212; status Complete.
- Failures: 0.
- Network: None detected.
- No evidence of hidden-test access: the only test-name match (test_gedzip) is in the agent's own and its subagents' test scripts under /tmp/refs and /workspace/output/tests.
- Harness 0.2.0 conditions; first Rust run of GEDCOM with cargo on PATH. Seven same-model Agent subagents; stream, native and modelUsage all claude-sonnet-5-5.
- Two malformed tool calls (bash, bash_placeholder), harmless.
- Heaviest max run so far: $83.41, 125 min; started at 15:52 just before the 16:20 five-hour reset and ended at 83% of the new window.
- At session end the CLI stopped one still-running background subagent ('Independent pragmatic reference implementation') after the agent's complete final summary. The agent did not report pending work, so the run stays Complete.

### Opus 5.5 max — `5e0af7e6-c495-4d04-9c5d-5813af25591f`

- Score 212/212; status Complete.
- Failures: 0.
- Network: Fetched FamilySearch GEDCOM sample files from GitHub (10 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- No evidence of hidden-test access: no references to hidden test files, Evals/GEDCOM or CLISpecBench in the transcript.
- Harness 0.2.1 conditions; cargo on PATH (28 invocations, none not found); no subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- Above Opus GEDCOM Rust high (210/212). First cell after the 2026-10-24 host restart; it started at 01:00 on 2026-10-25.
