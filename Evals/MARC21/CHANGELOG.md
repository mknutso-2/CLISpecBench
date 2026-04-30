# Changelog

## v3.0.0 — 2026-04-29

**Breaking — invocation form is no longer Python-specific.**

`prompt/technical-requirements-prompt.md` previously opened with:

> The program must be runnable as:
> ```
> python main.py --input <request.json> --output <response.json>
> ```

That phrasing was authored when `marc21` was registered only in `py`.
After the harness language-decoupling refactor (clispecbench commit
`0e1d965`), `marc21-cpp`, `marc21-js`, and `marc21-rs` are now valid
task ids — but the prompt was still telling agents the literal
invocation form was `python main.py …`. Cross-language agents
reconciled this by shipping a real native implementation alongside a
`main.py` Python wrapper that accepts `--input/--output` and exec's
the binary. The harness ignores the wrapper and invokes the native
binary directly, so the agent's binary must independently honor
`--input/--output`. When it didn't (e.g. the binary used positional
args and relied on the wrapper to translate), tests failed with
`returncode != 0` even though the agent's logic was correct.

The contract is now language-agnostic:

> The program must accept these command-line flags:
> - `--input <path>`: path to a JSON file containing the request.
> - `--output <path>`: path where the program writes its JSON response.

This is the same flag-shape contract used by BibTeX, ICal, IGES,
RS274, and WordCount.

**Breaks:** all prior `marc21-cpp`, `marc21-js`, `marc21-rs` runs are
invalidated; their agents were given a Python-specific invocation form
that is no longer the contract. Prior `marc21-py` runs remain valid in
spirit (the new prompt is a strict generalization — `python main.py
--input X --output Y` still satisfies it) but should be re-run for
prompt-version uniformity.

The self-containment clause and CLI smoke gate from v2.8.2 remain in
place.

## v2.8.2 — 2026-04-25

Two follow-ups from a multi-run analysis on v2.8.1 that surfaced a rule-3
cascade: in some runs (e.g. one codex run scored 0.017, one Claude run
scored 0.386) a single agent CLI startup bug failed every test that
invoked the binary, masking ~2,840 independent capability tests with the
same `returncode != 0` assertion. The score variance from 0.02 to 0.98
across runs of the same model was not reflective of capability differences;
it was the cascade.

**Test-side rule-3 fix — CLI smoke gate** (`tests/conftest.py`):

- The shared `submission_command` fixture is now overridden in marc21's
  conftest. It runs a single minimum-valid `inspect` request once per
  session before returning the command tuple. If the program exits
  non-zero, the fixture calls `pytest.skip` with a uniform reason, which
  transitively skips every test that requests `submission_command` (i.e.
  every CLI-invoking test). Tests that do not invoke the CLI
  (`test_build`, anything driven only by `prepared_submission`) keep
  running.
- Net effect: a startup-class bug now costs one clearly-named gate skip
  per affected test instead of ~2,840 near-identical assertion failures.
  The pass-rate is unchanged (skipped tests still count in `total`), so
  scoring still reflects actual capability — only the diagnostic surface
  changes.

**Prompt clarification — submission self-containment**
(`prompt/technical-requirements-prompt.md`):

- Added a user-voice deployment constraint: only files placed in `output/`
  are present at run time; anything outside `output/` (including `docs/`)
  is unavailable to the running program. Phrased as a deployment
  statement, not as eval/grading instruction.
- Removes the ambiguity that drove the codex `_find_docs_root()` failure
  mode, where the agent reached for prompt-time HTML files at run time.

## v2.8.1 — 2026-04-25

Bug fix: Test infrastructure was reading two JSON rules files
(`marc21_field_rules.json`, `marc21_fixed_field_rules.json`) from
`reference-implementation-py/generated/` via a `parents[1]` path.
The harness scoring container only mounts `tests/`, the submission,
and the clispecbench `src/`, so the reference-implementation tree
is unavailable at scoring time. The result was an unconditional
collection-time `FileNotFoundError` in `test_fixed_fields.py` and
`marc21_spec_support.py` that caused pytest to exit with code 2 and
no report.json — every run scored 0/0 regardless of agent output.

- Copied `marc21_field_rules.json` and `marc21_fixed_field_rules.json`
  into `tests/generated/` (alongside the existing
  `marc21_field_examples.json`).
- Updated `marc21_spec_support.py` and `test_fixed_fields.py` to load
  from the new in-tree path.
- Reference implementation paths are unchanged.

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
