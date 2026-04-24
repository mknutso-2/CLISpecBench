"""Deeper schema conformance — extends test_schema.py beyond key-presence.

`test_schema.py` asserts the required top-level keys exist. This file
asserts:

  * Types match the schema spec (arrays are lists, not null).
  * ISO-8601 fields match the documented format regex.
  * Warning array entries always have a `kind` key.
  * Occurrences sorted by dtstart with uid tie-break.
  * All RFC 7986 calendar-level keys are present even when absent
    (null or empty default).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

from conftest import run_expand, run_parse, wrap_event

ISO_DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UTC_OFFSET = re.compile(r"^[+-]\d{4,6}$")


BASIC_CAL = (
    "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
    "BEGIN:VEVENT\n"
    "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
    "END:VEVENT\n"
    "END:VCALENDAR\n"
)


# ---------------------------------------------------------------------------
# Arrays are never null (even when empty)
# ---------------------------------------------------------------------------


def test_events_array_is_always_a_list(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, BASIC_CAL, tmp_path)
    assert isinstance(out.get("events"), list)


def test_empty_calendar_has_empty_arrays_not_nulls(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    empty = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\nEND:VCALENDAR\n"
    out = run_parse(submission_command, empty, tmp_path)
    # All top-level list keys declared by tech-reqs MUST be empty
    # lists on an empty VCALENDAR, not null. `availabilities` is in
    # the tech-reqs mandatory set so it's checked here alongside the
    # other list-shaped keys.
    for key in (
        "events", "todos", "journals", "freebusy",
        "timezones", "availabilities", "warnings",
    ):
        val = out.get(key)
        assert val is not None, f"{key} is null; should be []"
        assert isinstance(val, list), f"{key} not a list: {type(val)}"


def test_warnings_entries_have_kind_key(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Every warning entry must have a 'kind' key (strict contract)."""
    # Trigger some warning via EXRULE (deprecated).
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "EXRULE:FREQ=DAILY;COUNT=1\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    assert len(warnings) >= 1
    for w in warnings:
        assert "kind" in w, f"warning missing 'kind': {w}"
        assert isinstance(w["kind"], str) and w["kind"], f"kind not a non-empty string: {w}"


# ---------------------------------------------------------------------------
# ISO-8601 format for datetime fields
# ---------------------------------------------------------------------------


def test_event_dtstart_matches_iso_format(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, BASIC_CAL, tmp_path)
    ev = cast(list[dict[str, Any]], out["events"])[0]
    dtstart = ev.get("dtstart")
    assert isinstance(dtstart, str), f"dtstart not a string: {dtstart!r}"
    assert ISO_DATE_TIME.match(dtstart) or ISO_DATE.match(dtstart), (
        f"dtstart {dtstart!r} doesn't match ISO-8601 format"
    )


def test_occurrence_dtstart_matches_iso_utc(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Expand output's occurrence.dtstart is always ISO-8601 UTC (Z-suffixed)."""
    body = "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    occs = cast(list[dict[str, Any]], out.get("occurrences") or [])
    assert len(occs) == 1
    dt = occs[0].get("dtstart")
    assert isinstance(dt, str) and dt.endswith("Z"), (
        f"occurrence dtstart not UTC ISO-8601: {dt!r}"
    )
    assert ISO_DATE_TIME.match(dt)


# ---------------------------------------------------------------------------
# Occurrences sorted by dtstart then uid (strict tie-break)
# ---------------------------------------------------------------------------


def test_occurrences_sorted_by_dtstart(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + "BEGIN:VEVENT\nUID:late\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T100000Z\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:early\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nEND:VEVENT\n"
        + "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-01-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    occs = cast(list[dict[str, Any]], out.get("occurrences") or [])
    assert len(occs) == 2
    assert occs[0]["dtstart"] < occs[1]["dtstart"], (
        f"occurrences not sorted: {[o['dtstart'] for o in occs]}"
    )


def test_occurrences_uid_tiebreak_on_equal_dtstart(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two events with identical dtstart sort by uid lexicographic."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        + "BEGIN:VEVENT\nUID:zebra\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:apple\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nEND:VEVENT\n"
        + "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-01-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    occs = cast(list[dict[str, Any]], out.get("occurrences") or [])
    assert len(occs) == 2
    # Equal dtstart; uid-ascending tie-break: "apple" before "zebra".
    assert occs[0]["uid"] == "apple"
    assert occs[1]["uid"] == "zebra"


# ---------------------------------------------------------------------------
# RFC 7986 calendar-level keys always present
# ---------------------------------------------------------------------------


def test_calendar_object_has_all_rfc7986_keys(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The `calendar` object always has the full key set, even when values
    are null / empty."""
    out = run_parse(submission_command, BASIC_CAL, tmp_path)
    cal = cast(dict[str, Any], out.get("calendar") or {})
    for key in (
        "prodid", "version", "calscale", "method",
        "name", "description", "refresh_interval", "source",
        "color", "url", "categories", "images", "conferences",
    ):
        assert key in cal, f"calendar missing key {key!r}: {list(cal)}"


def test_calendar_categories_array_when_absent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """calendar.categories is an empty list (not null) when absent."""
    out = run_parse(submission_command, BASIC_CAL, tmp_path)
    cal = cast(dict[str, Any], out["calendar"])
    assert isinstance(cal.get("categories"), list)


def test_calendar_images_array_when_absent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, BASIC_CAL, tmp_path)
    cal = cast(dict[str, Any], out["calendar"])
    assert isinstance(cal.get("images"), list)


# ---------------------------------------------------------------------------
# Event object has full set of required keys
# ---------------------------------------------------------------------------


def test_event_has_all_required_keys(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Every VEVENT object surfaces the full schema key set, even empty."""
    out = run_parse(submission_command, BASIC_CAL, tmp_path)
    ev = cast(list[dict[str, Any]], out["events"])[0]
    required = {
        "uid", "dtstamp", "dtstart", "summary", "description",
        "status", "categories", "rrule", "rdate", "exdate",
        "alarms", "attendees", "raw_properties",
    }
    missing = required - set(ev.keys())
    assert not missing, f"event missing keys {missing!r}; got {list(ev)}"
