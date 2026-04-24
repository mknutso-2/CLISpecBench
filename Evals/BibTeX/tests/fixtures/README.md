# BibTeX Reference Fixtures

## Purpose

These fixtures drive `test_reference_styles.py`, which asserts
**byte-exact `.bbl` parity** between the submission's output and
BibTeX 0.99c's output when running Patashnik's canonical reference
styles against a realistic `.bib` database.

## Files

Two curated `.bib` corpora × four canonical styles = 8 parity fixtures.

### Corpus 1: `refs.bib` / `refs.cites` — core surface

Covers all entry types, simple name grammar, `@string` macros,
concatenation, and basic `crossref` inheritance.

Expected `.bbl` outputs:

- `plain.refs.expected.bbl`
- `alpha.refs.expected.bbl`
- `unsrt.refs.expected.bbl`
- `abbrv.refs.expected.bbl`

### Corpus 2: `refs-edge.bib` / `refs-edge.cites` — grammar edges

Covers name-grammar edges (Form 2/3, tied tokens, brace-protected
von), long author lists with `and others`, `@preamble`
concatenation, case-insensitive `crossref` lookup, depth-1 LaTeX
accents, predefined month macros, and complex `@string`-based
concatenation.

Expected `.bbl` outputs:

- `plain.refs-edge.expected.bbl`
- `alpha.refs-edge.expected.bbl`
- `unsrt.refs-edge.expected.bbl`
- `abbrv.refs-edge.expected.bbl`

## Regenerating fixtures against real BibTeX 0.99c

The expected `.bbl` files MUST be regenerated against the historic
BibTeX 0.99c binary. A helper script lives at
[`../../tools/regenerate_bbl_fixtures.sh`](../../tools/regenerate_bbl_fixtures.sh).

```bash
# With TeX Live installed on the host:
bash Evals/BibTeX/tools/regenerate_bbl_fixtures.sh

# With Docker + texlive image:
bash Evals/BibTeX/tools/regenerate_bbl_fixtures.sh --docker
```

The script writes `.expected.bbl` files back under `fixtures/`.

## Known-good toolchain

The expected fixtures were generated with:

- TeX Live YYYY (`texlive/texlive:latest` Docker image at the commit
  pinned in `tools/regenerate_bbl_fixtures.sh`).
- `plain.bst` / `alpha.bst` / `unsrt.bst` / `abbrv.bst` from CTAN,
  tagged as `bibtex-0.99c-*`.

## What "byte-exact" means

A submission must match these `.bbl` files byte-for-byte, with two
documented approximations per summary.md §8:

1. `width$` values may differ from cmr10 within a stable monotone
   ordering; tests exercise relative comparisons, not absolute.
2. `change.case$` and `purify$` on nested LaTeX accent macros past
   depth 1 (e.g. `{{\"o}}`) are not asserted by parity tests; they
   are covered by narrower unit tests.
