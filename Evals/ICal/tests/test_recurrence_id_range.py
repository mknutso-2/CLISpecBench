"""RECURRENCE-ID with RANGE=THISANDFUTURE per RFC 5545 §3.8.4.4 and §3.2.13.

The RECURRENCE-ID property identifies a single instance within a recurrence
set by echoing that instance's original DTSTART. §3.2.13 defines a RANGE
parameter; the only allowed value is THISANDFUTURE, meaning "this instance
and every subsequent instance". Without RANGE, only the single instance is
affected (the default).

When RANGE=THISANDFUTURE is present:
  * the override component rewrites the pointed-to instance AND all later
    instances defined by the original RRULE.
  * if the override shifts DTSTART by some delta (or modifies the
    duration), every later instance is shifted by the same delta / gets
    the new duration.
  * subsequent instances defined by a separate component (a separate UID)
    are NOT affected.

In parsed output:
  * `event["recurrence_id"]` is `{"value": "<ISO>", "range":
    "THISANDFUTURE" | null, "tzid": <string> | null}`.

In expanded output, each override occurrence surfaces:
  * `recurrence_id`: ISO-8601 value of the override's RECURRENCE-ID
  * `range`: "THISANDFUTURE" | null
  * `override`: true
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import occurrences_of, run_expand, run_parse, starts_for


def _rid_field(ev: dict[str, Any]) -> dict[str, Any]:
    rid = ev.get("recurrence_id")
    assert isinstance(rid, dict), (
        f"recurrence_id must be an object with value/range/tzid, got {type(rid).__name__}"
    )
    return cast(dict[str, Any], rid)


def test_recurrence_id_without_range_has_null_range(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.13: if RANGE is not specified, the default is the single instance only.
    In the parsed schema, `range` is null."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260302T100000Z\nDTSTART:20260302T120000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    # Find the override event (the one with a recurrence_id).
    overrides = [e for e in out["events"] if e.get("recurrence_id") is not None]
    assert len(overrides) == 1
    rid = _rid_field(overrides[0])
    assert rid.get("value") == "2026-03-02T10:00:00Z"
    assert rid.get("range") is None


def test_recurrence_id_with_range_parsed(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.13: RANGE=THISANDFUTURE is surfaced on the recurrence_id object."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=5\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260303T100000Z\n"
        "DTSTART:20260303T140000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    overrides = [e for e in out["events"] if e.get("recurrence_id") is not None]
    assert len(overrides) == 1
    rid = _rid_field(overrides[0])
    assert rid.get("range") == "THISANDFUTURE"


def test_range_shifts_all_future_occurrences(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.4: rescheduling one instance with RANGE=THISANDFUTURE shifts
    that instance and every subsequent instance by the same delta."""
    # Daily at 10:00 for 5 days (3/1..3/5). Override 3/3 with +4h.
    # Expected: 3/1 10:00, 3/2 10:00, 3/3 14:00, 3/4 14:00, 3/5 14:00.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=5\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260303T100000Z\n"
        "DTSTART:20260303T140000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    starts = sorted(starts_for(occurrences_of(out), "e1"))
    assert starts == [
        "2026-03-01T10:00:00Z",
        "2026-03-02T10:00:00Z",
        "2026-03-03T14:00:00Z",
        "2026-03-04T14:00:00Z",
        "2026-03-05T14:00:00Z",
    ]


def test_range_does_not_affect_past_occurrences(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.4: past instances (before the RECURRENCE-ID anchor) are untouched."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=5\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260303T100000Z\n"
        "DTSTART:20260303T140000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    starts = starts_for(occurrences_of(out), "e1")
    # 3/1 and 3/2 stay at 10:00.
    assert "2026-03-01T10:00:00Z" in starts
    assert "2026-03-02T10:00:00Z" in starts
    # The original 3/3 10:00 is replaced; no stray copy.
    assert "2026-03-03T10:00:00Z" not in starts


def test_range_flag_surfaces_on_override_occurrence(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.4: the override occurrence exposes `range=THISANDFUTURE` and `override=true`."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260302T100000Z\n"
        "DTSTART:20260302T150000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    anchor = [o for o in occurrences_of(out) if o.get("dtstart") == "2026-03-02T15:00:00Z"]
    assert len(anchor) == 1
    assert anchor[0].get("override") is True
    assert anchor[0].get("range") == "THISANDFUTURE"
    assert anchor[0].get("recurrence_id") == "2026-03-02T10:00:00Z"


def test_range_with_unbounded_rrule(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.4: THISANDFUTURE on an unbounded RRULE shifts every instance from
    the anchor forward; the test window bounds what we can observe."""
    # Daily with no COUNT/UNTIL; window is [3/1, 3/6).
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260303T100000Z\n"
        "DTSTART:20260303T160000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-03-06T00:00:00Z", tmp_path
    )
    starts = sorted(starts_for(occurrences_of(out), "e1"))
    assert starts == [
        "2026-03-01T10:00:00Z",
        "2026-03-02T10:00:00Z",
        "2026-03-03T16:00:00Z",
        "2026-03-04T16:00:00Z",
        "2026-03-05T16:00:00Z",
    ]


def test_range_does_not_affect_other_uid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.4: "Subsequent instances defined in separate components are not
    impacted by the given recurrence instance." A separate UID's daily series
    must not be touched by another event's THISANDFUTURE override."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        # e1 daily, with THISANDFUTURE override starting 3/3.
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260302T100000Z\n"
        "DTSTART:20260302T180000Z\nEND:VEVENT\n"
        # e2 daily at 10:00 — must be unaffected.
        "BEGIN:VEVENT\nUID:e2\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    e2_starts = starts_for(occurrences_of(out), "e2")
    assert sorted(e2_starts) == [
        "2026-03-01T10:00:00Z",
        "2026-03-02T10:00:00Z",
        "2026-03-03T10:00:00Z",
    ]


def test_range_with_mismatched_recurrence_id_warns(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.4: RECURRENCE-ID value must correspond to an instance generated
    by the base series. An orphan override (no matching instance in the
    recurrence set) should produce an `orphan_override` warning."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        # Weekly MO — no Tuesday in the series.
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T100000Z\nRRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=4\nEND:VEVENT\n"
        # Override anchored to a Tuesday that doesn't belong to the series.
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID;RANGE=THISANDFUTURE:20260303T100000Z\n"
        "DTSTART:20260303T140000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [w.get("kind") for w in out.get("warnings", [])]
    assert "orphan_override" in kinds


def test_single_instance_override_does_not_shift_future(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.13 default: without RANGE, only the single instance is overridden.
    Contrast with THISANDFUTURE: later instances stay at the original time."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=4\nEND:VEVENT\n"
        # No RANGE param: only 3/2 itself is replaced.
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260302T100000Z\nDTSTART:20260302T150000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    starts = sorted(starts_for(occurrences_of(out), "e1"))
    assert starts == [
        "2026-03-01T10:00:00Z",
        "2026-03-02T15:00:00Z",  # overridden
        "2026-03-03T10:00:00Z",  # unchanged (no THISANDFUTURE)
        "2026-03-04T10:00:00Z",  # unchanged
    ]


def test_range_flag_null_for_single_instance_overrides(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.13 default: an override with no RANGE param surfaces range=null on
    the expanded occurrence."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260302T100000Z\nDTSTART:20260302T110000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    overrides = [o for o in occurrences_of(out) if o.get("override") is True]
    assert len(overrides) == 1
    assert overrides[0].get("range") is None
    assert overrides[0].get("recurrence_id") == "2026-03-02T10:00:00Z"
