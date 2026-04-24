"""Stress + regression tests.

These tests verify the parser/expander handle large inputs in
reasonable time and produce correct output. They also cover
regression scenarios that previously surfaced edge-case bugs.

The time bounds are generous — a correct implementation should
handle these within the pytest default 30s timeout.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_expand, run_parse, starts_for

HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
TAIL = "END:VCALENDAR\n"


# ---------------------------------------------------------------------------
# Large event count
# ---------------------------------------------------------------------------


def test_parse_500_events_in_reasonable_time(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A calendar with 500 events parses and surfaces all of them."""
    events = []
    for i in range(500):
        events.append(
            f"BEGIN:VEVENT\nUID:e{i:04d}\nDTSTAMP:20260101T120000Z\n"
            f"DTSTART:20260{(i % 12) + 1:02d}01T100000Z\n"
            f"SUMMARY:Event {i}\nEND:VEVENT\n"
        )
    ics = HEAD + "".join(events) + TAIL
    out = run_parse(submission_command, ics, tmp_path, timeout=60)
    assert len(cast(list[Any], out.get("events") or [])) == 500


# ---------------------------------------------------------------------------
# Large RRULE expansion
# ---------------------------------------------------------------------------


def test_rrule_count_1000_expands(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A daily RRULE with COUNT=1000 expands without error."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260101T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=1000\n"
    )
    ics = HEAD + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-01-01T00:00:00Z",
        "2029-01-01T00:00:00Z",
        tmp_path,
        timeout=60,
    )
    starts = starts_for(out.get("occurrences") or [], "e1")
    assert len(starts) == 1000


def test_rrule_hourly_expansion_bounded_by_window(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An HOURLY recurrence with no COUNT is safely bounded by the expand
    window (24 hours = 24 occurrences)."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\n"
        "RRULE:FREQ=HOURLY\n"
    )
    ics = HEAD + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-03-01T00:00:00Z",
        "2026-03-02T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out.get("occurrences") or [], "e1")
    assert len(starts) == 24


# ---------------------------------------------------------------------------
# Deep override chain
# ---------------------------------------------------------------------------


def test_deep_override_chain(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A base event + 20 overrides on consecutive daily instances."""
    base = (
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=30\n"
        "END:VEVENT\n"
    )
    overrides = []
    for i in range(20):
        day = i + 2  # override days 3/2 through 3/21
        overrides.append(
            f"BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
            f"RECURRENCE-ID:202603{day:02d}T100000Z\n"
            f"DTSTART:202603{day:02d}T150000Z\n"
            f"SUMMARY:Override day {day}\n"
            f"END:VEVENT\n"
        )
    ics = HEAD + base + "".join(overrides) + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    occs = cast(list[dict[str, Any]], out.get("occurrences") or [])
    # 30 base instances; 20 overridden (one per RID); total still 30
    # occurrences (overrides REPLACE base instances, not add to them).
    assert len(occs) == 30
    overridden_count = sum(1 for o in occs if o.get("override") is True)
    assert overridden_count == 20


# ---------------------------------------------------------------------------
# Mid-file malformed entry: parsing continues, emits warning
# ---------------------------------------------------------------------------


def test_malformed_midfile_preserves_later_valid_events(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A malformed property in one event doesn't lose the events around it."""
    ics = (
        HEAD
        + "BEGIN:VEVENT\nUID:a\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:b\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T100000Z\nGEO:garbage\nEND:VEVENT\n"  # malformed GEO
        + "BEGIN:VEVENT\nUID:c\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260303T100000Z\nEND:VEVENT\n"
        + TAIL
    )
    out = run_parse(submission_command, ics, tmp_path)
    events = cast(list[dict[str, Any]], out.get("events") or [])
    uids = {ev.get("uid") for ev in events}
    assert uids == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# Deep VALARM nesting on a single event
# ---------------------------------------------------------------------------


def test_many_alarms_on_one_event(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An event with 50 VALARMs parses and all alarms surface."""
    alarms = []
    for i in range(50):
        alarms.append(
            "BEGIN:VALARM\n"
            "ACTION:DISPLAY\n"
            f"TRIGGER:-PT{(i + 1) * 5}M\n"
            f"DESCRIPTION:Reminder {i}\n"
            "END:VALARM\n"
        )
    body = (
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"
        + "".join(alarms) +
        "END:VEVENT\n"
    )
    ics = HEAD + body + TAIL
    out = run_parse(submission_command, ics, tmp_path)
    events = cast(list[dict[str, Any]], out.get("events") or [])
    assert len(events) == 1
    alarms_out = cast(list[Any], events[0].get("alarms") or [])
    assert len(alarms_out) == 50


# ---------------------------------------------------------------------------
# YEARLY + BYMONTHDAY across a decade
# ---------------------------------------------------------------------------


def test_yearly_bymonthday_across_decade(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=15 produces one occurrence per year."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260315T100000Z\n"
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=15\n"
    )
    ics = HEAD + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-01-01T00:00:00Z",
        "2036-01-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out.get("occurrences") or [], "e1")
    assert len(starts) == 10, f"expected 10 yearly occurrences, got {len(starts)}"


# ---------------------------------------------------------------------------
# UNTIL at exactly the window end
# ---------------------------------------------------------------------------


def test_until_at_exact_window_boundary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """UNTIL at exactly the window end is inclusive per RFC 5545 §3.3.10."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"
        "RRULE:FREQ=DAILY;UNTIL=20260305T100000Z\n"
    )
    ics = HEAD + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-03-01T00:00:00Z",
        "2026-03-10T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out.get("occurrences") or [], "e1")
    # 3/1, 3/2, 3/3, 3/4, 3/5 — 5 occurrences inclusive of UNTIL.
    assert len(starts) == 5


# ---------------------------------------------------------------------------
# Empty expand window
# ---------------------------------------------------------------------------


def test_expand_window_before_event_is_empty(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Expand window entirely before DTSTART produces no occurrences."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T100000Z\n"
    )
    ics = HEAD + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-01-01T00:00:00Z",
        "2026-05-01T00:00:00Z",
        tmp_path,
    )
    assert out.get("occurrences") == []


# ---------------------------------------------------------------------------
# Mixed zoned + floating + UTC in same calendar
# ---------------------------------------------------------------------------


def test_mixed_timekinds_coexist(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Three events with UTC, floating, and zoned DATE-TIMEs all parse and
    expand independently."""
    tz = (
        "BEGIN:VTIMEZONE\n"
        "TZID:America/Chicago\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20200101T000000\n"
        "TZOFFSETFROM:-0600\nTZOFFSETTO:-0600\n"
        "END:STANDARD\n"
        "END:VTIMEZONE\n"
    )
    ics = (
        HEAD
        + tz
        + "BEGIN:VEVENT\nUID:utc\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260601T100000Z\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:floating\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260602T100000\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:zoned\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/Chicago:20260603T100000\nEND:VEVENT\n"
        + TAIL
    )
    out = run_expand(
        submission_command,
        ics,
        "2026-06-01T00:00:00Z",
        "2026-06-04T00:00:00Z",
        tmp_path,
    )
    occs = cast(list[dict[str, Any]], out.get("occurrences") or [])
    uids = {o.get("uid") for o in occs}
    assert uids == {"utc", "floating", "zoned"}
