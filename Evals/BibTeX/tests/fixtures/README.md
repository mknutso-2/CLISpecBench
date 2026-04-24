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

- The current `texlive/texlive:latest` Docker image (`tools/regenerate_bbl_fixtures.sh`
  uses the floating `latest` tag; re-running the script today pulls a
  newer image than the last fixture-regeneration run. If a submission
  ever diverges due to BibTeX upstream changes, re-run the script to
  refresh the fixtures and commit the diff alongside the submission
  update).
- `plain.bst` / `alpha.bst` / `unsrt.bst` / `abbrv.bst` from CTAN,
  tagged as `bibtex-0.99c-*`.

## What "byte-exact" means

A submission must match these `.bbl` files byte-for-byte, with two
documented approximations per summary.md §8:

1. `change.case$` and `purify$` on nested LaTeX accent macros past
   depth 1 (e.g. `{{\"o}}`) are not asserted by parity tests; they
   are covered by narrower unit tests.

**`width$` and parity.** `alpha.bst` uses `width$` to pick the
widest entry label for the `\begin{thebibliography}{<longest>}`
line, so the `width$` implementation actually changes the bytes
written into the `.bbl`. The fixtures in this directory were
regenerated against BibTeX 0.99c (cmr10-exact `width$` values),
so passing the parity tests REQUIRES cmr10-exact `width$`.
An implementation that uses the §8.1 approximation table will
pass the deep `width$` unit tests but fail the `alpha.*.expected.bbl`
parity tests because the `longest` label argument embedded in
`\begin{thebibliography}{...}` will differ. summary.md §8.1's
"reference-style parity caveat" spells this out in prose.
