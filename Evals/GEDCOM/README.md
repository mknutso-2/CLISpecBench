# GEDCOM

FamilySearch GEDCOM 7 full-spec-corpus eval for CLISpecBench.

This eval now uses the checked-in official GEDCOM 7 HTML corpus in
`prompt/docs/FamilySearchGEDCOMv7.html` and a generic tree-shaped inspect/render
contract so the task can represent the broader standard instead of a small
family-record profile.

The current shipped surface covers GEDCOM line grammar, payload continuation and
escaping rules, dataset-envelope validation, pointer resolution and target-type
checks, top-level record constraints, major record-level required-child rules,
selected nested-structure cardinality rules, official `Y|<NULL>` event payload
constraints, and the curated set of official level-0 record fragments extracted
from the FamilySearch corpus.

## CLI Contract

```text
python main.py --input <request.json> --output <response.json>
```

Supported actions:

- `inspect`: parse GEDCOM text into a canonical nested record tree, folding
  GEDCOM `CONT` line continuations into payload strings
- `render`: render that canonical nested record tree back into GEDCOM text

See [prompt/technical-requirements-prompt.md](prompt/technical-requirements-prompt.md)
for the exact request and response schema.

## Running Tests

```bash
uv run pytest Evals/GEDCOM/tests --language=py
```
