# Reviewed Claude 5.5 collection, October 13-29, 2026 — marc21-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `bd4ba7f9-7be5-4942-b633-a83442bfc139`

- Score 2857/2900; status Complete.
- Failures: 43, mostly fixed-field validation: test_inspect_rejects_007_category_lengths_outside_official_range (15), test_render_rejects_008_fill_character_in_each_date_entered_position (6), test_inspect_rejects_008_non_digit_in_each_date_entered_position (6), test_render_rejects_fixed_control_fields_with_wrong_official_length (3), test_render_rejects_fixed_control_fields_with_disallowed_fill_positions (3), test_inspect_rejects_fixed_control_field_codes_outside_official_tables (3), test_render_rejects_006_lengths_other_than_18 (2), test_inspect_rejects_each_008_position_code_outside_official_tables (2), test_inspect_rejects_short_007_map_category (1), test_inspect_rejects_008_cataloging_source_outside_official_table (1), test_inspect_marcxml_rejects_non_digit_008_date_entered (1)
- Network: None (no network commands; no WebFetch/WebSearch).
- Reported technical-requirements-prompt.md and base-prompt.md missing from the workspace; their content is assembled into prompt.md.

### Opus 5.5 high — `160a2824-7877-4dc5-ac9f-ed8d4af04787`

- Score 2865/2900; status Complete.
- Failures: 35, all fixed control-field (006/007/008) validation the prompt does not mention (same pattern as every Sonnet MARC21 run).
- Network: none

### Sonnet 5.5 max — `5a93db46-29fa-4ac2-aed4-f9b8220d1ffb`

- Score 2857/2900; status Complete.
- Failures: 43, all fixed-field (006/007/008) content validation in test_fixed_fields.py: 007 category lengths, 008 date-entered positions, fixed-field lengths, fill positions and code tables. The agent disclosed that fixed-field content of 005/006/007/008 is not validated. This is the same family every Claude 5.5 MARC21 run fails; the prompt never asks for these checks.
- Network: None detected.
- Harness 0.2.1 conditions; two same-model subagents, 21 ListAgents, 1 TaskStop; modelUsage only claude-sonnet-5-5.

### Opus 5.5 max — `e91b4792-48ea-4c03-98b5-719540dfb18a`

- Score 2857/2900; status Complete.
- Failures: 43, all in test_fixed_fields.py: 006/007/008 fixed-field validation (wrong lengths, 007 category lengths, 008 date-entered digits and fill characters, codes outside the official tables, cataloging source). Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- Harness 0.2.2 conditions; no subagents; 9 task notifications all completed; modelUsage only claude-opus-5-5.
- 8 below Opus MARC21 C++ high (2865/2900); same as Sonnet MARC21 C++ max (2857/2900).
