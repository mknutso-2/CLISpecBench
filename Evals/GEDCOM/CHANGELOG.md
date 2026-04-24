# Changelog

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
