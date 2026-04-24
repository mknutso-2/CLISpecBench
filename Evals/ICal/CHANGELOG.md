# ICal Eval Changelog

## v1.0.0 — 2026-04-22

**Authoritative-spec release.** Previous versions shipped a
clean-room ~500-line summary of RFC 5545. v1.0 reverses the
authority relationship: the agent now receives the IETF RFCs
themselves verbatim, and the clean-room file is demoted to a
navigation index.

Test count: **245** (was 105).

**New docs structure** ([`prompt/docs/`](prompt/docs/)):

- `docs/authoritative/rfc5545.txt` — core iCalendar spec (RFC 5545,
  September 2009, 345 KB / 165 pages).
- `docs/authoritative/rfc5546.txt` — iTIP scheduling (RFC 5546,
  318 KB).
- `docs/authoritative/rfc6868.txt` — parameter-value escaping
  (RFC 6868, `^n`, `^'`, `^^`).
- `docs/authoritative/rfc7529.txt` — non-Gregorian recurrence rules
  with `RSCALE` (RFC 7529).
- `docs/authoritative/rfc7986.txt` — new calendar-level properties
  (RFC 7986: NAME, REFRESH-INTERVAL, COLOR, IMAGE, CONFERENCE,
  SOURCE, and applicability of CATEGORIES / URL / GEO / LOCATION to
  components beyond VEVENT).
- `docs/summary.md` — reworked from the former clean-room spec into
  a reading index pointing into the RFCs. Explicitly notes the
  RFCs govern when they disagree.
- `docs/LICENSES.md` — preserves IETF TLP 5.0 notices; explains
  the multi-license repo structure.

**Contract expansion** ([`technical-requirements-prompt.md`](prompt/technical-requirements-prompt.md)):

- **Calendar-level object** expanded to include RFC 7986 properties
  (NAME, DESCRIPTION, REFRESH-INTERVAL, SOURCE, COLOR, URL,
  CATEGORIES, IMAGE, CONFERENCE).
- **VEVENT / VTODO / VJOURNAL / VFREEBUSY objects** expanded with:
  `priority`, `transp`, `url`, `geo`, `resources`, `contact`,
  `created`, `last_modified`, `attachments`, `conferences`,
  `color`, `images`, `alarms`.
- **ATTENDEE / ORGANIZER** expanded to the full RFC 5545 §3.2
  `cal-address` grammar: `cn`, `cutype`, `role`, `partstat`,
  `rsvp`, `member`, `delegated_from`, `delegated_to`, `sent_by`,
  `dir`, `language`.
- **RDATE** entries may be plain ISO-8601 strings OR period objects
  (`{"start": ..., "end": ...}` or `{"start": ..., "duration": ...}`)
  per RFC 5545 §3.8.5.2 `VALUE=PERIOD`.
- **RECURRENCE-ID** normalized to an object `{value, range, tzid}`
  rather than a bare string; `range` is `THISANDFUTURE | null`.
- **VTIMEZONE** may contain multiple STANDARD / DAYLIGHT observances
  for historical rule changes per RFC 5545 §3.6.5 (last-modified,
  tzurl fields added).
- **VALARM** parsed and surfaced in event/todo `alarms` arrays:
  `action`, `trigger` with `related=START/END/null`, `duration`,
  `repeat`, `attach`, `description`, `summary`, `attendees`,
  `acknowledged`.
- **RRULE** adds `rscale` and `skip` fields (RFC 7529).
- **Warning kinds** expanded: `rscale_unsupported`, `duplicate_uid`,
  `timezone_fold_ambiguous`, `nonexistent_local_time`,
  `binary_decode_failed`, `param_escape_invalid`, `line_too_long`.
- **Expand** output adds `recurrence_id`, `range`, `cancelled` to
  each occurrence (supporting RANGE=THISANDFUTURE + explicit
  cancellation semantics per RFC 5545 §3.8.4.4).
- **Sort stability**: `occurrences` sorted by `dtstart` then
  `uid` lexicographically (explicit tie-break).

**Test-suite expansion** — targeting exhaustive RFC coverage:

- `test_valarm.py` (new): TRIGGER relative-to-start/end/absolute,
  REPEAT / DURATION interaction, ACTION dispatch (AUDIO/DISPLAY/
  EMAIL/PROCEDURE), attach/attendees on EMAIL alarms, acknowledged
  field.
- `test_attendee_grammar.py` (new): every RFC 5545 §3.2 parameter
  surface — CN / CUTYPE / ROLE / PARTSTAT / RSVP / MEMBER /
  DELEGATED-FROM/TO / SENT-BY / DIR / LANGUAGE. Delegate chains
  and MEMBER groups.
- `test_rdate_period.py` (new): VALUE=PERIOD RDATE entries in
  start/end form and start/duration form.
- `test_vtimezone_historical.py` (new): multiple STANDARD /
  DAYLIGHT observances per TZID with staggered DTSTARTs modeling
  historical rule changes (e.g. US pre-2007 DST).
- `test_param_escape.py` (new): RFC 6868 `^n`, `^'`, `^^` in
  quoted parameter values; round-trip preservation in
  `raw_properties`.
- `test_rscale.py` (new): RFC 7529 RSCALE=HEBREW / ISLAMIC /
  CHINESE parsed and at least `rscale_unsupported` warning emitted
  where expansion is not implemented.
- `test_calendar_properties.py` (new): RFC 7986 NAME /
  REFRESH-INTERVAL / SOURCE / COLOR / IMAGE / CONFERENCE parsed
  and surfaced on the `calendar` object.
- `test_line_folding_octets.py` (new): folding at exactly 75
  octets (not codepoints) with multi-byte UTF-8 characters
  straddling the boundary.
- `test_itip_methods.py` (new): method-specific requirements
  from RFC 5546 — REQUEST requires ORGANIZER, REPLY requires
  ATTENDEE + PARTSTAT, CANCEL requires STATUS:CANCELLED. Emits
  `itip_missing_property`.
- `test_recurrence_id_range.py` (new): RANGE=THISANDFUTURE
  override replaces all base occurrences from the recurrence-id
  forward with the override's shifted timing.

**Reference implementation** adds parsers and handlers for all
expanded fields above, plus:

- VTIMEZONE observance selection honors historical reload via
  per-observance DTSTART ordering.
- RFC 6868 unescape applied at parameter-value decode time.
- RFC 7529 RSCALE parse + warning (expansion is not implemented
  but the RRULE round-trips).
- RFC 7986 calendar-level property parse.
- VALARM parse + trigger normalization.
- DST fold-ambiguous / gap detection emits
  `timezone_fold_ambiguous` / `nonexistent_local_time` warnings.

## v0.3.0 — 2026-04-22

Response to the adversarial Codex review (transcript:
`codex-conversations/2026-04-21-22-07-adversarial-ical-review.md`).
Pinning under-defined RFC corners, separating semantic schema from
harness formatting, and emitting warnings the spec promised.

**Spec changes** ([`prompt/docs/icalendar-spec.md`](prompt/docs/icalendar-spec.md)):

- §4.2 Expansion algorithm: **BYSETPOS × time expansion pinned.**
  BYSETPOS applies to the fully time-expanded candidate list, not
  date-only. Matches python-dateutil; rrule.js < v2.8 paths that
  applied BYSETPOS before time-expand are non-conformant. Added
  regression tests in `test_library_divergence.py`.
- §5.1 VTIMEZONE resolution renamed to "portable-no-network mode"
  and reframed as a benchmark-design choice, not a claim about
  real-world CalDAV behavior.
- §5.1.1 **DST fold tie-break pinned.** Fall-back overlap resolves
  to pre-transition offset (PEP 495 `fold=0`, dateutil default).
  Spring-forward gap resolves to post-transition offset. Previously
  the spec only said "latest observance ≤ local"; now both edges
  are explicit with rationale and conformance language.
- §5.1.2 Unresolved TZID policy clarified: best-effort continuation
  (emit `unresolved_tzid`, treat as floating, surface `tz` field on
  the occurrence). Alternative strict-failure policy documented as
  conformant if implementations declare it on `--help`.

**Contract changes** ([`prompt/technical-requirements-prompt.md`](prompt/technical-requirements-prompt.md)):

- **Top-level key order is now a harness-recommended convention,
  not mandatory**. Tests assert only that the required keys are
  present, not that they appear in a specific order.
  (The adversarial review flagged this as contract leakage — the
  eval was scoring JSON-recipe compliance on equal footing with
  RFC comprehension.)
- `occurrences` sort order remains semantically mandatory.
- Warning-kind list moved to a dedicated section; `message` text
  is NOT asserted.

**Reference implementation** changes:

- `rrule.cpp` now emits `orphan_override` warnings for RECURRENCE-ID
  overrides that do not match any produced base occurrence (UID
  missing, time mismatched, or EXDATE-masked). Orphan overrides are
  still surfaced as standalone occurrences per spec §7.
- DST fall-back fold behavior formally documented as fold=0
  (pre-transition). This was already the impl's behavior; the spec
  previously disagreed.

**Test additions** (`test_library_divergence.py`, 8 new tests):

- BYSETPOS × BYHOUR picks last time-slot (not last date).
- BYSETPOS=1,-1 picks first-and-last Mondays monthly.
- WEEKLY+WKST=SU biweekly crossing week boundary (dateutil #1398).
- EXDATE beats override (produces orphan_override warning).
- Orphan override from non-matching UID.
- Orphan override from recurrence-id time mismatch.
- DST fall-back ambiguous-time uses pre-transition offset.
- DST spring-forward gap-time uses post-transition offset.

Total test count: **105** (was 97).

## v0.2.1 — 2026-04-21

Test-coverage fill. v0.2.0 had a full spec and a full reference
implementation, but the test suite only lightly probed the
adversarial corners that justify the eval. v0.2.1 adds 18
adversarial tests (new file `test_adversarial_corners.py`) and two
reference-implementation additions to support them.

**New tests** (18 total; 58 v0.1 + 21 v0.2 + 18 adversarial = 97):

- DST boundary crossings: spring-forward 1am / 3am on US transition
  day, fall-back on transition day, a recurring weekly event
  crossing the spring-forward boundary (offset change visible
  mid-series), Europe/London GMT↔BST, multi-year TZID resolution
  4 years after VTIMEZONE's DTSTART anchor.
- Sub-day FREQ crossings: HOURLY crossing midnight, MINUTELY
  crossing hour, HOURLY crossing month boundary.
- BYHOUR interacting with non-DAILY FREQ: WEEKLY+BYDAY+BYHOUR,
  MONTHLY+ordinal-BYDAY+BYHOUR, YEARLY+BYMONTH+BYMONTHDAY+BYHOUR.
- `RECURRENCE-ID;RANGE=THISANDFUTURE` override shifts all future
  occurrences by the override's DTSTART delta.
- EXRULE non-trivial: EXRULE + weekly base (2nd Friday of month
  excluded); EXRULE + EXDATE combined.
- BYYEARDAY expansion: positive (day 100 across a leap year
  boundary), negative (day −1 = Dec 31).

**Reference implementation additions**:

- `BYYEARDAY` expansion in YEARLY FREQ: convert each day-of-year
  value to a calendar date, respecting leap years; apply BYMONTH
  and BYDAY filters afterwards. Negative values count from the
  year's end.
- `RECURRENCE-ID;RANGE=THISANDFUTURE`: on the earliest
  THISANDFUTURE override per UID, compute the UTC shift between
  the override's `DTSTART` and its `RECURRENCE-ID` target; apply
  that shift to every base occurrence at or after the target.
  Non-THISANDFUTURE overrides continue to apply exact-match
  replacement and cancellation semantics.

No contract changes. No breaking changes. Bumping patch version.

## v0.2.0 — 2026-04-21

**Full-spec eval.** v0.1 deferred VTIMEZONE, sub-day frequencies, the
BYHOUR / BYMINUTE / BYSECOND / BYYEARDAY / BYWEEKNO RRULE parts,
VTODO / VJOURNAL / VFREEBUSY, RECURRENCE-ID overrides, iTIP METHOD,
and EXRULE. v0.2 is the full RFC 5545 eval.

**Additions:**

- **VTIMEZONE** — parsed into `timezones` with `standard` / `daylight`
  observances, each carrying `dtstart`, `tzoffsetfrom`, `tzoffsetto`,
  `tzname`, optional `rrule`, and `rdate` list. During `expand`, zoned
  DATE-TIMEs are resolved to UTC by looking up the observance active
  at the event's local time and applying its `TZOFFSETTO`.
- **`unresolved_tzid` warning** during `expand` when a TZID references
  a VTIMEZONE not defined in the file.
- **Sub-day frequencies**: `SECONDLY`, `MINUTELY`, `HOURLY` expand
  correctly with `INTERVAL`, `COUNT`, `UNTIL`, and the BYxxx time
  parts.
- **BYHOUR / BYMINUTE / BYSECOND** expansion within DAILY+
  frequencies, producing the cartesian product of time slots per
  candidate date. Applied in the RFC 5545 §3.3.10 fixed order.
- **BYYEARDAY / BYWEEKNO** parsed; produce no warning in v0.2 (the
  reference impl supports them as filters in YEARLY where tests
  require).
- **BYSETPOS** applies to the full datetime candidate set, not just
  dates, to handle interactions with time expansion correctly.
- **RECURRENCE-ID overrides**: an event with `RECURRENCE-ID` replaces
  the matching base-event instance. `STATUS:CANCELLED` overrides
  remove the instance. Occurrences carry an `override` boolean.
- **EXRULE** (deprecated but supported) applied as a subtractive
  filter over expanded occurrences. Still emits `exrule_deprecated`
  warning.
- **VTODO / VJOURNAL / VFREEBUSY** parsed and surfaced in the parse
  output at the new top-level keys `todos`, `journals`, `freebusy`.
- **METHOD** and **CALSCALE** surfaced on the `calendar` object.
- **Attendee PARTSTAT** parameter surfaced.

**Contract changes (breaking vs. v0.1):**

- **Top-level parse JSON keys** expanded and reordered:
  `calendar`, `events`, `todos`, `journals`, `freebusy`, `timezones`,
  `warnings`. (Replaced the v0.1 `unsupported_components` key.)
- **Expand occurrences** now include `tz` (TZID) and `override`
  fields. `tz` is null for floating/UTC occurrences.
- **TZID handling**: v0.1 emitted `unsupported_tzid` at parse time
  and treated the value as floating. v0.2 preserves TZID through
  parse (surfaces the param in `raw_properties`), and only emits
  `unresolved_tzid` at expand time if the referenced TZID has no
  matching VTIMEZONE.
- **`unsupported_freq` / `unsupported_rrule_part` warnings removed.**
  All FREQs and BYxxx parts are now supported.

**Reference implementation** additions: VTIMEZONE parsing, TZID
resolution via observance walk + offset application, sub-day
interval advance, time-expand helper, EXRULE expansion, override
matching by UTC-comparable key. Total C++ LOC grew from ~1,200
(v0.1) to ~1,700.

**Known bounded gaps vs. full RFC 5545:**

- iTIP scheduling (RFC 5546) method-specific property validation is
  not exercised beyond surfacing METHOD.
- `RANGE=THISANDFUTURE` on `RECURRENCE-ID` is preserved in the
  parsed event but v0.2 applies overrides only at the exact
  recurrence-id, not forward.
- BYYEARDAY / BYWEEKNO are recognized but tests exercise them
  lightly.

## v0.1.0 — 2026-04-20

Initial eval release. Scope: iCalendar (RFC 5545) `.ics` text parsing,
property parameter decoding, and RRULE expansion for the common
frequencies (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`) with common
modifier parts (`INTERVAL`, `COUNT`, `UNTIL`, `BYDAY`, `BYMONTHDAY`,
`BYMONTH`, `BYSETPOS`, `WKST`). Output is canonical JSON listing
VCALENDAR components, parsed VEVENTs, and expanded occurrences within
an agent-supplied date range.

**Deferred to v0.2+** (documented in `README.md`):

- `VTIMEZONE` parsing and external tzdata resolution. v0.1 requires
  UTC or floating-time inputs only.
- `BYYEARDAY`, `BYWEEKNO`, `BYHOUR`, `BYMINUTE`, `BYSECOND` RRULE
  parts — these produce `unsupported_rrule_part` warnings in v0.1.
- `EXRULE`, `VTODO`, `VJOURNAL`, `VALARM`.
- `RECURRENCE-ID` override resolution beyond surfacing the field.
- iTIP scheduling semantics (RFC 5546).

The first-pass proposal in
[`Evals/EVAL_CANDIDATE_DISCUSSION.md`](../EVAL_CANDIDATE_DISCUSSION.md) pitched ICal as
the strongest non-BibTeX candidate specifically because the
adversarial RRULE corners (BYSETPOS + BYDAY, WKST interactions) are
well-documented sources of real bugs in mainstream libraries
(rrule.js #375, #309, #556; dateutil #1398). v0.1 targets those
corners while deferring the VTIMEZONE complexity that would require
an external tzdata.
