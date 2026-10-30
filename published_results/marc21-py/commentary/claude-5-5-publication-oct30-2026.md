# Reviewed Claude 5.5 collection, October 13-29, 2026 — marc21-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `857c368f-1443-4c1b-9fa5-066e925934ab`

- Score 2857/2900; status Complete.
- Failures: 43, all fixed control-field (006/007/008) length, fill, digit and code-table validation (same set as the C++ run).
- Network: None (no network commands; no WebFetch/WebSearch).
- The agent explicitly chose not to validate 005/006/007/008 content because the prompt's list of validation rules named indicators, subfield codes and repeatability. Every failure falls in that deliberately skipped area; worth checking whether the prompt states the fixed-field requirement clearly enough.

### Opus 5.5 high — `e72f9a51-1e30-4c1f-a2c8-40e513e1484d`

- Score 2863/2900; status Complete.
- Failures: 37, all fixed control-field (006/007/008) validation the prompt does not mention.
- Network: none

### Sonnet 5.5 max — `3757f3fe-ba45-43eb-8c1d-86f082b06986`

- Score 2857/2900; status Complete.
- Failures: 43, the same fixed-field (006/007/008) content-validation set as the other Sonnet MARC21 runs. The agent explicitly says 005/006/007/008 contents are not validated because the task only asks for indicators, subfield codes and repeatability.
- Network: None detected.
- Harness 0.2.1 conditions; two same-model subagents; modelUsage only claude-sonnet-5-5. One malformed tool call, harmless.

### Opus 5.5 max — `c02cd70a-2455-43b5-9662-abe1fa3e365d`

- Score 2857/2900; status Complete.
- Failures: 43, all in test_fixed_fields.py: 006/007/008 fixed-field validation. The last message says the agent deliberately did not check 005/006/007/008 contents, not even 008's length, and calls it the easiest choice to reverse.
- Network: pip download pymarc 5.4.0 and install into a throwaway /tmp venv, for cross-checking only (no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness 0.2.2 conditions; no subagents; modelUsage only claude-opus-5-5. 9 task notifications completed, 1 failed (a background shell task 'Create test venv with pymarc installed', which the agent then redid); none stopped.
- 6 below Opus MARC21 Python high (2863/2900); same as Sonnet MARC21 Python max (2857/2900).
