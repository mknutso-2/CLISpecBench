# Reviewed Claude 5.5 collection, October 13-29, 2026 — bibtex-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `6ec17dc8-5c4e-4971-8dda-a1aced50f17a`

- Score 384/386; status Complete.
- Failures: 2: pending output-buffer text should be discarded at end of run (agent flushed it per summary.md and said real BibTeX drops it), missing-vs-empty string distinction in one built-in.
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `e78ac770-b1d5-45f9-8813-1ace4bf58414`

- Score 377/386; status Complete.
- Failures: 9: warning$ messages expected as log warning entries (6, where the hidden tests follow summary.md rather than real BibTeX), chr.to.int$ wrong-length type error (2), missing-vs-empty string distinction (1).
- Network: Under the historical web-enabled condition, used Bash curl/apt-get/dpkg -x (not WebSearch/WebFetch, so web_requests=0) to download Ubuntu texlive-binaries and texlive-base 2023 packages, extract the real BibTeX 0.99d and use it as a differential reference oracle; also downloaded public .bib files from CTAN and ftp.math.utah.edu. Nothing was added to the submission. Disclose in publication commentary.

### Sonnet 5.5 max — `64c41964-1652-445c-9109-c335e532e16d`

- Score 378/386; status Complete.
- Failures: 8: five warning$-log tests (agent deliberately kept warning$ messages out of the JSON warnings because none of the seven kinds fit, and disclosed it), missing-vs-empty string distinction, warning entry in log, and pending output written at end of run (agent followed the task contract over real BibTeX and disclosed it).
- Network: Downloaded Ubuntu noble package indexes and texlive-binaries/texlive-base/texlive-bibtex-extra .debs from archive.ubuntu.com to use the real bibtex as a test oracle (web-enabled condition; disclose).
- Ran under harness 0.1.0 conditions (ScheduleWakeup offered, unused; C++ so the Rust PATH defect is irrelevant). result.json says harness_version 0.2.0 only because the package was bumped to 0.2.0 while this run was finishing; correct to 0.1.0 at publication.
- Retry of the attempt interrupted by the WSL disk-full freeze (sonnet-bibtex-cpp-max-interrupted1, infra_other).
- Used Monitor 4 times and one same-model Agent subagent; all models claude-sonnet-5-5.
- Published with harness_version 0.1.0: the run ran under 0.1.0 conditions; the result was stamped 0.2.0 only because the package was bumped while it was finishing.

### Opus 5.5 max — `68a31a88-1d81-4396-b162-1e851fc1958e`

- Score 379/386; status Complete.
- Failures: 7: five warning$-log tests, warning entry in log, and missing-vs-empty string distinction; the same family as the Sonnet BibTeX max runs.
- Network: Downloaded TeX Live bibtex binaries from mirror.ctan.org, TeX-Live texlive-source files and tags from GitHub, real .bib databases and CTAN style packages as test oracles (web-enabled condition; disclose).
- First Opus max run under harness 0.2.1: container had the subagent and helper models set to claude-opus-5-5; modelUsage only claude-opus-5-5; no subagents.
- Above Opus BibTeX C++ high (377/386).
