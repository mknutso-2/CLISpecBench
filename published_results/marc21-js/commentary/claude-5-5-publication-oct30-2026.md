# Reviewed Claude 5.5 collection, October 13-29, 2026 — marc21-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `07a690e7-f746-4c19-8e63-36241f327ea5`

- Score 2865/2900; status Complete.
- Failures: 35, all fixed control-field validation: 007 category lengths (15), 008 date-entered fill/non-digit (13), 008 code tables and cataloging source (3), other 006/007/008 length/fill/code checks (4).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `4e41a8a8-6bb8-4bbb-bb0b-5b1baf5afdc2`

- Score 2857/2900; status Complete.
- Failures: 43, all fixed control-field (006/007/008) validation the prompt does not mention.
- Network: none

### Sonnet 5.5 max — `1a783906-13ae-4077-a75b-ca0a756dd868`

- Score 2857/2900; status Complete.
- Failures: 43, the same fixed-field (006/007/008) content-validation set as Sonnet MARC21 C++ max. The agent listed the contents of 005/006/007/008 as not validated; the prompt never asks for these checks.
- Network: None detected.
- Harness 0.2.1 conditions; two same-model subagents; modelUsage only claude-sonnet-5-5. One malformed tool call, harmless.
- 8 below Sonnet MARC21 JS high (2865/2900).

### Opus 5.5 max — `01d0e5e2-dfa5-409a-b94b-e3dbaf2c4587`

- Score 2857/2900; status Incomplete.
- Failures: 43, all in test_fixed_fields.py: 006/007/008 fixed-field validation (wrong lengths, 007 category lengths, 008 date-entered digits and fill characters, codes outside the official tables, cataloging source). Not mentioned.
- Network: pip download pymarc 5.2.0 and pip install it with lxml into a throwaway /tmp venv, for cross-checking only (no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness 0.2.2 conditions; modelUsage only claude-opus-5-5, including the background subagent. 13 task notifications completed, 1 stopped.
- Queued for one rerun at the end under the 2026-10-24 'Keep, rerun at end' decision for background-stop runs, keeping both attempts.
- Same score as Opus MARC21 JS high and Sonnet MARC21 JS max (2857/2900).

### Opus 5.5 max (rerun) — `f1a9f8d7-26e5-42bf-8e11-430183c14c4a`

- Score 2857/2900; status Complete.
- Failures: 43, all in test_fixed_fields.py: 006/007/008 fixed-field validation. The last message says the agent deliberately did not check 005-008 contents position by position, only repeatability.
- Network: pip download pymarc 5.4.0 (wheel and sdist) into a throwaway /tmp venv for cross-checking (disclosed); curl download of the Perl MARC-Lint 1.53 distribution from CPAN, whose embedded rule tables the agent diffed against its own extracted rules (not mentioned in the last message); no WebFetch/WebSearch (web-enabled condition; disclose).
- Rerun of opus-marc21-js-max (2857/2900, Incomplete, background subagent stopped) under the 2026-10-24 'Keep, rerun at end' decision; both attempts kept. Same score as the first attempt.
- Harness 0.2.2 conditions; no subagents this time; modelUsage only claude-opus-5-5; 1 result event. 4 task notifications, all completed; none stopped.
- Same score as Opus MARC21 JS high and Sonnet MARC21 JS max (2857/2900).
