"""RFC 5545 §3.6.4 / §3.8.2.6 VFREEBUSY semantics.

VFREEBUSY is a top-level component carrying FREEBUSY properties: each
FREEBUSY property is a list of PERIOD values with an optional FBTYPE
parameter (default BUSY).

The v1.0 reference implementation surfaced VFREEBUSY as a generic
VEvent with no dedicated FREEBUSY handling. This file pins the proper
shape: each VFREEBUSY in the parse output carries `freebusy: [{fbtype,
periods}, ...]`.

Codex v1.0 adversarial-review finding #1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_parse

HEADER = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
FOOTER = "END:VCALENDAR\n"


def _wrap_fb(body: str) -> str:
    return HEADER + "BEGIN:VFREEBUSY\n" + body + "END:VFREEBUSY\n" + FOOTER


def _freebusy_list(out: dict[str, Any]) -> list[dict[str, Any]]:
    raw = out.get("freebusy")
    assert isinstance(raw, list), f"parse output missing 'freebusy' array: {list(out)}"
    return cast(list[dict[str, Any]], raw)


def _entries(fb: dict[str, Any]) -> list[dict[str, Any]]:
    raw = fb.get("freebusy")
    assert isinstance(raw, list), f"VFREEBUSY object missing 'freebusy' entry list: {list(fb)}"
    return cast(list[dict[str, Any]], raw)


# ---------------------------------------------------------------------------
# Basic shape
# ---------------------------------------------------------------------------


def test_vfreebusy_with_one_freebusy_property(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.4: a VFREEBUSY with one FREEBUSY property (one period)."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260301T235959Z\n"
        "FREEBUSY:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    assert len(fbs) == 1
    entries = _entries(fbs[0])
    assert len(entries) == 1
    periods = entries[0].get("periods")
    assert isinstance(periods, list) and len(cast(list[Any], periods)) == 1


def test_vfreebusy_default_fbtype_is_busy(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.9: default FBTYPE is BUSY when not specified."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert entries[0].get("fbtype") == "BUSY"


def test_vfreebusy_fbtype_free(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY;FBTYPE=FREE:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert entries[0].get("fbtype") == "FREE"


def test_vfreebusy_fbtype_busy_unavailable(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY;FBTYPE=BUSY-UNAVAILABLE:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert entries[0].get("fbtype") == "BUSY-UNAVAILABLE"


def test_vfreebusy_fbtype_busy_tentative(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY;FBTYPE=BUSY-TENTATIVE:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert entries[0].get("fbtype") == "BUSY-TENTATIVE"


# ---------------------------------------------------------------------------
# Multiple FREEBUSY properties
# ---------------------------------------------------------------------------


def test_vfreebusy_multiple_freebusy_properties_accumulate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two FREEBUSY lines → two entries in `freebusy`."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY;FBTYPE=BUSY:20260301T090000Z/20260301T100000Z\n"
        "FREEBUSY;FBTYPE=FREE:20260301T100000Z/20260301T110000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert len(entries) == 2
    fbtypes = [e.get("fbtype") for e in entries]
    assert "BUSY" in fbtypes and "FREE" in fbtypes


# ---------------------------------------------------------------------------
# Multiple periods in one FREEBUSY property
# ---------------------------------------------------------------------------


def test_vfreebusy_comma_separated_periods(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A single FREEBUSY value may carry multiple comma-separated periods."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY:20260301T090000Z/20260301T100000Z,"
        "20260301T140000Z/20260301T150000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert len(entries) == 1
    periods = entries[0].get("periods")
    assert isinstance(periods, list) and len(cast(list[Any], periods)) == 2


# ---------------------------------------------------------------------------
# PERIOD value types: start/end and start/duration
# ---------------------------------------------------------------------------


def test_vfreebusy_period_with_explicit_end(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    periods = cast(list[dict[str, Any]], _entries(fbs[0])[0].get("periods"))
    per = periods[0]
    # Explicit end present.
    assert "end" in per and per["end"]


def test_vfreebusy_period_with_duration(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY:20260301T090000Z/PT1H\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    periods = cast(list[dict[str, Any]], _entries(fbs[0])[0].get("periods"))
    per = periods[0]
    # Duration form.
    assert "duration" in per and per["duration"]


# ---------------------------------------------------------------------------
# VFREEBUSY common fields
# ---------------------------------------------------------------------------


def test_vfreebusy_reports_uid_and_dtstart(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """VFREEBUSY carries UID / DTSTAMP / DTSTART / DTEND like events."""
    body = (
        "UID:fb-report\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260301T235959Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    assert fbs[0].get("uid") == "fb-report"
    assert fbs[0].get("dtstart")
    assert fbs[0].get("dtend")


def test_vfreebusy_organizer_is_cal_address(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """ORGANIZER on VFREEBUSY uses the same cal-address grammar."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER;CN=Alice:mailto:alice@example.com\n"
        "FREEBUSY:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    org = fbs[0].get("organizer")
    assert org is not None
    assert org.get("cn") == "Alice"


def test_vfreebusy_attendees_accumulate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "ATTENDEE:mailto:a@example.com\n"
        "ATTENDEE:mailto:b@example.com\n"
        "FREEBUSY:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    attendees = fbs[0].get("attendees")
    assert isinstance(attendees, list)
    assert len(cast(list[Any], attendees)) == 2


# ---------------------------------------------------------------------------
# FBTYPE x-name preservation
# ---------------------------------------------------------------------------


def test_vfreebusy_xname_fbtype_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """x-name FBTYPE values are preserved verbatim."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "FREEBUSY;FBTYPE=X-HOLIDAY:20260301T090000Z/20260301T100000Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert entries[0].get("fbtype") == "X-HOLIDAY"


# ---------------------------------------------------------------------------
# Empty VFREEBUSY
# ---------------------------------------------------------------------------


def test_vfreebusy_without_freebusy_property(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A VFREEBUSY with no FREEBUSY properties has an empty entries list."""
    body = (
        "UID:fb1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260301T235959Z\n"
    )
    out = run_parse(submission_command, _wrap_fb(body), tmp_path)
    fbs = _freebusy_list(out)
    entries = _entries(fbs[0])
    assert entries == []
