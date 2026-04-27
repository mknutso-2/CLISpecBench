# Changelog

## Investigation — 2026-04-27 (no version change)

- Reviewed GEDCOM frontier-agent results after v3.2.1 because successful runs
  from OpenAI and Anthropic models clustered around 45-52% while the same
  models score 90%+ on other evals. The Python reference implementation still
  passes the full suite (`203 passed`), so the low scores do not appear to come
  from a broken eval runtime or an unsatisfiable reference/test mismatch.
- Across the 19 non-busted published runs that passed at least 80 tests, models
  almost always implemented the core parser/renderer: parse coverage was
  usually 46-47/47 and schema coverage was 3/3. The consistent gap is full
  GEDCOM 7 validation: 69 tests failed in every one of those 19 runs, and 97
  tests failed in at least 17 of them.
- The consistent failures are concentrated in a few rule families, not in
  GEDZIP or basic tree handling. All 19 non-busted runs missed all 32
  `Y|<NULL>` event-payload rejection cases, 19 datatype-render/validation
  cases, 6 pointer-target-type cases, and 9 render-side validation cases.
  Xref-required record tests failed in 17-18 of 19 runs. GEDZIP was not the
  primary cause; it is hard in C++/Rust under the stdlib-only rule, but it is
  only 9 tests and many runs passed most or all of it.
- Found one prompt-packaging cleanup issue: `base-prompt.md` says the request
  and response contract is described in `technical-requirements-prompt.md`, but
  the harness mounts only the assembled `prompt.md` plus `docs/`. The contract
  text is present in `prompt.md`, so this is unlikely to explain a 50% score by
  itself, but at least one agent explicitly wasted effort looking for the
  missing standalone file.
- Proposed prompt/docs fixes: remove the stale standalone-file reference; add a
  short mounted docs navigation note that makes the intended validation scope
  explicit without introducing new behavior beyond the official spec; and call
  out that a conforming solution is expected to validate GEDCOM line grammar,
  official structure cardinalities, pointer target types, datatype syntax, and
  GEDZIP attachment rules rather than only parse/render a generic tree.
- Proposed scoring/test cleanup: keep the single GEDCOM eval, but make the
  reported subscores clearly distinguish core parse/render, structure
  validation, datatype validation, and GEDZIP, and avoid letting one generalized
  missed rule dominate raw score. The 32 `Y|<NULL>` parametrized cases are
  independent examples, but they currently behave like one missed implementation
  concept repeated 32 times.
- Expected model capability after cleanup: fixing the stale contract reference
  alone should recover little, probably 0-5% of the 69 currently consistent
  failures. A concise spec-navigation/validation-scope note should make the
  simpler table-driven families attainable, plausibly recovering about 20-35%
  of the consistent failures, especially generalized event payloads, required
  child/cardinality checks, and pointer target maps. The remaining 65-80% of
  current consistent failures should be expected to continue failing for most
  one-shot frontier-agent runs unless agents are given more explicit derived
  tables; current runs do not show reliable ability to derive and implement
  exact GEDCOM date/calendar grammar, BCP 47 language validation, media type and
  local-file path rules, coordinate bounds, and comprehensive render-side
  validation from the 38k-word official HTML corpus.

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
