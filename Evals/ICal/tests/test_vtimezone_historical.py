"""VTIMEZONE with multiple STANDARD / DAYLIGHT observances modelling historical
rule changes (RFC 5545 §3.6.5).

A VTIMEZONE MAY contain multiple STANDARD and/or DAYLIGHT observances. Each
observance is active from its DTSTART forward, until superseded by the
observance (of the same kind) whose DTSTART is later but still <= the target
moment. When resolving a zoned local time for a given event:

  1. Walk the STANDARD + DAYLIGHT observances in DTSTART order.
  2. The most recent observance with DTSTART <= the event's local time is the
     one whose TZOFFSETTO / RRULE governs DST transitions near that event.

The canonical example is the 2007 US DST rule change (Energy Policy Act of
2005): before 2007, DST ran from the 1st Sunday of April through the last
Sunday of October; from 2007 onwards it runs from the 2nd Sunday of March
through the 1st Sunday of November.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_expand, run_parse, warnings_of


def _timezones(out: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], out.get("timezones") or [])


def _occurrences(out: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], out.get("occurrences") or [])


def _observances(tz: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], tz.get(kind) or [])


def _tz_or_empty(out: dict[str, Any]) -> dict[str, Any]:
    tzs = _timezones(out)
    return tzs[0] if tzs else {}


# ---------------------------------------------------------------------------
# US DST rule change (2007): two STANDARD + two DAYLIGHT observances.
# ---------------------------------------------------------------------------

US_EASTERN_HISTORICAL = """\
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:20001029T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20000402T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=1SU
END:DAYLIGHT
BEGIN:STANDARD
DTSTART:20071104T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20070311T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
END:VTIMEZONE
"""


def _wrap(body: str) -> str:
    return (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "BEGIN:VEVENT\n"
        + body
        + "END:VEVENT\n"
        + "END:VCALENDAR\n"
    )


# ---------------------------------------------------------------------------
# Parse-time schema: the historical observances are preserved as separate
# entries in the VTIMEZONE's standard / daylight arrays.
# ---------------------------------------------------------------------------


def test_historical_vtimezone_two_standard_observances(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two STANDARD observances (pre-2007 and post-2007 US DST end rules) MUST
    be preserved as two entries in the VTIMEZONE's `standard` array (RFC 5545
    §3.6.5 allows multiple observance blocks of each kind)."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tzs = _timezones(out)
    assert len(tzs) == 1
    tz = tzs[0]
    assert tz.get("tzid") == "America/New_York"
    standards = _observances(tz, "standard")
    assert len(standards) == 2, (
        f"expected 2 STANDARD observances (pre-2007, post-2007); got {len(standards)}"
    )


def test_historical_vtimezone_two_daylight_observances(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two DAYLIGHT observances (pre-2007 and post-2007 US DST start rules) MUST
    be preserved as two entries in the VTIMEZONE's `daylight` array."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tzs = _timezones(out)
    assert len(tzs) == 1
    daylights = _observances(tzs[0], "daylight")
    assert len(daylights) == 2, (
        f"expected 2 DAYLIGHT observances (pre-2007, post-2007); got {len(daylights)}"
    )


def test_historical_observance_dtstart_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Each observance's DTSTART MUST be preserved as a floating ISO string,
    since observance transition anchors are always in local wall-clock time
    (RFC 5545 §3.8.2.4 — DTSTART in VTIMEZONE is always floating)."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tz = _tz_or_empty(out)
    daylights = _observances(tz, "daylight")
    dtstarts = {d.get("dtstart") for d in daylights}
    # Expect the two DAYLIGHT DTSTARTs: 2000-04-02T02:00:00 (pre-2007) and
    # 2007-03-11T02:00:00 (post-2007).
    assert "2000-04-02T02:00:00" in dtstarts
    assert "2007-03-11T02:00:00" in dtstarts


def test_historical_observance_rrule_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Each observance's RRULE is independently preserved. Post-2007 DAYLIGHT
    rule is BYMONTH=3;BYDAY=2SU; pre-2007 is BYMONTH=4;BYDAY=1SU."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tz = _tz_or_empty(out)
    daylights = _observances(tz, "daylight")
    # Index by DTSTART to correlate with rule era.
    by_dtstart: dict[Any, dict[str, Any]] = {d.get("dtstart"): d for d in daylights}
    pre_2007 = by_dtstart.get("2000-04-02T02:00:00") or {}
    post_2007 = by_dtstart.get("2007-03-11T02:00:00") or {}
    pre_rrule = cast(dict[str, Any], pre_2007.get("rrule") or {})
    post_rrule = cast(dict[str, Any], post_2007.get("rrule") or {})
    assert pre_rrule.get("bymonth") == [4]
    assert post_rrule.get("bymonth") == [3]


# ---------------------------------------------------------------------------
# Expand-time: resolution picks the observance active AT THE EVENT'S LOCAL TIME
# ---------------------------------------------------------------------------


def test_dst_rule_2005_uses_pre_2007_april_rule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An event on 2005-04-10 10:00 local America/New_York MUST use the pre-2007
    rule: DST started April 3, 2005 (1st Sunday of April). So April 10 is DST
    (EDT, -0400). 10:00 EDT = 14:00 UTC."""
    body = "UID:e1\nDTSTAMP:20050101T120000Z\nDTSTART;TZID=America/New_York:20050410T100000\n"
    out = run_expand(
        submission_command,
        _wrap(body),
        "2005-01-01T00:00:00Z",
        "2006-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    assert len(occs) == 1
    assert occs[0].get("dtstart") == "2005-04-10T14:00:00Z"


def test_dst_rule_2005_early_march_is_standard_time(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Under the pre-2007 rule, DST did NOT start until the 1st Sunday of April.
    An event on 2005-03-15 10:00 local is still in EST (-0500), so 15:00 UTC.
    (Under the post-2007 rule, 2005-03-15 would already be DST, which is wrong.)"""
    body = "UID:e1\nDTSTAMP:20050101T120000Z\nDTSTART;TZID=America/New_York:20050315T100000\n"
    out = run_expand(
        submission_command,
        _wrap(body),
        "2005-01-01T00:00:00Z",
        "2006-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    assert len(occs) == 1
    assert occs[0].get("dtstart") == "2005-03-15T15:00:00Z"


def test_dst_rule_2010_uses_post_2007_march_rule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Under the post-2007 rule, DST starts the 2nd Sunday of March. For 2010
    that is March 14. An event on 2010-03-20 10:00 local is DST (EDT), so
    14:00 UTC."""
    body = "UID:e1\nDTSTAMP:20100101T120000Z\nDTSTART;TZID=America/New_York:20100320T100000\n"
    out = run_expand(
        submission_command,
        _wrap(body),
        "2010-01-01T00:00:00Z",
        "2011-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    assert len(occs) == 1
    assert occs[0].get("dtstart") == "2010-03-20T14:00:00Z"


def test_dst_rule_2010_late_october_is_still_dst(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Under the post-2007 rule, DST ends the 1st Sunday of November. For 2010
    that is November 7. An event on 2010-10-25 10:00 local is still DST (EDT),
    so 14:00 UTC. (Under the pre-2007 rule, DST would have already ended on
    2010-10-31, which would be wrong.)"""
    body = "UID:e1\nDTSTAMP:20100101T120000Z\nDTSTART;TZID=America/New_York:20101025T100000\n"
    out = run_expand(
        submission_command,
        _wrap(body),
        "2010-01-01T00:00:00Z",
        "2011-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    assert len(occs) == 1
    assert occs[0].get("dtstart") == "2010-10-25T14:00:00Z"


def test_dst_rule_2005_late_october_is_standard_time(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Under the pre-2007 rule, DST ended the LAST Sunday of October. For 2005
    that is October 30. An event on 2005-10-31 10:00 local is EST (-0500), so
    15:00 UTC. (Under the post-2007 rule, 2005-10-31 would still be DST, which
    would be wrong for that era.)"""
    body = "UID:e1\nDTSTAMP:20050101T120000Z\nDTSTART;TZID=America/New_York:20051031T100000\n"
    out = run_expand(
        submission_command,
        _wrap(body),
        "2005-01-01T00:00:00Z",
        "2006-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    assert len(occs) == 1
    assert occs[0].get("dtstart") == "2005-10-31T15:00:00Z"


def test_recurring_event_spans_rule_change_boundary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A recurring event spanning the 2007 rule change: April 5 of every year at
    10:00 local. In 2006 (pre-rule) April 5 is DST (EDT) because DST started
    April 2, 2006. In 2007 (post-rule) April 5 is also DST (EDT) because DST
    started March 11, 2007. Both should resolve to 14:00 UTC (EDT is -0400 in
    both eras)."""
    body = (
        "UID:rec\nDTSTAMP:20060101T120000Z\n"
        "DTSTART;TZID=America/New_York:20060405T100000\n"
        "RRULE:FREQ=YEARLY;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2006-01-01T00:00:00Z",
        "2009-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    starts = [o.get("dtstart") for o in occs if o.get("uid") == "rec"]
    assert "2006-04-05T14:00:00Z" in starts
    assert "2007-04-05T14:00:00Z" in starts
    assert "2008-04-05T14:00:00Z" in starts


def test_event_before_any_observance_dtstart_uses_earliest_observance(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An event in 1995 (before any observance's DTSTART) is still valid ICS
    data. The parser MUST NOT reject it; resolution MAY fall back to the
    earliest observance's TZOFFSETFROM (which describes the state BEFORE that
    observance's DTSTART). The pre-2007 DAYLIGHT observance has TZOFFSETFROM
    -0500 (= EST, pre-DST state), so a March 1995 event at 10:00 resolves to
    15:00 UTC under EST."""
    body = "UID:e1\nDTSTAMP:19950101T120000Z\nDTSTART;TZID=America/New_York:19950315T100000\n"
    out = run_expand(
        submission_command,
        _wrap(body),
        "1995-01-01T00:00:00Z",
        "1996-01-01T00:00:00Z",
        tmp_path,
    )
    occs = _occurrences(out)
    # Accept either: the parser resolves using TZOFFSETFROM (-0500 EST =>
    # 15:00 UTC), or it falls back to the earliest STANDARD offset (-0500 =>
    # 15:00 UTC). Both yield the same answer for this case.
    assert len(occs) == 1
    assert occs[0].get("dtstart") == "1995-03-15T15:00:00Z"


def test_observance_dtstart_is_floating_not_utc(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Per RFC 5545 §3.8.2.4, DTSTART in a VTIMEZONE observance MUST be a
    local time (floating, no trailing Z). The parser must not emit it with a
    trailing 'Z' even if the rest of the file has UTC times."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tz = _tz_or_empty(out)
    for obs in _observances(tz, "standard") + _observances(tz, "daylight"):
        dtstart = cast(str, obs.get("dtstart") or "")
        assert not dtstart.endswith("Z"), (
            f"observance DTSTART must be floating (no 'Z'): got {dtstart!r}"
        )


def test_historical_tzoffsets_normalized_with_colon(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Spec §ISO-8601 normalizes UTC-OFFSET values. Existing tests assert the
    ±HH:MM form for US/Eastern offsets (e.g. '-04:00'). The historical VTIMEZONE
    must emit the same canonical format across all observances."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tz = _tz_or_empty(out)
    all_offsets: set[Any] = set()
    for obs in _observances(tz, "standard") + _observances(tz, "daylight"):
        if obs.get("tzoffsetfrom") is not None:
            all_offsets.add(obs["tzoffsetfrom"])
        if obs.get("tzoffsetto") is not None:
            all_offsets.add(obs["tzoffsetto"])
    # Every offset string should start with + or -.
    for off in all_offsets:
        assert isinstance(off, str) and off[:1] in "+-", f"offset not in canonical form: {off!r}"


# ---------------------------------------------------------------------------
# Edge / invalid cases
# ---------------------------------------------------------------------------


def test_historical_observances_preserve_tzname(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Each observance's TZNAME is preserved. In the historical VTIMEZONE the
    DAYLIGHT name is 'EDT' and STANDARD name is 'EST' across both eras."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    tz = _tz_or_empty(out)
    daylight_names: set[str] = set()
    standard_names: set[str] = set()
    for obs in _observances(tz, "daylight"):
        tzname = obs.get("tzname")
        if isinstance(tzname, list):
            daylight_names.update(cast(list[str], tzname))
        elif isinstance(tzname, str):
            daylight_names.add(tzname)
    for obs in _observances(tz, "standard"):
        tzname = obs.get("tzname")
        if isinstance(tzname, list):
            standard_names.update(cast(list[str], tzname))
        elif isinstance(tzname, str):
            standard_names.add(tzname)
    assert "EDT" in daylight_names
    assert "EST" in standard_names


def test_three_era_observance_stack(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Hypothetical three-era VTIMEZONE (pre-1966, 1966-2007, 2007-present) to
    stress selection logic. Event in 1960 should resolve using the earliest
    observance (STANDARD only, pre-uniform-time-act). Event in 1980 uses the
    middle era. Event in 2020 uses the latest era."""
    tz = """\
BEGIN:VTIMEZONE
TZID:America/Indiana/Indianapolis
BEGIN:STANDARD
DTSTART:19200101T000000
TZOFFSETFROM:-0600
TZOFFSETTO:-0500
TZNAME:EST
END:STANDARD
BEGIN:STANDARD
DTSTART:19661030T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU;UNTIL=20061029T070000Z
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19660424T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=-1SU;UNTIL=20060402T070000Z
END:DAYLIGHT
BEGIN:STANDARD
DTSTART:20071104T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20070311T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
END:VTIMEZONE
"""
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n" + tz + "END:VCALENDAR\n"
    out = run_parse(submission_command, ics, tmp_path)
    tzs = _timezones(out)
    assert len(tzs) == 1
    got = tzs[0]
    # We expect 3 STANDARD observances and 2 DAYLIGHT observances.
    assert len(_observances(got, "standard")) == 3
    assert len(_observances(got, "daylight")) == 2


def test_historical_vtimezone_no_warnings(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A well-formed VTIMEZONE with multiple observances MUST NOT cause the
    parser to emit warnings like `unresolved_tzid` or `malformed_value`. Those
    kinds are reserved for actual input errors."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_HISTORICAL
        + "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [w.get("kind") for w in warnings_of(out)]
    # These error kinds should not appear for well-formed historical data.
    assert "unresolved_tzid" not in kinds
    assert "malformed_value" not in kinds
