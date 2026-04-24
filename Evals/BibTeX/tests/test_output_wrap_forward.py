"""bibtex.web §15 forward-scan wrap rule.

Per *Designing BibTeX Styles* and the bibtex.web output-buffer logic:

  * BibTeX attempts to break an output line at the last whitespace
    in columns ``[min_print_line, max_print_line]`` = ``[3, 79]``.
  * If there is NO whitespace in that window but there IS a
    whitespace later in the line, BibTeX scans **forward** past
    column 79 to the first whitespace and breaks there. The
    continuation is indented with two spaces.
  * If there is no whitespace anywhere, the line is emitted
    verbatim (no wrap possible).

The v1.0 reference implementation only implemented the backward-
scan case, so any line without whitespace in [3, 79] kept growing.
This file pins the §15 forward-scan rule in place.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex

MINI_BIB = '@misc{a}\n'


def _run(submission_command: tuple[str, ...], tmp_path: Path, body: str) -> str:
    style = "ENTRY { } { } { }\n" + f"FUNCTION {{f}} {{ {body} }}\n" + "READ\nEXECUTE {f}\n"
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    return bbl


# ---------------------------------------------------------------------------
# Forward-scan case: long token at start, whitespace later.
# ---------------------------------------------------------------------------


def test_forward_scan_wraps_at_first_whitespace_past_79(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A 90-char unbroken-by-leading word followed by ' B': break is at the
    space (col 91), NOT an arbitrary truncation.

    The continuation starts with two-space indent per bibtex.web §15.
    """
    long_word = "x" * 90
    body = f'"{long_word} B" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    lines = bbl.split("\n")
    # First emitted line is the long word (possibly overflowing 79 cols).
    # Second emitted line is the "  B" continuation.
    non_empty = [ln for ln in lines if ln]
    assert len(non_empty) >= 2, f"expected wrap, got {non_empty!r}"
    assert non_empty[0] == long_word, (
        f"first line should be the unbreakable word, got {non_empty[0]!r}"
    )
    assert non_empty[1] == "  B", (
        f"continuation must be two-space-indented 'B', got {non_empty[1]!r}"
    )


def test_forward_scan_preserves_content_order(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Reassembling the wrapped lines returns the original content."""
    long_word = "y" * 100
    body = f'"{long_word} end" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    # Strip the 2-space continuation indent and join. The original was
    # "<long> end", so after normalizing wrap we should see those two tokens.
    normalized = " ".join(
        part.strip() for part in bbl.split("\n") if part.strip()
    )
    assert normalized == f"{long_word} end"


def test_forward_scan_multiple_spaces_picks_first(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When multiple whitespaces exist past col 79, break at the FIRST one."""
    long_word = "z" * 85
    # After col 85 we have "z A B C D" — the first space is between "z" and "A".
    body = f'"{long_word} A B C D" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    non_empty = [ln for ln in bbl.split("\n") if ln]
    # The first line is the long word (breaks at the first space past 79).
    assert non_empty[0] == long_word
    # The remainder is "  A B C D" (two-space indent + rest).
    remainder = " ".join(non_empty[1:])
    assert "A B C D" in remainder, (
        f"continuation should contain 'A B C D', got {remainder!r}"
    )


# ---------------------------------------------------------------------------
# Backward-scan still works (regression guard).
# ---------------------------------------------------------------------------


def test_backward_scan_still_wraps_at_70(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A line with whitespace at col 70 still wraps there (not forward-scan)."""
    prefix = "a" * 65
    # Total structure: "<65 a's> END OF LINE" — space at col 66.
    body = f'"{prefix} END OF LINE SOMETHING LONGER TO EXCEED 79" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    lines = [ln for ln in bbl.split("\n") if ln]
    # The first line must be <= 79 chars since a break point was reachable.
    assert len(lines[0]) <= 79, f"first line too long: {len(lines[0])}"


# ---------------------------------------------------------------------------
# Degenerate case: no whitespace anywhere → verbatim emission.
# ---------------------------------------------------------------------------


def test_no_whitespace_anywhere_emits_verbatim(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """If a line has NO whitespace, BibTeX emits it verbatim (overflow)."""
    long_word = "q" * 150
    body = f'"{long_word}" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    assert long_word in bbl, "long unbreakable word must be emitted"


# ---------------------------------------------------------------------------
# Boundary cases.
# ---------------------------------------------------------------------------


def test_whitespace_exactly_at_79_breaks_there(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Space at exactly column 79 is a valid break point (backward scan takes it)."""
    # Position 79 means 78 chars of content then a space at index 78 (0-based).
    prefix = "a" * 78
    body = f'"{prefix} TRAILER" write$ newline$'
    bbl = _run(submission_command, tmp_path, body)
    lines = [ln for ln in bbl.split("\n") if ln]
    # First line should be the 78 a's, no trailer
    assert lines[0] == prefix
    assert lines[1].strip() == "TRAILER"
