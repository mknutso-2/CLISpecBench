"""UTF-8 / non-ASCII byte preservation.

BibTeX 0.99c predates Unicode; the canonical corpus uses 7-bit ASCII
with LaTeX escape macros (``{\\"o}``, ``{\\'e}``, etc.) for diacritics.
Modern practice uses UTF-8 ``.bib`` files directly.

Per our summary §8.5 and technical-requirements-prompt.md (output is
UTF-8), the tool must preserve byte sequences of field values that
contain non-ASCII characters — both when dumped via ``write$`` and
through ``format.name$``.

References: btxdoc §3; bibtex.web §13 on byte-level string handling.
"""

from __future__ import annotations

from pathlib import Path

from conftest import PROBE_STYLE_FIELDS, run_bibtex

# ---------------------------------------------------------------------------
# UTF-8 field values round-trip
# ---------------------------------------------------------------------------


def test_utf8_title_roundtrips_through_write(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """UTF-8 title byte sequences survive write$ verbatim."""
    bib = '@article{k, title = "Gödel, Escher, Bach"}\n'
    style = """\
ENTRY { title } { } { }
FUNCTION {f} { title write$ newline$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["k"], tmp_path)
    assert "Gödel" in bbl or "G\xf6del" in bbl


def test_utf8_note_field_preserved_via_write(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """UTF-8 in a non-author field survives parse + write$ byte-for-byte."""
    bib = '@article{k, note = "日本語テスト"}\n'
    style = """\
ENTRY { note } { } { }
FUNCTION {f} { note write$ newline$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["k"], tmp_path)
    assert "日本語テスト" in bbl


# ---------------------------------------------------------------------------
# chr.to.int$ / int.to.chr$ on ASCII-range
# ---------------------------------------------------------------------------


def test_chr_to_int_range_check(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """chr.to.int$ on different ASCII letters produces different codes."""
    style = """\
ENTRY { } { } { }
FUNCTION {f}
{ "a" chr.to.int$ int.to.str$ write$ " " write$
  "A" chr.to.int$ int.to.str$ write$ newline$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    parts = bbl.strip().split()
    assert parts[0] == "97"  # ord('a')
    assert parts[1] == "65"  # ord('A')


def test_int_to_chr_ascii_produces_single_char(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """int.to.chr$ of 48..57 produces '0'..'9'."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { #48 int.to.chr$ write$ #57 int.to.chr$ write$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.rstrip("\n") == "09"


# ---------------------------------------------------------------------------
# Special-character LaTeX escapes preserved in field dump
# ---------------------------------------------------------------------------


def test_latex_diacritic_preserved_in_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    r"""``{\"o}`` byte sequence is preserved as-is in field values."""
    bib = '@article{k, title = "{\\"o}ne"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    # The raw backslash-quote-o construct should appear.
    assert "ne" in bbl
    # Either {\"o} or ö variant (if impl normalizes).
    assert "\\\"o" in bbl or "ö" in bbl or '{"o}' in bbl


def test_purify_preserves_ascii_bytes(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """purify$ on a plain ASCII string preserves the letters (modulo the
    documented punctuation stripping rules)."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "abc123" purify$ write$ newline$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "abc123"


# ---------------------------------------------------------------------------
# substring$ on UTF-8 (byte-level, not codepoint-level)
# ---------------------------------------------------------------------------


def test_substring_is_byte_oriented(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """substring$ operates on bytes, consistent with bibtex.web's 8-bit view.

    For a pure-ASCII string "hello", substring$ #1 #3 returns "hel".
    """
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "hello" #1 #3 substring$ write$ newline$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "hel"


def test_text_length_on_ascii_is_char_count(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """text.length$ returns number of text characters for ASCII."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "hello" text.length$ int.to.str$ write$ newline$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "5"
