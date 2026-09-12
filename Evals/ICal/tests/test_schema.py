"""Top-level JSON schema shape gate. Isolated from behavioral tests."""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, run_parse, wrap_event

SIMPLE = wrap_event("UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nSUMMARY:x\n")


def test_parse_top_level_keys(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = run_parse(submission_command, SIMPLE, tmp_path)
    # Tech-reqs declares every key in this set as MANDATORY on parse
    # output — including `availabilities` (the RFC 7953 VAVAILABILITY
    # top-level array, empty when no VAVAILABILITY components were
    # parsed). Keep this as a subset-check so an implementation that
    # adds additional extension keys (reserved x-names etc.) isn't
    # penalized.
    required = {
        "calendar",
        "events",
        "todos",
        "journals",
        "freebusy",
        "timezones",
        "availabilities",
        "warnings",
    }
    assert required.issubset(set(out.keys()))


def test_parse_top_level_value_types(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # The contract mandates value types; this used to duplicate the presence
    # gate without testing any independent schema requirement.
    out = run_parse(submission_command, SIMPLE, tmp_path)
    assert isinstance(out.get("calendar"), dict)
    for key in (
        "events",
        "todos",
        "journals",
        "freebusy",
        "timezones",
        "availabilities",
        "warnings",
    ):
        assert isinstance(out.get(key), list), f"{key} must be an array"


def test_expand_top_level_keys(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = run_expand(
        submission_command, SIMPLE, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    assert {"occurrences", "warnings"}.issubset(out)


def test_expand_top_level_value_types(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Independently score array types, not a second copy of key presence.
    out = run_expand(
        submission_command, SIMPLE, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    assert isinstance(out.get("occurrences"), list)
    assert isinstance(out.get("warnings"), list)


def test_calendar_has_prodid_version(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = run_parse(submission_command, SIMPLE, tmp_path)
    cal = out.get("calendar")
    assert isinstance(cal, dict)
    assert "prodid" in cal and "version" in cal
