"""75-octet folding edge cases beyond test_line_folding_octets.py.

Closes Codex v1.0 adversarial-review finding #3. `test_line_folding_octets.py`
explicitly declined to assert `line_too_long` or invalid-fold behavior;
this file pins them.

References: RFC 5545 §3.1 — "SHOULD NOT be longer than 75 octets,
excluding the line break" and the fold/unfold rules.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast


def _parse_raw(
    submission_command: tuple[str, ...], tmp_path: Path, raw_bytes: bytes
) -> tuple[int, dict[str, Any]]:
    """Parse raw bytes (no CRLF normalization). Returns (exit_code, json)."""
    input_file = tmp_path / "in.ics"
    output_file = tmp_path / "out.json"
    input_file.write_bytes(raw_bytes)
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
    if not output_file.exists():
        return result.returncode, {}
    return result.returncode, cast(
        dict[str, Any], json.loads(output_file.read_text(encoding="utf-8"))
    )


# ---------------------------------------------------------------------------
# line_too_long warning
# ---------------------------------------------------------------------------


def test_unfolded_line_over_75_octets_warns(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A content line longer than 75 octets (not folded) SHOULD emit
    line_too_long per RFC 5545 §3.1."""
    # DESCRIPTION: is 12 chars; pad the value to reach 90 total octets.
    long_desc = "X" * 90  # 12 + 90 = 102 > 75
    ics = (
        b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//T//EN\r\n"
        b"BEGIN:VEVENT\r\n"
        b"UID:e1\r\nDTSTAMP:20260101T120000Z\r\nDTSTART:20260301T100000Z\r\n"
        b"DESCRIPTION:" + long_desc.encode() + b"\r\n"
        b"END:VEVENT\r\n"
        b"END:VCALENDAR\r\n"
    )
    code, data = _parse_raw(submission_command, tmp_path, ics)
    assert code == 0, "long unfolded lines should not hard-fail"
    warnings = cast(list[dict[str, Any]], data.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "line_too_long" in kinds, (
        f"expected line_too_long warning for 102-octet line; got {kinds!r}"
    )


def test_exactly_75_octet_line_does_not_warn(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A content line of exactly 75 octets is within spec (SHOULD NOT >75)."""
    # "DESCRIPTION:" is 12 octets; pad the value to 63 to reach 75 total.
    desc = "X" * 63
    ics = (
        b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//T//EN\r\n"
        b"BEGIN:VEVENT\r\n"
        b"UID:e1\r\nDTSTAMP:20260101T120000Z\r\nDTSTART:20260301T100000Z\r\n"
        b"DESCRIPTION:" + desc.encode() + b"\r\n"
        b"END:VEVENT\r\n"
        b"END:VCALENDAR\r\n"
    )
    code, data = _parse_raw(submission_command, tmp_path, ics)
    assert code == 0
    warnings = cast(list[dict[str, Any]], data.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "line_too_long" not in kinds, (
        "75-octet line should not warn"
    )


def test_properly_folded_long_line_does_not_warn(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A long logical line that's been properly folded into 75-octet chunks
    should not trigger line_too_long."""
    # Build a DESCRIPTION that unfolds to ~200 bytes, but each physical line
    # is folded at 74 octets + CRLF + SP.
    # Physical line 1: "DESCRIPTION:" (12) + 63 X's = 75 octets → fits.
    # Continuation: " " (1) + 74 X's = 75 octets → fits.
    # Continuation: " " (1) + remaining
    ics = (
        b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//T//EN\r\n"
        b"BEGIN:VEVENT\r\n"
        b"UID:e1\r\nDTSTAMP:20260101T120000Z\r\nDTSTART:20260301T100000Z\r\n"
        b"DESCRIPTION:" + b"X" * 63 + b"\r\n"
        b" " + b"X" * 74 + b"\r\n"
        b" " + b"X" * 60 + b"\r\n"
        b"END:VEVENT\r\n"
        b"END:VCALENDAR\r\n"
    )
    code, data = _parse_raw(submission_command, tmp_path, ics)
    assert code == 0
    warnings = cast(list[dict[str, Any]], data.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "line_too_long" not in kinds


# ---------------------------------------------------------------------------
# Fold inside TEXT escape: escape should still apply after unfolding
# ---------------------------------------------------------------------------


def test_fold_before_escape_sequence(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A fold that splits "\\" and "n" of a \\n escape should still produce
    a newline after unfolding (the unfolder removes the CRLF+SP before the
    escape processor runs)."""
    # DESCRIPTION:a\CRLF SP n → unfold to "a\n" → TEXT escape → "a" + LF
    ics = (
        b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//T//EN\r\n"
        b"BEGIN:VEVENT\r\n"
        b"UID:e1\r\nDTSTAMP:20260101T120000Z\r\nDTSTART:20260301T100000Z\r\n"
        b"DESCRIPTION:line1\\\r\n n" + b"line2\r\n"
        b"END:VEVENT\r\n"
        b"END:VCALENDAR\r\n"
    )
    code, data = _parse_raw(submission_command, tmp_path, ics)
    assert code == 0
    events = cast(list[dict[str, Any]], data.get("events") or [])
    assert len(events) == 1
    desc = events[0].get("description", "")
    # After unfold: "line1\nline2" (literal backslash-n). After TEXT
    # escape: "line1" + LF + "line2". Pin the exact "\n"-separated
    # output so that a parser which emitted literal backslash-n
    # (no escape processing) would fail this test.
    assert desc == "line1\nline2", (
        f"expected unfold+escape to produce 'line1\\nline2' with real LF; "
        f"got {desc!r}"
    )


# ---------------------------------------------------------------------------
# Multi-byte UTF-8 safety
# ---------------------------------------------------------------------------


def test_multibyte_char_straddling_75_octet_boundary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A 3-byte UTF-8 character that would straddle the 75-octet boundary
    must not be split by the folder. Producers MUST fold at a character
    boundary. We test that a well-folded file with a straddling char at
    the boundary parses without corruption."""
    # Place 한 (U+D55C, 0xED 0x95 0x9C) around octet 73-75.
    # DESCRIPTION: (12) + 61 a's (61) = 73 octets; then 한 would be 74-76.
    # Producer's job: fold after the 73 a's (or before the 한).
    prefix = b"a" * 61
    korean = "한".encode()  # 3 bytes
    # Fold AT octet 74 (after 'a' #61), continuation starts with SP + 한.
    ics = (
        b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//T//EN\r\n"
        b"BEGIN:VEVENT\r\n"
        b"UID:e1\r\nDTSTAMP:20260101T120000Z\r\nDTSTART:20260301T100000Z\r\n"
        b"DESCRIPTION:" + prefix + b"\r\n "
        + korean + b"\r\n"
        b"END:VEVENT\r\n"
        b"END:VCALENDAR\r\n"
    )
    code, data = _parse_raw(submission_command, tmp_path, ics)
    assert code == 0
    events = cast(list[dict[str, Any]], data.get("events") or [])
    desc = events[0].get("description", "")
    assert "한" in desc, f"multi-byte char not preserved; got {desc!r}"
