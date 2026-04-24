# BibTeX Reference Fixtures

## Purpose

These fixtures drive `test_reference_styles.py`, which asserts
**byte-exact `.bbl` parity** between the submission's output and
BibTeX 0.99c's output when running Patashnik's canonical reference
styles against a realistic `.bib` database.

## Files

- `refs.bib` — a reference `.bib` covering all entry types, name
  grammar corners, `@string` macros, concatenation, and `crossref`
  inheritance.
- `refs.cites` — the citation list used for the runs.
- `plain.expected.bbl` — the expected `.bbl` for `plain.bst` on
  `refs.bib` / `refs.cites`.
- `alpha.expected.bbl` — same for `alpha.bst`.
- `unsrt.expected.bbl` — same for `unsrt.bst`.
- `abbrv.expected.bbl` — same for `abbrv.bst`.

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
