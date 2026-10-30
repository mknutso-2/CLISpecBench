# Reviewed Claude 5.5 collection, October 13-29, 2026 — bibtex-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `5ea908f9-fcd0-4d1f-966d-e836850a55a9`

- Score 379/386; status Complete.
- Failures: 7: warning$ messages expected as log warning entries (5) plus warning entry in log (1), from following bibtex.web; missing-vs-empty string distinction (1).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `d08db8b4-6a11-4299-97f4-f6f2a7144f1b`

- Score 379/386; status Complete.
- Failures: 7: warning$ messages expected as log entries (6), missing-vs-empty string distinction (1).
- Network: none

### Sonnet 5.5 max — `7d94f9db-5acb-4da1-83fe-d2038c34e53a`

- Score 377/386; status Complete.
- Failures: 9: five warning$-log tests and warning entry in log (agent disclosed that warning$ output is not reported), two chr.to.int$ wrong-length type-error tests, missing-vs-empty string distinction.
- Network: Downloaded texlive-binaries/libkpathsea6/texlive-base .debs from archive.ubuntu.com and xampl.bib plus contributed .bst files from mirrors.ctan.org as a test oracle (web-enabled condition; disclose).
- Harness 0.2.0 conditions. One malformed lowercase 'bash' tool call, harmless; no subagents; all models claude-sonnet-5-5.

### Opus 5.5 max — `ff56b6c4-13ed-4d69-b8f2-56d151ac54bd`

- Score 379/386; status Complete.
- Failures: 7: the same warning$-log and missing-vs-empty family as Opus BibTeX C++ and JS max.
- Network: Downloaded the TeX Live bibtex binary and bibtex.ch/texmf.cnf sources and large public bibliographies as test oracles (12 network commands) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; no subagents; modelUsage only claude-opus-5-5.
- Equal to Opus BibTeX Python high (379/386).
