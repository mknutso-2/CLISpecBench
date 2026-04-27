"""v0.2 additions: sub-day FREQ, BYHOUR/MINUTE/SECOND, RECURRENCE-ID overrides,
EXRULE, VTODO/VJOURNAL/VFREEBUSY, METHOD on VCALENDAR."""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, run_parse, starts_for, wrap_event

# --- Sub-day FREQ ---


def test_hourly_expansion(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nRRULE:FREQ=HOURLY;COUNT=3\n"
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-05T00:00:00Z",
        "2026-03-06T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-05T11:00:00Z",
        "2026-03-05T12:00:00Z",
    ]


def test_minutely_expansion(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=MINUTELY;INTERVAL=15;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-05T00:00:00Z",
        "2026-03-06T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-05T10:15:00Z",
        "2026-03-05T10:30:00Z",
    ]


def test_secondly_expansion(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=SECONDLY;INTERVAL=30;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-05T00:00:00Z",
        "2026-03-06T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-05T10:00:30Z",
        "2026-03-05T10:01:00Z",
    ]


# --- BYHOUR / BYMINUTE / BYSECOND expansion within DAILY ---


def test_daily_byhour_expands(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T090000Z\n"
        "RRULE:FREQ=DAILY;BYHOUR=9,13,17;COUNT=3\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-03-06T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 3 candidates per day; COUNT=3 should cap at first 3.
    assert starts == [
        "2026-03-05T09:00:00Z",
        "2026-03-05T13:00:00Z",
        "2026-03-05T17:00:00Z",
    ]


def test_daily_byhour_byminute_grid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T090000Z\n"
        "RRULE:FREQ=DAILY;BYHOUR=9,13;BYMINUTE=0,30;COUNT=4\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-05T00:00:00Z",
        "2026-03-06T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 2 hours × 2 minutes = 4 slots on one day.
    assert starts == [
        "2026-03-05T09:00:00Z",
        "2026-03-05T09:30:00Z",
        "2026-03-05T13:00:00Z",
        "2026-03-05T13:30:00Z",
    ]


# --- RECURRENCE-ID overrides ---


def test_recurrence_id_replaces_occurrence(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Base recurring event + one override at a specific recurrence-id.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=5\nEND:VEVENT\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "RECURRENCE-ID:20260307T100000Z\n"
        "DTSTART:20260307T150000Z\n"  # moved by 5 hours
        "SUMMARY:moved\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-03-15T00:00:00Z", tmp_path
    )
    starts = starts_for(out["occurrences"], "e1")
    # The 2026-03-07T10:00 instance should be replaced with 15:00.
    assert "2026-03-07T10:00:00Z" not in starts
    assert "2026-03-07T15:00:00Z" in starts
    # Other instances unchanged.
    assert "2026-03-05T10:00:00Z" in starts
    assert "2026-03-06T10:00:00Z" in starts


def test_recurrence_id_cancel_marks_occurrence_cancelled(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """summary.md §7: an override with STATUS:CANCELLED marks the
    occurrence as cancelled but does NOT drop it from the array.
    §9.2's occurrence schema keeps every key present including the
    `cancelled` boolean. The occurrence at 2026-03-07 10:00Z MUST be
    in the output with `cancelled: true`, not silently removed —
    consumers should observe the cancellation explicitly."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=5\nEND:VEVENT\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "RECURRENCE-ID:20260307T100000Z\n"
        "STATUS:CANCELLED\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-03-15T00:00:00Z", tmp_path
    )
    occs = out.get("occurrences") or []
    cancelled_occs = [
        o for o in occs if o.get("uid") == "e1" and o.get("dtstart") == "2026-03-07T10:00:00Z"
    ]
    assert len(cancelled_occs) == 1, (
        f"expected the 2026-03-07 override occurrence to be emitted "
        f"with cancelled=true per §9.2; got {cancelled_occs!r}"
    )
    assert cancelled_occs[0].get("cancelled") is True


def test_override_flag_set(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "RECURRENCE-ID:20260306T100000Z\nDTSTART:20260306T120000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-03-15T00:00:00Z", tmp_path
    )
    overrides = [o for o in out["occurrences"] if o.get("override") is True]
    assert len(overrides) == 1
    assert overrides[0]["dtstart"] == "2026-03-06T12:00:00Z"


# --- EXRULE ---


def test_exrule_subtracts(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260301T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=7\n"
        "EXRULE:FREQ=WEEKLY;BYDAY=SA,SU\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-03-10T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    # 2026-03-01 is Sunday; 2026-03-07 is Saturday. EXRULE filters weekends.
    assert "2026-03-01T10:00:00Z" not in starts
    assert "2026-03-07T10:00:00Z" not in starts
    assert "2026-03-02T10:00:00Z" in starts  # Monday


def test_exrule_emits_deprecated_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260301T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=7\n"
        "EXRULE:FREQ=WEEKLY;BYDAY=SA,SU\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    kinds = [w.get("kind") for w in out.get("warnings", [])]
    assert "exrule_deprecated" in kinds


# --- VTODO / VJOURNAL / VFREEBUSY ---


def test_vtodo_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VTODO\n"
        "UID:t1\nDTSTAMP:20260420T120000Z\n"
        "SUMMARY:Write report\nDUE:20260425T170000Z\n"
        "PERCENT-COMPLETE:40\n"
        "STATUS:IN-PROCESS\n"
        "END:VTODO\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    todos = out["todos"]
    assert len(todos) == 1
    t = todos[0]
    assert t["summary"] == "Write report"
    assert t["due"] == "2026-04-25T17:00:00Z"
    assert t["percent_complete"] == 40
    assert t["status"] == "IN-PROCESS"


def test_vjournal_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VJOURNAL\n"
        "UID:j1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART;VALUE=DATE:20260425\n"
        "SUMMARY:Conference notes\n"
        "END:VJOURNAL\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    journals = out["journals"]
    assert len(journals) == 1
    assert journals[0]["summary"] == "Conference notes"


def test_vfreebusy_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VFREEBUSY\n"
        "UID:fb1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART:20260425T090000Z\nDTEND:20260425T170000Z\n"
        "END:VFREEBUSY\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert len(out["freebusy"]) == 1


# --- METHOD ---


def test_calendar_method_surfaced(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "METHOD:REQUEST\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART:20260305T100000Z\nSEQUENCE:0\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert out["calendar"]["method"] == "REQUEST"


def test_calendar_calscale_surfaced(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "CALSCALE:GREGORIAN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART:20260305T100000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert out["calendar"]["calscale"] == "GREGORIAN"


# --- Attendee PARTSTAT ---


def test_attendee_partstat_surfaced(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=Jane;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED:mailto:jane@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    att = out["events"][0]["attendees"][0]
    assert att["partstat"] == "ACCEPTED"
