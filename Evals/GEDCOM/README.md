# GEDCOM

FamilySearch GEDCOM 7 eval for CLISpecBench.

This eval uses the checked-in official GEDCOM 7 HTML corpus in
`prompt/docs/FamilySearchGEDCOMv7.html` and a generic tree-shaped inspect/render
contract for FamilySearch GEDCOM datasets and GEDZIP archives.

The tested surface covers GEDCOM line grammar, payload continuation and escaping
rules, dataset-envelope validation, pointer resolution and target-type checks,
top-level record constraints, major record-level required-child rules, selected
nested-structure cardinality rules, official `Y|<NULL>` event payload
constraints, official datatype and enumeration validation for commonly used
payload-bearing structures, GEDZIP archive entry rules, and the curated set of
official level-0 record fragments extracted from the FamilySearch corpus. The
maintainer-only generated artifacts extract structure grammar, examples, and
enumeration sets from the HTML corpus and include curated summaries for datatype
and GEDZIP sections used by the hidden tests.

## CLI Contract

```text
python main.py --input <request.json> --output <response.json>
```

Supported actions:

- `inspect`: parse GEDCOM text into a canonical nested record tree, folding
  GEDCOM `CONT` line continuations into payload strings
- `render`: render that canonical nested record tree back into GEDCOM text
- `inspect_gedzip`: parse a base64-encoded FamilySearch GEDZIP archive
- `render_gedzip`: render a GEDCOM dataset and attachment map as GEDZIP

See [prompt/technical-requirements-prompt.md](prompt/technical-requirements-prompt.md)
for the exact request and response schema.

## Reference Language

GEDCOM ships only with a Python reference implementation. The GEDCOM 7 contract
leans heavily on text line grammar, ZIP archive handling, BCP 47 and RFC 2045
style payload validation, and URL/URI parsing. Python's standard library covers
all of this without external dependencies, so a C++ reference implementation
would be disproportionately large for no additional coverage.

## Running Tests

```bash
uv run pytest Evals/GEDCOM/tests --language=py
```
