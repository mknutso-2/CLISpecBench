"""VTIMEZONE resolution depth.

Closes Codex v1.0 adversarial-review finding #5. The ref impl's
observance resolver only stepped simple RRULEs, used first-BYMONTH
+ ordinal-BYDAY, ignored observance UNTIL, and didn't enumerate
observance RDATEs. This file pins:

  * UNTIL bounds an observance — events after UNTIL use the next
    observance in the history.
  * RDATE in an observance adds extra transition instants.
  * Southern-hemisphere DST (Australia) works with month-order
    reversed.
  * No-DST zone (UTC, Arizona) resolves without a DAYLIGHT component.
  * Observance without RRULE uses DTSTART literally as the single
    transition point.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, starts_for, wrap_event

HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
TAIL = "END:VCALENDAR\n"


def _wrap_with_tz(tz_body: str, event_body: str) -> str:
    return (
        HEAD
        + "BEGIN:VTIMEZONE\n" + tz_body + "END:VTIMEZONE\n"
        + "BEGIN:VEVENT\n" + event_body + "END:VEVENT\n"
        + TAIL
    )


# ---------------------------------------------------------------------------
# No-DST zone
# ---------------------------------------------------------------------------


def test_utc_zone_resolves_without_daylight(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A VTIMEZONE with only STANDARD (no DST) still resolves."""
    tz = (
        "TZID:Etc/UTC\n"
        "BEGIN:STANDARD\n"
        "DTSTART:19700101T000000\n"
        "TZOFFSETFROM:+0000\nTZOFFSETTO:+0000\n"
        "END:STANDARD\n"
    )
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Etc/UTC:20260601T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # UTC offset 0 means local = UTC.
    assert starts == ["2026-06-01T12:00:00Z"]


def test_arizona_no_daylight_zone(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Arizona stays at MST year-round (no DAYLIGHT observance)."""
    tz = (
        "TZID:America/Phoenix\n"
        "BEGIN:STANDARD\n"
        "DTSTART:19700101T000000\n"
        "TZOFFSETFROM:-0700\nTZOFFSETTO:-0700\n"
        "END:STANDARD\n"
    )
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/Phoenix:20260615T090000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-06-01T00:00:00Z",
        "2026-07-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 09:00 MST (-0700) = 16:00 UTC.
    assert starts == ["2026-06-15T16:00:00Z"]


# ---------------------------------------------------------------------------
# Southern-hemisphere DST (Australia)
# ---------------------------------------------------------------------------


def test_sydney_dst_month_order(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Sydney DST: October → April (reversed from northern hemisphere)."""
    tz = (
        "TZID:Australia/Sydney\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20080406T030000\n"
        "TZOFFSETFROM:+1100\nTZOFFSETTO:+1000\n"
        "RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=1SU\n"
        "END:STANDARD\n"
        "BEGIN:DAYLIGHT\n"
        "DTSTART:20081005T020000\n"
        "TZOFFSETFROM:+1000\nTZOFFSETTO:+1100\n"
        "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=1SU\n"
        "END:DAYLIGHT\n"
    )
    # Pick January 15, 2026 — firmly in Sydney summer (DST = AEDT +1100).
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Australia/Sydney:20260115T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-01-01T00:00:00Z",
        "2026-02-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 12:00 AEDT (+1100) = 01:00 UTC.
    assert starts == ["2026-01-15T01:00:00Z"]


# ---------------------------------------------------------------------------
# Observance with no RRULE (single-point DTSTART only)
# ---------------------------------------------------------------------------


def test_observance_without_rrule_uses_dtstart_literally(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An observance with DTSTART but no RRULE applies from DTSTART forever."""
    tz = (
        "TZID:Test/Static\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20200101T000000\n"
        "TZOFFSETFROM:+0000\nTZOFFSETTO:+0300\n"
        "END:STANDARD\n"
    )
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Test/Static:20260601T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 12:00 local at +0300 → 09:00 UTC.
    assert starts == ["2026-06-01T09:00:00Z"]


# ---------------------------------------------------------------------------
# Observance RDATE enumeration
# ---------------------------------------------------------------------------


def test_observance_rdate_adds_transition(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RDATE inside an observance adds extra transition instants."""
    tz = (
        "TZID:Test/RDate\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20200101T000000\n"
        "TZOFFSETFROM:+0100\nTZOFFSETTO:+0000\n"
        "RDATE:20250701T000000,20260701T000000\n"
        "END:STANDARD\n"
        "BEGIN:DAYLIGHT\n"
        "DTSTART:20250101T000000\n"
        "TZOFFSETFROM:+0000\nTZOFFSETTO:+0100\n"
        "RDATE:20260101T000000\n"
        "END:DAYLIGHT\n"
    )
    # Pick Aug 1, 2026 — after the July 1 2026 RDATE transition to +0000.
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Test/RDate:20260801T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-08-01T00:00:00Z",
        "2026-09-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # At +0000, 12:00 local = 12:00 UTC.
    assert starts == ["2026-08-01T12:00:00Z"]


# ---------------------------------------------------------------------------
# Observance UNTIL honored
# ---------------------------------------------------------------------------


def test_observance_until_bounds_rrule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An observance RRULE UNTIL bounds when the observance's transitions
    apply. After UNTIL, a later observance's rules take over.

    Setup: pre-2020 rule stops via UNTIL=20200101T000000. Post-2020 rule
    has a different offset. An event in 2026 must use the post-2020 rule.
    """
    tz = (
        "TZID:Test/History\n"
        # Old rule: +0200 year-round, ends Jan 2020.
        "BEGIN:STANDARD\n"
        "DTSTART:20100101T000000\n"
        "TZOFFSETFROM:+0200\nTZOFFSETTO:+0200\n"
        "RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1;UNTIL=20200101T000000\n"
        "END:STANDARD\n"
        # New rule: +0300 starting 2020.
        "BEGIN:STANDARD\n"
        "DTSTART:20200101T000000\n"
        "TZOFFSETFROM:+0200\nTZOFFSETTO:+0300\n"
        "RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1\n"
        "END:STANDARD\n"
    )
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Test/History:20260601T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 12:00 at +0300 = 09:00 UTC.
    assert starts == ["2026-06-01T09:00:00Z"]


# ---------------------------------------------------------------------------
# BYMONTHDAY instead of ordinal BYDAY
# ---------------------------------------------------------------------------


def test_observance_bymonthday(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An observance can use BYMONTHDAY (e.g. always the 1st) instead of BYDAY."""
    tz = (
        "TZID:Test/FirstOfMonth\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20200401T000000\n"
        "TZOFFSETFROM:+0400\nTZOFFSETTO:+0300\n"
        "RRULE:FREQ=YEARLY;BYMONTH=4;BYMONTHDAY=1\n"
        "END:STANDARD\n"
        "BEGIN:DAYLIGHT\n"
        "DTSTART:20201001T000000\n"
        "TZOFFSETFROM:+0300\nTZOFFSETTO:+0400\n"
        "RRULE:FREQ=YEARLY;BYMONTH=10;BYMONTHDAY=1\n"
        "END:DAYLIGHT\n"
    )
    # June 2026: should be in STANDARD (+0300).
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Test/FirstOfMonth:20260615T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 12:00 at +0300 = 09:00 UTC.
    assert starts == ["2026-06-15T09:00:00Z"]


# ---------------------------------------------------------------------------
# Yearly + BYMONTHDAY: the anniversary-of-transition shape
# ---------------------------------------------------------------------------


def test_observance_yearly_bymonthday_transition(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An observance that fires once per year on the 15th of the configured
    month (FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=15) resolves correctly for a
    mid-year event several years past DTSTART. The resolver must apply
    the single-offset rule literally without confusing year anchoring."""
    tz = (
        "TZID:Test/Anniversary\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20200115T000000\n"
        "TZOFFSETFROM:+0100\nTZOFFSETTO:+0100\n"
        "RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=15\n"
        "END:STANDARD\n"
    )
    ev = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Test/Anniversary:20260601T120000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_with_tz(tz, ev),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # Single-offset +0100 zone: 12:00 local = 11:00 UTC.
    assert starts == ["2026-06-01T11:00:00Z"]


# ---------------------------------------------------------------------------
# Unknown TZID gracefully emits unresolved_tzid warning
# ---------------------------------------------------------------------------


def test_unknown_tzid_emits_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Fictional/Nowhere:20260601T120000\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    kinds = [w.get("kind") for w in out.get("warnings", []) or []]
    assert "unresolved_tzid" in kinds
