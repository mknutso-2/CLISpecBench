"""RFC 5546 iTIP per-method matrices — depth beyond test_itip_methods.py.

Closes Codex v1.0 adversarial-review finding #4. `test_itip_methods.py`
covers REQUEST / REPLY / CANCEL / PUBLISH (the heavily-used methods).
This file adds the less-common methods RFC 5546 §3.2 requires:

  * ADD (§3.2.4) — adds a new recurrence to an existing VEVENT. Requires
    ORGANIZER + UID + DTSTAMP + SEQUENCE. The new occurrence typically
    carries RECURRENCE-ID.
  * REFRESH (§3.2.6) — attendee requests an updated iCal from the
    organizer. Requires ORGANIZER + ATTENDEE + UID.
  * COUNTER (§3.2.7) — attendee proposes a change. Requires the
    proposed event details + ATTENDEE + ORGANIZER + UID.
  * DECLINECOUNTER (§3.2.8) — organizer rejects a COUNTER. Requires
    ORGANIZER + ATTENDEE + UID + SEQUENCE.

Plus depth on PUBLISH requirements (§3.2.1) that weren't asserted before.

For each method, the tests verify:
  (a) a well-formed instance does NOT emit `itip_missing_property`.
  (b) an instance missing a required property DOES emit the warning.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_parse

HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
TAIL = "END:VCALENDAR\n"


def _warn_kinds(out: dict[str, Any]) -> list[str]:
    raw = out.get("warnings") or []
    if not isinstance(raw, list):
        return []
    return [w.get("kind", "") for w in cast(list[dict[str, Any]], raw)]


def _wrap(method: str, event_body: str) -> str:
    return (
        HEAD
        + f"METHOD:{method}\n"
        + "BEGIN:VEVENT\n" + event_body + "END:VEVENT\n"
        + TAIL
    )


# ---------------------------------------------------------------------------
# PUBLISH (§3.2.1)
# ---------------------------------------------------------------------------


def test_publish_forbids_attendee(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.1: PUBLISH MUST NOT include ATTENDEE."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "SUMMARY:Event\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("PUBLISH", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_publish_without_attendee_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A PUBLISH without ATTENDEE and without ORGANIZER is legal per RFC 5546."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "SUMMARY:Event\n"
    )
    out = run_parse(submission_command, _wrap("PUBLISH", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# ADD (§3.2.4)
# ---------------------------------------------------------------------------


def test_add_requires_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """METHOD:ADD without ORGANIZER → itip_missing_property."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260305T100000Z\n"
        "RECURRENCE-ID:20260305T100000Z\n"
    )
    out = run_parse(submission_command, _wrap("ADD", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_add_with_organizer_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260305T100000Z\n"
        "SEQUENCE:0\nRECURRENCE-ID:20260305T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _wrap("ADD", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# REFRESH (§3.2.6)
# ---------------------------------------------------------------------------


def test_refresh_requires_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """REFRESH without ORGANIZER → itip_missing_property."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("REFRESH", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_refresh_requires_attendee(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """REFRESH without ATTENDEE → itip_missing_property."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _wrap("REFRESH", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_refresh_with_both_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nSEQUENCE:0\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("REFRESH", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# COUNTER (§3.2.7)
# ---------------------------------------------------------------------------


def test_counter_requires_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("COUNTER", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_counter_requires_attendee(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _wrap("COUNTER", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_counter_with_both_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nSEQUENCE:0\n"
        "DTSTART:20260301T110000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("COUNTER", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# DECLINECOUNTER (§3.2.8)
# ---------------------------------------------------------------------------


def test_declinecounter_requires_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("DECLINECOUNTER", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_declinecounter_with_organizer_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nSEQUENCE:0\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _wrap("DECLINECOUNTER", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# Case insensitivity on METHOD value
# ---------------------------------------------------------------------------


def test_method_value_canonicalization(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Lowercase `method:request` triggers REQUEST-style validation
    regardless of how the tool canonicalizes the casing."""
    ics = (
        HEAD
        + "method:request\n"
        + "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "SUMMARY:Event\n"  # missing ORGANIZER
        "END:VEVENT\n"
        + TAIL
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


# ---------------------------------------------------------------------------
# Multiple events in one iTIP calendar
# ---------------------------------------------------------------------------


def test_itip_requires_sequence(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3: every iTIP message (other than PUBLISH) requires
    SEQUENCE."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=ACCEPTED:mailto:a@example.com\n"
        # deliberately missing SEQUENCE
    )
    out = run_parse(submission_command, _wrap("REQUEST", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_itip_requires_dtstamp(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3: DTSTAMP is required on every iTIP message (other
    than PUBLISH)."""
    body = (
        "UID:e1\nSEQUENCE:0\nDTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=ACCEPTED:mailto:a@example.com\n"
        # deliberately missing DTSTAMP
    )
    out = run_parse(submission_command, _wrap("REQUEST", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_request_requires_attendee(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.2: REQUEST requires at least one ATTENDEE."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nSEQUENCE:0\n"
        "DTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        # deliberately missing ATTENDEE
    )
    out = run_parse(submission_command, _wrap("REQUEST", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_publish_does_not_require_sequence(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """PUBLISH does NOT need SEQUENCE (RFC 5546 §3.2.1 relaxes)."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "SUMMARY:Event\nORGANIZER:mailto:boss@example.com\n"
        # no SEQUENCE, no ATTENDEE — valid PUBLISH
    )
    out = run_parse(submission_command, _wrap("PUBLISH", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


def test_itip_warning_per_event(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When a calendar has multiple events, validation runs per-event."""
    ics = (
        HEAD
        + "METHOD:REQUEST\n"
        + "BEGIN:VEVENT\n"
        "UID:a\nDTSTAMP:20260101T120000Z\nSEQUENCE:0\n"
        "DTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=ACCEPTED:mailto:x@example.com\n"
        "END:VEVENT\n"
        + "BEGIN:VEVENT\n"
        "UID:b\nDTSTAMP:20260101T120000Z\nSEQUENCE:0\n"
        "DTSTART:20260302T100000Z\n"
        # missing ORGANIZER on the second event
        "END:VEVENT\n"
        + TAIL
    )
    out = run_parse(submission_command, ics, tmp_path)
    # The first event is fine; the second should warn.
    assert "itip_missing_property" in _warn_kinds(out)
