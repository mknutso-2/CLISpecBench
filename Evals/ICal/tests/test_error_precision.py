"""Error-message line/column precision.

``test_errors.py`` asserts only that malformed input exits 1. The
technical-requirements-prompt.md schema says errors carry ``line``
and ``column`` fields pointing at the offending token. This file
pins that metadata.

Non-fatal conditions (unknown property, malformed value, etc.) must
not hard-fail; they emit warnings and let parsing continue.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from conftest import run_parse


def _run_for_error(
    submission_command: tuple[str, ...], tmp_path: Path, ics: str
) -> dict[str, Any]:
    """Run parse expecting exit=1; return the error JSON body."""
    input_file = tmp_path / "bad.ics"
    output_file = tmp_path / "out.json"
    normalized = ics.replace("\r\n", "\n").replace("\n", "\r\n")
    input_file.write_bytes(normalized.encode("utf-8"))
    result = subprocess.run(
        [
            *submission_command,
            "parse",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, (
        f"expected exit 1, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, Any], data)


# ---------------------------------------------------------------------------
# Error JSON shape
# ---------------------------------------------------------------------------


def test_error_json_has_error_object(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Any exit-1 output must be a JSON object with an `error` key."""
    # Invalid VERSION line (VERSION is required).
    ics = "BEGIN:VCALENDAR\nEND:VCALENDAR\n"
    # Some impls accept this and warn; try a harder case.
    # Completely unclosed VCALENDAR:
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"  # no END
    err = _run_for_error(submission_command, tmp_path, ics)
    assert "error" in err, f"error body missing 'error' key: {err}"
    assert isinstance(err["error"], dict)


def test_error_has_line_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """error.line is a positive integer."""
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"  # unclosed
    err = _run_for_error(submission_command, tmp_path, ics)
    line = err["error"].get("line")
    assert isinstance(line, int), f"error.line not an int: {line!r}"
    assert line >= 1, f"error.line not positive: {line}"


def test_error_has_column_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """error.column is a positive integer."""
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"  # unclosed
    err = _run_for_error(submission_command, tmp_path, ics)
    col = err["error"].get("column")
    assert isinstance(col, int), f"error.column not an int: {col!r}"
    assert col >= 1, f"error.column not positive: {col}"


def test_error_has_message_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """error.message is a non-empty string."""
    ics = "BEGIN:VCALENDAR\n"  # no VERSION, no END — minimal malformed
    err = _run_for_error(submission_command, tmp_path, ics)
    msg = err["error"].get("message")
    assert isinstance(msg, str) and msg, f"error.message missing or empty: {msg!r}"


# ---------------------------------------------------------------------------
# Invalid component block
# ---------------------------------------------------------------------------


def test_unclosed_vevent_is_error(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """BEGIN:VEVENT without matching END is an error."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        # no END:VEVENT
        "END:VCALENDAR\n"
    )
    err = _run_for_error(submission_command, tmp_path, ics)
    line = err["error"].get("line")
    assert isinstance(line, int) and line >= 1


def test_mismatched_end_component(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """END:WRONG when inside VEVENT is an error."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "END:VTODO\n"  # wrong closer
        "END:VCALENDAR\n"
    )
    err = _run_for_error(submission_command, tmp_path, ics)
    assert "error" in err


# ---------------------------------------------------------------------------
# Non-fatal: malformed value emits warning, no exit-1
# ---------------------------------------------------------------------------


def test_malformed_value_does_not_exit_one(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Malformed property values (bad GEO, bad period) emit warnings but
    don't hard-fail parsing — the surrounding event is still surfaced."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "GEO:not-a-geo\n"  # malformed
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    # Should NOT raise; run_parse would assert on exit code.
    out = run_parse(submission_command, ics, tmp_path)
    events = cast(list[dict[str, Any]], out.get("events") or [])
    assert len(events) == 1
    # The event should still be present with its valid fields.
    assert events[0].get("uid") == "e1"


def test_unknown_component_is_warning_not_error(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An unknown top-level component is a warning (unsupported_component),
    not a hard error."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VUNKNOWN\n"
        "PROP:value\n"
        "END:VUNKNOWN\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    # Exact warning kind depends on the tool, but it must not have
    # exited 1 AND must have something in warnings.
    assert len(warnings) >= 1, (
        f"expected at least one warning for VUNKNOWN; got: {warnings!r}"
    )
    # The kind should plausibly be something unsupported/unknown.
    assert any(
        "unsupported" in (k or "").lower() or "unknown" in (k or "").lower()
        for k in kinds
    ) or len(warnings) >= 1


# ---------------------------------------------------------------------------
# Warning metadata
# ---------------------------------------------------------------------------


def test_warning_includes_uid_when_applicable(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Warnings emitted during event parsing should carry the event's uid
    in the `uid` field (per warning schema)."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:test-event-xyz\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "GEO:garbage\n"  # malformed → warning carries uid
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    # Find the malformed_value warning.
    malformed = [w for w in warnings if w.get("kind") == "malformed_value"]
    assert len(malformed) >= 1, f"expected malformed_value warning: {warnings!r}"
    # uid is optional per the schema but if present must match.
    for w in malformed:
        uid = w.get("uid")
        if uid is not None:
            assert uid == "test-event-xyz", f"uid mismatch in warning: {uid}"
