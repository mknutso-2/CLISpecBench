# ICal 3.0.2 validation — 2026-09-12

This patch changes only hidden fixtures, assertions and the C++ reference. All
model-visible prompt and supplied RFC bytes remain identical. Eleven failures
in a completed Astra Python submission, plus a Terra CANCEL failure, exposed
the following scoring problems:

| Cases | Public basis and repair |
| --- | --- |
| Weekly BYDAY and monthly BYSETPOS | RFC 5545 §3.8.5.3 explicitly leaves unsynchronized DTSTART/RRULE recurrence sets undefined. Start on the first selected Friday/17:00 slot; expected recurrence sequences remain unchanged. |
| RDATE fold, year-end gap and its mirror | RFC 5545 §3.8.3.3 defines TZOFFSETFROM as the state in effect immediately before an onset. The fixtures repeatedly declared a transition from an offset no longer in effect. Add the intervening return transition so each tested fold/gap actually exists. |
| Valid METHOD:ADD | RFC 5546 §3.2.4 allows zero attendees but expressly forbids RECURRENCE-ID. Remove that unrelated forbidden property. |
| VFREEBUSY missing UID/DTSTAMP metadata | The public iTIP matrix specifies property presence. Omit UID instead of using a present empty TEXT property, avoiding an unstated empty-value-to-missing-warning convention. |
| Nested component isolation | RFC 9073 §7.1 permits VLOCATION/VRESOURCE within PARTICIPANT, not VALARM. Use a legal nested VLOCATION and require the containing event's UID and description to stay unchanged. |
| 500-event parse | RFC 5545 §3.3.5 requires eight date digits. The old formatting inserted an extra zero and generated nine-digit dates for every event. |
| Implicit VALARM RELATED | RFC 5545 §3.2.14 defines the semantic default START, while the public JSON schema permits null and does not require materializing omitted parameters. Accept null/START, preserve the exact duration, and reject a contradictory END. Explicit RELATED preservation remains independently tested. |
| AVAILABLE RECURRENCE-ID parameters | RFC 5545 §3.6.5 places VTIMEZONE at VCALENDAR scope. Move it outside VAVAILABILITY; keep the same AVAILABLE parameter assertions. |
| CANCEL scope and organizer isolation | RFC 5546 §3.2.5 permits omitted STATUS when uninviting selected attendees, and requires CANCELLED for whole-event cancellation. Name an affected ATTENDEE in every CANCEL fixture; use CANCELLED in the missing-organizer negative and observe its exact ORGANIZER metadata. |

The repaired ADD organizer and SEQUENCE negative fixtures now satisfy unrelated
requirements, and their observations require the exact method/component/property
warning metadata. An unrelated warning can no longer earn these points. A new
control isolates ADD's forbidden RECURRENCE-ID row, and the C++ reference now
emits the required structured warning. There is no generic shared acceptance
gate or score reweighting, and dedicated schema coverage remains intact.

Pinned offline Docker image:
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
The repository was mounted read-only and all execution used disposable copies.

| Implementation | Previous 3.0.1 grade | Corrected 3.0.2 grade |
| --- | ---: | ---: |
| Corrected C++ reference | — | 468/468 |
| Retained GPT-6 Astra Max Python | 456/467 | 468/468 |
| Retained GPT-5.6 Terra Max Python | 444/467 | 448/468 |

The old C++ reference fails the new isolated RECURRENCE-ID prohibition control
(0/1, 467 deselected), while both the corrected reference and Astra pass it.
No full run has skips or errors. Actual responses from the original suspect
Astra fixtures confirm deliberate document validation: forbidden RECURRENCE-ID,
invalid nine-digit date, VALARM illegally nested in PARTICIPANT, and VTIMEZONE
illegally nested in VAVAILABILITY. They were not infrastructure failures.
The corrected reference emits START for omitted RELATED while Astra emits null;
the repaired test accepts both representations and preserves the duration.

The final CANCEL fixtures also reveal a Terra implementation defect: it treats
any ATTENDEE as proof of selective uninviting and warns when STATUS:CANCELLED
is present. RFC 5546 expressly permits affected attendees on whole-event
cancellation. The two uppercase/lowercase CANCELLED positives now expose this
same bug, while the corrected selected-attendee case passes. In total, six
previous Terra fixture failures recover, two previously masked model failures
appear, and the new ADD RECURRENCE-ID control fails. Its remaining 20 failures
are implementation behavior, not infrastructure failures. Exact reports are
retained as `astra-final.json`, `terra-final.json` and `reference-final.json` in
the isolated validation work directory.

No new missing-STATUS negative is scored: with an attendee, no STATUS is the
permitted selective form; without an attendee, a fixture cannot isolate that
property from missing recipient context or infer whole-event intent. The
reference's CANCEL comments are corrected without adding that inference.

Test suite hash:
`d426a7ab321e19565ecd8cdd36962a2a75527423f11046a1dc039b8cb23b2d35`.
Ruff and strict Pyright pass for the isolated test suite. A byte comparison of
all prompt-directory files confirms unchanged public inputs. Source, original
results, sessions, token usage and raw grade artifacts remain unchanged. These
isolated measurements validate the rubric; official regrades are separate
records with their own provenance.

A future public-input revision may explicitly specify default materialization
for nullable output fields and warning behavior for present empty identifiers.
Those choices cannot fairly be imposed retroactively. The existing deferred
spring-gap summary discrepancy remains documented in the 3.0.1 validation;
RFC precedence already determines the scored behavior.
