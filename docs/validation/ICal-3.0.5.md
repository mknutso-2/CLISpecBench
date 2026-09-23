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
