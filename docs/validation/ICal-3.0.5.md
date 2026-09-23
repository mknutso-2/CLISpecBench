# ICal 3.0.5 CANCEL fixture isolation — 2026-09-22

This tests-only correction changes six existing cases, retaining their node IDs
and the 467-case denominator. All 28 assembled non-RS274 model inputs and the
ICal reference source remain identical to checkpoint `deb5c75`. The original
generation results, transcripts, sessions and source trees are preserved.

## Authority and failure attribution

The fresh Sol Max Python retry completed normally at **463/467** on 3.0.4.
Three failures share one invalid prerequisite: the purported valid CANCEL
fixtures carry `SEQUENCE:0`. The implementation correctly warns about SEQUENCE;
these are not three separate STATUS defects.

The supplied RFC 5545 §3.8.7.4 starts the revision sequence at zero. RFC 5546
§2.1.4 requires incrementing it each time ADD or CANCEL is used (supplied lines
634–635); §3.2.5 repeats that obligation for VEVENT cancellation (1636–1637).
The summary's omission of an explicit positive annotation for CANCEL does not
override the RFC: both public base prompt and summary expressly prioritize it.
A stateless reader cannot verify an exact prior-to-current increment, but may
legitimately warn about zero. The test need not impose a new zero-rejection
policy; it must use an unambiguously valid positive sequence for other checks.

Only the five CANCEL-specific STATUS/ORGANIZER fixtures now use `SEQUENCE:1`.
The shared initial sequence for other methods remains zero. The invalid-STATUS
negative identifies `method=CANCEL`, `component=VEVENT`, `property=STATUS`,
rather than accepting an unrelated warning. The existing missing-ORGANIZER
metadata assertion remains intact.

The sixth case still deliberately omits SEQUENCE. It now names an affected
ATTENDEE and omits STATUS, the valid uninvite form in RFC 5546 §3.2.5. Requiring
the SEQUENCE warning's method/component/property metadata prevents a different
iTIP violation from satisfying this test. These are already public fields.

The Python submission separately omits the VEVENT ADD prohibition on
RECURRENCE-ID, despite supplying the other required fields. RFC 5546 §3.2.4
marks that property presence zero. The existing phase-3.0.4 test avoids forcing
the ambiguous RECURRENCE-ID property-name enumeration; this remains a supported
implementation defect. A measured retained-source regrade is required before
publishing its corrected score.

## Validation

Ruff and strict Pyright pass for both edited test modules. The unchanged C++
reference passes **467/467** in offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.

Disposable reference controls run sequentially in the same image:

| Control | Prior six cases | Corrected six cases |
| --- | ---: | ---: |
| Warn on zero CANCEL sequence | 3/6; only the three invalid positives fail | 6/6 |
| Replace STATUS diagnostic with unrelated DTSTAMP diagnostic | — | 5/6; only invalid STATUS fails |
| Replace ORGANIZER diagnostic with unrelated DTSTAMP diagnostic | — | 5/6; only missing ORGANIZER fails |
| Replace SEQUENCE diagnostic with unrelated DTSTAMP diagnostic | — | 5/6; only missing SEQUENCE fails |

The negative controls retain an iTIP warning so a broad warning-kind assertion
would wrongly award credit. They verify the named behavior, not mere warning
presence. Every grade has zero errors/skips and preserves its source hash.
No control makes a model call or executes submission code on the host.

Suite hash:
`975e15674d3802b6d44a5ccc401121319a4ab3d18f0c594a34d600a29f68adb1`.

Retained-source migration must compare all 461 untouched outcomes for each of
the eight previously published current-cohort sources and the fresh Python
retry. Prior publication payloads and linked audit history remain preserved.
The local migration ledger is `work/non-rs274-audit/ical-3.0.5-validation/`;
generation review is in `work/non-rs274-audit/runs/ical-py-gpt-5.6-sol-max/`.

## Retained-source results

All nine official regrades use rubric commit `6bd747a` and the pinned image
above. Every source preserves all 461 untouched outcomes. The eight prior
publications also preserve all six changed-case outcomes; the fresh Sol Python
retry gains exactly the three justified CANCEL positives. There are no errors
or skips. Full prior publication payloads and linked audit history are retained.

| Model / language | Prior 3.0.4 | Corrected 3.0.5 |
| --- | ---: | ---: |
| gpt-6-astra / cpp | 466/467 | 466/467 |
| gpt-6-astra / js | 466/467 | 466/467 |
| gpt-6-astra / py | 467/467 | 467/467 |
| gpt-6-astra / rs | 465/467 | 465/467 |
| gpt-5.6-sol / cpp | 464/467 | 464/467 |
| gpt-5.6-sol / js | 462/467 | 462/467 |
| gpt-5.6-sol / rs | 461/467 | 461/467 |
| gpt-5.6-terra / py | 448/467 | 448/467 |
| gpt-5.6-sol / py | 463/467 | 466/467 |

Independent corrected-grade review approves Sol Python at **466/467**, with one
supported ADD diagnostic defect family. Its final completeness claim exceeds
the measured coverage. Actual schema, recurrence, DST, duration and CLI checks
are corroborated; the last range-order edit was not followed by a targeted
range regression. The official grader does exercise the final saved source.

The generation retains **104,099 reasoning tokens within 202,566 output tokens**,
35,463,654 input tokens including 34,944,896 cached tokens, and a **$20.104310**
API-equivalent estimate. This is not a subscription charge. Accounting commit
`f0f3dbb` recognizes the exact display-only exit-code template after one awaited
command; it does not change the v2 definition. Independent evidence and the
recomputed audit agree on **230 tool calls**: 229 canonical actions and one
pre-process rejection. The raw null metric remains preserved, and every
non-tool usage field is unchanged. The regression fails on the old parser;
59 tests/58 subtests and 14 telemetry tests pass, alongside Ruff, strict
Pyright and Node syntax validation. The earlier quota-interrupted Python
attempt remains preserved and excluded.

Both dashboards pass the full migration comparison: **1,845 runs and
1,173,853 test rows**, with exactly one added run and 467 added rows. All
unrelated rows are preserved except expected run-index shifts; unique test
identities remain 20,550. The streamed validation takes 162.03 seconds, peaks
at 55,152 KiB RSS under a 512 MiB address-space cap, and records zero swaps.
The build takes 35.97 seconds and peaks at 37,264 KiB, also without swapping.
All 65 validator controls pass, including an explicit SHA-bound allowance for
the approved null-to-230 tool-count correction; every non-tool usage field
remains fixed. Independent provenance review preserves 1,864 unrelated
publication files, 955 prior audit files and all eight prior target payloads.
The known ancillary CSV newline normalization is documented and untouched.
