# Reviewed Claude 5.5 collection, October 13-29, 2026 — bibtex-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `253a76ca-17cd-4784-89c5-a9d94ab62ecc`

- Score 379/386; status Complete.
- Failures: 7: warning$ messages expected as log warning entries (5 tests; agent sent warning$ text to stderr only, a disclosed choice), missing-vs-empty string distinction (1), warning entry in log (1).
- Network: None (no network commands; no WebFetch/WebSearch).
- Two result events: main session 53 turns, then a 1-turn follow-up when the background review subagent finished. One call to a nonexistent lowercase 'bash' tool failed harmlessly.

### Opus 5.5 high — `8acb8c07-b8ea-494a-b3ad-1da8027df4ce`

- Score 379/386; status Complete.
- Failures: 7: warning$ messages expected as log entries (6, where the hidden tests follow summary.md over real BibTeX), missing-vs-empty string distinction (1).
- Network: Under the web-enabled condition, used Bash curl to download Ubuntu TeX Live BibTeX 0.99d as a differential reference, ten public .bib databases (CTAN, ftp.math.utah.edu) and texmf.cnf from tug.org; nothing added to the submission. Comparable reference downloads appear in published Haiku 5.5 high/max BibTeX runs. Disclose in commentary.

### Sonnet 5.5 max — `d5c55e7a-3f47-46fb-bc55-9ac369638b15`

- Score 379/386; status Complete.
- Failures: 7: five warning$-log tests and warning entry in log (agent mapped standard-style warning$ messages to bst_undefined_field only for 'empty X' cases and disclosed the choice), missing-vs-empty string distinction.
- Network: Downloaded texlive-binaries/libkpathsea6/texlive-base .debs from archive.ubuntu.com and the standard .bst/.bib files from mirrors.ctan.org as a test oracle (web-enabled condition; disclose).
- First run under harness 0.2.0: init tool list lacks ScheduleWakeup, Cron* and RemoteTrigger; launch command carries the image PATH.
- One TaskStop, no subagents; all models claude-sonnet-5-5.

### Opus 5.5 max — `064e7204-f328-4c90-9a01-2d8387143475`

- Score 379/386; status Complete.
- Failures: 7: the same warning$-log and missing-vs-empty family as Opus BibTeX C++ max.
- Network: Downloaded TeX Live bibtex sources/config from GitHub (TeX-Live texlive-source) and a BibTeX binary as a test oracle (7 network commands) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; no subagents; modelUsage only claude-opus-5-5.
- Equal to Opus BibTeX JS high (379/386).
