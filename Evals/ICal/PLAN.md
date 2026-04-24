# ICal Eval — Doc + Test Surface Expansion Plan

Post-v1.0 plan to (a) widen the authoritative documentation corpus
by adding four more IETF RFCs that extend or fix gaps in our
current contract and (b) push test coverage from 245 to ~400 by
closing the specific Codex v1.0-review findings and extending into
RFC-defined areas we don't yet probe.

**Baseline**: 245 tests, 100% pass vs. the cpp reference impl.
**Target**: ~400 tests after this plan lands.
**Branch**: one of `ical-docs-expansion`, `ical-test-expansion`
(may be split into two).

## Guiding principles

- Same as `Evals/BibTeX/PLAN.md`: self-contained tests, `.get()`
  defensive asserts, derive from authoritative RFCs verbatim under
  `prompt/docs/authoritative/`.
- RFCs shipped under `authoritative/` must preserve IETF TLP 5.0
  notices (already the pattern — just extend).
- Where v1.0's contract already mentions a field but the ref impl
  doesn't handle it (Codex finding #2), we *implement* rather than
  shrink the contract. Shrinking is the last resort.
- Tests that assert behavior come with the authoritative RFC
  citation in the test docstring.

## Part A — Documentation surface expansion

Current shipped: RFC 5545 (core), RFC 5546 (iTIP), RFC 6868 (param
escape), RFC 7529 (RSCALE / SKIP), RFC 7986 (new calendar
properties).

### A1 — RFC 9074: VALARM Extensions (March 2021)

**Size**: ~20 KB, ~500 lines.
**License**: IETF TLP 5.0 (same as existing RFCs).
**Why**: Resolves Codex v1.0 finding #2. Our `technical-requirements-
prompt.md` already mentions `acknowledged` on the VAlarm object,
but ACKNOWLEDGED is defined in RFC 9074, not RFC 5545. Shipping
9074 brings the contract in line with the authoritative corpus.

**New surface introduced**:
- `ACKNOWLEDGED` property on VALARM (date-time of last user ack).
- `PROXIMITY` property on VALARM (`ARRIVE` / `DEPART` / x-name).
- `RELATED-TO` linking alarms to other alarms (or events).
- Enhanced EMAIL alarm semantics (attachments, thread linkage).
- New `UID` requirement inside VALARM (for cross-component linking).

### A2 — RFC 7953: VAVAILABILITY (August 2016)

**Size**: ~35 KB, ~1,000 lines.
**License**: IETF TLP 5.0.
**Why**: VAVAILABILITY is a real top-level component used by
CalDAV scheduling clients to represent availability windows. Our
v1.0 parse output has no `availability` array; adding this RFC
lets us model it properly.

**New surface**:
- `VAVAILABILITY` component (top level inside VCALENDAR).
- `AVAILABLE` sub-component (free-time window).
- `BUSYTYPE` property (BUSY / BUSY-UNAVAILABLE / BUSY-TENTATIVE).
- Availability overlapping rules.
- Applicable to FREEBUSY expansion (interacts with VFREEBUSY).

### A3 — RFC 9073: Event Publishing Extensions (August 2021)

**Size**: ~45 KB, ~1,300 lines.
**License**: IETF TLP 5.0.
**Why**: Adds rich-event surface that mainstream calendar clients
(Google Calendar, Microsoft Outlook) already emit. Including:
- `STRUCTURED-DATA` property (JSON / XML payloads).
- `STYLED-DESCRIPTION` (multi-language formatted descriptions).
- `LOCATION-TYPE` parameter.
- `PARTICIPANT` component (distinct from ATTENDEE).
- `VRESOURCE` component (bookable resource definition).
- `VLOCATION` sub-component (rich location with GEO + hierarchy).

Not shipping this means agents don't see the most-used modern iCal
extension — a gap vs. "full spec".

### A4 — RFC 9253: IANA Time Zone Parameter (November 2022)

**Size**: ~10 KB, ~250 lines.
**License**: IETF TLP 5.0.
**Why**: Defines `TZIDALIASOF` parameter that lets TZID references
track IANA aliases (`America/New_York` → `US/Eastern`). Small but
relevant for VTIMEZONE historical tests.

**New surface**:
- `TZIDALIASOF` parameter on `TZID` in VTIMEZONE.

### A5 — (optional) RFC 8607: Calendaring Availability Extensions

**Size**: ~14 KB.
**Why**: Extends RFC 7953 with `CALENDAR-ADDRESS`, `LOCATION-TYPE`,
and new BUSYTYPE values. Consider if we ship 7953.

### Doc expansion exit criteria

- `Evals/ICal/prompt/docs/authoritative/rfc9074.txt` +
  `rfc7953.txt` + `rfc9073.txt` + `rfc9253.txt` committed.
- `Evals/ICal/prompt/docs/summary.md` updated to list and briefly
  describe the four new RFCs, including navigation pointers.
- `Evals/ICal/prompt/docs/LICENSES.md` unchanged (IETF TLP 5.0
  covers all of them).
- `prompt/base-prompt.md` updated to mention the extended corpus.
- `Evals/ICal/prompt/technical-requirements-prompt.md` extended
  with the new schema fields (see Part B).

## Part B — Test surface expansion

### B1 — VFREEBUSY full modeling (~15 tests)

**Codex v1.0 finding #1 (SEVERE)**: VFREEBUSY is a label; the ref
impl stores it as a `VEvent`, there's no dedicated VFreeBusy type,
and the only test asserts `len(freebusy) == 1`.

Tests to add:
- Parse `FREEBUSY` property into `freebusy: [{fbtype, periods}]`.
- Multiple FREEBUSY properties on one VFREEBUSY accumulate.
- FBTYPE values: `FREE`, `BUSY`, `BUSY-UNAVAILABLE`,
  `BUSY-TENTATIVE`, x-name.
- Default FBTYPE is BUSY (per RFC 5545 §3.8.2.6).
- PERIOD values parsed into `{start, end}` or `{start, duration}`.
- Multiple comma-separated periods in one FREEBUSY value.
- VFREEBUSY with DTSTART/DTEND defines the reporting window.
- VFREEBUSY ORGANIZER/ATTENDEE same cal-address grammar.
- VFREEBUSY in combination with VAVAILABILITY (once shipped).
- VFREEBUSY with METHOD:REPLY (iTIP free-busy response).

**Ref-impl work**: introduce dedicated `VFreeBusy` type in
`ical.hpp` with `freebusy: [FreeBusyPeriod]` and appropriate
parser/writer paths.

### B2 — Contract-vs-implementation gap (~25 tests)

**Codex v1.0 finding #2 (SEVERE)**: technical-requirements-prompt
promises event fields `priority`, `transp`, `url`, `geo`,
`resources`, `contact`, `created`, `last_modified`, `attachments`,
`conferences`, `color`, `images`, plus VTIMEZONE `last_modified`,
`tzurl`, `comment`, and warning kinds `duplicate_uid`,
`timezone_fold_ambiguous`, `line_too_long`, but the ref impl
doesn't parse or emit most of them.

Per-field tests for each:
- **`priority`** (integer 0–9, RFC 5545 §3.8.1.9) — 2 tests
- **`transp`** (OPAQUE / TRANSPARENT, §3.8.2.7) — 2 tests
- **`url`** (URI, §3.8.4.6) — 2 tests
- **`geo`** (`lat;lon` float pair, §3.8.1.6) — 3 tests
- **`resources`** (text-list, §3.8.1.10) — 2 tests
- **`contact`** (text, §3.8.4.2) — 2 tests
- **`created`** (date-time UTC, §3.8.7.1) — 1 test
- **`last_modified`** (date-time UTC, §3.8.7.3) — 1 test
- **`attachments`** (ATTACH §3.8.1.1, may be URI or inline
  BASE64) — 3 tests
- **VTIMEZONE `last_modified`, `tzurl`, `comment`** — 3 tests
- **Warnings** `duplicate_uid`, `timezone_fold_ambiguous`,
  `nonexistent_local_time`, `line_too_long` — 4 tests

**Ref-impl work**: extend `apply_common_prop` / `emit_event_common`
/ `emit_vtimezone` / DST-boundary detection to handle all these.

### B3 — VTIMEZONE resolution depth (~12 tests)

**Codex v1.0 finding #5 (MAJOR)**: the resolver steps simple RRULEs
but uses only first-BYMONTH + ordinal-BYDAY, ignores observance
UNTIL, doesn't enumerate observance RDATE.

Tests to add:
- VTIMEZONE with RRULE `UNTIL=YYYYMMDD` — observance active only
  until that date; an event after UNTIL uses the next observance.
- VTIMEZONE with RDATE listing specific transition dates (Israel /
  Iran pre-rule-change).
- Observance with multi-BYMONTH (e.g. `BYMONTH=3,10`) — pick the
  correct month for a given event date.
- Observance with `BYMONTHDAY` instead of `BYDAY` ordinal
  (less common but valid).
- `BYMONTH=0` or invalid ordinal → drop per RFC.
- A zone with Southern-hemisphere DST (Australia / South America).
- A zone without DST (UTC, Arizona) — no DAYLIGHT observance.
- VTIMEZONE without RRULE on an observance — uses DTSTART
  literally.
- Leap-year interaction (Feb 29 transition date).
- Event exactly on a transition instant.
- Event in the microsecond range that crosses a transition.

**Ref-impl work**: full observance-resolution algorithm with UNTIL
+ RDATE enumeration.

### B4 — DST fold/gap warnings (~8 tests)

**Codex v1.0 finding #5**: `timezone_fold_ambiguous` and
`nonexistent_local_time` warnings are promised but not implemented.

- Event at 01:30 local on fall-back day (ambiguous) → warning
  `timezone_fold_ambiguous` emitted; resolution uses pre-transition
  per v1.0 spec §5.1.1.
- Event at 02:30 local on spring-forward day (nonexistent) →
  `nonexistent_local_time` warning; resolution uses post-transition.
- Expand produces these warnings for every ambiguous/nonexistent
  occurrence, not just DTSTART.
- Multi-year RRULE hitting fall-back each year → N warnings.
- Override at ambiguous time inherits the fold rule.
- Floating time events in affected windows don't trigger warnings
  (no TZID to resolve).
- Event in a TZID with no DST doesn't trigger warnings.

### B5 — iTIP per-method matrices (~20 tests)

**Codex v1.0 finding #4 (MAJOR)**: `validate_itip` only checks
ORGANIZER / ATTENDEE / PARTSTAT presence; RFC 5546 §3.2 defines
per-method property matrices we don't really assert.

Per RFC 5546 §3.2:
- **PUBLISH** (§3.2.1) — requires ORGANIZER, DTSTAMP, DTSTART,
  SUMMARY, UID. No ATTENDEE. ~3 tests.
- **REQUEST** (§3.2.2) — requires ORGANIZER, ATTENDEE with
  PARTSTAT, DTSTAMP, DTSTART, SUMMARY, UID. SEQUENCE required. ~3 tests.
- **REPLY** (§3.2.3) — requires ORGANIZER, ATTENDEE (just the
  responding one), DTSTAMP, UID, SEQUENCE. PARTSTAT on attendee. ~3 tests.
- **ADD** (§3.2.4) — adds new occurrence to existing event. Requires
  RECURRENCE-ID. ~2 tests.
- **CANCEL** (§3.2.5) — requires ORGANIZER, ATTENDEE, UID,
  SEQUENCE. STATUS:CANCELLED or implied. ~2 tests.
- **REFRESH** (§3.2.6) — requires ATTENDEE, ORGANIZER, UID. ~2 tests.
- **COUNTER** (§3.2.7) — attendee's proposed change. ~2 tests.
- **DECLINECOUNTER** (§3.2.8) — organizer rejecting a counter. ~2 tests.
- Happy-path + failure for each METHOD.

**Ref-impl work**: fully implement `validate_itip` per §3.2.

### B6 — RFC 9074 VALARM extensions (~10 tests)

(Requires A1 — RFC 9074 docs shipped.)

- `ACKNOWLEDGED` round-trip.
- `PROXIMITY=ARRIVE` on location-based alarm.
- `PROXIMITY=DEPART`.
- Unknown PROXIMITY x-name preserved.
- `RELATED-TO` linking two VALARMs.
- EMAIL alarm with multiple ATTACH.
- UID required inside VALARM (9074 extension over 5545).
- Alarm snooze workflow (ACKNOWLEDGED + SEQUENCE).
- Alarm repeat + ACKNOWLEDGED interaction.
- Alarm with PROXIMITY but no TRIGGER — error or warning?

### B7 — RFC 7953 VAVAILABILITY (~12 tests)

(Requires A2 — RFC 7953 docs shipped.)

- Basic VAVAILABILITY component with DTSTART/DTEND window.
- VAVAILABILITY containing multiple AVAILABLE sub-components.
- AVAILABLE with its own DTSTART/DURATION.
- BUSYTYPE `BUSY-UNAVAILABLE` value.
- Overlapping AVAILABLE windows (earlier wins / later wins?).
- VAVAILABILITY + VFREEBUSY interaction.
- VAVAILABILITY with RRULE for recurring availability.
- VAVAILABILITY without ATTENDEE — is that valid?
- Priority: higher-PRIORITY VAVAILABILITY overrides lower.
- VAVAILABILITY in METHOD:PUBLISH.
- Multi-timezone VAVAILABILITY.
- Parse output includes top-level `availabilities` array.

### B8 — RFC 9073 Event Publishing Extensions (~20 tests)

(Requires A3 — RFC 9073 docs shipped.)

- `STRUCTURED-DATA` with VALUE=TEXT (JSON payload).
- `STRUCTURED-DATA` with VALUE=BINARY (base64 with FMTTYPE).
- `STRUCTURED-DATA` with URI ref.
- `STYLED-DESCRIPTION` with DERIVED parameter.
- Multiple STYLED-DESCRIPTION for different languages.
- LANGUAGE parameter on STYLED-DESCRIPTION.
- `LOCATION-TYPE` parameter on LOCATION.
- `PARTICIPANT` component inside VEVENT.
- PARTICIPANT `PARTICIPANT-TYPE` values.
- PARTICIPANT with CAL-ADDRESS vs without.
- `VRESOURCE` top-level definition.
- VRESOURCE referenced from VEVENT by UID.
- `VLOCATION` sub-component.
- VLOCATION nested in PARTICIPANT.
- Geographic hierarchy via LOCATION-TYPE.

### B9 — RFC 9253 TZID parameter (~3 tests)

(Requires A4 — RFC 9253 docs shipped.)

- `TZIDALIASOF` preserved on VTIMEZONE.
- Event's TZID resolves through alias.
- Unknown alias doesn't crash.

### B10 — Deeper schema conformance (~10 tests)

`test_schema.py` currently asserts key presence. Extend:

- Every top-level key's type matches the schema spec (types, not
  just presence).
- Array fields are never `null` (empty array instead).
- ISO-8601 fields match the documented regex.
- DURATION fields round-trip through parse.
- Warning-array entries all have `kind` key.
- Occurrences sorted by `dtstart` then `uid` tie-break (spec
  requires; current test may not assert tie).
- `parse` output contains all RFC 7986 calendar-level keys even
  when absent (null/empty).

### B11 — 75-octet fold edge cases (~5 tests)

**Codex v1.0 finding #3**: `test_line_folding_octets.py` declines
to assert `line_too_long` or invalid-fold behavior.

- Line 76+ octets without fold → emit `line_too_long` warning.
- Invalid fold (CRLF without following whitespace) is a hard
  parse error per RFC 5545 §3.1.
- Fold inside a TEXT value's TEXT-escape (e.g. between `\` and `n`)
  does NOT preserve the split — escape is still applied correctly.
- Trailing whitespace on an unfolded continuation line is
  preserved.
- Zero-length continuation (CRLF+SP at EOF) is stripped cleanly.

### B12 — Real-world corpus (~10 tests)

Like BibTeX's `refs-edge.bib`, add `calendars/` fixture dir:
- `gmail-export.ics` — a representative Gmail calendar export
  (synthesized; real-world-shape).
- `outlook-export.ics` — ditto for Outlook.
- `scheduling-reply.ics` — iTIP REPLY trace.
- Assert end-to-end parse + expand semantics.

### B13 — Error line/column precision (~8 tests)

Same pattern as BibTeX P7. `test_errors.py` currently only asserts
exit=1. Add:
- Malformed `.ics` (missing `END:`) → error pins the line.
- Unknown VCALENDAR property → warning with line/col, not error.
- Invalid DURATION value (`PT3XYZ`) → error at property location.
- Invalid TZID reference → warning, not error.
- Malformed RRULE (`FREQ=QUARTERLY`) → error at RRULE line.
- Invalid BYSETPOS ordinal (`BYSETPOS=0`) → warning + drop.
- DATE-TIME with day 31 in April → error (RFC requires valid).
- Circular RECURRENCE-ID → warning.

### B14 — Stress + regression tests (~10 tests)

- Calendar with 500 events parses in <5 seconds.
- RRULE with `COUNT=10000` expands in <10 seconds.
- Override chain of 50 RECURRENCE-IDs resolves correctly.
- Deeply-nested VLOCATION hierarchy.
- Calendar with malformed entry mid-file — parsing continues,
  emits warning, surfaces valid entries.

## Progress table

### Part A — Documentation

| RFC | Status | Size | Tests driven by |
|---|---|---|---|
| 9074 (VALARM extensions) | ✅ done | 32 KB | B6 |
| 7953 (VAVAILABILITY) | pending | ~35 KB | B7 |
| 9073 (event pub) | pending | ~45 KB | B8 |
| 9253 (TZID alias) | pending | ~10 KB | B9 |

### Part B — Tests

| Priority | Status | Tests | Depends on docs |
|---|---|---|---|
| B1: VFREEBUSY modeling | ✅ done | 14 | — |
| B2: Contract-vs-impl gap | ✅ done | 29 | — |
| B3: VTIMEZONE resolution depth | ✅ done | 9 | — |
| B4: DST fold/gap warnings | ✅ done | 8 | — |
| B5: iTIP per-method matrices | ✅ done | 14 | RFC 5546 (shipped) |
| B6: RFC 9074 VALARM ext | ✅ done | 12 | A1 |
| B7: RFC 7953 VAVAILABILITY | pending | 0/~12 | A2 |
| B8: RFC 9073 event pub | pending | 0/~20 | A3 |
| B9: RFC 9253 TZID alias | pending | 0/~3 | A4 |
| B10: Deeper schema conformance | ✅ done | 11 | — |
| B11: 75-octet fold edges | pending | 0/~5 | — |
| B12: Real-world corpus | pending | 0/~10 | — |
| B13: Error line/col precision | pending | 0/~8 | — |
| B14: Stress + regression | pending | 0/~10 | — |
| **v1.1 landed** | **97** | **245 → 342** | |
| **v1.2 pending** | **~68** | A2–A4 + B7–B9 + B11–B14 | |

## Suggested execution order

Doc additions → test additions per RFC (so agents see the new
authoritative text before a test asserts against it):

1. **A1 + B6** together (RFC 9074 + VALARM-ext tests)
2. **B1** (VFREEBUSY modeling, no new docs needed — already in 5545)
3. **B2** (contract-vs-impl gap) — biggest single fix
4. **B3 + B4** (VTIMEZONE resolution + fold/gap warnings)
5. **B5** (iTIP per-method matrices — big, uses existing 5546)
6. **A2 + B7** (RFC 7953 + VAVAILABILITY tests)
7. **A3 + B8** (RFC 9073 + event-pub tests)
8. **A4 + B9** (RFC 9253 + TZID-alias tests)
9. **B10 + B11** (schema + folding)
10. **B12** (real-world corpus)
11. **B13 + B14** (error precision + stress)

## Non-goals (not in this plan)

- Implementing CalDAV (transport-layer, out of eval scope).
- iMIP (RFC 6047 email-based iTIP).
- xCal (RFC 6321) or jCal (RFC 7265) alternative serializations.
- Full IANA tzdata integration — we remain strictly in-file.
- VPOLL (draft, not yet RFC).

## Exit criteria

- 4 new authoritative RFCs shipped under `authoritative/`.
- `summary.md` updated with navigation into all nine RFCs.
- Technical-requirements-prompt extended with new schema fields.
- All ~168 new tests pass against the extended reference impl.
- Ruff + pyright strict-mode clean.
- No regression in the existing 245 tests.
- `CHANGELOG.md` gets a v1.1 entry summarizing the expansion.
- `README.md` updates the test count claim.
