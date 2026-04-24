"""VTIMEZONE parsing and TZID resolution to UTC during expand. Spec §5."""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, run_parse, warnings_of

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


def test_vtimezone_parsed_into_timezones(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n" + US_EASTERN_TZ + "END:VCALENDAR\n"
    out = run_parse(submission_command, ics, tmp_path)
    tzs = out["timezones"]
    assert len(tzs) == 1
    tz = tzs[0]
    assert tz["tzid"] == "America/New_York"
    assert len(tz["standard"]) == 1
    assert len(tz["daylight"]) == 1


def test_vtimezone_observance_fields(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n" + US_EASTERN_TZ + "END:VCALENDAR\n"
    out = run_parse(submission_command, ics, tmp_path)
    std = out["timezones"][0]["standard"][0]
    assert std["tzoffsetfrom"] == "-04:00"
    assert std["tzoffsetto"] == "-05:00"
    assert std["tzname"] == "EST"
    assert std["rrule"] is not None
    assert std["rrule"]["freq"] == "YEARLY"


def test_tzid_resolves_to_utc_in_expand(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # 2026-07-15 is in DST (EDT, -0400). 10:00 local = 14:00 UTC.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n" + US_EASTERN_TZ + "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART;TZID=America/New_York:20260715T100000\n"
        "SUMMARY:summer meeting\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", tmp_path
    )
    assert len(out["occurrences"]) == 1
    occ = out["occurrences"][0]
    assert occ["dtstart"] == "2026-07-15T14:00:00Z"
    assert occ["tz"] == "America/New_York"


def test_tzid_resolves_in_standard_time(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # 2026-01-15 is in EST (-0500). 10:00 local = 15:00 UTC.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n" + US_EASTERN_TZ + "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART;TZID=America/New_York:20260115T100000\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z", tmp_path
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-01-15T15:00:00Z"


def test_unresolved_tzid_warning(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # No VTIMEZONE provided for referenced TZID -> warning + treat as floating.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART;TZID=Mars/Tharsis:20260305T100000\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-01-01T00:00:00Z", "2026-12-01T00:00:00Z", tmp_path
    )
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "unresolved_tzid" in kinds
