# IGES 1.0.21 appendix Real literal — 2026-09-30

Suite SHA-256:
`ec84b63fbbbbf9a90c8d6e4a88cb5e29ab2e93424e7f25f96176569451382135`.
All 249 case IDs and assertions, model inputs, reference implementations and
saved generated sources are unchanged. This repair changes one hidden token.

## Authority and evidence

Sol Max JavaScript `613cdda8-16a8-40af-9de6-f4b39e80053b` completed normally
at 245/249 under 1.0.20. The ex1 integration case failed before its observations.
An isolated Docker parse reproduced `values[4] is not a valid Real` at line 74.
The Type 406 Form 5 record ends in integer `0`; §4.101 declares this extension
length Real, and §2.2.2.2 requires a decimal point or exponent in a Real literal.
Its value is unused for the selected extension mode, but that does not clearly
waive the field's lexical type. The generic FieldValue union does not clearly
override form-specific types. A strict conforming reader must not be penalized
for rejecting this positive fixture.

The hidden record now spells the same zero as `0.0`. Its padding changes to
retain 80 columns; columns 65 onward and all other lines remain byte-identical.
All 75 records retain their widths. The model-visible specification and corpus
are frozen. The corrected disposable file parses with 21 entities and the
expected real/int/int/int/real property kinds. No new behavior, assertion or
score weighting is introduced. One integration prerequisite affects one score.

The other three failures share the already documented Type 130 direction
mismatch: the implementation follows physical IGES normal-cross-tangent
geometry, whereas the explicit benchmark contract specifies direct displacement.
These are three observations of one defect family. Public-content cleanup is
separate from this hidden-fixture correction.

## Validation and preservation

Independent review verified the exact byte transformation, candidate identity,
all test ASTs excluding the explanatory docstring, and unchanged prompts and
references. The unchanged C++ reference passes 249/249 in offline image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
Ruff check/format and strict Pyright pass. Pyright was run on the real host
because the sandbox did not expose its installed pytest package.

Six preserved submissions will be regraded sequentially after the rubric
commit: four Astra languages and Sol C++/JavaScript. Publication requires all
248 untouched outcomes per source to remain identical, independent corrected-
grade review, and complete dashboard preservation checks. Regrades add no
model calls or inference cost; raw results, source, sessions and usage remain
immutable and replacement audits retain complete previous publications.

Local evidence is under `work/non-rs274-audit/iges-1.0.21-validation/` and
`work/non-rs274-audit/runs/iges-js-gpt-5.6-sol-max/`.
