# Changelog

## v3.2.1 — 2026-04-24

- Removed `tests/test_official_data_rules.py`; the maintainer-only
  `tests/generated/` artifact is already policed by the repo-level drift test at
  `src/clispecbench/tests/test_gedcom_generated_artifacts.py` and does not
  belong in the agent-scoring suite.
- Mentioned GEDZIP archive inspect/produce as a domain-expert need in
  `prompt/base-prompt.md` so the behavioral scope is not smuggled through the
  technical-requirements contract prompt.
- Removed the reference implementation's cross-directory dependency on
  `tests/generated/gedcom_data_rules.json`. Enumeration sets now come from the
  inlined tables the ref impl already carried as fallbacks.
- Parametrized four previously aggregated validation tests so each spec case
  (xref-required record tags, Y-or-NULL event tags, and inspect/render pointer
  target types) fails independently.
- Rewrote the error-envelope schema test in `test_schema.py` to trigger
  `invalid_request` via an unsupported action, so it no longer overlaps with
  the missing-HEAD validation test.
- Split the official-fragment parse/render test in `test_parse.py` into a
  parse-only test and a roundtrip test with independent failure modes.
- Documented in the eval README why GEDCOM ships a Python-only reference
  implementation.

## v3.2.0 — 2026-04-24

- Added GEDZIP inspect/render coverage and reference support for ZIP archives
  containing `gedcom.ged` plus local-file attachments.
- Added generated maintainer data-rule artifacts that extract GEDCOM enumeration
  sets from the official HTML corpus and curate datatype/GEDZIP section
  summaries for hidden-test authors.
- Expanded tests and reference validation for date, time, age, language, media
  type, file path, email, coordinate, standard enum, and extension enum
  payloads.
- Reduced invalid-behavior test cascade risk by routing validation assertions
  through defensive error-code helpers.

## v3.1.0 — 2026-04-23

- Added broader GEDCOM 7 structure-validation coverage derived from the checked-in
  official grammar, including top-level record requirements, major record
  required-child rules, and `Y|<NULL>` event payload checks.
- Added nested structure validation for `HEAD/PLAC`, `CHAN`, `CREA`,
  `ASSO/ROLE`, `NAME/TRAN`, `FILE/FORM`, `FILE/TRAN/FORM`, and `PLAC/MAP`.
- Tightened pointer handling so hidden tests now check both pointer existence
  and target record type while still allowing context-dependent non-pointer
  structures such as `HEAD/SOUR` and family-event `HUSB` / `WIFE`.
- Added a richer positive roundtrip corpus with repository, source, multimedia,
  and association structures, plus new negative tests generated from the
  official record-root and event grammar artifacts.

## v3.0.0 — 2026-04-22

- Replaced the old profile-specific inspect/render contract with a generic
  nested GEDCOM record-tree contract.
- Switched the reference implementation from a hand-authored family-record model
  to generic GEDCOM nodes and dataset records.
- Folded `CONT` continuations into payload strings, rejected `CONC` for GEDCOM
  7, and added `@@` line-string escape handling.
- Added official-corpus-driven tests for the curated set of level-0 GEDCOM
  record fragments mirrored from the checked-in FamilySearch spec.
- Registered `gedcom-py` in the harness task registry.

## v2.3.2 — 2026-04-22

- Reworded the prompt-doc provenance note so it describes the current GEDCOM
  docs corpus directly instead of referencing repo migration history.

## v2.3.1 — 2026-04-22

- Updated the technical requirements prompt to refer to the checked-in official
  `docs/` corpus instead of the deleted hand-authored profile filename.

## v2.3.0 — 2026-04-22

- Replaced the hand-authored GEDCOM profile doc in `prompt/docs/` with the
  official single-file FamilySearch GEDCOM HTML specification.
- Added a docs provenance note documenting the upstream source URL and retrieval
  date for the mirrored spec artifact.

## v2.2.0 — 2026-04-21

- Added broader GEDCOM structure coverage around duplicate `HEAD` records,
  `CONC` misuse, `HEAD/DATE` and `HEAD/GEDC` child restrictions, and render
  rejection of unsupported family event tags.
- Added explicit duplicate-`TRLR` coverage and tightened the `GEDC` invalid
  child test so it isolates the forbidden-child rule instead of also removing
  the required `VERS`.
- Added explicit multiline inline-note rendering coverage so `CONT` emission is
  exercised independently of shared-note rendering.
- Clarified the prompt docs around exact `HEAD` / `TRLR` cardinality and the
  restricted child sets under `DATE` and `GEDC`.

## v2.1.0 — 2026-04-21

- Clarified that multiline `CONT` / `CONC` continuations are allowed under any
  inline `NOTE` structure in this profile, not just top-level shared notes.
- Split the `HEAD` required-field coverage into independent tests for `SOUR`,
  `GEDC/VERS`, and `CHAR`.
- Renamed the top-level-tag rejection test to reflect that it is enforcing this
  eval profile, not the entire upstream GEDCOM 7 standard.

## v2.0.0 — 2026-04-21

- Expanded the GEDCOM eval to cover submitter records, shared-note records,
  richer HEAD metadata, name parts, and a broader individual/family fact
  profile.
- Reworked the canonical JSON model and reference implementation around the
  wider record graph.
- Replaced the initial narrow pytest suite with broader coverage of pointers,
  shared notes, submitters, and rendering order.

## v1.0.0 — 2026-04-20

- Initial GEDCOM core-profile eval.
- Added prompt artifacts, Python reference implementation, and pytest suite.
