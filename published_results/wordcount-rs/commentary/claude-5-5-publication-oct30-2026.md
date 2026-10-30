# Reviewed Claude 5.5 collection, October 13-29, 2026 — wordcount-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `bc3fd756-0388-4e04-b3e6-bd96c2c1795e`

- Score 46/46; status Complete.
- Failures: none
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `d21f2ff7-9232-473f-8658-4d40f726fb4f`

- Score 46/46; status Complete.
- Failures: none
- Network: Bash: ls ~/.rustup ~/.cargo 2>&1 | head; ls /usr/local/cargo /usr/local/rustup 2>&1 | head; curl -sI https://static.rust-lang.org | head -1

### Sonnet 5.5 max — `6646fbd0-5aec-42cd-ad19-c681b50e6f9a`

- Score 46/46; status Complete.
- Failures: 0.
- Network: None detected.
- Harness 0.2.1 conditions; cargo on PATH (69 invocations, none not found); no stopped background subagents; modelUsage only claude-sonnet-5-5.
- Far longer and costlier than the other WordCount max runs (105 min, $21.31 vs 19-48 min, $2.74-4.67): 179 turns and 187 Bash calls of extra verification for the same perfect score.
- Completes Sonnet max: all eight evals, four languages.

### Opus 5.5 max — `f764f84d-999d-4b15-9459-ce5aa08f117d`

- Score 46/46; status Complete.
- Failures: None.
- Network: rustup component add rustfmt clippy, rustup toolchain install 1.70.0 --profile minimal (later uninstalled), and a rustup self-update to 1.29.2, all to check formatting, lints and older-Rust builds; no crates added; no WebFetch/WebSearch (web-enabled condition; disclose).
- Harness 0.2.2 conditions; no subagents; modelUsage only claude-opus-5-5; 1 result event. 28 task notifications completed, 1 failed (a background benchmark shell task, which the agent redid); none stopped.
- cargo was available and used (24 cargo commands).
- Same score as Sonnet WordCount Rust max (46/46), in 42.5 min vs 105.2.
