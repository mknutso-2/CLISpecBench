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
    assert isinstance(raw, list), (
        f"parse output missing 'availabilities' array: {list(out)}"
    )
    return cast(list[dict[str, Any]], raw)


# ---------------------------------------------------------------------------
# Basic VAVAILABILITY parsing
# ---------------------------------------------------------------------------


def test_vavailability_with_uid_and_dtstamp(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\nDTEND:20261231T235959Z\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert len(vas) == 1
    assert vas[0].get("uid") == "av1"
    assert vas[0].get("dtstart")
    assert vas[0].get("dtend")


def test_vavailability_busytype_busy(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BUSYTYPE:BUSY\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("busytype") == "BUSY"


def test_vavailability_busytype_busy_unavailable(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "BUSYTYPE:BUSY-UNAVAILABLE\n"
    )
    out = run_parse(submission_command, _wrap_va(body), tmp_path)
    vas = _availabilities(out)
    assert vas[0].get("busytype") == "BUSY-UNAVAILABLE"


def test_vavailability_priority(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
        "PRIORITY:5\n"
    )
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


def test_available_with_rrule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
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
    assert rrule.get("freq") == "WEEKLY"


# ---------------------------------------------------------------------------
# Organizer + description on VAVAILABILITY
# ---------------------------------------------------------------------------


def test_vavailability_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
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


def test_empty_vavailability_parses(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A VAVAILABILITY with just UID/DTSTAMP/DTSTART parses; available[] empty."""
    body = (
        "UID:av1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T000000Z\n"
    )
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
