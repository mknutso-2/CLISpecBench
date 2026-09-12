# MARC21 3.0.1 scoring audit — 2026-09-11

All model-visible `Evals/MARC21/prompt/` and shared prompt files remain
unchanged. The rubric has 2,900 cases, compared with 2,894 in 3.0.0.

## Corrected scoring defects

- **Cross-interface gate:** the 2.8.2 session fixture treated failure of one
  control-only ISO inspect request as a reason to skip all four interfaces.
  An implementation with working XML and render paths therefore lost evidence
  unrelated to its inspect defect. The shared build fixture remains unchanged;
  individual CLI tests now report their own outcomes without universal skips.
- **Repeated unrelated assertions:** corpus field examples now compare their
  named field, and Leader code cases compare their named position. Complete
  record checks, leader normalization, exit codes and success/error envelopes
  retain separate coverage. Exact error-code mapping is checked per action,
  not once per invalid field in the corpus.
- **Invalid positive fixtures:** LOC example `#` denotes a blank; the old
  `007` example supplied a literal `#` at a blank/fill-only position. The `006`
  category matrix now uses explicitly permitted fill after position 00.
  Changing a Leader material type no longer retains an unrelated book's `008`.
  Date-type cases supply compatible Date 1/Date 2 values and serial context
  where relevant. These follow `bd006.html`, `bd007a.html`, `bd008a.html`,
  and `bdleader.html` in the unchanged public corpus.
- **False credit:** the size-overflow fixture used thousands of nonrepeatable
  `245` fields, so rejection could succeed without enforcing record length.
  It now uses repeatable `500`. Fixed-field acceptance checks require rendered
  content rather than a success envelope alone. Each invocation clears stale
  output before running.
- **Serialization assumptions:** render fixtures use the contract's normalized
  leader input. XML escaping is checked as decoded text, allowing equivalent
  entity references and CDATA.

## Validation

Docker reference controls used this exact existing image, with network disabled
and the repository mounted read-only:

`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`

The Python reference passed the full 2,900-case sweep. After completing the
date fixtures, all 187 fixed-field cases passed again. After independent review
localized the Leader comparison further, a final 109-case Leader/field-example
selection passed. Ruff and strict Pyright passed on the changed test files.
No reference implementation changes were needed for this eval.

Seven temporary Python-reference mutants exercised 28 selected cases (all
schema gates, field 245 positive/negative cases, and record-size overflow):

| Mutation | Passed | Intended diagnostic |
| --- | ---: | --- |
| Bare exit-1 crash, no response | 0/28 | No rejection credit without observable response |
| Always structured-reject | 16/28 | Negative-classifier baseline; fails positive behavior |
| Omit inspected leader | 26/28 | Two leader normalization gates |
| Omit success `error: null` | 24/28 | Four success schema gates |
| Disable ISO inspect only | 24/28 | Four inspect failures; working interfaces still run |
| Remove record-length ceiling | 27/28 | Repaired overflow case |
| Report every error as `invalid_request` | 26/28 | Two inspect error-mapping gates |

On the original 3.0.0 selection, disabling inspect skipped all 22 selected
cases, and removing the record-length ceiling still passed all 22. The new
selection adds six dedicated schema/normalization cases; counts across versions
are therefore not directly interchangeable.

## Interpretation and remaining limits

A structured always-reject classifier earns points on negative examples, as
shown above; those points do not demonstrate usable parsing or rendering.
Introducing another generic valid-control gate would recreate a shared
prerequisite cascade, so this audit records the baseline instead. Per-feature
paired valid/invalid cases are a possible future coverage improvement.

The large corpus-derived matrix still contains correlated implementations of
field-table and datatype rules. A failure count is not a count of independent
defects. This audit fixes the identified shared gates, fixtures and assertions;
it does not certify exhaustive coverage of every conditional requirement in
the Library of Congress corpus.
