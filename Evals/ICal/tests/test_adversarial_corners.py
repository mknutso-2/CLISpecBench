"""Adversarial corners of RFC 5545 — the parts where mainstream libraries
have filed bugs and where the eval earns its discrimination signal:

  - VTIMEZONE DST boundary crossings (spring-forward gap, fall-back overlap)
  - Sub-day FREQ with INTERVAL crossings of day / month / year boundaries
  - BYHOUR / BYMINUTE / BYSECOND interacting with non-DAILY frequencies
  - RECURRENCE-ID with RANGE=THISANDFUTURE
  - EXRULE with non-trivial BY* combinations
  - BYYEARDAY expansion in YEARLY
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, starts_for, wrap_event

# ---------------------------------------------------------------------------
# VTIMEZONE fixtures
# ---------------------------------------------------------------------------

US_EASTERN_TZ = """\
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:20061105T020000
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

EUROPE_LONDON_TZ = """\
BEGIN:VTIMEZONE
TZID:Europe/London
BEGIN:STANDARD
DTSTART:19961027T020000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
TZNAME:GMT
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19960331T010000
TZOFFSETFROM:+0000
TZOFFSETTO:+0100
TZNAME:BST
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
END:VTIMEZONE
"""


def _wrap(tz: str, body: str) -> str:
    return (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + tz
        + "BEGIN:VEVENT\n"
        + body
        + "END:VEVENT\n"
        + "END:VCALENDAR\n"
    )


# ---------------------------------------------------------------------------
# VTIMEZONE DST-boundary crossings
# ---------------------------------------------------------------------------


def test_dst_spring_forward_day_3am(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # 2026-03-08 is the 2nd Sunday of March → DST transition day (EST → EDT).
    # Transition happens at local 02:00 → 03:00. An event at 03:00 on this day
    # falls AFTER the transition, so it's EDT (-0400). 03:00 EDT = 07:00 UTC.
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=America/New_York:20260308T030000\n"
    out = run_expand(
        submission_command,
        _wrap(US_EASTERN_TZ, body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-03-08T07:00:00Z"


def test_dst_spring_forward_day_1am_before_transition(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # 2026-03-08 01:00 local is BEFORE the 02:00 transition, so EST (-0500).
    # 01:00 EST = 06:00 UTC.
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=America/New_York:20260308T010000\n"
    out = run_expand(
        submission_command,
        _wrap(US_EASTERN_TZ, body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-03-08T06:00:00Z"


def test_dst_fall_back_day_after_transition(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # 2026-11-01 is the 1st Sunday of November → DST end day (EDT → EST).
    # Transition at local 02:00 → 01:00. An event at 03:00 is in EST (-0500).
    # 03:00 EST = 08:00 UTC.
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=America/New_York:20261101T030000\n"
    out = run_expand(
        submission_command,
        _wrap(US_EASTERN_TZ, body),
        "2026-10-01T00:00:00Z",
        "2026-12-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-11-01T08:00:00Z"


def test_dst_recurring_event_crosses_spring_forward(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Weekly Thursday meeting at 10:00 local, starting 2026-03-05 (pre-DST).
    # Before transition: EST (-0500), 10:00 = 15:00 UTC.
    # After transition: EDT (-0400), 10:00 = 14:00 UTC.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20260305T100000\n"
        "RRULE:FREQ=WEEKLY;BYDAY=TH;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        _wrap(US_EASTERN_TZ, body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T15:00:00Z",  # EST, pre-DST
        "2026-03-12T14:00:00Z",  # EDT, post-DST
        "2026-03-19T14:00:00Z",  # EDT
    ]


def test_london_timezone_gmt_vs_bst(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Non-US timezone to exercise another observance pair.
    # July 15 is BST (+0100). 10:00 local = 09:00 UTC.
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=Europe/London:20260715T100000\n"
    out = run_expand(
        submission_command,
        _wrap(EUROPE_LONDON_TZ, body),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-07-15T09:00:00Z"


def test_london_winter_gmt(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # December is GMT (+0000). 10:00 local = 10:00 UTC.
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=Europe/London:20261215T100000\n"
    out = run_expand(
        submission_command,
        _wrap(EUROPE_LONDON_TZ, body),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-12-15T10:00:00Z"


def test_multi_year_tz_resolution(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Resolve a date several years after the VTIMEZONE's DTSTART anchors.
    # 2030-07-15 should still resolve (EDT).
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=America/New_York:20300715T120000\n"
    out = run_expand(
        submission_command,
        _wrap(US_EASTERN_TZ, body),
        "2030-01-01T00:00:00Z",
        "2031-01-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    # 12:00 EDT = 16:00 UTC.
    assert out["occurrences"][0]["dtstart"] == "2030-07-15T16:00:00Z"


# ---------------------------------------------------------------------------
# Sub-day FREQ with boundary crossings
# ---------------------------------------------------------------------------


def test_hourly_crosses_midnight(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260305T230000Z\nRRULE:FREQ=HOURLY;COUNT=3\n"
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-05T00:00:00Z",
        "2026-03-07T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T23:00:00Z",
        "2026-03-06T00:00:00Z",
        "2026-03-06T01:00:00Z",
    ]


def test_minutely_crosses_hour(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260305T095500Z\n"
        "RRULE:FREQ=MINUTELY;INTERVAL=5;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-05T00:00:00Z",
        "2026-03-06T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T09:55:00Z",
        "2026-03-05T10:00:00Z",
        "2026-03-05T10:05:00Z",
    ]


def test_hourly_crosses_month(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260331T230000Z\n"
        "RRULE:FREQ=HOURLY;INTERVAL=2;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-05-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-31T23:00:00Z",
        "2026-04-01T01:00:00Z",
        "2026-04-01T03:00:00Z",
    ]


# ---------------------------------------------------------------------------
# BYHOUR / BYMINUTE interacting with non-DAILY frequencies
# ---------------------------------------------------------------------------


def test_weekly_with_byhour(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Every Thursday at 09:00 and 17:00 UTC.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260305T090000Z\n"
        "RRULE:FREQ=WEEKLY;BYDAY=TH;BYHOUR=9,17;COUNT=4\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T09:00:00Z",
        "2026-03-05T17:00:00Z",
        "2026-03-12T09:00:00Z",
        "2026-03-12T17:00:00Z",
    ]


def test_monthly_byday_ordinal_plus_byhour(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # First Monday of each month at 09:00 and 13:00.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T090000Z\n"
        "RRULE:FREQ=MONTHLY;BYDAY=1MO;BYHOUR=9,13;COUNT=4\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-07-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # March 2, 2026 is a Mon. April 6. May 4.
    assert starts == [
        "2026-03-02T09:00:00Z",
        "2026-03-02T13:00:00Z",
        "2026-04-06T09:00:00Z",
        "2026-04-06T13:00:00Z",
    ]


def test_yearly_bymonth_bymonthday_byhour(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # July 4th at noon each year, 3 years.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260704T120000Z\n"
        "RRULE:FREQ=YEARLY;BYMONTH=7;BYMONTHDAY=4;BYHOUR=12;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-01-01T00:00:00Z",
        "2030-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-07-04T12:00:00Z",
        "2027-07-04T12:00:00Z",
        "2028-07-04T12:00:00Z",
    ]


# ---------------------------------------------------------------------------
# RECURRENCE-ID RANGE=THISANDFUTURE
# ---------------------------------------------------------------------------


def test_range_thisandfuture_replaces_future(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Daily at 10:00, COUNT=5. On 2026-03-07, apply THISANDFUTURE to move to 15:00.
    # Expected: 3/5 10:00, 3/6 10:00, 3/7 15:00, 3/8 15:00, 3/9 15:00.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=5\nEND:VEVENT\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260307T100000Z\n"
        "DTSTART:20260307T150000Z\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command,
        ics,
        "2026-03-01T00:00:00Z",
        "2026-03-15T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert "2026-03-05T10:00:00Z" in starts
    assert "2026-03-06T10:00:00Z" in starts
    # From 3/7 onwards, everything should be at 15:00, not 10:00.
    assert "2026-03-07T10:00:00Z" not in starts
    assert "2026-03-07T15:00:00Z" in starts
    assert "2026-03-08T10:00:00Z" not in starts
    assert "2026-03-08T15:00:00Z" in starts
    assert "2026-03-09T10:00:00Z" not in starts
    assert "2026-03-09T15:00:00Z" in starts


# ---------------------------------------------------------------------------
# EXRULE non-trivial
# ---------------------------------------------------------------------------


def test_exrule_monthly_second_friday(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Weekly meeting every Friday, but exclude the second Friday of each month.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260306T100000Z\n"
        "RRULE:FREQ=WEEKLY;BYDAY=FR;COUNT=10\n"
        "EXRULE:FREQ=MONTHLY;BYDAY=2FR\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-06-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # March 2026: Fridays are 6, 13, 20, 27. Second Friday is 13.
    # April 2026: Fridays are 3, 10, 17, 24. Second Friday is 10.
    # May 2026: Fridays are 1, 8, 15, 22, 29. Second Friday is 8.
    assert "2026-03-13T10:00:00Z" not in starts
    assert "2026-04-10T10:00:00Z" not in starts
    assert "2026-05-08T10:00:00Z" not in starts
    # Other Fridays present.
    assert "2026-03-06T10:00:00Z" in starts
    assert "2026-03-20T10:00:00Z" in starts


def test_exrule_combined_with_exdate(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Daily for 7 days, EXRULE excludes weekends, EXDATE additionally excludes 2026-03-04.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T100000Z\n"  # Mon 3/2
        "RRULE:FREQ=DAILY;COUNT=7\n"
        "EXRULE:FREQ=WEEKLY;BYDAY=SA,SU\n"
        "EXDATE:20260304T100000Z\n"  # Wed 3/4
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-03-10T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 3/2 Mon, 3/3 Tue kept; 3/4 Wed excluded by EXDATE; 3/5 Thu, 3/6 Fri kept;
    # 3/7 Sat, 3/8 Sun excluded by EXRULE.
    assert starts == [
        "2026-03-02T10:00:00Z",
        "2026-03-03T10:00:00Z",
        "2026-03-05T10:00:00Z",
        "2026-03-06T10:00:00Z",
    ]


# ---------------------------------------------------------------------------
# BYYEARDAY
# ---------------------------------------------------------------------------


def test_yearly_byyearday_specific_day(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Day 100 of each year.
    # 2026-04-10 is the 100th day of 2026 (non-leap).
    # 2027-04-10, 2028-04-09 (leap year has Feb 29, so day 100 = Apr 9).
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260410T120000Z\n"
        "RRULE:FREQ=YEARLY;BYYEARDAY=100;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-01-01T00:00:00Z",
        "2030-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-04-10T12:00:00Z",
        "2027-04-10T12:00:00Z",
        "2028-04-09T12:00:00Z",
    ]


def test_yearly_byyearday_negative(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Last day of each year (BYYEARDAY=-1 = Dec 31).
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20261231T120000Z\n"
        "RRULE:FREQ=YEARLY;BYYEARDAY=-1;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-01-01T00:00:00Z",
        "2030-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-12-31T12:00:00Z",
        "2027-12-31T12:00:00Z",
        "2028-12-31T12:00:00Z",
    ]
