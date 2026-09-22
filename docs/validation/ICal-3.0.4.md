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
Retained-source migration is the next required step.

Local evidence: `work/non-rs274-audit/ical-3.0.4-validation/` and
`work/non-rs274-audit/runs/ical-js-gpt-5.6-sol-max/`.
