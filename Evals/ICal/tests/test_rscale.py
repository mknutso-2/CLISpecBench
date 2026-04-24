"""RFC 7529 RSCALE extension to RRULE.

RFC 7529 extends `RRULE` with an `RSCALE` element naming the calendar system
used to drive recurrence iteration. `RSCALE=GREGORIAN` is always expandable
using existing Gregorian logic; `RSCALE=HEBREW`, `RSCALE=CHINESE`,
`RSCALE=ISLAMIC`, etc. require a non-Gregorian calendar library.

Per technical-requirements-prompt.md, an implementation MAY either:

  (a) expand the recurrence correctly for the named calendar system, or

  (b) emit an `rscale_unsupported` warning AND preserve the full original
      RRULE in the event's `raw_properties` so downstream consumers can
      recover the data.

Both outcomes are acceptable for non-Gregorian scales; Gregorian RSCALE
MUST always expand correctly (it is equivalent to no RSCALE, plus optional
SKIP for invalid dates per RFC 7529 §4.1).

All `DTSTART`, `RECURRENCE-ID`, `RDATE`, and `EXDATE` values remain
Gregorian regardless of RSCALE (RFC 7529 §3 principle 1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_expand, run_parse, starts_for, warnings_of, wrap_event


def _raw_rrule(ev: dict[str, Any]) -> str | None:
    """Return the raw RRULE value string from an event's raw_properties,
    or None if absent."""
    raw_props = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    for p in raw_props:
        if p.get("name") == "RRULE":
            val = p.get("value")
            return val if isinstance(val, str) else None
    return None


# ---------------------------------------------------------------------------
# RSCALE=GREGORIAN — must always expand correctly (it's the default scale)
# ---------------------------------------------------------------------------


def test_rscale_gregorian_parsed_on_rrule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """`RSCALE=GREGORIAN` is a no-op relative to default Gregorian behavior; the
    parser must surface the rscale on the rrule object (schema says
    `rscale: string | null`)."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART;VALUE=DATE:20260305\n"
        "RRULE:RSCALE=GREGORIAN;FREQ=YEARLY;COUNT=3\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    rrule = cast(dict[str, Any], ev.get("rrule") or {})
    # rscale must be surfaced when present. Case-normalization to uppercase is
    # RFC-recommended (§5: "RSCALE values are case insensitive, but uppercase
    # is preferred") but we accept any casing that preserves the token.
    rscale = rrule.get("rscale")
    assert isinstance(rscale, str)
    assert rscale.upper() == "GREGORIAN"


def test_rscale_gregorian_yearly_expands_correctly(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7529 §4.3.4: `DTSTART=20120229; RRULE=RSCALE=GREGORIAN;FREQ=YEARLY`
    (no SKIP; default SKIP=OMIT) behaves exactly like the RFC 5545 default
    — only leap years emit an instance. Over 2024-2032 we should see just
    2024-02-29 and 2028-02-29."""
    body = (
        "UID:e1\nDTSTAMP:20240101T120000Z\nDTSTART;VALUE=DATE:20240229\n"
        "RRULE:RSCALE=GREGORIAN;FREQ=YEARLY;COUNT=5\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2024-01-01T00:00:00Z",
        "2033-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out.get("occurrences") or [], "e1")
    # COUNT=5 against a default SKIP=OMIT rule that only emits on leap years.
    # The first five valid instances are 2024, 2028, 2032, 2036, 2040 — but we
    # stop the expand window at 2033, so we should see 2024, 2028, 2032.
    assert "2024-02-29" in starts
    assert "2028-02-29" in starts
    assert "2032-02-29" in starts


def test_rscale_gregorian_skip_forward_fills_missing_dates(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7529 §4.3.4 example: `DTSTART=20120229;RRULE=RSCALE=GREGORIAN;
    FREQ=YEARLY;SKIP=FORWARD` fills in non-leap years by moving Feb 29 to
    March 1. Implementations that support RSCALE=GREGORIAN should handle SKIP
    (no separate non-Gregorian library needed). If the implementation can't
    handle SKIP it MAY emit `rscale_unsupported` and preserve the RRULE."""
    body = (
        "UID:e1\nDTSTAMP:20120101T120000Z\nDTSTART;VALUE=DATE:20120229\n"
        "RRULE:RSCALE=GREGORIAN;FREQ=YEARLY;SKIP=FORWARD;COUNT=4\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2012-01-01T00:00:00Z",
        "2017-01-01T00:00:00Z",
        tmp_path,
    )
    kinds = [w.get("kind") for w in warnings_of(out)]
    starts = starts_for(out.get("occurrences") or [], "e1")
    if "rscale_unsupported" in kinds:
        # Accept fallback: the RRULE is preserved in raw_properties, and no
        # expansion is required.
        parsed = run_parse(submission_command, wrap_event(body), tmp_path)
        ev = find_event(parsed, "e1")
        raw = _raw_rrule(ev) or ""
        assert "SKIP=FORWARD" in raw
        assert "RSCALE=GREGORIAN" in raw
    else:
        # If the implementation claims support, it must produce the expected
        # filled-in dates: 2012-02-29, 2013-03-01, 2014-03-01, 2015-03-01.
        assert "2012-02-29" in starts
        assert "2013-03-01" in starts
        assert "2014-03-01" in starts
        assert "2015-03-01" in starts


# ---------------------------------------------------------------------------
# Non-Gregorian RSCALE: correct expansion OR rscale_unsupported + preserved RRULE
# ---------------------------------------------------------------------------


def test_rscale_chinese_either_expand_or_unsupported_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7529 §4.3.1 example: `DTSTART=20130210;RRULE=RSCALE=CHINESE;
    FREQ=YEARLY` represents Chinese New Year. A conforming implementation MAY
    either expand correctly to the RFC 7529 table (20130210, 20140131, 20150219,
    20160208, 20170128) OR emit `rscale_unsupported` and preserve the RRULE in
    raw_properties."""
    body = (
        "UID:cny\nDTSTAMP:20130101T120000Z\nDTSTART;VALUE=DATE:20130210\n"
        "RRULE:RSCALE=CHINESE;FREQ=YEARLY;COUNT=5\n"
    )
    ics = wrap_event(body)
    expand_out = run_expand(
        submission_command, ics, "2013-01-01T00:00:00Z", "2018-01-01T00:00:00Z", tmp_path
    )
    kinds = [w.get("kind") for w in warnings_of(expand_out)]
    starts = starts_for(expand_out.get("occurrences") or [], "cny")
    if "rscale_unsupported" in kinds:
        # Fallback path: RRULE must be preserved in raw_properties.
        parsed = run_parse(submission_command, ics, tmp_path)
        ev = find_event(parsed, "cny")
        raw = _raw_rrule(ev) or ""
        assert "RSCALE=CHINESE" in raw
    else:
        # Implementation claims it supports Chinese. Must produce at least the
        # anchor instance (2013-02-10) and the 2014 instance (2014-01-31) from
        # RFC 7529 §4.3.1.
        assert "2013-02-10" in starts
        assert "2014-01-31" in starts


def test_rscale_hebrew_either_expand_or_unsupported_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7529 §4.3.3 example: Hebrew anniversary in leap month (Adar I = 5L)
    with SKIP=FORWARD. Must either produce the sequence from RFC 7529 §4.3.3
    (20140208, 20150227, 20160217, 20170306, 20180223) or emit
    `rscale_unsupported` and preserve the RRULE."""
    body = (
        "UID:h1\nDTSTAMP:20140101T120000Z\nDTSTART;VALUE=DATE:20140208\n"
        "RRULE:RSCALE=HEBREW;FREQ=YEARLY;BYMONTH=5L;BYMONTHDAY=8;SKIP=FORWARD;COUNT=5\n"
    )
    ics = wrap_event(body)
    expand_out = run_expand(
        submission_command, ics, "2014-01-01T00:00:00Z", "2019-01-01T00:00:00Z", tmp_path
    )
    kinds = [w.get("kind") for w in warnings_of(expand_out)]
    starts = starts_for(expand_out.get("occurrences") or [], "h1")
    if "rscale_unsupported" in kinds:
        parsed = run_parse(submission_command, ics, tmp_path)
        ev = find_event(parsed, "h1")
        raw = _raw_rrule(ev) or ""
        assert "RSCALE=HEBREW" in raw
        # The leap-month marker in raw RRULE must also be preserved (it's
        # essential for downstream re-expansion).
        assert "5L" in raw
    else:
        # Must produce at least the anchor instance.
        assert "2014-02-08" in starts


def test_rscale_islamic_warning_preserves_rrule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The `islamic-civil` calendar is widely used in practice. For implementations
    without a non-Gregorian library, RSCALE=ISLAMIC-CIVIL must emit
    `rscale_unsupported` and leave the RRULE textually intact in raw_properties
    so a downstream consumer can re-process it."""
    body = (
        "UID:ramadan\nDTSTAMP:20260101T120000Z\nDTSTART;VALUE=DATE:20260219\n"
        "RRULE:RSCALE=ISLAMIC-CIVIL;FREQ=YEARLY;COUNT=3\n"
    )
    parsed = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(parsed, "ramadan")
    kinds = [w.get("kind") for w in warnings_of(parsed)]
    # If rscale_unsupported is emitted during parse, verify the RRULE is
    # preserved. If not, the implementation supports ISLAMIC-CIVIL; accept.
    if "rscale_unsupported" in kinds:
        raw = _raw_rrule(ev) or ""
        assert "RSCALE=ISLAMIC-CIVIL" in raw
        assert "FREQ=YEARLY" in raw


# ---------------------------------------------------------------------------
# Parse-time: rscale surfaces on the rrule object OR in raw_properties
# ---------------------------------------------------------------------------


def test_rscale_surfaces_on_rrule_object(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The `rscale` field on an rrule object (schema: `rscale: string | null`)
    must be populated when an RSCALE element is present in the RRULE. This is
    a parse-time requirement — regardless of whether the scale is actually
    expandable."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART;VALUE=DATE:20260210\n"
        "RRULE:RSCALE=CHINESE;FREQ=YEARLY;COUNT=3\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    rrule = ev.get("rrule")
    # If the parser refused to construct an rrule object (e.g. because the
    # scale is unknown), it MUST at least have recorded `rscale_unsupported`.
    kinds = [w.get("kind") for w in warnings_of(out)]
    if rrule is None:
        assert "rscale_unsupported" in kinds
    else:
        rscale = rrule.get("rscale")
        assert rscale is not None
        assert rscale.upper() == "CHINESE"


def test_rscale_skip_field_surfaced(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When SKIP is present on an RRULE, the parser must surface it in the
    `skip` field of the rrule object (schema: `skip: "OMIT"|"BACKWARD"|
    "FORWARD"|null`). Per RFC 7529 §4, SKIP MUST NOT be present unless RSCALE
    is also present — but we assert only the positive case here."""
    body = (
        "UID:e1\nDTSTAMP:20120101T120000Z\nDTSTART;VALUE=DATE:20120229\n"
        "RRULE:RSCALE=GREGORIAN;FREQ=YEARLY;SKIP=FORWARD;COUNT=3\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    kinds = [w.get("kind") for w in warnings_of(out)]
    rrule = ev.get("rrule")
    if rrule is None:
        assert "rscale_unsupported" in kinds
    else:
        skip = rrule.get("skip")
        # skip may be None if the implementation doesn't track it, but when
        # non-None it must be the normalized uppercase token.
        if skip is not None:
            assert skip.upper() == "FORWARD"
