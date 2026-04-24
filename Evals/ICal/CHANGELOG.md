# ICal Eval Changelog

## v1.3.0 — 2026-04-24

Eval-authoring rule-3 hardening from a 136-failure classification
review across Opus 4.7 max and gpt-5.5 xhigh runs. Fixes spec
ambiguities, removes one false impl/spec contradiction, and
tightens four test contracts to localize failures.

**Spec changes** (`prompt/docs/summary.md`):

- §5.1 **VTIMEZONE resolution** gained explicit step 4 covering
  local times before any observance's DTSTART: tool MUST use the
  earliest observance's TZOFFSETFROM (the pre-observance state
  per RFC 5545 §3.8.3.1). Was previously undefined behavior.

- §7 **Override resolution** reconciled with §9.2's occurrence
  schema: `STATUS:CANCELLED` overrides keep the occurrence in the
  array with `cancelled: true` rather than dropping it (consumers
  observe the cancellation explicitly). Reference implementation
  patched in both the non-RRULE and RRULE code paths to emit at
  the original recurrence-id time with the cancelled flag set,
  including the THISANDFUTURE + CANCELLED case.

**Contract clarifications** (`prompt/technical-requirements-prompt.md`):

- iTIP `itip_missing_property` warning contract tightened. Message
  MUST contain the adjacent phrase `<METHOD> <COMPONENT>` (or
  reverse), the specific property name token, and AT MOST ONE
  property token from the allowed list (rules out "omnibus" messages
  that list every required property and would spuriously satisfy
  every property-specific test).

**Test isolation**:

- `test_recurrence_id_cancel_marks_occurrence_cancelled` (renamed
  from `_removes_occurrence`) now asserts the §9.2 schema shape.
- `test_itip_per_component.py` `_warn_mentions_method_component_property`
  helper enforces the tightened contract; 9 assertions migrated.

## v1.2.0 — 2026-04-24

Completes PLAN.md — all remaining priorities landed. Adds 68 new
tests (342 → 410) and three new authoritative RFCs.

New authoritative RFCs under `prompt/docs/authoritative/`:

  * `rfc7953.txt` — *Calendar Availability* (August 2016, 47 KB)
  * `rfc9073.txt` — *Event Publishing Extensions to iCalendar*
    (August 2021, 58 KB)
  * `rfc9253.txt` — *Support for iCalendar Relationships*
    (August 2022, 38 KB)

Test-surface additions:

  * **B13 — Error line/column precision** (+9 tests,
    `test_error_precision.py`). Error JSON carries 1-indexed
    positive line/column; non-fatal conditions warn without
    hard-failing; warnings include uid when applicable.

  * **B11 — 75-octet folding edges** (+5 tests,
    `test_folding_edges.py`). `line_too_long` warning emitted on
    unfolded >75-octet lines; exactly 75-octet and properly-folded
    long lines do not warn; TEXT escapes preserved across folds;
    multi-byte UTF-8 chars intact across fold boundaries. Parser
    extended with LineRecord.was_folded tracking.

  * **B14 — Stress + regression** (+10 tests, `test_stress.py`).
    500-event calendar parses; RRULE COUNT=1000 expands correctly;
    HOURLY bounded by window; 20-deep override chain resolves;
    mid-file malformed entry preserves surrounding events; 50
    VALARMs on one event; YEARLY+BYMONTHDAY across a decade; UNTIL
    at window boundary inclusive; empty window → no occurrences;
    mixed UTC/floating/zoned coexist.

  * **B12 — Real-world calendar corpus** (+10 tests + 3 fixtures,
    `test_real_world_corpora.py` + `calendars/`). Gmail-style,
    Outlook-style, and iTIP REQUEST .ics exercise full feature
    stack: VTIMEZONE, RRULE, full attendee grammar, VALARM,
    quoted TZID params, X-MICROSOFT extensions.

  * **A4+B9 — RFC 9253 iCalendar Relationships** (+8 tests,
    `test_rfc9253_relationships.py`). LINK with LINKREL, GAP
    parameter on RELATED-TO, expanded RELTYPE values
    (FINISHTOSTART, FINISHTOFINISH, DEPENDS-ON, etc.),
    STRUCTURED-CATEGORIES, CONCEPT, REFID preserved in
    raw_properties.

  * **A2+B7 — RFC 7953 VAVAILABILITY** (+12 tests,
    `test_vavailability.py`). Full typed VAvailability +
    AVAILABLE sub-components; BUSYTYPE values; PRIORITY;
    ORGANIZER; RRULE on AVAILABLE; multiple VAVAILABILITY per
    calendar; empty availabilities key always present.

  * **A3+B8 — RFC 9073 Event Publishing Extensions** (+14 tests,
    `test_rfc9073_event_publishing.py`). STRUCTURED-DATA (URI,
    inline TEXT, binary BASE64); STYLED-DESCRIPTION (HTML,
    markdown, multi-language); LOCATION-TYPE parameter;
    PARTICIPANT / VLOCATION / VRESOURCE sub-components don't
    crash the parser; CALENDAR-ADDRESS preserved.

Reference implementation additions:

  * `ical.hpp`: new `Available` + `VAvailability` structs;
    `Calendar.availabilities` vector.
  * `parser.cpp`: new VAVAILABILITY / AVAILABLE component handling
    with typed property dispatch; `skip_depth` counter prevents
    unknown sub-components (PARTICIPANT / VLOCATION / VRESOURCE)
    from clobbering parent component UID and other fields;
    `line_too_long` warning on unfolded >75-octet lines;
    `LineRecord.was_folded` flag plumbed through unfold.
  * `json_writer.cpp`: emits `availabilities` top-level array.

Test contract changes:

  * `test_schema.py:test_parse_top_level_keys` is now a SUPERSET
    check (required keys present) rather than exact match.
    Implementations MAY emit additional keys for RFC extensions
    (e.g. `availabilities`).

PLAN.md complete: 14 / 14 priorities landed. Full ICal suite is
**410 tests**, all passing. Ruff + pyright strict-mode clean.

## v1.1.0 — 2026-04-24

Test-surface expansion per `PLAN.md` Parts B1-B10 (B7-B9 and B11-B14
deferred). Adds 97 new tests (245 -> 342) across six areas that close
the specific findings from the Codex v1.0 adversarial review.

New authoritative RFC (prompt/docs/authoritative/):

- `rfc9074.txt` - "VALARM" Extensions for iCalendar (RFC 9074,
  August 2021). Closes the contract gap where `ACKNOWLEDGED` was in
  the schema without a shipped authoritative source. Also introduces
  UID, PROXIMITY, RELATED-TO on VALARM.

A1+B6 - RFC 9074 VALARM Extensions (+12 tests,
test_valarm_rfc9074.py):
  - VALARM uid preserved.
  - ACKNOWLEDGED absolute DATE-TIME; absence -> null.
  - PROXIMITY = ARRIVE / DEPART / x-name; absence -> null.
  - RELATED-TO plain UID; with RELTYPE; multiple entries accumulate.
  - Snooze workflow (REPEAT + DURATION + ACKNOWLEDGED).
  - raw_properties carries RFC 9074 props even if unfielded.

B1 - VFREEBUSY full modeling (+14 tests, test_vfreebusy.py):
  - Closes Codex v1.0 review finding #1. Previously VFreeBusy was
    an alias for VEvent and no FREEBUSY property was parsed.
  - Adds dedicated FreeBusyEntry struct (fbtype + periods).
  - FBTYPE values: FREE / BUSY / BUSY-UNAVAILABLE / BUSY-TENTATIVE /
    x-name. Default is BUSY.
  - Multiple FREEBUSY properties accumulate.
  - Comma-separated periods in one FREEBUSY value.
  - PERIOD value types: start/end, start/duration.
  - Common VFREEBUSY fields (UID/DTSTART/DTEND/ORGANIZER/ATTENDEE).

B2 - Contract-vs-impl gap (+29 tests, test_event_fields.py +
test_vtimezone_fields.py):
  - Closes Codex v1.0 review finding #2.
  - Event-level RFC 5545 fields newly modeled: priority, transp,
    url, geo (with malformed-value warning), resources, contact,
    created, last_modified, attachments (with FMTTYPE / ENCODING).
  - RFC 7986 at event level: color, images, conferences.
  - VTIMEZONE fields: last_modified, tzurl, comment (repeating).
  - New warning: duplicate_uid (sec 3.8.4.7).

B3+B4 - VTIMEZONE resolution depth + DST fold/gap warnings
(+17 tests, test_vtimezone_resolution.py + test_dst_warnings.py):
  - Closes Codex v1.0 review finding #5.
  - Resolver honors observance RRULE UNTIL.
  - Resolver enumerates observance RDATE entries.
  - BYMONTHDAY honored in observance RRULE.
  - detect_tz_anomaly() detects timezone_fold_ambiguous (fall-back
    overlap) and nonexistent_local_time (spring-forward gap).
  - Southern-hemisphere DST (Sydney) and no-DST zones exercised.

B5 - iTIP per-method matrices (+14 tests, test_itip_methods_deep.py):
  - Closes Codex v1.0 review finding #4. Adds depth on RFC 5546
    sec 3.2 methods: ADD / REFRESH / COUNTER / DECLINECOUNTER.
  - PUBLISH MUST NOT include ATTENDEE (RFC 5546 sec 3.2.1) enforced.
  - Case-insensitive METHOD value handling.
  - Per-event validation across multi-event calendars.

B10 - Schema conformance depth (+11 tests, test_schema_depth.py):
  - Arrays always lists, never null (empty -> []).
  - Warning entries always carry kind.
  - ISO-8601 regex pins on dtstart fields.
  - Occurrences sorted by dtstart with UID lexicographic tie-break.
  - Calendar object carries all RFC 7986 keys.

Reference implementation changes:
  - ical.hpp: added RelatedTo, FreeBusyEntry, Geo, ImageEntry,
    ConferenceEntry; expanded VAlarm, VEvent, VTimezone, VFreeBusy.
  - parser.cpp: extended apply_common_prop (12 new fields);
    apply_alarm_prop (RFC 9074); FREEBUSY parsing in VFREEBUSY;
    VTIMEZONE-level LAST-MODIFIED/TZURL/COMMENT; new
    validate_duplicate_uids() pass; PUBLISH-forbids-ATTENDEE check.
  - json_writer.cpp: new emit_freebusy(); emit_alarm() extended;
    emit_event_common() emits 12 new fields; emit_vtimezone() extends.
  - datetime.cpp: enumerate_observance now includes RDATE, honors
    UNTIL, handles BYMONTHDAY; new detect_tz_anomaly().
  - rrule.cpp: to_comparable emits fold/gap warnings; occurrence
    sort adds UID tie-break.

Deferred to a future v1.2 (per PLAN.md):
  - A2+B7: RFC 7953 VAVAILABILITY.
  - A3+B8: RFC 9073 Event Publishing Extensions.
  - A4+B9: RFC 9253 TZIDALIASOF.
  - B11: 75-octet folding edges (line_too_long, invalid fold).
  - B12: real-world calendar corpus.
  - B13: error-message line/column precision.
  - B14: stress + regression.

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
