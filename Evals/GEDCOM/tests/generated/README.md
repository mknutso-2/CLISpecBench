This directory contains maintainer-generated GEDCOM artifacts derived from the
official HTML spec in
`Evals/GEDCOM/prompt/docs/FamilySearchGEDCOMv7.html`.

These files are evaluator-only helpers. They are not mounted into the agent
prompt.

Regenerate them with:

```powershell
uv run python Evals\GEDCOM\scripts\generate_official_artifacts.py
```

Do not hand-edit the generated JSON. The repo-level drift test
`src/clispecbench/tests/test_gedcom_generated_artifacts.py` checks that the
committed files still match the generator output.

Current files:

- `gedcom_structure_grammar.json`: maps official structure-production headings
  to their decoded `gedstruct` bodies. Keys preserve the source heading
  spelling, including the Title-Case top-level `Dataset` production.
- `gedcom_examples.json`: a list of GEDCOM code-block records with:
  `text`, `section_id`, `source_block_id`, `context_classes`, `lead_text`,
  `context_text`, `classification_hint`, `starts_at_level_zero`, `has_head`,
  `has_trlr`, and `is_full_dataset`.
- `gedcom_data_rules.json`: maintainer-only data-rule helper containing
  enumeration sets extracted from the official HTML plus curated datatype and
  GEDZIP section summaries used to guide hidden-test coverage.

`classification_hint` is heuristic. It helps triage which official code blocks
look like counterexamples, note snippets, record fragments, or full datasets,
but it does not replace reading the surrounding official prose before writing a
test against a block. The hint is driven by the nearest lead paragraph plus
container context; `context_text` is included for additional inspection, not as
the sole source of the label.
