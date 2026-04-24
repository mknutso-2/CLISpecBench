# iCalendar — Navigation Summary

> **This document is a navigation index, not the authoritative spec.**
> The authoritative sources are the IETF RFCs shipped verbatim under
> [`authoritative/`](authoritative/):
>
> - [`authoritative/rfc5545.txt`](authoritative/rfc5545.txt) — *Internet
>   Calendaring and Scheduling Core Object Specification (iCalendar)*
>   (RFC 5545, September 2009) — core format and RRULE grammar.
> - [`authoritative/rfc5546.txt`](authoritative/rfc5546.txt) — *iCalendar
>   Transport-Independent Interoperability Protocol (iTIP)*
>   (RFC 5546, December 2009) — scheduling METHOD semantics.
> - [`authoritative/rfc6868.txt`](authoritative/rfc6868.txt) — *Parameter
>   Value Encoding in iCalendar and vCard* (RFC 6868) — `^n`, `^'`, `^^`
>   parameter-value escapes.
> - [`authoritative/rfc7529.txt`](authoritative/rfc7529.txt) —
>   *Non-Gregorian Recurrence Rules* (RFC 7529) — `RSCALE` and `SKIP`.
> - [`authoritative/rfc7986.txt`](authoritative/rfc7986.txt) — *New
>   Properties for iCalendar* (RFC 7986) — calendar-level `NAME`,
>   `REFRESH-INTERVAL`, `COLOR`, `IMAGE`, `CONFERENCE`, etc.
> - [`authoritative/rfc9074.txt`](authoritative/rfc9074.txt) —
>   *"VALARM" Extensions for iCalendar* (RFC 9074, August 2021) —
>   `ACKNOWLEDGED`, `PROXIMITY`, `RELATED-TO`, snooze workflow,
>   enhanced EMAIL alarm semantics. Updates RFC 5545 §3.6.6.
> - [`authoritative/rfc7953.txt`](authoritative/rfc7953.txt) —
>   *Calendar Availability* (RFC 7953, August 2016) — VAVAILABILITY
>   top-level component for publishing recurring availability
>   windows, AVAILABLE sub-component, `BUSYTYPE` parameter. Updates
>   RFC 5545.
> - [`authoritative/rfc9073.txt`](authoritative/rfc9073.txt) —
>   *Event Publishing Extensions to iCalendar* (RFC 9073, August
>   2021) — `PARTICIPANT` component, `VLOCATION` / `VRESOURCE`
>   sub-components, `STRUCTURED-DATA`, `STYLED-DESCRIPTION`,
>   `LOCATION-TYPE` parameter. Updates RFC 5545.
> - [`authoritative/rfc9253.txt`](authoritative/rfc9253.txt) —
>   *Support for iCalendar Relationships* (RFC 9253, August 2022) —
>   `LINK` property with `LINKREL` parameter, `GAP` parameter on
>   `RELATED-TO`, expanded `RELTYPE` values
>   (`FINISHTOSTART` / `FINISHTOFINISH` / `STARTTOFINISH` /
>   `STARTTOSTART` / `FIRST` / `NEXT` / `DEPENDS-ON` / …),
>   `STRUCTURED-CATEGORIES`, `CONCEPT`, `REFID`. Updates RFC 5545.
>
> **Where this summary and the authoritative RFCs conflict, the RFCs
> are authoritative.** Tests in this eval assert behavior that is
> unambiguously specified by the RFCs above; this summary exists to
> help an implementer orient faster, not to replace or reinterpret
> them.

This document is a navigation summary over the iCalendar format
covered by RFC 5545 and companion RFCs: `.ics` text parsing,
component and property semantics, value types, the full RRULE
recurrence grammar, timezone resolution via `VTIMEZONE`, expansion of
recurring events over a window, VALARM state, ATTENDEE grammar, and
the METHOD-driven iTIP scheduling layer.

## 1. Lexical structure (RFC 5545 §3.1)

### 1.1 Content lines

An iCalendar file is a sequence of **content lines**, each terminated
by CRLF (`\r\n`). A lone LF (`\n`) is accepted as equivalent. Each
content line is:

```
name *(";" param) ":" value CRLF
```

- `name` is a property name, case-insensitive, normalized to
  uppercase in the JSON output.
- `param` is `PARAM=VALUE`; `VALUE` may be quoted (`"..."`) or
  unquoted.
- `value` is the property value, up to CRLF.

### 1.2 Line folding

A long content line may be split by inserting CRLF followed by one
whitespace character (SPACE or TAB). The unfolding pass removes each
such CRLF+whitespace pair, rejoining the content line.

### 1.3 TEXT escapes

In property values whose value-type is `TEXT` (SUMMARY, DESCRIPTION,
LOCATION, COMMENT, CATEGORIES items), the following escape sequences
are unescaped:

- `\\` → `\`
- `\;` → `;`
- `\,` → `,`
- `\N` or `\n` → LF (newline)

In non-TEXT values and in parameter values, these escapes are NOT
processed.

## 2. Components (RFC 5545 §3.6)

The outer component is `VCALENDAR`. Recognized subcomponents:

- `VEVENT` — a calendar event (§2.3).
- `VTODO` — a to-do task (§2.4).
- `VJOURNAL` — a journal entry (§2.4).
- `VFREEBUSY` — free/busy info (§2.4).
- `VTIMEZONE` — a timezone definition (§5).
- `VALARM` — alarm, only appears nested inside VEVENT/VTODO.

### 2.1 Required VCALENDAR properties

- `PRODID` (string)
- `VERSION` (must be `2.0`)

Optional: `CALSCALE` (default GREGORIAN), `METHOD` (for iTIP).

### 2.2 Output shape

Output JSON organizes components as:

- `calendar` — PRODID, VERSION, CALSCALE, METHOD.
- `events` — VEVENTs.
- `todos` — VTODOs.
- `journals` — VJOURNALs.
- `freebusy` — VFREEBUSYs.
- `timezones` — VTIMEZONE definitions (§5.3).
- `warnings` — structured warnings.

### 2.3 VEVENT

VEVENT properties surfaced in output:

| Property | Type |
|---|---|
| `UID` | string |
| `DTSTAMP` | DATE-TIME |
| `DTSTART` | DATE or DATE-TIME |
| `DTEND` | DATE or DATE-TIME (or `DURATION`) |
| `DURATION` | duration string (XOR with DTEND) |
| `SUMMARY`, `DESCRIPTION`, `LOCATION` | TEXT |
| `STATUS` | CONFIRMED / TENTATIVE / CANCELLED |
| `CLASS` | PUBLIC / PRIVATE / CONFIDENTIAL |
| `CATEGORIES` | comma-separated TEXT list |
| `ORGANIZER`, `ATTENDEE` | CAL-ADDRESS with CN / ROLE / PARTSTAT params |
| `RRULE` | recurrence rule (§4) |
| `RDATE` | explicit extra occurrences |
| `EXDATE` | occurrences to exclude |
| `EXRULE` | deprecated; parsed but yields `exrule_deprecated` warning |
| `RECURRENCE-ID` | identifies an override instance |
| `SEQUENCE`, `TRANSP`, `PRIORITY` | metadata |
| `VALARM` | nested alarm; surfaced as raw sub-component |

### 2.4 VTODO / VJOURNAL / VFREEBUSY

VTODO: like VEVENT plus `DUE`, `COMPLETED`, `PERCENT-COMPLETE`,
`STATUS` (NEEDS-ACTION / IN-PROCESS / COMPLETED / CANCELLED).

VJOURNAL: like VEVENT minus `DTEND`/`DURATION`.

VFREEBUSY: `DTSTART`, `DTEND`, `FREEBUSY` (list of PERIOD values with
`FBTYPE` parameter), `ORGANIZER`, `ATTENDEE`, `CONTACT`.

All three surface the same subset of common properties plus their
type-specific ones.

## 3. Value types

### 3.1 DATE / DATE-TIME

- DATE: `YYYYMMDD` (8 digits).
- DATE-TIME floating: `YYYYMMDDTHHMMSS`.
- DATE-TIME UTC: `YYYYMMDDTHHMMSSZ`.
- DATE-TIME zoned: `YYYYMMDDTHHMMSS` with `TZID=...` parameter; the
  TZID must resolve to a local `VTIMEZONE` in the file (§5).

### 3.2 DURATION

`[+|-]P[<n>W | <n>D T <n>H <n>M <n>S | <n>H <n>M <n>S | <n>M <n>S]`
where each `<n>` is digits.

### 3.3 PERIOD

`<date-time> / (<date-time> | <duration>)`. Used in RDATE with
`VALUE=PERIOD`, and in VFREEBUSY's FREEBUSY.

### 3.4 Integer / Boolean / URI / CAL-ADDRESS

Standard types. `CAL-ADDRESS` values carry the URI plus optional
`CN`, `ROLE`, `PARTSTAT` parameters.

## 4. RRULE (RFC 5545 §3.3.10) — full

`RRULE:<part>=<value>;<part>=<value>;...`

### 4.1 Parts

| Part | Value | Required? |
|---|---|---|
| `FREQ` | `SECONDLY` / `MINUTELY` / `HOURLY` / `DAILY` / `WEEKLY` / `MONTHLY` / `YEARLY` | Required |
| `INTERVAL` | positive integer, default 1 | Optional |
| `COUNT` | positive integer; mutually exclusive with UNTIL | Optional |
| `UNTIL` | DATE or DATE-TIME (UTC required if DATE-TIME) | Optional |
| `BYSECOND` | integer list 0..60 | Optional |
| `BYMINUTE` | integer list 0..59 | Optional |
| `BYHOUR` | integer list 0..23 | Optional |
| `BYDAY` | comma list of `<ord>?<day>` where `<day>` ∈ `SU`/`MO`/`TU`/`WE`/`TH`/`FR`/`SA`, `<ord>` is a signed int valid only for MONTHLY / YEARLY | Optional |
| `BYMONTHDAY` | integer list 1..31 or -1..-31 | Optional |
| `BYYEARDAY` | integer list 1..366 or -1..-366; valid only in YEARLY | Optional |
| `BYWEEKNO` | integer list 1..53 or -1..-53; valid only in YEARLY | Optional |
| `BYMONTH` | integer list 1..12 | Optional |
| `BYSETPOS` | integer list (1-based or negative); picks from the per-period candidate list | Optional |
| `WKST` | weekday (default `MO`); affects WEEKLY and YEARLY with BYWEEKNO | Optional |

### 4.2 Expansion algorithm

Given DTSTART (the seed) and the RRULE, expand by walking intervals
from DTSTART forward. For each interval:

1. Generate candidate occurrences scoped to the interval, using the
   BYxxx parts in the RFC 5545 §3.3.10 **fixed application order**:
   `BYMONTH` → `BYWEEKNO` → `BYYEARDAY` → `BYMONTHDAY` → `BYDAY` →
   `BYHOUR` → `BYMINUTE` → `BYSECOND`.
2. At each step, the part either **expands** (produces additional
   candidates) or **filters** (removes non-matching candidates). The
   RFC's Table 2 specifies expand-vs-filter per FREQ. Summary:

| Part | SECONDLY | MINUTELY | HOURLY | DAILY | WEEKLY | MONTHLY | YEARLY |
|---|---|---|---|---|---|---|---|
| BYMONTH | filter | filter | filter | filter | filter | filter | expand |
| BYWEEKNO | — | — | — | — | — | — | expand |
| BYYEARDAY | filter | filter | filter | — | — | — | expand |
| BYMONTHDAY | filter | filter | filter | filter | — | expand | expand |
| BYDAY | filter | filter | filter | filter | expand | expand-or-filter* | expand-or-filter* |
| BYHOUR | filter | filter | expand | expand | expand | expand | expand |
| BYMINUTE | filter | expand | expand | expand | expand | expand | expand |
| BYSECOND | expand | expand | expand | expand | expand | expand | expand |

*BYDAY in MONTHLY/YEARLY: if BYMONTHDAY or BYYEARDAY is also
present, BYDAY becomes a filter; otherwise it expands.*

3. **BYSETPOS** is applied last, to the full candidate set within
   the current period (e.g. the current month for MONTHLY). Positive
   N picks the Nth; negative N picks Nth-from-end.

   **BYSETPOS × time expansion — pinned.** When BYHOUR / BYMINUTE /
   BYSECOND expand dates into multiple datetime candidates (e.g.
   `FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,17;BYSETPOS=-1`),
   BYSETPOS is applied to the **fully time-expanded** candidate list
   sorted ascending. This matches the behavior of `python-dateutil`
   (the de-facto reference) and is the interpretation of RFC 5545
   §3.3.10 that this spec commits to. Implementations that apply
   BYSETPOS to the date-only candidate list before time expansion
   (as rrule.js < v2.8 did in some paths) are non-conformant.

4. Drop candidates where the date is invalid (Feb 30 etc.) or
   outside the local-time range for the rule.

5. Merge with RDATE (add explicit), filter by EXDATE (drop matching),
   apply COUNT / UNTIL termination, filter to the query window.

6. **Invalid dates are dropped silently**. For example,
   `FREQ=MONTHLY;BYMONTHDAY=31` skips months with fewer than 31
   days; it does not roll over.

### 4.3 BYDAY specifics

`BYDAY` values have an optional signed ordinal prefix:

- In `MONTHLY`: ordinal N picks the Nth occurrence of that weekday
  within the month. Negative counts from the end: `-1FR` = last
  Friday.
- In `YEARLY` (without BYMONTH): ordinal scopes to the year.
- In `YEARLY` with BYMONTH: ordinal scopes to each matching month.
- In `WEEKLY`: no ordinals allowed; a bare `MO` matches every
  Monday in the weekly interval.

### 4.4 WKST

`WKST` defines the first day of the week for:

- `WEEKLY` expansion (affects which days fall inside the current
  weekly interval when BYDAY crosses a week boundary).
- `YEARLY` with `BYWEEKNO` (affects ISO week numbering).

Default: `MO`.

### 4.5 COUNT / UNTIL termination

- `COUNT=N` emits exactly N occurrences starting with the first
  valid one (DTSTART if it satisfies the rule; otherwise the first
  generated one that does).
- `UNTIL=<date-time>` inclusive. If UNTIL is a DATE, compare against
  the occurrence's date portion. If DATE-TIME, it must be UTC.

## 5. VTIMEZONE (§3.6.5)

A `VTIMEZONE` defines a named local timezone via one or more
`STANDARD` and `DAYLIGHT` subcomponents. Each sub-component carries:

- `TZNAME` — the zone's abbreviated name (e.g. `EST`, `EDT`).
- `TZOFFSETFROM` — UTC offset before this transition (format `±HHMM`
  or `±HHMMSS`).
- `TZOFFSETTO` — UTC offset after this transition.
- `DTSTART` — when the observance starts.
- `RRULE` — rule describing recurring transitions (e.g. 2nd Sunday of
  March at 02:00 in STANDARD).
- `RDATE` — explicit transition dates.

### 5.1 Resolution ("portable-no-network" mode)

This eval operates in a deliberately portable mode: the tool MUST
resolve TZID entirely from VTIMEZONE definitions present in the same
`.ics` file. No IANA tzdata lookup is required or permitted. This is
a benchmark-design choice (it lets the tool ship without a
platform-dependent `tzdata` database and makes outputs reproducible
across hosts); it is NOT a claim about real-world CalDAV clients,
which typically resolve TZID against a system tzdata.

To resolve a zoned DATE-TIME (`TZID=X:YYYYMMDDTHHMMSS`):

1. Look up VTIMEZONE with `TZID=X` in the same VCALENDAR. If not
   found, emit an `unresolved_tzid` warning and treat the value as
   floating time.
2. Find the transitions for this VTIMEZONE by expanding each
   observance's `DTSTART + RRULE + RDATE` into a time-sorted list.
3. Pick the **most recent transition whose effective local start is
   ≤ the local date-time being resolved**, and apply that
   observance's `TZOFFSETTO` to convert local to UTC:
   `UTC = local − TZOFFSETTO`.

### 5.1.1 DST-fold disambiguation (pinned)

Two cases arise at DST transitions that the "latest transition ≤
local" rule alone does not fully disambiguate:

**Fall-back overlap (local time happens twice).** When clocks fall
back, a local time like `01:30` in the one-hour window immediately
after the transition is ambiguous: it could mean the first `01:30`
(under the pre-transition DAYLIGHT offset) or the second `01:30`
(under the post-transition STANDARD offset). This spec pins the
interpretation as the **pre-transition offset** — i.e. the *first*
occurrence of the ambiguous local time, matching PEP 495's
`fold=0` convention and `python-dateutil`'s default. This falls
out naturally from "latest observance whose DTSTART ≤ local time":
at local 01:30 on fall-back day, the STANDARD observance
(DTSTART=02:00 local) has not yet started, so the active
observance is still DAYLIGHT. An implementation returning the
post-transition offset (EST in the US case) for ambiguous fall-back
times is conformant ONLY if it also documents `fold=1` as its
default; the reference implementation uses `fold=0`.

**Spring-forward gap (local time does not exist).** When clocks
spring forward, local times like `02:30` in the gap never occur in
the wall clock. This spec pins the interpretation as the
**post-transition offset**: treat `02:30` as if it were interpreted
under the new offset. Rationale: the gap-time implicitly refers to
a moment that wall-clock reasoning skipped; the forward-looking
choice matches most real-world consumer behavior. The alternative
(reject as malformed, or interpret under the pre-transition offset
and thus produce a UTC time that the wall clock never displayed) is
non-conformant.

### 5.1.2 Unresolved TZID policy

When a TZID is referenced but not defined in the file, the tool
MUST:

1. Emit an `unresolved_tzid` warning (§10).
2. Continue processing by treating the value as **floating** (kind
   `floating`, no UTC conversion).
3. Include the offender's occurrence in `expand` output, with the
   `tz` field set to the unresolved TZID string (so consumers can
   see which TZID was attempted).

This is a "best-effort continuation" policy. Implementations MAY
alternatively treat unresolved TZID as a hard parse error; that
MUST be clearly documented on the tool's `--help` output if so. The
reference implementation implements the continuation policy.

### 5.2 VTIMEZONE output shape

In the `parse` output, each VTIMEZONE appears in `timezones` as:

```json
{
  "tzid": "string",
  "standard": [
    {
      "dtstart": "ISO-8601 string",
      "tzoffsetfrom": "±HH:MM",
      "tzoffsetto": "±HH:MM",
      "tzname": "string | null",
      "rrule": <rrule object | null>,
      "rdate": [ "ISO-8601 string", ... ]
    }
  ],
  "daylight": [ <same shape> ]
}
```

### 5.3 Zoned output convention

In `expand`, zoned DATE-TIMEs are emitted as UTC strings (trailing
`Z`). A `tz` field on each occurrence reports the originating TZID
string so the consumer can reconstruct local time if desired:

```json
{"uid": "...", "dtstart": "2026-03-05T15:00:00Z", "tz": "America/New_York"}
```

Floating occurrences emit no `tz` field.

## 6. iTIP scheduling (§3.6.1; RFC 5546 §3)

`METHOD` on VCALENDAR (one of: `PUBLISH`, `REQUEST`, `REPLY`,
`ADD`, `CANCEL`, `REFRESH`, `COUNTER`, `DECLINECOUNTER`) adjusts how
the file should be interpreted as a scheduling message. The tool:

- Surfaces `METHOD` in the `calendar` object.
- For `REQUEST` / `CANCEL` / `REPLY`, validates that each VEVENT has
  the properties iTIP requires for that method (UID, DTSTAMP,
  SEQUENCE; for CANCEL: STATUS=CANCELLED). Missing required
  properties emit `itip_missing_property` warnings.
- Does not implement any networking or mailbox delivery.

## 7. RECURRENCE-ID overrides

An event with `RECURRENCE-ID` is an **override** that replaces the
recurring instance matching that date-time. Override resolution
rules:

- If a base event (UID=X with no RECURRENCE-ID) and an override event
  (UID=X with RECURRENCE-ID=Y) both appear, the base's occurrence at
  time Y is **replaced** by the override in `expand` output.
- An override with `STATUS:CANCELLED` removes that one occurrence
  entirely.
- `RECURRENCE-ID` with a `RANGE=THISANDFUTURE` parameter extends the
  override to all future occurrences (replaces the base's RRULE
  expansion from Y onwards). `RANGE=THISANDPRIOR` is deprecated.

Overrides that reference a recurrence-id not produced by the base
event emit `orphan_override` warnings; the override is still emitted
as a standalone occurrence.

## 8. EXRULE (deprecated)

`EXRULE` is parsed but removed in RFC 5545 (was in RFC 2445). This
tool parses EXRULE, emits an `exrule_deprecated` warning, and
expands it as a subtractive filter (occurrences matching EXRULE are
excluded). Publishers should use `EXDATE` or `RRULE` adjustments
instead.

## 9. CLI output

See `technical-requirements-prompt.md` for the CLI contract.
Semantically:

### 9.1 `parse`

```
ical parse --input <file.ics> --output <out.json>
```

Writes a JSON object with keys (in this order):
`calendar`, `events`, `todos`, `journals`, `freebusy`, `timezones`,
`warnings`.

### 9.2 `expand`

```
ical expand --input <file.ics> --from <ISO> --to <ISO> --output <out.json>
```

Writes a JSON object with keys (in this order):
`occurrences`, `warnings`.

`occurrences` is sorted ascending by `dtstart`. Each occurrence:

```json
{
  "uid": "string",
  "dtstart": "ISO-8601 string",
  "dtend": "ISO-8601 string | null",
  "tz": "string | null",   // present only for zoned events
  "override": true | false  // present if from a RECURRENCE-ID override
}
```

## 10. Warning kinds

- `unsupported_component` — an unrecognized top-level component.
- `unresolved_tzid` — a `TZID=` referenced a VTIMEZONE not defined
  in the file. Value is treated as floating.
- `exrule_deprecated` — an `EXRULE` was encountered (handled as a
  subtractive filter, with warning).
- `orphan_override` — a `RECURRENCE-ID` references a time not
  produced by the base event's recurrence.
- `itip_missing_property` — required iTIP property is absent.
- `malformed_value` — a value could not be parsed under its type.

## 11. Error handling

Exit codes:

- `0` on successful parse/expand.
- `1` on:
  - missing `BEGIN:VCALENDAR` / unmatched BEGIN/END pairs
  - syntactically invalid content lines (no colon, malformed
    fold-continuation)
  - malformed required date/time in DTSTART/DTEND/DTSTAMP
  - invalid `--from` / `--to` arguments to `expand`
  - missing required CLI flags
- `2` on internal error.

On exit 1, the `--output` file contains:

```json
{"error": {"line": integer, "column": integer, "message": "string"},
 "warnings": [ ... ]}
```

## 12. Character encoding

All input and output is UTF-8. The tool MUST NOT attempt IANA tzdata
lookup; timezone resolution is strictly in-file via `VTIMEZONE`
components.
