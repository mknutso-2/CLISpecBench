# Reviewed Claude 5.5 collection, October 13-29, 2026 — gedcom-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `ce2ef6c2-368c-4ceb-a35b-5b8323f53e37`

- Score 190/212; status Complete.
- Failures: 22, mostly render-time validation: pointers to wrong record types (5), family back-links (6), empty individual (2), lat/long and datatype payloads (3), duplicate xref, shared note without payload, NAME TRAN without LANG, multimedia FILE/FORM and top-level TITL, submitter without NAME.
- Network: None (no network commands; no WebFetch/WebSearch).
- Second GEDCOM agent to report technical-requirements-prompt.md missing from the workspace; its content is appended to prompt.md. Same prompt hash as published runs.

### Opus 5.5 high — `bec0d398-ab93-4efc-9306-bd5fac632642`

- Score 212/212; status Complete.
- Failures: none
- Network: none

### Sonnet 5.5 max — `3ff9d3d5-fe8b-4713-838e-8a3517132dfc`

- Score 191/212; status Complete.
- Failures: 21: FAMS/FAMC back-links (6), empty individual (2) and shared-note payload (1) were disclosed as deliberately unenforced; render-side record validation (wrong pointer target type x5, name TRAN without LANG, OBJE without FILE.FORM or with top-level TITL, SUBM without NAME, invalid datatype payloads) and latitude/longitude payload checks (2) were not mentioned.
- Network: Fetched FamilySearch GEDCOM and GEDCOM.io repo files and test files, the gedcom7code js-gedcom validator, GEDCOM-registries data and ArmidaleSoftware gedcom7 sources from GitHub, and tried pip install of gedcom7 packages (web-enabled condition; disclose).
- Rerun after sonnet-gedcom-js-max-interrupted1 (infra_usage_cap, 207/212 at the cap, excluded). This attempt scored lower than the capped one; the capped score is not a model result and must not be used.
- Harness 0.2.0 conditions. Two same-model Agent subagents, 11 ListAgents and 4 SendMessage calls; stream, native and modelUsage all claude-sonnet-5-5.
- Wrote a memory note inside the container's own ~/.claude; no host effect.
- Used about 67% of a five-hour window in 92 min (~0.73%/min).

### Opus 5.5 max — `0d4739fd-f0c5-45fc-a94b-52f04487b24c`

- Score 204/212; status Incomplete.
- Failures: 8: FAMS/FAMC back-link validation for HUSB/WIFE/CHIL in inspect and render (6) and latitude/longitude payload validation (2).
- Network: Fetched GEDCOM sample files and reference material by curl (11 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness artifact: the background-subagent variant of the ScheduleWakeup trap, the second under harness 0.2.1 after sonnet-iges-rs-max. Six earlier background tasks completed normally; the review agent was stopped when the main turn ended.
- Harness 0.2.1 conditions; one same-model subagent; modelUsage only claude-opus-5-5.
- 8 below Opus GEDCOM JS high (212/212). The failing back-link rule is one a final pass might have added, but the run ended before any final pass.

### Opus 5.5 max (rerun) — `9fb36a60-9d5d-40b8-9da3-256958c31e5d`

- Score 203/212; status Complete.
- Failures: 9, all in test_validation.py: FAMS/FAMC back-link validation for HUSB/WIFE/CHIL in inspect and render (6), shared note record requires payload (1), empty individual structure rejected in inspect and render (2). The last message names all three as rules it deliberately does not enforce because official sample files break them.
- Network: curl downloads of FamilySearch's published GEDCOM 7 test files and machine-readable spec tables (raw.githubusercontent.com and api.github.com for FamilySearch/GEDCOM.io, FamilySearch/GEDCOM and gedcom7code/test-files), used for checking only; disclosed in the last message; no WebFetch/WebSearch (web-enabled condition; disclose).
- Rerun of opus-gedcom-js-max (204/212, Incomplete, background subagent stopped) under the 2026-10-24 'Keep, rerun at end' decision; both attempts kept. One test lower than the first attempt.
- Harness 0.2.2 conditions. Two background same-model review subagents; modelUsage only claude-opus-5-5. The agent kept backup timer tasks running so notifications re-invoked it until both reviewers reported; 4 result events. 18 task notifications completed, 1 failed (a background regex timing task), 1 stopped by the agent itself with TaskStop ('Test validators for regex backtracking blowups'), not by the CLI at turn end.
- The stored last message is the final summary written after both reviews and the fixes.
