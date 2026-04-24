"""RFC 5545 §3.1 content-line folding at the 75-octet boundary.

Line folding rules (RFC 5545 §3.1):

  - Content lines SHOULD NOT be longer than 75 OCTETS (not codepoints),
    excluding the trailing CRLF.
  - A long line is split by inserting CRLF immediately followed by exactly
    one linear white-space character (SPACE or HTAB).
  - Unfolding removes the CRLF + single-whitespace pair; the whitespace
    itself is NOT part of the resulting value.
  - Implementations MUST NOT fold in the middle of a UTF-8 multi-octet
    sequence. A fold point must fall on a UTF-8 character boundary.

These tests drive the submission's `parse` subcommand with raw bytes and
verify unfolding behaviour. Byte-level precision matters — the helper
here bypasses the conftest `run_parse` normalization so we can place
CRLF+WS at exact octet positions (including near multi-byte characters).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast


def _run_parse_bytes(
    command: tuple[str, ...], ics_bytes: bytes, tmp_path: Path
) -> dict[str, Any]:
    """Run `ical parse` with raw bytes; no CRLF normalization."""
    ics_file = tmp_path / "in.ics"
    ics_file.write_bytes(ics_bytes)
    output_file = tmp_path / "out.json"
    result = subprocess.run(
        [*command, "parse", "--input", str(ics_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"ical exited {result.returncode} (expected 0)\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert output_file.exists(), "output file was not created"
    return cast(dict[str, Any], json.loads(output_file.read_text(encoding="utf-8")))


def _find_event(payload: dict[str, Any], uid: str) -> dict[str, Any]:
    events = payload.get("events")
    if not isinstance(events, list):
        raise AssertionError(
            f"output has no 'events' array (top-level keys: {list(payload)})"
        )
    for raw in cast(list[Any], events):
        if isinstance(raw, dict):
            ev = cast(dict[str, Any], raw)
            if ev.get("uid") == uid:
                return ev
    raise AssertionError(f"event with uid {uid!r} not found")


def _assemble(body_bytes: bytes) -> bytes:
    """Assemble a VCALENDAR wrapper around a pre-built VEVENT byte body.

    The caller controls the exact byte sequence of `body_bytes` (including
    any CRLF+WS fold injections); this function only adds the surrounding
    VCALENDAR/VEVENT envelope with CRLF separators.
    """
    header = (
        b"BEGIN:VCALENDAR\r\n"
        b"VERSION:2.0\r\n"
        b"PRODID:-//Test//EN\r\n"
        b"BEGIN:VEVENT\r\n"
    )
    footer = b"END:VEVENT\r\nEND:VCALENDAR\r\n"
    return header + body_bytes + footer


# ---------------------------------------------------------------------------
# Basic unfolding: CRLF + single whitespace is removed entirely
# ---------------------------------------------------------------------------


def test_unfold_crlf_space_joins_zero_space(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: CRLF + one SP is removed; if no additional
    whitespace follows in the continuation line, the fold is a zero-space
    join. `ABCD\\r\\n XYZ` unfolds to `ABCDXYZ`."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        # "Hello" + CRLF + single SP + "World" -> "HelloWorld"
        b"SUMMARY:Hello\r\n World\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "HelloWorld"


def test_unfold_crlf_tab_also_unfolds(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: The folding whitespace is SPACE *or* HTAB. CRLF+HTAB
    must also be stripped (the HTAB is NOT kept in the unfolded value)."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        b"SUMMARY:Hello\r\n\tWorld\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "HelloWorld"


def test_unfold_preserves_extra_whitespace_in_continuation(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: Exactly one whitespace character after CRLF is part
    of the fold marker and is removed. Any *additional* whitespace on the
    continuation line is literal content. `A\\r\\n  B` -> `A B` (one SP
    consumed by unfolding, one SP kept)."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        # Two spaces after CRLF: first is fold, second is content.
        b"SUMMARY:A\r\n  B\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "A B"


def test_unfold_multiple_consecutive_folds(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: Multiple CRLF+WS sequences in a row should each be
    consumed. `A\\r\\n B\\r\\n C\\r\\n D` -> `ABCD`."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        b"SUMMARY:A\r\n B\r\n C\r\n D\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "ABCD"


def test_unfold_does_not_join_lines_without_ws(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: CRLF NOT followed by whitespace terminates the
    content line; subsequent bytes start a new property. A plain CRLF
    separates the SUMMARY line from the DESCRIPTION line (no fold)."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        b"SUMMARY:First\r\n"
        b"DESCRIPTION:Second\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    ev = _find_event(out, "e1")
    assert ev.get("summary") == "First"
    assert ev.get("description") == "Second"


# ---------------------------------------------------------------------------
# UTF-8 multi-byte character boundary safety (RFC 5545 §3.1 note on multi-octet
# sequences — folds MUST NOT split a codepoint)
# ---------------------------------------------------------------------------


def test_utf8_two_byte_char_preserved_after_unfold(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: Unfolding MUST properly restore the original UTF-8
    byte sequence. A two-byte character like 'é' (0xC3 0xA9) placed
    immediately before a fold must round-trip intact."""
    # "café" then fold then "bar" -> "cafébar"
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        b"SUMMARY:caf\xc3\xa9\r\n bar\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "cafébar"


def test_utf8_three_byte_char_intact_across_fold(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A Korean syllable '한' (U+D55C) is three UTF-8 bytes: ED 95 9C.
    The character must be treated as a single codepoint across a fold
    boundary; the parser must NOT split it in the middle of its byte
    sequence."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        # "AB" + "한" + fold + "CD" -> "AB한CD"
        b"SUMMARY:AB\xed\x95\x9c\r\n CD\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "AB한CD"


def test_long_description_with_utf8_folded_at_char_boundary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.1: A producer folding a line with a multi-byte UTF-8
    character near the 75-octet limit MUST place the fold at a character
    boundary, not in the middle of the codepoint. This test supplies a
    DESCRIPTION where '한' (3 bytes) sits right at the edge of octet 75
    and the producer (correctly) folded just BEFORE the 한 to keep the
    first line at 73 octets rather than splitting the character.

    The parser's job is just to unfold and produce the expected string.
    """
    # Prefix: "DESCRIPTION:" (12 bytes) + 61 'a's = 73 bytes before the fold.
    # Then CRLF + SP + '한CD' on the continuation. Total unfolded value:
    # ('a' * 61) + '한CD'.
    prefix = b"DESCRIPTION:" + (b"a" * 61)
    assert len(prefix) == 73
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        + prefix
        + b"\r\n \xed\x95\x9cCD\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    expected = ("a" * 61) + "한CD"
    assert _find_event(out, "e1").get("description") == expected


def test_four_byte_emoji_intact_across_fold(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A 4-byte UTF-8 codepoint (U+1F600 '😀' = F0 9F 98 80) placed
    immediately before a fold must not be split. This exercises the
    widest UTF-8 sequence."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        b"SUMMARY:hi\xf0\x9f\x98\x80\r\n there\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "hi😀there"


def test_utf8_prefix_exactly_75_octets_then_fold(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A line whose first content line is exactly 75 octets (the
    RFC 5545 §3.1 maximum) followed by CRLF+SP+continuation must unfold
    correctly. No codepoint is split because the fold falls exactly on
    a character boundary."""
    # "SUMMARY:" (8 bytes) + 67 'x's = 75 octets. Then fold + "tail".
    prefix = b"SUMMARY:" + (b"x" * 67)
    assert len(prefix) == 75
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        + prefix
        + b"\r\n tail\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == ("x" * 67) + "tail"


# ---------------------------------------------------------------------------
# Line-length warning (`line_too_long`) is permitted but not asserted here —
# folding/unfolding correctness is the subject of these tests. We do assert
# that the *parse* succeeds (exit 0) regardless.
# ---------------------------------------------------------------------------


def test_folding_at_realistic_75_octet_wrap(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Realistic folded line: a long ASCII DESCRIPTION that a conformant
    producer wrapped roughly every 75 octets. Must unfold to the single
    logical value with no whitespace introduced."""
    # Craft a long description that was folded into three pieces.
    line1 = b"DESCRIPTION:" + b"A" * 63  # 12 + 63 = 75 octets
    line2 = b" " + b"B" * 74  # leading SP = fold; 74 B's as continuation
    line3 = b" " + b"C" * 20
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        + line1
        + b"\r\n"
        + line2
        + b"\r\n"
        + line3
        + b"\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    expected = ("A" * 63) + ("B" * 74) + ("C" * 20)
    assert _find_event(out, "e1").get("description") == expected


def test_short_line_without_fold_unchanged(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Sanity: a short line with no fold marker is unchanged. Protects
    against over-eager unfolders that strip leading whitespace when no
    CRLF precedes it."""
    body = (
        b"UID:e1\r\n"
        b"DTSTAMP:20260420T120000Z\r\n"
        b"DTSTART:20260305T100000Z\r\n"
        b"SUMMARY:short\r\n"
    )
    out = _run_parse_bytes(submission_command, _assemble(body), tmp_path)
    assert _find_event(out, "e1").get("summary") == "short"
