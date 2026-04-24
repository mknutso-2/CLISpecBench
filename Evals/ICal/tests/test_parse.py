"""Parsing tests: line unfolding, property parsing, components, text escapes. Spec §1, §2, §3."""

from __future__ import annotations

from pathlib import Path

from conftest import find_event, run_parse, wrap_event


def test_simple_vevent(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nDTEND:20260305T110000Z\nSUMMARY:Hello\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert ev["summary"] == "Hello"
    assert ev["dtstart"] == "2026-03-05T10:00:00Z"
    assert ev["dtend"] == "2026-03-05T11:00:00Z"


def test_content_line_unfolding(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # RFC 5545 §3.1: CRLF + one whitespace character is removed. The space before
    # the fold is part of the original content; the folder injects exactly one
    # space after CRLF, which unfolds to a zero-space join. Two spaces after
    # CRLF gives a one-space join.
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "SUMMARY:This is a long\n  summary that was folded\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["summary"] == "This is a long summary that was folded"


def test_text_escape_backslash(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "SUMMARY:Path is C:\\\\Users\\\\docs\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    # `\\` → `\` per spec §1.3. So `\\\\` in the value (two backslashes in the
    # raw bytes) unescapes to one backslash.
    assert find_event(out, "e1")["summary"] == "Path is C:\\Users\\docs"


def test_text_escape_newline(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nDESCRIPTION:Line1\\nLine2\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["description"] == "Line1\nLine2"


def test_text_escape_semicolon(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nSUMMARY:a\\;b\\;c\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["summary"] == "a;b;c"


def test_property_name_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = wrap_event("uid:e1\ndtstamp:20260420T120000Z\nDtStart:20260305T100000Z\nsummary:ok\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert ev["summary"] == "ok"


def test_property_parameter_parsing(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=Jane Doe;ROLE=REQ-PARTICIPANT:mailto:jane@example.com\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert len(ev["attendees"]) == 1
    assert ev["attendees"][0]["cn"] == "Jane Doe"


def test_quoted_parameter_value(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        'ATTENDEE;CN="Smith, John":mailto:j@example.com\n'
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["attendees"][0]["cn"] == "Smith, John"


def test_date_value_type(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART;VALUE=DATE:20260305\nSUMMARY:all-day\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["dtstart"] == "2026-03-05"


def test_floating_datetime(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event("UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000\nSUMMARY:x\n")
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["dtstart"] == "2026-03-05T10:00:00"


def test_utc_datetime(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event("UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nSUMMARY:x\n")
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["dtstart"] == "2026-03-05T10:00:00Z"


def test_two_events(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        "BEGIN:VEVENT\nUID:a\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nSUMMARY:A\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:b\nDTSTAMP:20260420T120000Z\nDTSTART:20260306T100000Z\nSUMMARY:B\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    uids = {e["uid"] for e in out["events"]}
    assert uids == {"a", "b"}


def test_categories_split(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nCATEGORIES:work,urgent,proj-x\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert find_event(out, "e1")["categories"] == ["work", "urgent", "proj-x"]


def test_tzid_param_surfaced(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # v0.2: TZID params surface in raw_properties; unresolved ones emit
    # `unresolved_tzid` warnings only during expand (where resolution is
    # attempted), not during parse.
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\n"
        "DTSTART;TZID=America/New_York:20260305T100000\nSUMMARY:x\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    events = out["events"]
    assert len(events) == 1
    raw = events[0]["raw_properties"]
    found = False
    for p in raw:
        if p["name"] == "DTSTART" and p["params"].get("TZID") == "America/New_York":
            found = True
            break
    assert found
