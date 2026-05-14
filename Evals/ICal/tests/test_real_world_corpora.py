"""Real-world calendar corpus tests.

Loads curated `.ics` fixtures from `tests/calendars/` that simulate
the shape of real-world calendars from Gmail, Outlook, and iTIP
scheduling flows. Each file exercises multiple features in one
test: timezones, recurrence, alarms, attendee grammar, X-properties.

These tests are complementary to the targeted feature tests: a bug
in any one component tends to cascade visibly in the real-world
fixtures, but the smaller tests localize the failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_expand, run_parse

FIXTURES_DIR = Path(__file__).parent / "calendars"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Gmail-style export
# ---------------------------------------------------------------------------


def test_gmail_export_parses_successfully(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A realistic Gmail export parses without error."""
    ics = _load("gmail-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    cal = cast(dict[str, Any], out.get("calendar") or {})
    assert cal.get("prodid", "").startswith("-//Google")
    assert cal.get("method") == "PUBLISH"


def test_gmail_export_surfaces_timezone(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _load("gmail-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    tzs = cast(list[dict[str, Any]], out.get("timezones") or [])
    assert len(tzs) == 1
    assert tzs[0].get("tzid") == "America/Los_Angeles"
    assert len(cast(list[Any], tzs[0].get("standard") or [])) >= 1
    assert len(cast(list[Any], tzs[0].get("daylight") or [])) >= 1


def test_gmail_export_event_has_full_attendee_grammar(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _load("gmail-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "gmail-event-0001@google.com")
    attendees = cast(list[dict[str, Any]], ev.get("attendees") or [])
    assert len(attendees) == 2
    # First attendee is Bob, ACCEPTED.
    bob = next(a for a in attendees if a.get("cn") == "Bob Jones")
    assert bob.get("partstat") == "ACCEPTED"
    assert bob.get("cutype") == "INDIVIDUAL"
    assert bob.get("role") == "REQ-PARTICIPANT"
    assert bob.get("rsvp") is True


def test_gmail_export_expands_to_weekly_occurrences(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The weekly team sync expands to several Tuesdays in a month."""
    ics = _load("gmail-export.ics")
    out = run_expand(
        submission_command,
        ics,
        "2026-06-01T00:00:00Z",
        "2026-07-01T00:00:00Z",
        tmp_path,
    )
    occs = [
        o
        for o in cast(list[dict[str, Any]], out.get("occurrences") or [])
        if o.get("uid") == "gmail-event-0001@google.com"
    ]
    # June 2026 has Tuesdays on 6/2, 6/9, 6/16, 6/23, 6/30 = 5.
    assert len(occs) == 5


def test_gmail_export_alarm_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = _load("gmail-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "gmail-event-0001@google.com")
    alarms = cast(list[dict[str, Any]], ev.get("alarms") or [])
    assert len(alarms) == 1
    assert alarms[0].get("action") == "DISPLAY"


# ---------------------------------------------------------------------------
# Outlook-style export
# ---------------------------------------------------------------------------


def test_outlook_export_parses_successfully(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _load("outlook-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    cal = cast(dict[str, Any], out.get("calendar") or {})
    assert "Microsoft" in cal.get("prodid", "")


def test_outlook_quoted_tzid_parameter(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Outlook emits TZID params with DQUOTE around multi-word zone
    names (RFC 5545 §3.1 quoted-string parameter form). The parser
    may either strip the surrounding DQUOTEs (recommended — yields
    a clean TZID string consumable by downstream resolvers) or
    preserve them literally in raw_properties. This test accepts
    both forms because RFC 5545 doesn't strictly mandate stripping;
    but at least one form MUST appear so Outlook-exported
    calendars round-trip."""
    ics = _load("outlook-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "outlook-000001-aabbccdd")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    dtstart_raws = [p for p in raw if str(p.get("name", "")).upper() == "DTSTART"]
    assert len(dtstart_raws) >= 1
    params = cast(dict[str, Any], dtstart_raws[0].get("params", {}))
    tzid = params.get("TZID")
    assert tzid in ("Eastern Standard Time", '"Eastern Standard Time"'), (
        f"unexpected TZID param: {tzid!r} (expected stripped or literal-quoted form)"
    )


def test_outlook_x_properties_in_raw(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Microsoft's X-MICROSOFT-* properties are preserved in raw_properties."""
    ics = _load("outlook-export.ics")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "outlook-000001-aabbccdd")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    names = [str(p.get("name", "")).upper() for p in raw]
    assert any(n.startswith("X-MICROSOFT") for n in names)


# ---------------------------------------------------------------------------
# iTIP REQUEST corpus
# ---------------------------------------------------------------------------


def test_itip_request_has_organizer_and_three_attendees(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _load("itip-request.ics")
    out = run_parse(submission_command, ics, tmp_path)
    cal = cast(dict[str, Any], out.get("calendar") or {})
    assert cal.get("method") == "REQUEST"
    ev = find_event(out, "itip-request-12345@example.com")
    assert ev.get("organizer") is not None
    attendees = cast(list[dict[str, Any]], ev.get("attendees") or [])
    assert len(attendees) == 3
    roles = {a.get("role") for a in attendees}
    assert "REQ-PARTICIPANT" in roles
    assert "OPT-PARTICIPANT" in roles


def test_itip_request_no_missing_property_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A well-formed REQUEST should NOT produce itip_missing_property."""
    ics = _load("itip-request.ics")
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [str(w.get("kind", "")) for w in cast(list[dict[str, Any]], out.get("warnings") or [])]
    assert "itip_missing_property" not in kinds
