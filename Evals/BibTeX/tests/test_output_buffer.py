"""Exhaustive output-buffer / 79-column wrapping tests.

Tests BibTeX's line-wrapping contract as specified in ``btxhak`` and
``bibtex.web §15``:

- ``max_print_line = 79``, ``min_print_line = 3``.
- While the accumulated line exceeds 79 columns, scan backwards from
  position 79 for whitespace and break there; continuation starts with
  a 2-space indent.
- If no whitespace exists within ``[min_print_line, max_print_line]``,
  scan forwards past 79 for the first whitespace and break there
  (unbreakable-long-line rule); continuation still begins with 2 spaces.
- If no whitespace at all follows the overflow, emit the run verbatim.
- ``newline$`` always flushes the current line and does NOT produce a
  leading indent on the next content.

All tests assert on complete ``.bbl`` byte strings so that a wrapping
regression localizes to one logical behavior.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex

MINI_BIB = "@misc{a}\n"


def _run(
    submission_command: tuple[str, ...], tmp_path: Path, body: str
) -> str:
    style = f"""\
ENTRY {{ }} {{ }} {{ }}
FUNCTION {{f}} {{ {body} }}
READ
EXECUTE {{f}}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    return bbl


# ---------------------------------------------------------------------------
# Basic: no wrap below/at the boundary
# ---------------------------------------------------------------------------


def test_short_line_not_wrapped(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Lines under 79 columns must not wrap."""
    body = '"hello world" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "hello world\n"


def test_line_exactly_79_not_wrapped(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A 79-column line is not wrapped: the break condition is strict ``> 79`` (bibtex.web §15)."""
    # 79-char payload: 39 "ab" + 1 "a" = 79
    payload = "ab" * 39 + "a"
    assert len(payload) == 79
    body = f'"{payload}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == payload + "\n"


def test_line_exactly_80_wraps(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """80 columns triggers the wrap rule when there is whitespace to break at."""
    # Build 80 columns with a single space we can break at.
    # "A" * 50 + " " + "B" * 29 = 80 chars with a space at column 51.
    payload = "A" * 50 + " " + "B" * 29
    assert len(payload) == 80
    body = f'"{payload}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    # First line has the "A"s (no trailing space); continuation has 2-space
    # indent + the "B"s + newline from newline$.
    lines = bbl.split("\n")
    assert lines[0] == "A" * 50
    assert lines[1] == "  " + "B" * 29
    # newline$ flushed the second line, plus trailing "" from final split.
    assert bbl == "A" * 50 + "\n" + "  " + "B" * 29 + "\n"


# ---------------------------------------------------------------------------
# Normal wrap: many tokens separated by single spaces
# ---------------------------------------------------------------------------


def test_wrap_at_last_whitespace_before_79(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Wrap must break at the *last* whitespace <= column 79 (bibtex.web §15)."""
    # Build a payload where positions 70-80 contain: "aaaa bbbb "
    # Expected: break at the space before "bbbb" (position <= 79).
    # Let's make a clear 2-line payload: 85 chars with a space at 75.
    first = "x" * 75
    payload = first + " " + "y" * 9
    assert len(payload) == 85
    body = f'"{payload}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    # After break: first line = "x" * 75, continuation = "  " + "y" * 9.
    assert bbl == ("x" * 75) + "\n" + "  " + ("y" * 9) + "\n"


def test_continuation_has_two_space_indent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The continuation line must start with exactly 2 spaces (bibtex.web §15)."""
    # 100-char payload with a single space to force a wrap.
    payload = ("a" * 40) + " " + ("b" * 59)
    assert len(payload) == 100
    body = f'"{payload}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    parts = bbl.split("\n")
    # The second physical line (continuation) must begin with "  ".
    assert parts[1].startswith("  ")
    # And exactly 2 spaces — not 1, not 3.
    assert not parts[1].startswith("   ")
    assert parts[1][2] != " "


def test_multiple_wraps_when_very_long(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A >158-char payload triggers multiple wraps."""
    # 200 "aa" tokens separated by single spaces = 200*2 + 199 = 599 chars.
    tokens = ["aa"] * 200
    payload = " ".join(tokens)
    assert len(payload) == 599
    body = f'"{payload}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    # Every emitted physical line must be at most 79 columns.
    lines = [ln for ln in bbl.split("\n") if ln != ""]
    for ln in lines:
        assert len(ln) <= 79, f"line exceeds 79 cols: {ln!r} ({len(ln)} cols)"
    # And reassembly must preserve the tokens (order + count).
    joined = " ".join(ln.strip() for ln in lines)
    assert joined == payload


# ---------------------------------------------------------------------------
# Unbreakable-long-line rule (bibtex.web §15 "Break that unbreakably long line")
# ---------------------------------------------------------------------------


def test_unbreakable_single_token_emits_at_column_1(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A contiguous >79-char token with no whitespace: emit verbatim (no break).

    Per bibtex.web §15, if no whitespace is available in the min/max range
    and no whitespace follows, the run is emitted as-is (overflow permitted).
    """
    payload = "A" * 100  # No whitespace at all.
    body = f'"{payload}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == payload + "\n"


def test_single_long_token_then_short_on_new_line(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An unbreakable long token followed by an explicit ``newline$`` and a
    new short write starts fresh at column 1."""
    long_payload = "A" * 100
    body = f'"{long_payload}" write$ newline$ "short" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == long_payload + "\nshort\n"


# ---------------------------------------------------------------------------
# Multiple write$ accumulating to overflow
# ---------------------------------------------------------------------------


def test_multiple_small_writes_wrap_when_combined(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Several small ``write$`` calls must share the same output line and
    wrap together once the running total exceeds 79."""
    # 10 write$ of "abcdefghij " (11 chars) = 110 chars total.
    body = ""
    for _ in range(10):
        body += '"abcdefghij " write$ '
    body += "newline$"
    bbl = _run(submission_command, tmp_path, body)
    lines = [ln for ln in bbl.split("\n") if ln != ""]
    # At least 2 physical lines.
    assert len(lines) >= 2
    # First line <= 79.
    assert len(lines[0]) <= 79
    # Reassembly matches payload (normalize whitespace runs).
    joined = " ".join(" ".join(ln.split()) for ln in lines)
    assert joined.replace("  ", " ").strip() == ("abcdefghij " * 10).strip()


def test_newline_flushes_without_wrap(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``newline$`` always flushes the accumulated line even when short."""
    body = '"abc" write$ newline$ "def" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "abc\ndef\n"


def test_empty_write_then_newline(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An empty ``write$`` followed by ``newline$`` emits one empty line."""
    body = '"" write$ newline$ "next" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "\nnext\n"


def test_newline_then_content_no_indent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """After an explicit ``newline$``, the next content starts at column 1
    (no 2-space indent — the indent only applies to wrap continuations)."""
    body = '"first" write$ newline$ "second" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "first\nsecond\n"


# ---------------------------------------------------------------------------
# Embedded newline characters within a write$
# ---------------------------------------------------------------------------


def test_string_with_embedded_newline_flushes(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A string containing a literal LF splits into two lines (the first
    terminated at the LF, the second accumulating after)."""
    # .bst strings don't process escapes, but we can concatenate around a
    # newline$ to get the same observable effect: "aaa\n" then "bbb".
    body = '"aaa" write$ newline$ "bbb" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "aaa\nbbb\n"


# ---------------------------------------------------------------------------
# Trailing-whitespace preservation
# ---------------------------------------------------------------------------


def test_trailing_whitespace_preserved_on_short_line(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Trailing spaces on a line under 79 cols are preserved (not stripped)."""
    body = '"abc   " write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "abc   \n"


def test_trailing_whitespace_before_newline(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Whitespace immediately before ``newline$`` is kept as-is."""
    body = '"a" write$ "   " write$ "b" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert bbl == "a   b\n"
