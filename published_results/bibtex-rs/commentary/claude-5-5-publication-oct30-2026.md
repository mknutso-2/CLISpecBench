# Reviewed Claude 5.5 collection, October 13-29, 2026 — bibtex-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `7464c968-32e3-41a1-bb41-d5ab014bcd46`

- Score 376/386; status Complete.
- Failures: 10: warning$ messages expected as log warning entries (6), chr.to.int$ on a multi-character or wrong-length string should be a type error (2), pending output-buffer text should be discarded at end of run (1), missing-vs-empty string distinction (1).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `7f28496c-a476-4095-a4bb-697c58383d85`

- Score 377/386; status Complete.
- Failures: 9: warning$ messages expected as log entries (6), chr.to.int$ wrong-length type error (2), missing-vs-empty string distinction (1).
- Network: Under the web-enabled condition, used Bash curl to download Ubuntu TeX Live 2023 bibtex 0.99d into /tmp as a differential reference and ran 111 TeX Live .bib files through it; nothing added to the submission. Disclose in commentary.

### Sonnet 5.5 max — `588f0c2d-1d36-400f-85ea-36e7921e3896`

- Score 377/386; status Complete.
- Failures: 9: five warning$-log tests and warning entry in log, two chr.to.int$ wrong-length type-error tests, missing-vs-empty string distinction. Same family as Sonnet BibTeX Python max.
- Network: Downloaded texlive-binaries .debs from archive.ubuntu.com, many .bst/.bib files from mirrors.ctan.org, and sample .bib files from raw.githubusercontent.com (biber, pandoc) as test oracles and inputs (web-enabled condition; disclose).
- First Rust run with the 0.2.0 PATH fix: 26 cargo invocations, no PATH workarounds or cargo-not-found errors. The only 'command not found' was xxd, which the image lacks.
- Monitor used 17 times; one malformed 'bash_placeholder' tool call, harmless; no subagents; all models claude-sonnet-5-5.

### Opus 5.5 max — `2ee8abfc-453c-48d2-b285-b3ab3f538404`

- Score 379/386; status Complete.
- Failures: 7: the same warning$-log and missing-vs-empty family as the other Opus BibTeX max runs.
- Network: Downloaded BibTeX/kpathsea binaries from mirror.ctan.org as a test oracle (5 network commands) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; cargo on PATH (12 invocations, none not found); no subagents; modelUsage only claude-opus-5-5.
- Above Opus BibTeX Rust high (377/386). Opus BibTeX max: 379 in all four languages.
