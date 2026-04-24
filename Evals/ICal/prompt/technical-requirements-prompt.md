The tool must be a single command-line executable named `ical` with two
subcommands.

```
ical parse --input <path.ics> --output <out.json>
ical expand --input <path.ics> --from <ISO-8601> --to <ISO-8601> --output <out.json>
```

`--from` / `--to` may be `YYYY-MM-DD` dates or `YYYY-MM-DDTHH:MM:SSZ`
UTC date-times. `--from` is inclusive; `--to` is exclusive.

## Mandatory semantic schema (required for scoring)

### `parse` output

```json
{
  "calendar": {
    "prodid": "string",
    "version": "string",
    "calscale": "string | null",
    "method": "string | null",
    "name": "string | null",
    "description": "string | null",
    "refresh_interval": "ISO-8601 duration | null",
    "source": "URI | null",
    "color": "string | null",
    "url": "URI | null",
    "categories": ["string", ...],
    "images": [{"value": "string", "fmttype": "string | null",
                 "encoding": "string | null", "display": "string | null"}, ...],
    "conferences": [{"value": "URI", "feature": "string | null",
                      "label": "string | null"}, ...]
  },
  "events": [<vevent object>, ...],
  "todos": [<vtodo object>, ...],
  "journals": [<vjournal object>, ...],
  "freebusy": [<vfreebusy object>, ...],
  "timezones": [<vtimezone object>, ...],
  "availabilities": [<vavailability object>, ...],
  "warnings": [<warning object>, ...]
}
```

Where `availabilities` is the array of RFC 7953 VAVAILABILITY
components parsed from the input (empty list when none are present).

### `expand` output

```json
{
  "occurrences": [
    {"uid": "string", "dtstart": "ISO-8601",
     "dtend": "ISO-8601 | null", "tz": "string | null",
     "override": boolean, "recurrence_id": "ISO-8601 | null",
     "range": "THISANDFUTURE | null", "cancelled": boolean}
  ],
  "warnings": [<warning object>, ...]
}
```

The *set of top-level keys* shown above is mandatory. Each key's type
and semantic content is mandatory. Per-entry field names (`uid`,
`dtstart`, `rrule`, etc.) and their types are mandatory.
`occurrences` MUST be sorted ascending by `dtstart`, with ties
broken by `uid` lexicographic order (stable sort).

## Harness-recommended formatting (scored as soft hints)

These are evaluator conveniences, not part of the RFC-5545 contract.
An agent that follows them makes the evaluator's life easier; an
agent that emits the same *semantic* content in a different
formatting style is not penalized by any explicit test:

- Top-level key order: `calendar`, `events`, `todos`, `journals`,
  `freebusy`, `timezones`, `warnings` for `parse`; `occurrences`,
  `warnings` for `expand`. JSON's own object-key ordering is
  unordered; the harness does not assert on object-key order except
  where semantically meaningful (e.g. occurrences sort order).
- Stable emission of optional fields as `null` vs. absence.
- `dtstart` / `dtend` ISO formatting (§ISO-8601 below) is semantic
  and is asserted.

## VEVENT object schema

```json
{
  "uid": "string",
  "dtstamp": "ISO-8601",
  "dtstart": "ISO-8601",
  "dtend": "ISO-8601 | null",
  "duration": "ISO-8601 duration | null",
  "summary": "string | null",
  "description": "string | null",
  "location": "string | null",
  "status": "string | null",
  "class": "string | null",
  "priority": integer | null,
  "transp": "string | null",
  "url": "string | null",
  "geo": {"lat": float, "lon": float} | null,
  "categories": ["string", ...],
  "resources": ["string", ...],
  "contact": "string | null",
  "organizer": <cal-address object | null>,
  "attendees": [<cal-address object>, ...],
  "rrule": <rrule object | null>,
  "rdate": [<rdate entry>, ...],
  "exdate": ["ISO-8601", ...],
  "exrule": <rrule object | null>,
  "recurrence_id": {"value": "ISO-8601", "range": "THISANDFUTURE | null",
                     "tzid": "string | null"} | null,
  "sequence": integer | null,
  "created": "ISO-8601 | null",
  "last_modified": "ISO-8601 | null",
  "attachments": [{"value": "string", "fmttype": "string | null",
                     "encoding": "string | null"}, ...],
  "conferences": [{"value": "URI", "feature": "string | null",
                     "label": "string | null"}, ...],
  "color": "string | null",
  "images": [{"value": "string", "fmttype": "string | null",
                "encoding": "string | null", "display": "string | null"}, ...],
  "alarms": [<valarm object>, ...],
  "raw_properties": [{"name": "string", "params": {},
                        "value": "string"}, ...]
}
```

An `rdate entry` is either a plain ISO-8601 string (for
`VALUE=DATE-TIME` / `VALUE=DATE`) or a period object:

```json
{"start": "ISO-8601", "end": "ISO-8601"} | {"start": "ISO-8601", "duration": "ISO-8601 duration"}
```

A `cal-address object`:

```json
{
  "value": "string",
  "cn": "string | null",
  "cutype": "string | null",
  "role": "string | null",
  "partstat": "string | null",
  "rsvp": boolean | null,
  "member": ["string", ...],
  "delegated_from": ["string", ...],
  "delegated_to": ["string", ...],
  "sent_by": "string | null",
  "dir": "string | null",
  "language": "string | null"
}
```

A `valarm object` (includes RFC 9074 extensions):

```json
{
  "uid": "string | null",
  "action": "AUDIO | DISPLAY | EMAIL | PROCEDURE | string",
  "trigger": {"value": "ISO-8601 | ISO-8601 duration",
               "related": "START | END | null"},
  "description": "string | null",
  "summary": "string | null",
  "attendees": [<cal-address object>, ...],
  "duration": "ISO-8601 duration | null",
  "repeat": integer | null,
  "attach": [<attachment>, ...],
  "acknowledged": "ISO-8601 | null",
  "proximity": "ARRIVE | DEPART | string | null",
  "related_to": [{"value": "string",
                     "reltype": "string | null"}, ...],
  "raw_properties": [{"name": "string", "params": {},
                        "value": "string"}, ...]
}
```

RFC 9074 adds:

- `UID` on VALARM to uniquely identify alarms across replicas.
- `ACKNOWLEDGED` — UTC DATE-TIME of the user's last acknowledgement
  of this alarm (used for snooze workflows).
- `PROXIMITY` — geographic-trigger hint: `ARRIVE`, `DEPART`, or
  an x-name.
- `RELATED-TO` — links this alarm to other components (e.g.,
  another VEVENT or VALARM UID) with an optional `RELTYPE`
  parameter.
- Enhanced EMAIL-alarm semantics with multiple ATTACH values
  interpretable as email attachments.

VTODO/VJOURNAL/VFREEBUSY objects carry the common base (`uid`,
`dtstamp`, `summary`, `description`, `categories`, `organizer`,
`attendees`, `raw_properties`) plus their type-specific fields:

- **VTODO** adds `due` (ISO-8601 | null), `completed` (ISO-8601 |
  null), `percent_complete` (integer | null), `status`, `priority`,
  `rrule`, `rdate`, `exdate`, `recurrence_id`, `alarms`.
- **VJOURNAL** adds `status`, `related_to` (array of strings),
  `attachments`, `rrule`, `rdate`, `exdate`, `recurrence_id`.
- **VFREEBUSY** adds `dtstart`, `dtend`, `freebusy` (array of
  `{"fbtype": "string | null", "periods": [<period>, ...]}`).

## VTIMEZONE object schema

```json
{
  "tzid": "string",
  "last_modified": "ISO-8601 | null",
  "tzurl": "string | null",
  "comment": ["string", ...],
  "standard": [<observance object>, ...],
  "daylight": [<observance object>, ...]
}
```

Where each observance object:

```json
{
  "dtstart": "ISO-8601 string (floating)",
  "tzoffsetfrom": "±HH:MM",
  "tzoffsetto": "±HH:MM",
  "tzname": "string | null",
  "rrule": <rrule object | null>,
  "rdate": ["ISO-8601", ...]
}
```

Notes:

- `tzoffsetfrom` / `tzoffsetto` are emitted in the colonized form
  (`+HH:MM` / `-HH:MM`); the input RFC 5545 form (`±HHMM`) is
  normalized on read.
- `tzname` is a scalar string, not an array. An observance with no
  TZNAME emits null.
- VTIMEZONE-level `comment` (top-level, not inside an observance) is
  an array of strings. Observance-level COMMENT is OUT OF SCOPE:
  this schema does not expose it on the observance object (neither
  as a typed field nor through `raw_properties`), and the reference
  implementation silently drops COMMENT properties that appear
  inside STANDARD / DAYLIGHT blocks.
- VTIMEZONE may contain multiple STANDARD and/or multiple DAYLIGHT
  observances to model historical rule changes (each observance is
  active from its DTSTART forward until superseded by the next
  observance's DTSTART — per RFC 5545 §3.6.5).

## RRULE object schema

```json
{
  "freq": "SECONDLY | MINUTELY | HOURLY | DAILY | WEEKLY | MONTHLY | YEARLY",
  "interval": integer,
  "count": integer | null,
  "until": "ISO-8601 | null",
  "bymonth": [integer, ...] | null,
  "byweekno": [integer, ...] | null,
  "byyearday": [integer, ...] | null,
  "bymonthday": [integer, ...] | null,
  "byday": [{"weekday": "MO..SU", "offset": integer | null}, ...] | null,
  "byhour": [integer, ...] | null,
  "byminute": [integer, ...] | null,
  "bysecond": [integer, ...] | null,
  "bysetpos": [integer, ...] | null,
  "wkst": "MO..SU | null",
  "rscale": "string | null",
  "skip": "OMIT | BACKWARD | FORWARD | null"
}
```

## ISO-8601 normalization (semantic, asserted)

- DATE → `YYYY-MM-DD`.
- DATE-TIME UTC → `YYYY-MM-DDTHH:MM:SSZ`.
- DATE-TIME floating → `YYYY-MM-DDTHH:MM:SS` (no suffix).
- Zoned DATE-TIMEs in `expand` output are converted to UTC (trailing
  `Z`); the source TZID is reported in the `tz` field on the
  occurrence. In `parse` output, zoned date-times are preserved as
  floating-form strings and the TZID appears in the corresponding
  `raw_properties[...]["params"]`.
- DURATION values → ISO-8601 duration strings (`PT1H30M`, `-P1D`,
  etc.).
- UTC-OFFSET values are normalized to the colonized ISO-8601 form
  `±HH:MM` (or `±HH:MM:SS` when the input includes seconds). The
  RFC 5545 on-wire form is `±HHMM` / `±HHMMSS` (no colon); our JSON
  output adds the colon for readability and parity with the ISO
  date-time strings in the rest of the schema.

## VAVAILABILITY object schema (RFC 7953)

A `vavailability object` carries publishing-grade availability
windows:

```json
{
  "uid": "string",
  "dtstamp": "ISO-8601 | null",
  "dtstart": "ISO-8601 | null",
  "dtend": "ISO-8601 | null",
  "duration": "ISO-8601 duration | null",
  "summary": "string | null",
  "description": "string | null",
  "busytype": "BUSY | BUSY-UNAVAILABLE | BUSY-TENTATIVE | string | null",
  "priority": "integer | null",
  "organizer": <cal-address object | null>,
  "available": [<available object>, ...],
  "raw_properties": [...]
}
```

An `available object` is the AVAILABLE sub-component (RFC 7953
§3.2). The schema covers every AVAILABLE property RFC 7953 §3.2
mentions. Any additional extension property appears in
`raw_properties`:

```json
{
  "uid": "string",
  "dtstamp": "ISO-8601 | null",
  "dtstart": "ISO-8601 | null",
  "dtend": "ISO-8601 | null",
  "duration": "ISO-8601 duration | null",
  "summary": "string | null",
  "description": "string | null",
  "location": "string | null",
  "contact": "string | null",
  "created": "ISO-8601 | null",
  "last_modified": "ISO-8601 | null",
  "recurrence_id": {"value": "ISO-8601", "range": "THISANDFUTURE | null",
                     "tzid": "string | null"} | null,
  "categories": ["string", ...],
  "comment": ["string", ...],
  "rrule": <rrule object | null>,
  "rdate": [<rdate entry>, ...],
  "exdate": ["ISO-8601", ...],
  "raw_properties": [...]
}
```

## Warning schema

```json
{"kind": "string", "message": "string",
 "uid": "string?", "value": "string?", "line": "integer?",
 "column": "integer?"}
```

Warning `kind` values emitted by this tool:

- `unsupported_component`
- `unresolved_tzid`
- `orphan_override`
- `exrule_deprecated`
- `malformed_value`
- `itip_missing_property`
- `rscale_unsupported`
- `duplicate_uid`
- `timezone_fold_ambiguous`
- `nonexistent_local_time`
- `binary_decode_failed`
- `param_escape_invalid`
- `line_too_long`

The presence of any listed kind is semantic (tests will assert
whether a given warning *kind* appears in the `warnings` array), but
the specific `message` text is NOT asserted. The metadata fields are
optional — tests must not fail on their absence.

## Error output

On exit 1:

```json
{
  "error": {"line": integer, "column": integer, "message": "string"},
  "warnings": [...]
}
```

## Exit codes

- `0`: success.
- `1`: invalid input — malformed `.ics`, invalid CLI args, missing
  required flag.
- `2`: unexpected internal error.
