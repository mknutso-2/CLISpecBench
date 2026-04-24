"""Regression tests targeting published bugs in mainstream RRULE libraries.
These are the corners where rrule.js / python-dateutil have filed issues;
a strong agent should handle each correctly by following the RFC.

References:
  - rrule.js #375 — BYSETPOS with multiple BYDAY in MONTHLY
  - rrule.js #309 — DTSTART in RRuleSet (overrides, exclusion ordering)
  - rrule.js #556 — BYDAY returning wrong days in certain WKST configurations
  - dateutil #1398 — WEEKLY + WKST + BYSETPOS interaction
  - plus the v0.3 adversarial-corner tests already in test_adversarial_corners.py
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, starts_for, warnings_of, wrap_event

# ---------------------------------------------------------------------------
# BYSETPOS × time expansion (the v0.3 spec pins this to dateutil semantics).
# ---------------------------------------------------------------------------


def test_bysetpos_with_byhour_picks_last_time_slot(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Monthly meeting with BYHOUR=9,17 and BYSETPOS=-1. Per v0.3 spec, BYSETPOS
    # applies to the fully time-expanded candidate list, so BYSETPOS=-1 picks
    # the LAST (timestamp) slot of the month, not the last DATE.
    # For FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,17;BYSETPOS=-1,
    # March 2026's last weekday is Tue 3/31. BYHOUR expands to 09:00 and 17:00.
    # BYSETPOS=-1 on the full list picks 3/31 17:00.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260331T090000Z\n"
        "RRULE:FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,17;BYSETPOS=-1;COUNT=2\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-06-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # March 2026: last weekday is Tue 3/31. April 2026: last weekday is Thu 4/30.
    # BYSETPOS=-1 on the time-expanded list picks the 17:00 slot.
    assert starts == [
        "2026-03-31T17:00:00Z",
        "2026-04-30T17:00:00Z",
    ]


def test_bysetpos_multiple_positions(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # BYSETPOS=1,-1 on MONTHLY;BYDAY=MO picks the first AND last Monday.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T100000Z\n"
        "RRULE:FREQ=MONTHLY;BYDAY=MO;BYSETPOS=1,-1;COUNT=4\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-06-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # March 2026 Mondays: 2, 9, 16, 23, 30 → BYSETPOS=1,-1 → 3/2 and 3/30.
    # April 2026 Mondays: 6, 13, 20, 27 → 4/6 and 4/27.
    assert starts == [
        "2026-03-02T10:00:00Z",
        "2026-03-30T10:00:00Z",
        "2026-04-06T10:00:00Z",
        "2026-04-27T10:00:00Z",
    ]


# ---------------------------------------------------------------------------
# WEEKLY + WKST interaction (dateutil #1398).
# ---------------------------------------------------------------------------


def test_weekly_wkst_sunday_changes_week_boundary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Biweekly on Sunday and Monday, WKST=SU. With WKST=SU, a week starts on
    # Sunday, so "every other week" starting on a Sunday means SU+MO, skip,
    # SU+MO, skip. With WKST=MO (default), the Sunday of week 1 and the
    # Monday after are in DIFFERENT weeks, so the "biweekly" pattern changes.
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"  # Sun 2026-03-01
        "RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=SU,MO;WKST=SU;COUNT=4\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # With WKST=SU: week 1 is Sun 3/1 - Sat 3/7. Emits 3/1 (Sun), 3/2 (Mon).
    # Skip week 2 (3/8-3/14). Week 3 is Sun 3/15 - Sat 3/21. Emits 3/15, 3/16.
    assert starts == [
        "2026-03-01T10:00:00Z",
        "2026-03-02T10:00:00Z",
        "2026-03-15T10:00:00Z",
        "2026-03-16T10:00:00Z",
    ]


# ---------------------------------------------------------------------------
# Overrides (rrule.js #309 / #556 style)
# ---------------------------------------------------------------------------


def test_exdate_removes_before_override_replaces(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # A recurrence-id that overrides a specific instance that is ALSO on the
    # EXDATE list: EXDATE wins (the instance is not produced, so there's
    # nothing to override). The override is therefore orphan.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=5\n"
        "EXDATE:20260307T100000Z\n"
        "END:VEVENT\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260307T100000Z\nDTSTART:20260307T150000Z\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-03-15T00:00:00Z", tmp_path
    )
    # The 3/7 10:00 base instance was EXDATE'd, so the override should become
    # an orphan_override warning. It's still surfaced as an occurrence.
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "orphan_override" in kinds


def test_orphan_override_non_matching_uid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # An override referencing a UID that has no base event.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:ghost\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260305T100000Z\nDTSTART:20260305T150000Z\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "orphan_override" in kinds


def test_orphan_override_time_mismatch(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Override references a recurrence-id that doesn't match any generated occurrence.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260401T100000Z\n"  # doesn't match any COUNT=3 base occurrence
        "DTSTART:20260401T150000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-05-01T00:00:00Z", tmp_path
    )
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "orphan_override" in kinds


# ---------------------------------------------------------------------------
# DST fold disambiguation — both-sides assertions
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


def _wrap_tz(body: str) -> str:
    return (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + US_EASTERN_TZ
        + "BEGIN:VEVENT\n"
        + body
        + "END:VEVENT\n"
        + "END:VCALENDAR\n"
    )


def test_dst_fall_back_ambiguous_time_uses_pre_transition(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # 2026-11-01 DST ends at 02:00 local (EDT → EST). Local time 01:30 occurs
    # TWICE on this day. Per v0.3 spec §5.1.1, we pick pre-transition (EDT),
    # matching PEP 495 fold=0 and python-dateutil's default.
    # 01:30 EDT = 05:30 UTC.
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=America/New_York:20261101T013000\n"
    out = run_expand(
        submission_command,
        _wrap_tz(body),
        "2026-10-01T00:00:00Z",
        "2026-12-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    # Pre-transition offset is -0400 (EDT), so 01:30 local = 05:30 UTC.
    assert out["occurrences"][0]["dtstart"] == "2026-11-01T05:30:00Z"


def test_dst_spring_forward_nonexistent_time_uses_post_transition(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # 2026-03-08 DST starts at 02:00 local (EST → EDT). Local time 02:30 does
    # NOT exist in the wall clock. Per v0.3 spec §5.1.1, pick post-transition
    # (EDT, -0400). 02:30 treated as 06:30 UTC (EDT equivalent).
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART;TZID=America/New_York:20260308T023000\n"
    out = run_expand(
        submission_command,
        _wrap_tz(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    # EDT (-0400): 02:30 local = 06:30 UTC.
    assert out["occurrences"][0]["dtstart"] == "2026-03-08T06:30:00Z"
