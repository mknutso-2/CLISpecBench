# ICal 3.0.4 fixture and diagnostic-oracle correction — 2026-09-22

This tests-only patch retains 467 cases and preserves every model-visible input
and reference implementation. Seven cases change, including two descriptive
renames; the other 460 cases retain their outcomes in the required migration
comparison. Original generation artifacts, usage and publication history are
preserved.

## Public authority

RFC 5545 §3.6 requires at least one calendar component, in both its ABNF and
normative prose (supplied lines 2838, 2867–2868 and 2878–2882). It explicitly
permits a VTIMEZONE-only calendar. RFC 7986 §4 extends calendar properties; it
does not permit a component-free calendar. Three positive fixtures incorrectly
required accepting one. The calendar-property case now supplies a valid fixed
VTIMEZONE; the array-schema and missing-availability cases supply a valid VEVENT.
They still measure calendar properties and the required output collections.

The isolated METHOD:ADD fixture correctly violates RFC 5546 §3.2.4 by carrying
RECURRENCE-ID. Summary §6 requires a diagnostic for inconsistent properties.
The technical warning schema requires method/component metadata, but its list
of property names omits RECURRENCE-ID. This case now checks the required warning
kind, ADD method and VEVENT component without forcing a resolution of that
metadata ambiguity. All required properties remain present; other property
metadata assertions remain intact.

Summary §§6–7 and 10 require orphan diagnostics uniformly across events, todos
and journals, but do not select parse versus expand as the mandatory validation
phase. Three unchanged finite-series fixtures now accept the diagnostic from
parse or, if absent there, expansion over March 1–April 1, 2026. That window
contains every base instance and override anchor in these fixtures. No todo or
journal occurrence output is required. Both commands still must succeed;
missing the warning in both phases still fails. Collection-schema checks remain
in their dedicated tests instead of gating the diagnostic fallback.

## Failure attribution and independence

Sol Max JavaScript completed voluntarily with an original score of 458/467.
Three observations share the invalid empty-calendar prerequisite; three more
share the forced parse phase. These are not six independent model defects.
The source separately lacks CANCEL STATUS and ADD prohibition checks, tests
orphan membership before EXDATE filtering, and lacks orphan validation for todos
and journals in both commands. Corrected scoring requires an actual regrade;
the original score is retained rather than edited.

The property fixture retains tolerant collection access so one array-schema
mistake does not newly fail a property-decoding test. The dedicated schema case
requires real empty arrays for absent component types. Orphan cases remain
separate component contexts, with any shared implementation gap reported as
one family. No score reweighting or broad shared gate is introduced.

## Validation

Independent reviewers checked the supplied authority, scope, final transcript,
patch, control sources and grader guards. All 28 assembled input hashes and the
reference source hash match the preceding checkpoint. The five edited test
modules pass Ruff and strict Pyright. The unchanged reference passes **467/467**
under offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.

Disposable reference controls, each run alone in that image:

| Control | Prior seven cases | Corrected seven cases |
| --- | ---: | ---: |
| Reject component-free calendars, defer orphan warnings to expand, omit ambiguous ADD property metadata | 0/7 | 7/7 |
| Suppress orphan warnings in both commands | — | 4/7; only the three orphan cases fail |
| Suppress the ADD diagnostic | — | 6/7; only the ADD case fails |
| Lose the calendar name | — | 6/7; only the property case fails |
| Emit null for empty todos/availabilities arrays | — | 5/7; only the two schema cases fail |

The positive control combines three independent permitted policy choices, not
one bug. Its recognized-component minimum is deliberately fixture-scoped and
is not a general validator for extension-only calendars. All controls preserve
source hashes and produce zero errors/skips. Negative failures reach the intended
assertions, and the null-array control leaves the property case passing.
No control or regrade makes a model call.

Test suite hash:
`cff7fe787baab73a073e1ac1b4a64d7104cd71d61b13c267d6030d8331c90f88`.

## Retained-source migration

Seven official regrades use rubric commit `2423b39` and the pinned image above.
All 460 unaffected node outcomes remain identical for every source. All seven
changed-case outcomes are also unchanged for the six previously published
sources; Sol JavaScript gains four justified points. Two test renames are mapped
explicitly, without treating them as added or removed cases.

| Model / language | Prior 3.0.3 | Corrected 3.0.4 |
| --- | ---: | ---: |
| Astra C++ | 466/467 | 466/467 |
| Astra JavaScript | 466/467 | 466/467 |
| Astra Python | 467/467 | 467/467 |
| Astra Rust | 465/467 | 465/467 |
| Terra Python | 448/467 | 448/467 |
| Sol C++ | 464/467 | 464/467 |
| Sol JavaScript | 458/467 | 462/467 |

Sol JavaScript passes the three valid calendar replacements and emits the
VEVENT orphan warning during expand. Its five remaining observations are four
families: missing VEVENT CANCEL STATUS validation, missing ADD prohibition,
EXDATE orphan membership checked before exclusions, and missing orphan checks
for both todos and journals. The corrected phase-flexible tests reach successful
parse and expand before failing for absent diagnostics; empty event-occurrence
arrays on todo/journal inputs are not penalized.

Independent corrected-grade review approved publication with these limits.
The final message's complete-CLI claim overstates the diagnostic coverage.
Selected semantic regression assertions are corroborated, including five exact
expected-array checks after the final edit. A final pipeline's count assertion
could be masked by its following printf, so its outer exit status is not proof
that the assertion was enforced. Some wider checks predate final edits; dateutil
was unavailable and no differential comparison occurred.

Accounting remains 170 tool calls (120 commands and 50 file changes), 88,969
reasoning tokens within 176,724 output tokens, and a $16.879538 API-equivalent
estimate. The raw 458/467 result, generation metadata, source and session remain
unchanged. These estimates are not subscription charges.

Both dashboard migration checks pass with **1,843 runs and 1,172,919 test rows**.
All unrelated rows remain unchanged except expected run-index shifts. Each
target matches its linked grader record; source, original result, accounting
and prior audit hashes are preserved. The exact streamed identity comparison
derives 20,550 unique tests: two renames across four languages add eight new
identities, with historical runs retaining the old names. Validation takes
162.86 seconds, peaks at 53,356 KiB RSS under a 512 MiB address-space cap, and
records zero swaps. Its verifier also passes 49 synthetic controls (seven valid
fixtures accepted and 42 corruptions rejected). The checkpoint preserves all
60 unrelated completed rows and all seven excluded attempts exactly.

Local evidence: `work/non-rs274-audit/ical-3.0.4-validation/` and
`work/non-rs274-audit/runs/ical-js-gpt-5.6-sol-max/`.
