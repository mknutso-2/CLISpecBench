# Changelog

## v2.8.0 — 2026-04-24

- Added `prompt/docs/MARCXML_Slim.md`, a maintainer-authored MARCXML slim
  structural reference, so that MARCXML-only rules (namespace, root elements,
  element ordering, required `ind1`/`ind2` attributes, subfield-only children
  of datafield, single-record collection wrapper, required `tag` on
  controlfield/datafield, required `code` on subfield) are unambiguously
  documented in the agent-visible docs corpus. Previously those rules were
  only implied by the technical requirements examples.
- Added MARCXML tests for the previously-undocumented-and-untested rejection
  cases: missing `tag` attribute on controlfield, missing `tag` attribute on
  datafield, missing `code` attribute on subfield, wrong root element,
  empty `<collection>`, and unknown element directly inside `<record>`.
- Moved the ISO 2709 UTF-8 validation behavior (reject records whose field
  payload bytes are not valid UTF-8) from `technical-requirements-prompt.md`
  into `base-prompt.md`, keeping only error-code scoping in the harness
  contract. Aligns with the eval-authoring rule that behavioral requirements
  belong in the base prompt or docs.
- Relaxed the 007 variable-length category rules: categories `c` (electronic
  resource) and `m` (motion picture) now only require at least positions
  00-01 (both defined for every category) instead of the full basic-set
  lengths previously asserted. The LOC docs describe those basic sets with
  permissive "should always be used" wording, so asserting them violated the
  unambiguous-tests rule. Maximum lengths and fixed-length category rules
  are unchanged.

## v2.7.0 — 2026-04-24

- Added maintainer-curated fixed-field rules for Leader, 006, 007, and 008 so
  the official fixed-field documentation is exercised in addition to standard
  field pages.
- Added fixed-control-field and leader validation tests across render, ISO 2709
  inspect, and MARCXML inspect paths.
- Expanded fixed-field tests to cover every deterministic Leader position,
  006/007/008 code table, and 007 category length rule in the bundled
  fixed-field artifact.
- Tightened 007 validation to use category-specific lengths and 008 validation
  to check the universal modified-record and cataloging-source code tables.
- Reworked parse roundtrip tests to validate rendered outputs with
  evaluator-side decoders instead of feeding submission render output back
  through submission inspect actions.
- Corrected the Leader/09 fixed-field table so the MARC-8 blank value remains
  accepted where the official Leader documentation permits it.
- Made the Unicode/UTF-8 ISO 2709 interchange scope explicit in the
  agent-visible prompt contract.
- Made the official-example render tests hermetic by parsing rendered ISO 2709
  and MARCXML outputs with evaluator-side decoders instead of feeding them back
  through submission inspect actions.
- Clarified that MARCXML inspection accepts a one-record collection wrapper and
  that MARCXML rendering emits the normalized leader template.

## v2.6.1 — 2026-04-24

- Clarified the `leader_template` contract so inspect paths must return a
  normalized leader with positions `00-04` and `12-16` zeroed and render paths
  must fill those positions back in from the serialized record.
- Made the inspect schema test hermetic by using bundled ISO 2709 fixture bytes
  instead of depending on the submission's `render_iso2709` action.
- Added a stable `001` control field to the official-example fixture records so
  the corpus-driven example tests no longer depend on accepting data-only
  records with no control fields.
- Tightened the generated MARC21 rule-table contract so indicator and subfield
  validation only uses fields whose extracted official HTML summaries were
  parsed completely, instead of silently trusting partial extractions.

## v2.6.0 — 2026-04-24

- Added direct `inspect` and `inspect_marcxml` positive coverage for the
  representative official field examples so the full checked-in LOC corpus now
  exercises parse paths without depending on the submission's render behavior.
- Added corpus-wide direct-parse validation coverage for official indicator
  constraints, subfield membership constraints, and nonrepeatable subfield
  rules across both ISO 2709 and MARCXML inspection paths.
- Refactored the official-rule mutation fixtures in the MARC21 tests so the
  same corpus-derived invalid records are exercised consistently across render,
  ISO 2709 inspect, and MARCXML inspect actions.

## v2.5.0 — 2026-04-23

- Reframed the eval as a full-corpus MARC 21 bibliographic task rather than an
  "expanded profile" and clarified that the checked-in Library of Congress
  corpus is the normative source for field semantics within the single-record
  UTF-8 interchange contract.
- Added corpus-wide repeatability coverage from the bundled MARC21 rule table
  for nonrepeatable control and data fields across `render_iso2709`,
  `inspect_marcxml`, and `inspect`.
- Added a generic ISO 2709 test helper so official-rule validation cases can be
  exercised through inspect-path fixtures without depending on the submission
  under test.

## v2.4.4 — 2026-04-22

- Moved the MARC21 artifact generator out of the agent-scored eval test suite
  into `Evals/MARC21/scripts/` and moved the artifact drift check into the
  repo-level `src/clispecbench/tests/` suite so evaluator-integrity checks no
  longer affect submission scores.
- Centralized the committed MARC21 rule table in
  `reference-implementation-py/generated/` and updated the eval-side helpers to
  read that canonical bundled copy instead of maintaining a duplicate under
  `tests/generated/`.
- Tightened the corpus-driven MARC21 helper selection logic so the official
  validation tests only parameterize over fields whose extracted indicator and
  subfield constraints are unambiguous and have a rule-compatible official
  example.

## v2.4.3 — 2026-04-22

- Reworded the prompt-doc provenance note so it describes the current MARC21
  docs corpus directly instead of referencing repo migration history.

## v2.4.2 — 2026-04-22

- Bundled the generated MARC21 rule table into `reference-implementation-py/`
  so the Python reference implementation no longer depends on `tests/` at
  runtime.
- Added a regression test that regenerates the evaluator-side MARC21 artifacts
  and compares them to the committed JSON, preventing silent drift between the
  mirrored Library of Congress HTML corpus and the derived rule tables.
- Softened reference-implementation error messages so they describe the bundled
  rule table rather than overstating the generated artifacts as the MARC21
  corpus itself.

## v2.4.1 — 2026-04-22

- Moved evaluator-generated field-rule and example artifacts out of
  `prompt/docs/` and into `tests/generated/` so the agent-visible MARC21 corpus
  remains limited to the mirrored official Library of Congress HTML sources and
  the stitched convenience mirror derived from them.
- Repointed the pytest helpers and Python reference implementation at the
  non-prompt generated artifacts without changing the normative MARC21 behavior
  exercised by the suite.

## v2.4.0 — 2026-04-22

- Added generated `prompt/docs/generated/` artifacts derived from the full
  mirrored Library of Congress bibliographic corpus so the eval can drive field
  rules and official examples directly from the checked-in specification docs.
- Expanded the MARC21 tests from a small profile-shaped core to a field-driven
  corpus-wide suite using representative official examples and official
  indicator / subfield definitions extracted from the full spec pages.
- Tightened the Python reference implementation so both inspect and render paths
  enforce official field repeatability, indicator constraints, and subfield
  membership / nonrepeatability derived from the checked-in MARC21 corpus.

## v2.3.1 — 2026-04-22

- Rewrote the stitched MARC21 convenience HTML file so its internal links and
  image references resolve into `loc-bibliographic-html/` when opened directly
  from `prompt/docs/`.
- Added the mirrored Library of Congress stylesheet to the stitched file so it
  renders more like the source pages in local file browsing.

## v2.3.0 — 2026-04-22

- Replaced the hand-authored MARC21 profile doc in `prompt/docs/` with a mirror
  of the current official Library of Congress bibliographic HTML corpus.
- Added a stitched single-file HTML convenience mirror generated from the
  checked-in official pages because a current one-file full-format download was
  not found.
- Added a docs provenance note documenting the upstream source root, retrieval
  date, and the distinction between the mirrored pages and the stitched file.

## v2.2.0 — 2026-04-21

- Added direct ISO 2709 inspect coverage, zero-subfield data-field roundtrips,
  MARCXML escaping checks, and a larger set of MARCXML structural error cases.
- Tightened the reference implementation and tests around fixed-width ISO 2709
  overflow handling for directory entries, base addresses, and total record
  length.
- Expanded inspect-side corruption coverage for leader length/base-address
  mismatches and non-UTF-8 variable-field payloads, and clarified those rules
  in the prompt docs.
- Corrected the directory-divisibility fixture so it now reaches the intended
  ISO 2709 rule instead of failing earlier on a leader-length mismatch.

## v2.1.1 — 2026-04-21

- Replaced the v2.1.0 test helper's repo-relative reference-implementation
  imports with hermetic embedded ISO 2709 fixture bytes so the hidden scorer
  container does not depend on directories outside `tests/`.

## v2.1.0 — 2026-04-21

- Removed render-path dependence from the ISO 2709 inspect corruption tests by
  generating fixture bytes from the bundled reference implementation instead of
  the submission under test.
- Added directory-entry digit-format coverage, inspect-side subfield-code
  corruption coverage, and additional render validation for punctuation and
  multi-character subfield codes.
- Added UTF-8 roundtrip coverage for CJK / combining-mark data and an explicit
  check that `render_iso2709` recomputes leader length and base address.

## v2.0.0 — 2026-04-21

- Expanded the MARC 21 eval from ISO 2709 inspection plus rendering into a
  broader interchange task with MARCXML inspection as well.
- Tightened leader, directory, field-structure, indicator, and subfield-code
  validation in the reference implementation and pytest suite.
- Widened the prompt/docs to cover the expanded MARCXML and transport rules.

## v1.0.0 — 2026-04-20

- Initial MARC 21 core-profile eval.
- Added prompt/docs, Python reference implementation, and pytest suite.
