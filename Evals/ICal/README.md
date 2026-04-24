# ICal

Full iCalendar (RFC 5545 + 5546 + 6868 + 7529 + 7986) eval for
CLISpecBench. Agents receive the IETF RFCs themselves verbatim and
must produce a CLI that parses calendar files, surfaces every
RFC-defined property and component, expands recurrence rules to
concrete occurrences over a date window, resolves zoned date-times
through in-file VTIMEZONE definitions, and honors the iTIP
scheduling layer.

> **Status.** v1.1.0 — test-surface expansion over v1.0. v1.0 was
> the authoritative-spec release (RFC 5545 + 5546 + 6868 + 7529 +
> 7986 shipped verbatim). v1.1 adds **97 new tests (245 → 342)** per
> [`PLAN.md`](PLAN.md) Parts B1–B10, ships RFC 9074 (VALARM
> extensions), and extends the reference implementation for VFREEBUSY
> full modeling, 12 event-level fields, 3 VTIMEZONE fields, iTIP
> ADD / REFRESH / COUNTER / DECLINECOUNTER, DST fold/gap warnings
> (`timezone_fold_ambiguous`, `nonexistent_local_time`), and deep
> schema conformance. **342 tests.**

## Directory structure

```
prompt/
  base-prompt.md                    # domain-expert persona prompt
  technical-requirements-prompt.md  # CLI contract + JSON schema
  docs/
    LICENSES.md                     # IETF TLP 5.0 notice
    summary.md                      # reading index (navigation only)
    authoritative/
      rfc5545.txt                   # core iCalendar (authoritative)
      rfc5546.txt                   # iTIP scheduling
      rfc6868.txt                   # parameter value escaping
      rfc7529.txt                   # non-Gregorian RSCALE
      rfc7986.txt                   # new calendar properties
tests/
  conftest.py                       # EVAL_CONFIG + helpers
  test_build.py                     # smoke: binary builds
  test_schema.py                    # top-level JSON shape gate
  test_parse.py                     # line unfolding, escapes, value types
  test_rrule_parse.py               # RRULE struct decoding
  test_rrule_expand.py              # common-case expansion (DAILY...YEARLY)
  test_vtimezone.py                 # VTIMEZONE parse + TZID → UTC resolution
  test_v02_features.py              # sub-day FREQ, BYHOUR/MINUTE/SECOND,
                                    # RECURRENCE-ID overrides, EXRULE
  test_adversarial_corners.py       # DST / sub-day / BY* edges
  test_library_divergence.py        # rrule.js / dateutil bug regressions
  test_valarm.py                    # VALARM TRIGGER/REPEAT/ACTION
  test_attendee_grammar.py          # full RFC 5545 §3.2 cal-address grammar
  test_rdate_period.py              # VALUE=PERIOD RDATE
  test_vtimezone_historical.py      # multi-observance / TZUNTIL reload
  test_param_escape.py              # RFC 6868 ^n / ^' / ^^
  test_rscale.py                    # RFC 7529 RSCALE
  test_calendar_properties.py       # RFC 7986 NAME/REFRESH-INTERVAL/etc.
  test_line_folding_octets.py       # 75-octet folding with multi-byte UTF-8
  test_itip_methods.py              # RFC 5546 method-specific requirements
  test_recurrence_id_range.py       # RANGE=THISANDFUTURE semantics
  test_errors.py                    # exit-1 cases
reference-implementation-cpp/
  CMakeLists.txt
  src/                              # see below
VERSION                             # 1.0.0
CHANGELOG.md
```

## What this eval evaluates

1. **`.ics` lexical parsing** — CRLF line folding, property name /
   parameter / value separation, quoted parameter values, TEXT
   escapes (`\\` / `\;` / `\,` / `\n`).
2. **Component parsing** — VEVENT / VTODO / VJOURNAL / VFREEBUSY /
   VTIMEZONE at top level; VALARM nested. All common properties
   surfaced per-component with proper typing.
3. **RRULE parsing and expansion** — every FREQ (SECONDLY through
   YEARLY), every BYxxx part (BYMONTH / BYWEEKNO / BYYEARDAY /
   BYMONTHDAY / BYDAY / BYHOUR / BYMINUTE / BYSECOND), BYSETPOS,
   WKST, COUNT / UNTIL termination. Applied in the RFC 5545 §3.3.10
   fixed order. Invalid candidate dates dropped silently. Time
   expansion produces the cartesian product across BYHOUR×BYMINUTE×
   BYSECOND.
4. **VTIMEZONE resolution** — parse STANDARD / DAYLIGHT observances
   with their DTSTART / TZOFFSETFROM / TZOFFSETTO / RRULE / RDATE.
   During `expand`, resolve `TZID=X` DATE-TIMEs to UTC by walking
   the observances and applying the appropriate TZOFFSETTO.
5. **Overrides** — `RECURRENCE-ID` events replace matching base
   instances; `STATUS:CANCELLED` overrides remove instances.
   Occurrences carry an `override` boolean.
6. **EXDATE / EXRULE / RDATE** — additive and subtractive
   modifiers applied correctly.

Tests use `.get()`-based helpers (`find_event`, `warnings_of`,
`occurrences_of`) so schema bugs don't cascade.

## Running tests

```bash
uv run pytest Evals/ICal/tests --language=cpp
```

The reference implementation passes all **342** tests. Run from the
repository root.

## Task IDs

- `ical-cpp` — C++20 target

## Why this task

RFC 5545 is known for subtle semantic bugs in mainstream libraries
(rrule.js #375, #309, #556; dateutil #1398; plus long-standing
VTIMEZONE DST-boundary bugs). Testing the expansion corners against
the full spec — especially DST boundary crossings with VTIMEZONE
resolution, BYSETPOS interacting with time expansion, and
`RECURRENCE-ID` override replacement — is what v0.1 deferred and
what v0.2 now probes. See `Evals/EVAL_CANDIDATE_DISCUSSION.md` for the
original ranking argument.

## Scope

In scope (v1.0):

- Full `.ics` lexical grammar (RFC 5545 §3.1), including line
  folding at the 75-**octet** boundary (UTF-8 multi-byte aware).
- Full RRULE grammar (RFC 5545 §3.3.10) with all FREQ values and
  all BY* parts.
- VTIMEZONE parsing with multiple STANDARD / DAYLIGHT observances
  per TZID (historical-reload support); TZID resolution strictly
  from in-file observance definitions (no IANA tzdata lookup
  required or permitted). DST fold / gap disambiguation per
  summary §5.1.1.
- RECURRENCE-ID override replacement, cancellation, and
  `RANGE=THISANDFUTURE` forward shift.
- EXRULE (deprecated) subtractive expansion with warning.
- VTODO / VJOURNAL / VFREEBUSY / VALARM parsed and surfaced with
  all RFC-defined properties.
- RFC 5546 iTIP METHOD-specific validation (REQUEST / REPLY /
  CANCEL required-property checks emit `itip_missing_property`).
- RFC 6868 parameter-value escape handling (`^n`, `^'`, `^^`).
- RFC 7529 `RSCALE` / `SKIP` parsing (non-Gregorian expansion is
  optional; `rscale_unsupported` warning permitted when unhandled).
- RFC 7986 calendar-level properties (NAME, DESCRIPTION,
  REFRESH-INTERVAL, SOURCE, COLOR, URL, CATEGORIES, IMAGE,
  CONFERENCE) surfaced on the `calendar` object.
- Full RFC 5545 §3.2 cal-address grammar on ATTENDEE / ORGANIZER
  (CN / CUTYPE / ROLE / PARTSTAT / RSVP / MEMBER / DELEGATED-FROM /
  DELEGATED-TO / SENT-BY / DIR / LANGUAGE).
- RDATE VALUE=PERIOD (start/end and start/duration).
- Fold / gap detection emits `timezone_fold_ambiguous` /
  `nonexistent_local_time` warnings.

## References

- [`prompt/docs/authoritative/rfc5545.txt`](prompt/docs/authoritative/rfc5545.txt)
  through [`rfc7986.txt`](prompt/docs/authoritative/rfc7986.txt) —
  the authoritative specs shipped verbatim.
- [`prompt/docs/summary.md`](prompt/docs/summary.md) — navigation
  index over the above.
- [`prompt/docs/LICENSES.md`](prompt/docs/LICENSES.md) — IETF TLP
  redistribution notice.
- [RFC 5545](https://datatracker.ietf.org/doc/html/rfc5545) — the
  authoritative upstream spec (online canonical version).
- [`Evals/EVAL_CANDIDATE_DISCUSSION.md`](../EVAL_CANDIDATE_DISCUSSION.md) — the
  proposal-ranking document that motivated building this eval.
