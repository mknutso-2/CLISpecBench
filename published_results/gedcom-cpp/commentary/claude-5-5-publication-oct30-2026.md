# Reviewed Claude 5.5 collection, October 13-29, 2026 — gedcom-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `e8eb3ae5-5797-4346-91a9-768c0bbd5496`

- Score 201/212; status Complete.
- Failures: 11: FAMS/FAMC back-link validation for HUSB/WIFE/CHIL in inspect and render (6), empty individual structure accepted (2), latitude/longitude payload validation (2), shared-note record without payload accepted (1).
- Network: None (no network commands; no WebFetch/WebSearch).
- The agent said technical-requirements-prompt.md was missing from the workspace. Its content is appended to prompt.md by the harness; base-prompt.md names the file. Same prompt hash as all published GEDCOM runs, so comparability is unaffected.

### Opus 5.5 high — `33c7d9fd-378b-4316-b86c-cf6ea233c9a7`

- Score 195/212; status Complete.
- Failures: 17, mostly render-time validation: wrong-record-type pointers (5), duplicate xref, shared note payload, NAME TRAN without LANG, multimedia FILE/FORM and TITL, submitter NAME, invalid datatype payloads, empty individual, and others.
- Network: Under the web-enabled condition, used Bash curl against the GitHub API to download FamilySearch's official GEDCOM 7 test files (23 .ged, 2 .gdz) from gedcom.io as extra validation input; nothing added to the submission. Disclose in commentary.

### Sonnet 5.5 max — `cc057492-160a-479d-a6e3-328d8c6d9771`

- Score 203/212; status Complete.
- Failures: 9: FAMS/FAMC back-link validation for HUSB/WIFE/CHIL in inspect and render (6), empty individual structure accepted (2), shared-note record without payload accepted (1). All three were disclosed as deliberate non-enforcement choices.
- Network: None detected.
- Harness 0.2.0 conditions. Invoked the bundled code-review skill once and one same-model Agent subagent; stream, native and modelUsage all claude-sonnet-5-5.
- Finished after the user paused collection; the STOP file then stopped the dispatcher before the next cell.

### Opus 5.5 max — `4d87b68e-e0e1-4a59-a01a-2e794abdd06a`

- Score 212/212; status Complete.
- Failures: 0.
- Network: Fetched FamilySearch GEDCOM 7 sample files and spec release tags from GitHub (10 network commands) (web-enabled condition; disclose).
- No evidence of hidden-test access: no references to hidden test files, Evals/GEDCOM or CLISpecBench in the transcript.
- Four result events (turns 153, 1, 8, 26) from background-task re-invocations; the final result is the full summary; no stopped subagents.
- Harness 0.2.1 conditions; two same-model subagents; modelUsage only claude-opus-5-5.
- Well above Opus GEDCOM C++ high (195/212).
