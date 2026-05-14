"""RFC 7953 — VAVAILABILITY component tests.

VAVAILABILITY is a top-level component used to publish recurring
availability windows (when a user or resource is busy/free for
scheduling). It contains AVAILABLE sub-components describing free
blocks, with an overall BUSYTYPE default for the containing
interval.

References:
  * RFC 7953 §3.1 — VAVAILABILITY top-level component.
  * RFC 7953 §3.2 — AVAILABLE sub-component.
  * RFC 7953 §7.1 — BUSYTYPE values: BUSY | BUSY-UNAVAILABLE |
    BUSY-TENTATIVE.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_parse

HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
TAIL = "END:VCALENDAR\n"


def _wrap_va(body: str) -> str:
    return HEAD + "BEGIN:VAVAILABILITY\n" + body + "END:VAVAILABILITY\n" + TAIL


def _availabilities(out: dict[str, Any]) -> list[dict[str, Any]]:
    raw = out.get("availabilities")
    assert isinstance(raw, list), f"parse output missing 'availabilities' array: {list(out)}"
    return cast(list[dict[str, Any]], raw)


# ---------------------------------------------------------------------------
# Basic VAVAILABILITY parsing
# ---------------------------------------------------------------------------


def test_vavailability_with_uid_and_dtstamp(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = "UID:av1\nDTSTAMP:20260101T120000Z\nDTSTART:20260101T000000Z\nDTEND:20261231T235959Z\n"
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert len(vas) == 1
    assert vas[0].get("uid") == "av1"
    assert vas[0].get("dtstart")
    assert vas[0].get("dtend")


def test_vavailability_busytype_busy(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "UID:av1\nDTSTAMP:20260101T120000Z\nDTSTART:20260101T000000Z\nBUSYTYPE:BUSY\n"
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("busytype") == "BUSY"


def test_vavailability_busytype_absent_emits_null(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """tech-reqs VAVAILABILITY schema §: when BUSYTYPE is absent on
    the VAVAILABILITY component, `busytype` is emitted as null
    (NOT materialized as "BUSY-UNAVAILABLE" — contrast VFREEBUSY's
    fbtype field which does materialize its default). This
    distinguishes the two availability surfaces."""
    body = (
        "UID:va1\nDTSTAMP:20260101T120000Z\nDTSTART:20260101T000000Z\nDTEND:20260201T000000Z\n"
        # deliberately no BUSYTYPE line
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("busytype") is None


def test_vavailability_busytype_busy_unavailable(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\nDTSTART:20260101T000000Z\nBUSYTYPE:BUSY-UNAVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("busytype") == "BUSY-UNAVAILABLE"


def test_vavailability_priority(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "UID:av1\nDTSTAMP:20260101T120000Z\nDTSTART:20260101T000000Z\nPRIORITY:5\n"
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("priority") == 5


# ---------------------------------------------------------------------------
# AVAILABLE sub-component
# ---------------------------------------------------------------------------


def test_vavailability_with_one_available(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:av1-av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "SUMMARY:Available 9-5 weekdays\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av_list = cast(list[dict[str, Any]], vas[0].get("available") or [])
    assert len(av_list) == 1
    av = av_list[0]
    assert av.get("uid") == "av1-av1"
    assert av.get("summary") == "Available 9-5 weekdays"


def test_vavailability_multiple_available(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\nUID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T120000Z\nEND:AVAILABLE\n"
        "BEGIN:AVAILABLE\nUID:a2\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T130000Z\nDTEND:20260601T170000Z\nEND:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av_list = cast(list[dict[str, Any]], vas[0].get("available") or [])
    assert len(av_list) == 2
    uids = {av.get("uid") for av in av_list}
    assert uids == {"a1", "a2"}


def test_available_with_rrule(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """AVAILABLE can carry its own RRULE for recurring availability."""
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:weekly-office-hours\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av_list = cast(list[dict[str, Any]], vas[0].get("available") or [])
    assert len(av_list) == 1
    rrule = av_list[0].get("rrule")
    assert isinstance(rrule, dict)
    rrule = cast(dict[str, Any], rrule)
    assert rrule.get("freq") == "WEEKLY"


# ---------------------------------------------------------------------------
# Organizer + description on VAVAILABILITY
# ---------------------------------------------------------------------------


def test_vavailability_organizer(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER;CN=Alice:mailto:alice@example.com\n"
        "DTSTART:20260101T000000Z\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    org = vas[0].get("organizer")
    assert org is not None
    assert org.get("cn") == "Alice"


def test_vavailability_description_unescaped(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "DESCRIPTION:Office hours\\, Mon-Fri 9-5\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert "Office hours, Mon-Fri 9-5" in cast(str, vas[0].get("description"))


# ---------------------------------------------------------------------------
# Empty VAVAILABILITY (just an envelope)
# ---------------------------------------------------------------------------


def test_empty_vavailability_parses(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """A VAVAILABILITY with just UID/DTSTAMP/DTSTART parses; available[] empty."""
    body = "UID:av1\nDTSTAMP:20260101T120000Z\nDTSTART:20260101T000000Z\n"
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("available") == []


# ---------------------------------------------------------------------------
# Multiple VAVAILABILITY components in one calendar
# ---------------------------------------------------------------------------


def test_multiple_vavailability_components(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "BEGIN:VAVAILABILITY\nUID:v1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\nEND:VAVAILABILITY\n"
        "BEGIN:VAVAILABILITY\nUID:v2\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T000000Z\nEND:VAVAILABILITY\n"
    )
    out = run_parse(submission_command, HEAD + body + TAIL, tmp_path)
    vas = _availabilities(out)
    assert len(vas) == 2
    uids = {va.get("uid") for va in vas}
    assert uids == {"v1", "v2"}


# ---------------------------------------------------------------------------
# Parse output always includes availabilities key
# ---------------------------------------------------------------------------


def test_availabilities_key_present_when_empty(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A calendar without any VAVAILABILITY still has the key as []."""
    out = run_parse(submission_command, HEAD + TAIL, tmp_path)
    availabilities = out.get("availabilities")
    assert availabilities == []


# ---------------------------------------------------------------------------
# AVAILABLE extended fields (RFC 7953 §3.2)
# ---------------------------------------------------------------------------


def test_available_with_location_and_contact(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "LOCATION:My Office\n"
        "CONTACT:Jane Doe\\, jane@example.com\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av = cast(list[dict[str, Any]], vas[0].get("available"))[0]
    assert av.get("location") == "My Office"
    assert "Jane Doe" in cast(str, av.get("contact"))


def test_available_with_created_and_last_modified(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Pin the full ISO-8601 form of CREATED / LAST-MODIFIED so that
    a date-only fragment match can't hide a broken time component or
    an incorrect UTC `Z` suffix. These are UTC-only properties per
    RFC 5545 §3.8.7.1 and §3.8.7.3."""
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "CREATED:20260101T080000Z\n"
        "LAST-MODIFIED:20260501T090000Z\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av = cast(list[dict[str, Any]], vas[0].get("available"))[0]
    # Pin the whole ISO-8601 value, not a substring. Format is
    # "YYYY-MM-DDTHH:MM:SSZ" — trailing Z required because RFC 5545
    # §3.8.7 forces UTC for both fields.
    assert av.get("created") == "2026-01-01T08:00:00Z"
    assert av.get("last_modified") == "2026-05-01T09:00:00Z"


def test_available_with_recurrence_id(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7953 §3.2: RECURRENCE-ID is allowed on AVAILABLE to override a
    specific instance of a recurring availability block. The JSON shape
    MUST match VEvent's recurrence_id object ({value, range, tzid}) so
    both recurrence surfaces carry identical parameter fidelity — a
    scalar string here would silently drop TZID/RANGE if they were
    present on other fixtures."""
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "RECURRENCE-ID:20260601T090000Z\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av = cast(list[dict[str, Any]], vas[0].get("available"))[0]
    rid = av.get("recurrence_id")
    assert isinstance(rid, dict), f"expected object, got {rid!r}"
    rid = cast(dict[str, Any], rid)
    # Pin the exact ISO-8601 value, not a date-fragment substring. A
    # substring match could hide a broken time component or lost
    # `Z` suffix.
    assert rid.get("value") == "2026-06-01T09:00:00Z"
    # Neither RANGE nor TZID is set in this fixture — both explicit null.
    assert rid.get("range") is None
    assert rid.get("tzid") is None


def test_available_recurrence_id_with_tzid_and_range(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.8.4.4 lets RECURRENCE-ID carry both a TZID= parameter
    and RANGE=THISANDFUTURE/THISANDPRIOR. The Available schema must
    preserve both parameters (the structured object shape); a scalar
    ISO string would silently drop them."""
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:VTIMEZONE\nTZID:America/New_York\n"
        "BEGIN:STANDARD\nDTSTART:20071104T020000\n"
        "TZOFFSETFROM:-0400\nTZOFFSETTO:-0500\n"
        "END:STANDARD\nEND:VTIMEZONE\n"
        "BEGIN:AVAILABLE\n"
        "UID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20260601T090000\n"
        "DTEND;TZID=America/New_York:20260601T170000\n"
        "RECURRENCE-ID;TZID=America/New_York;RANGE=THISANDFUTURE:20260601T090000\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av = cast(list[dict[str, Any]], vas[0].get("available"))[0]
    rid = av.get("recurrence_id")
    assert isinstance(rid, dict)
    rid = cast(dict[str, Any], rid)
    # Pin value along with the params so a silent loss of the time-
    # component can't pass.
    assert rid.get("value") == "2026-06-01T09:00:00"
    assert rid.get("tzid") == "America/New_York"
    assert rid.get("range") == "THISANDFUTURE"


def test_available_with_categories_and_comment(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "CATEGORIES:OFFICE-HOURS,CONSULTATION\n"
        "COMMENT:In-person only\n"
        "COMMENT:Bring your laptop\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av = cast(list[dict[str, Any]], vas[0].get("available"))[0]
    cats = cast(list[Any], av.get("categories") or [])
    assert "OFFICE-HOURS" in cats
    assert "CONSULTATION" in cats
    comments = cast(list[Any], av.get("comment") or [])
    assert len(comments) == 2


def test_available_with_exdate(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BEGIN:AVAILABLE\n"
        "UID:a1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T090000Z\nDTEND:20260601T170000Z\n"
        "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR\n"
        "EXDATE:20260703T090000Z\n"
        "END:AVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    av = cast(list[dict[str, Any]], vas[0].get("available"))[0]
    exdate = cast(list[Any], av.get("exdate") or [])
    assert len(exdate) == 1
