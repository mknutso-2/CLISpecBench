# ICal deferred fix: typed/raw alarm duplication

## User decision — October 2, 2026

The user directed us to document the issue for a future fix and continue data
collection. The publication hold below is historical and is now resolved: retain
the frozen ICal 3.0.5 suite and its observed scores, attach this limitation to the
affected result reviews, and resume the four-slot collection. Do not change
prompts, tests, scoring, or raw evidence during this collection, and do not pause
again solely for this known ambiguity. Other review and infrastructure gates
still apply.

**Future work:** at the next planned eval revision, explicitly define whether
typed VALARM properties must also appear in `raw_properties`, reconcile the
summary with the detailed schema, and align the four assertions below with that
documented policy. Use independent oracle review, focused positive/negative
controls, reference validation, and the normal eval version/changelog process.
Any later saved-source regrade must preserve the original result and report the
versioned score change separately. This note implements none of those changes.

## Historical hold and evidence

Related observations from the completed Terra JavaScript/Rust reviews belong in
the same future policy clarification. JavaScript also preserves decoded ATTENDEE
CN, RDATE PERIOD and two RELATED-TO RELTYPE values in typed fields while four tests
require duplicate raw records. Rust preserves Chinese/Islamic unsupported RSCALE
rules in typed fields while two tests require original raw RRULEs. The Hebrew
case must be distinguished: its typed BYMONTH loses the leap-month `L` marker,
which is genuine data loss without a raw fallback. Preserve all observed outcomes
and annotate these distinctions; do not infer that every raw-retention failure is
either a model defect or an oracle defect. Full evidence is in the per-UID reviews.

October 2, 2026. This is an adjudication request, not a test or scoring change.

Terra Max ICal C++ UID `add410c3-404e-42f1-85b0-3bbbaee99550` completed naturally
under frozen ICal 3.0.5: **456/467**, 11 failed, no skips/errors. At the initial
review it was unpublished and its slot was held. Raw result SHA-256:
`68617efce1e6d63a0b15e7757b5b2df81e5bf19d044df1c757541de20baeb53e`.

## Four disputed observations

These tests require named VALARM properties to appear in `raw_properties` even
when correctly represented in typed fields:

- `test_valarm.py::test_acknowledged_property`
- `test_valarm.py::test_alarm_raw_properties_include_action_trigger`
- `test_valarm_rfc9074.py::test_valarm_uid_preserved`
- `test_valarm_rfc9074.py::test_rfc9074_properties_in_raw_even_if_unfielded`

The mandatory technical schema, lines 157–176, defines typed alarm fields and a
raw-property array, but does not explicitly require duplication of every typed
property. Summary line 153 says alarms are surfaced as a raw sub-component, which
suggests preservation but does not clearly define duplication beside the detailed
typed schema. The RFCs define iCalendar, not this JSON projection. Specific public
raw-preservation rules for TZID and GAP do not establish universal duplication.

The saved source's `property_has_typed_slot`/`raw_properties_json` (main.cpp,
814–860) intentionally retain untyped properties and any properties carrying
parameters. `parse_alarm`/`alarm_json` (1494–1562) preserve the tested values in
typed fields. Two independent reviewers and the primary review found this a
defensible public-contract interpretation. Classify the four assertions as a
scoring ambiguity, not four missing alarm capabilities. The observed score stays
456/467; no adjusted official score has been calculated or published.

The other seven failures concern CANCEL STATUS and ADD RECURRENCE-ID diagnostics,
EXDATE/orphan-override ordering, two pre-transition timezone-gap observations,
reversed RDATE periods, and Gregorian RSCALE SKIP=FORWARD handling. Keep these
separate from the disputed raw-property rule. Full review is preserved in the
per-UID audit when finalized.

## Accounting and disposition

The completed generation has 24,465,353 input tokens (24,034,560 cached), 138,375
output tokens including 64,134 reasoning tokens, and $7.328998 estimated cost.
143 tools reconcile as 141 canonical actions plus two pre-item rejections. One
whole-module SyntaxError executed no nested tool and is excluded. Raw accounting
and evidence are unchanged. The network audit has 168 API-host allows and ten
denied startup asset requests, with no successful external reference acquisition.

The user prohibited prompt/test/scoring changes during collection. Therefore the
same-chat heartbeat and new dispatch were initially paused pending a decision, rather than
silently repairing tests, regrading, or publishing an unqualified result. Three
already-started workers (Terra ICal JS/Rust and IGES C++) continue naturally. No
extra chats or automations were created, and no Git changes were pushed.

The initial recommended decision was to authorize a focused test-oracle review/repair with
unchanged-input proof, independent review and saved-source regrades before ICal
publication, or retain the frozen suite and publish its observed score with this
limitation clearly attached. The user chose the latter collection policy above;
the actual fix is deferred.

## Luna Rust follow-up — October 2

UID `80f9891e-80b2-4b3b-b809-fc86693823ea`, frozen **442/467**, extends the
same review policy. Eleven failures demand duplicate raw records for typed
VALARM values (four), decoded ATTENDEE CN (one), RDATE PERIOD (one), RELATED-TO
RELTYPE (two), and unsupported RSCALE rules (three). Unlike the earlier Terra
Rust run, this source preserves the Hebrew `5L` marker as a string in typed
BYMONTH. Do not label it as marker loss or absent alarm/parameter decoding.

Two other observations lose a supplied LOCATION parameter entirely because the
typed location is only text and the raw record is omitted. These are not merely
duplicate-storage assertions. However, their fixture annotation is wrong:
`test_rfc9073_event_publishing.py` supplies LOCATION-TYPE as a parameter on
LOCATION and cites RFC 9073 section 5.1; the supplied RFC section 6.1 defines
LOCATION-TYPE as a property of VLOCATION. A future revision must separate actual
VLOCATION support from generic unmodeled-parameter preservation, correct the
fixture/citation, and explicitly define the latter output contract. Do not
describe these observations as proof of missing RFC 9073 LOCATION-TYPE support.

One additional positive fixture is invalid:
`test_vtimezone_resolution.py::test_observance_until_bounds_rrule` uses
`UNTIL=20200101T000000` inside STANDARD. Supplied RFC 5545 section 3.3.10
(lines 2265–2268) requires UTC UNTIL in STANDARD/DAYLIGHT. The Rust validator
correctly rejects that floating value before historical transitions are tested.
At the next authorized eval revision, choose a valid UTC cutoff preserving the
intended instant, then independently review and control-test the boundary;
do not mechanically append Z without considering TZOFFSETFROM. This observation
does not establish defective handling of valid UTC-bounded observances.

The remaining eleven failures cover EXRULE seed inclusion (two), fatal handling
of optional malformed values (six correlated observations), missing todo/journal
orphan warnings (two), and ADD/RECURRENCE-ID validation (one). Full source and
test anchors are in the portable per-UID review. Keep all 25 observed failures
and the original score; these notes implement no repair or adjusted score.
