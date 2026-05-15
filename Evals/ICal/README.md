# ICal

Full iCalendar (RFC 5545 + 5546 + 6868 + 7529 + 7953 + 7986 +
9073 + 9074 + 9253) eval for
CLISpecBench. Agents receive the IETF RFCs themselves verbatim and
must produce a CLI that parses calendar files, surfaces every
RFC-defined property and component, expands recurrence rules to
concrete occurrences over a date window, resolves zoned date-times
through in-file VTIMEZONE definitions, and honors the iTIP
scheduling layer.

> **Status.** v3.0.0 — author-eval review cleanup over the completed
> v1.x/v2.x expansion work, tightening the iTIP warning contract and
> documenting DST fold resolution. Ships **9 authoritative RFCs** verbatim:
> RFC 5545 (core) +
> RFC 5546 (iTIP) + RFC 6868 (param escaping) + RFC 7529 (RSCALE) +
> RFC 7953 (Calendar Availability) + RFC 7986 (calendar props) +
> RFC 9073 (event publishing) + RFC 9074 (VALARM extensions) +
> RFC 9253 (relationships). Test suite is **465 tests** (up from
> 245 at v1.0), covering VALARM ext, VFREEBUSY semantics, VTIMEZONE
> resolution depth, DST fold/gap warnings, iTIP per-method matrices,
> VAVAILABILITY, event-publishing extensions, 75-octet folding edges,
> stress scenarios, and real-world (Gmail / Outlook / iTIP) corpora.
> The v2.0.0 major bump introduced the `STATUS:CANCELLED` override
> contract: cancelled instances remain in the `occurrences` array with
> `cancelled: true` rather than being silently dropped. The v3.0.0 bump
> tightened structured iTIP warning metadata.

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
      rfc7953.txt                   # calendar availability
      rfc7986.txt                   # new calendar properties
      rfc9073.txt                   # event publishing extensions
      rfc9074.txt                   # VALARM extensions
      rfc9253.txt                   # iCalendar relationships
tests/
  conftest.py                       # EVAL_CONFIG + helpers
  test_build.py                     # smoke: binary builds
  test_schema.py                    # top-level JSON shape gate
  test_schema_depth.py              # deeper schema invariants
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
  test_folding_edges.py             # line_too_long and invalid fold cases
  test_itip_methods.py              # RFC 5546 method-specific requirements
  test_itip_methods_deep.py         # deeper iTIP method matrices
  test_itip_per_component.py        # component-specific iTIP requirements
  test_recurrence_id_range.py       # RANGE=THISANDFUTURE semantics
  test_dst_warnings.py              # fold/gap warning behavior
  test_event_fields.py              # common VEVENT/VTODO/VJOURNAL fields
  test_vtimezone_fields.py          # VTIMEZONE LAST-MODIFIED/TZURL/etc.
  test_vtimezone_resolution.py      # observance UNTIL/RDATE/BYMONTHDAY
  test_valarm_rfc9074.py            # RFC 9074 VALARM extensions
  test_vfreebusy.py                 # VFREEBUSY typed fields
  test_vavailability.py             # RFC 7953 VAVAILABILITY
  test_rfc9073_event_publishing.py  # RFC 9073 rich-event extensions
  test_rfc9253_relationships.py     # RFC 9253 LINK/RELATED-TO extensions
  test_real_world_corpora.py        # Gmail/Outlook/iTIP fixtures
  test_stress.py                    # scale and regression cases
  test_error_precision.py           # error line/column fields
  test_errors.py                    # exit-1 cases
reference-implementation-cpp/
  CMakeLists.txt
  src/                              # see below
VERSION                             # 3.0.0
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
   instances; `STATUS:CANCELLED` overrides keep the occurrence in
   the array but mark it `cancelled: true` so consumers can
   observe the cancellation explicitly. Occurrences carry an
   `override` boolean and a `cancelled` boolean.
6. **EXDATE / EXRULE / RDATE** — additive and subtractive
   modifiers applied correctly.

Tests use `.get()`-based helpers (`find_event`, `warnings_of`,
`occurrences_of`) so schema bugs don't cascade.

## Running tests

```bash
uv run pytest Evals/ICal/tests --language=cpp
```

The reference implementation passes all **465** tests. Run from the
repository root.

## Task IDs

- `ical-cpp` — C++20 target; reference implementation available
- `ical-js` — JavaScript target
- `ical-py` — Python target
- `ical-rs` — Rust target

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

- `prompt/docs/authoritative/rfc5545.txt`, `rfc5546.txt`,
  `rfc6868.txt`, `rfc7529.txt`, `rfc7953.txt`, `rfc7986.txt`,
  `rfc9073.txt`, `rfc9074.txt`, and `rfc9253.txt` — the
  authoritative specs shipped verbatim.
- [`prompt/docs/summary.md`](prompt/docs/summary.md) — navigation
  index over the above.
- [`prompt/docs/LICENSES.md`](prompt/docs/LICENSES.md) — IETF TLP
  redistribution notice.
- [RFC 5545](https://datatracker.ietf.org/doc/html/rfc5545) — the
  authoritative upstream spec (online canonical version).
- [`Evals/EVAL_CANDIDATE_DISCUSSION.md`](../EVAL_CANDIDATE_DISCUSSION.md) — the
  proposal-ranking document that motivated building this eval.
