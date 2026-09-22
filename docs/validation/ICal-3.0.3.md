# ICal 3.0.3 validity correction — 2026-09-22

This tests-only patch preserves every model-visible input and every reference
implementation. It corrects one invalid positive fixture and removes one
unsupported invalid-input recovery oracle. The suite changes from 468 to 467
cases. Original generation results, sources, transcripts and usage remain intact.

## Public authority and changes

RFC 5545 §§3.6.1 and 3.8.2.4 (supplied text around lines 2922–2928 and
5439–5443) require DTSTART on a VEVENT when VCALENDAR has no METHOD. The
cancelled-override positive omitted both METHOD and the override's DTSTART.
A conforming reader could reject that document before exercising cancellation.
The fixture now includes DTSTART equal to the RECURRENCE-ID. Its existing
assertions still require exactly one occurrence at that time with
`cancelled: true`, as the public summary §§7 and 9.2 specify. A cancellation
does not create an exception to the RFC's required-property rule.

The removed `test_missing_required_alarm_properties_warns` omitted TRIGGER and
required successful parsing, preservation of the containing event, and a
`malformed_value` warning. RFC 5545 §3.6.6 requires ACTION/TRIGGER in valid
alarms, but neither that RFC nor RFC 9074 prescribes the missing-property reader
recovery policy. The technical contract permits structured exit-1 errors for
malformed input. Summary §10 describes `malformed_value` for an unparseable
value, which does not establish that an absent property must produce this code.
The test therefore imposed hidden behavior. Removing it avoids replacing it
with a weak assertion that accepts almost any recovery path. Valid alarm and
typed-trigger coverage remain. Explicit rejection/recovery policy is deferred
in `non-rs274-2026-09-12/public-clarifications.md` until a public-input revision.

## Failure attribution

The completed Sol Max C++ generation scored 463/468 under 3.0.2. These two
observations cannot fairly be called model defects. Its other three failures
have independent public support: two cases share an EXRULE implementation that
unconditionally excludes DTSTART even when it does not match the exclusion
rule (summary §8's subtractive filter); the third omits the forbidden
RECURRENCE-ID check for METHOD:ADD (RFC 5546 §3.2.4). Report two defect families,
not three independent bugs. No shared schema gate or score reweighting is added.

Earlier published Astra C++, Astra Rust and Terra Python also failed the
removed alarm case. Any earlier claim that this specific recovery-code failure
was an unequivocal model defect is withdrawn. Their original scores and
editorial text remain preserved in the regrade audit chain.

## Validation

All 28 non-RS274 assembled prompt hashes match the prior committed checkpoint.
The unchanged C++ reference passes **467/467** under offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
Root and independent reviewers checked the public authority and fixture scope;
the scan found no other no-METHOD cancelled-override positive missing DTSTART.
The two edited test files pass strict Pyright; Ruff check and format pass for
the full ICal suite. A broader Pyright invocation reports five pre-existing
unknown-type import errors in unchanged shared fixture imports in conftest.py.

Independent disposable reference controls use the same offline image:

| Control | Prior cancellation fixture | Repaired fixture |
| --- | --- | --- |
| General no-METHOD/missing-DTSTART rejection | 15/16, cancellation fails at exit-0 precondition | 16/16 |
| Force emitted override `cancelled` to false | Not needed | 15/16, cancellation fails at its boolean assertion |

The 15 other cases in the focused module pass throughout. The repaired test
therefore admits strict input validation while still detecting lost cancellation
semantics. All control and reference source hashes remain unchanged after runs.

Test suite hash:
`0d248ca623958c8e513136119d538a7c1066d710303deeab8852d2f75ed51f06`.
Local evidence is under `work/non-rs274-audit/ical-3.0.3-validation/` and the
Sol C++ run ledger.

## Retained-source migration

Rubric commit `02335a6` is the basis of six sequential official Docker regrades
under the image above. Every run preserves all 466 unaffected node outcomes;
the repaired cancellation positive passes in all six. Original source and raw
result hashes are unchanged. No regrade makes a model call or adds generation
cost. Five prior publications are retained in full in their replacement audit,
including existing audit links; Sol C++ is a newly reviewed publication.

| Model / language | Prior 3.0.2 | Corrected 3.0.3 |
| --- | ---: | ---: |
| Astra C++ | 466/468 | 466/467 |
| Astra JavaScript | 467/468 | 466/467 |
| Astra Python | 468/468 | 467/467 |
| Astra Rust | 465/468 | 465/467 |
| Terra Python | 448/468 | 448/467 |
| Sol C++ | 463/468 | 464/467 |

The denominator reduction removes an unsupported point from every run, including
runs that previously passed it. Sol additionally gains the repaired cancellation
point. This is a rubric correction on identical source, not an implementation
improvement. Astra C++ and JavaScript retain the EXDATE/orphan-override
warning defect; Astra Rust also lacks the ADD prohibition warning. Terra's 19
remaining correlated observations retain their prior outcomes. Sol's three
remaining observations are the two defect families described above.

Sol's completed generation retains 247 tool calls (142 commands, 101 file
changes, three rejected patches and one rejected cleanup request), 96,801
reasoning tokens within 188,251 output tokens, and the $18.577074 API-equivalent
estimate. Final clean builds and sanitizer smoke runs are corroborated; the
model's local fixture sweeps mostly check process success and JSON syntax,
not exact expected semantics. Planned dateutil comparison was unavailable.
These estimates are not subscription charges.

Both rebuilt dashboards pass full migration validation: 1,842 runs and
1,172,452 test rows, with all unrelated records unchanged except their shifted
run indexes. The six target projections match the linked grader records. Exact
identity comparisons retain the removed alarm test in historical publications,
so the global unique count remains 20,542. An initial scratch validator wrongly
assumed that removing a current test removed its historical identity; the failed
log is preserved, and the corrected validator passed 38 synthetic controls and
the live comparison without changing dashboard data. The live check used
52,124 KiB peak RSS under a 512 MiB limit and zero swaps. Evidence:
`work/non-rs274-audit/ical-3.0.3-validation/dashboard-validation-v2.json`.
