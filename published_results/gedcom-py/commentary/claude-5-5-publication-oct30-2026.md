# Reviewed Claude 5.5 collection, October 13-29, 2026 — gedcom-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `99c4ce0a-5bfb-4270-a9d4-c51819bd8e4c`

- Score 201/212; status Complete.
- Failures: 11, identical to the C++ run: family back-links (6), empty individual (2), lat/long payloads (2), shared note without payload (1).
- Network: None (no network commands; no WebFetch/WebSearch).
- Generated its structure table from the spec HTML. Reported technical-requirements-prompt.md missing but used the contract in prompt.md (where its content is appended).

### Opus 5.5 high — `f62c6716-0f64-4393-a14e-cf96b4d3ff59`

- Score 212/212; status Complete.
- Failures: none
- Network: none

### Sonnet 5.5 max — `59e2ed72-a153-4e15-8a2f-1cae8e3cb40d`

- Score 202/212; status Complete.
- Failures: 10: FAMS/FAMC back-links (6), empty individual (2) and shared-note payload (1), all disclosed as deliberately unenforced; one GEDZIP test (reserved gedcom.ged entry referenced as a local FILE) not mentioned.
- Network: Fetched the GEDCOM 7 HTML spec and official test files from gedcom.io and GitHub (FamilySearch GEDCOM.io, GEDCOM-registries), and downloaded python-build-standalone CPython 3.11 and 3.13 builds from GitHub releases to test on extra Python versions (web-enabled condition; disclose).
- Harness 0.2.0 conditions. One same-model Agent subagent and one SendMessage; stream, native and modelUsage all claude-sonnet-5-5.
- Started at 11:09, just before the 11:20 five-hour reset; used about 50% of the new window.

### Opus 5.5 max — `0607f7c6-ab2e-46b3-8205-eb043abf65d7`

- Score 203/212; status Complete.
- Failures: 9: FAMS/FAMC back-links (6), empty individual structure (2) and shared-note payload (1) — the same set as Sonnet GEDCOM C++/Python max.
- Network: Fetched GEDCOM sample files and reference material by curl (13 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; no subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- 9 below Opus GEDCOM Python high (212/212).
