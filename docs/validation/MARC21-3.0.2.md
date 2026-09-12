# MARC21 3.0.2 validation

This is a private-test-only correction to 3.0.1. All model-visible prompt/doc
bytes, generated rule tables, and reference implementation files are unchanged.
The suite still contains 2900 scored cases. The three changed test files have
passed Ruff and strict Pyright and received independent review.

## Public evidence and changes

- `bd007c.html` Input Conventions recommends the first six positions;
  `bd007m.html` recommends the first eight. Both say "should always" and
  the general 007 page explicitly permits variable length for these categories.
  There is no unequivocal mandatory two-character minimum. Positive cases now
  exercise the recommended base and maximum. All undersized c/m acceptance and
  rejection are left unscored; over-maximum and other fixed-length bounds remain.
- `bd018.html` first two examples emphasize only `$a`; the currency dollar
  signs in `$01.25`/`$00.95` are literal content. The flattened text parser now
  preserves the complete fee code for these exact examples.
- `bd880.html` first example emphasizes `$6` and `$a`; `/$1` is the script code
  inside `$6`, not another subfield. The exact public example is preserved.
- `bd357.html` explicitly defines both indicators as blank. The first displayed
  `#0` example contradicts that table; the following `##` example supplies a
  valid positive fixture without changing the public document or field coverage.
- `bdintro.html` Directory says variable-data entries follow ascending first
  tag character. The empty 500 fixture is placed before 650 and checks the named
  empty field rather than unrelated whole-record order. The other two complete
  Unicode round-trip tests retain their original full-record assertions.

These changes avoid turning optional-length interpretations, display-extraction
errors, and unrelated ordering into model failures. No prerequisite skips or
blanket valid-input gates are introduced. Corpus cases still measure distinct
field/action requirements, so failures sharing a generated-rule implementation
bug can remain correlated; failure counts are not independent defect counts.

## Validation and saved submissions

All grader runs use
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with the original submission mounted read-only and executed only from a
container-local copy. Model inference is not involved in these regrades.

| Implementation | Original 3.0.1 | Corrected 3.0.2 |
|---|---:|---:|
| Python reference |2900/2900|2900/2900|
| Astra Python |2883/2900|2900/2900|
| Terra Python |2832/2900|2841/2900|

Astra's 17 original failures were four ambiguous 007 positives, twelve repeated
018/357/880 fixture errors across four interfaces, and the directory-order case.
Terra recovered the 357/880 and ordering cases. Its remaining 59 failures are 39
fixed-field validation cases plus 20 field/action cases across 018/041/085/810/811;
source inspection and direct probes confirm omitted fixed-field validation and
missing `$a` definitions in its extracted rule tables. The corrected 018 fixture
therefore still detects an independent Terra implementation defect.

The saved-source full runs above initially included the stronger one-character
c/m negatives; both models passed those. The final reference full run includes
the deferral, and the committed official saved-source regrades record the exact
final suite hash. This relaxation adds no passing prerequisite to another test.
Raw development reports are retained locally under `work/marc-followup`; official
regrade records preserve original scores, generation metadata, source hashes,
usage and the new complete test outcomes.

The unchanged public corpus still contains the 357 example contradiction and
underspecified short c/m lengths. Clarifying those documents belongs in a later
public-input revision, with fresh generations for comparisons under that input.
