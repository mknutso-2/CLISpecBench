# Reviewed Claude 5.5 collection, October 13-29, 2026 — marc21-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `d2e670f0-bb71-44b8-bb1c-781799a9ae5d`

- Score 2857/2900; status Complete.
- Failures: 43, all fixed control-field (006/007/008) validation (same set as C++ and Python).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `97d5478a-d4b8-4cf2-9092-bd4b7ef36eb6`

- Score 2860/2900; status Complete.
- Failures: 40, fixed control-field handling but inverted from the other MARC21 runs: it over-validates, rejecting valid 006/007 position-00 codes and recommended lengths that the official tables accept (30), plus 008 and related checks (10).
- Network: none

### Sonnet 5.5 max — `d704c58f-14ed-4f10-afce-6695e80d556f`

- Score 2857/2900; status Complete.
- Failures: 43, the same fixed-field (006/007/008) content-validation set as the other Sonnet MARC21 runs. The agent disclosed that the 005/006/007/008 lengths are not checked.
- Network: None detected.
- Harness 0.2.1 conditions; cargo on PATH (46 invocations, none not found); no stopped background subagents; one same-model subagent; modelUsage only claude-sonnet-5-5. One malformed tool call, harmless.
- Completes Sonnet MARC21 max: 2857/2900 in all four languages.

### Opus 5.5 max — `076b53ea-01bf-4948-ad4f-2bc118708c8e`

- Score 2882/2900; status Complete.
- Failures: 18, all in test_fixed_fields.py and mostly 008: date-entered digits and fill characters (12), 008 position codes and cataloging source outside the official tables (3), plus one each for 006/007 codes, disallowed fill positions and MARCXML 008 date entered. 006/007/008 lengths and 007 category lengths pass, unlike the other Opus MARC21 max runs. Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- Harness 0.2.2 conditions. One background review subagent on claude-opus-5-5; modelUsage only claude-opus-5-5. The agent kept wait timers running so task notifications re-invoked it until the reviewer reported; all 13 task notifications completed, none stopped. 6 result events.
- cargo was available and used (23 cargo build/test mentions).
- Best Claude 5.5 MARC21 result so far: 22 above Opus MARC21 Rust high (2860/2900) and 25 above Sonnet MARC21 Rust max (2857/2900).
