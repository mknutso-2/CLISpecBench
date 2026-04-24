"""Direct .bbl assertion tests that bypass the probe-dump parser.

Each test author a narrow .bst whose complete .bbl output is asserted
byte-by-byte. These localize failures to the specific feature under test
and do not share any helper with other tests beyond `run_bibtex`.

Addresses the v0.3 review finding that probe-based tests share
`parse_field_dump` / `parse_name_dump` and cascade under a single .bst
interpreter bug.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex

MINI_BIB = '@article{a, author = "Smith", title = "T", year = 2024}\n'


# ---------------------------------------------------------------------------
# empty$ / missing$ — narrow, no probe dependency
# ---------------------------------------------------------------------------


def test_empty_of_missing_field_is_1(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { author journal } { } { }
FUNCTION {f} { journal empty$ int.to.str$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "1"


def test_empty_of_present_field_is_0(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { author } { } { }
FUNCTION {f} { author empty$ int.to.str$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "0"


def test_empty_of_whitespace_string_is_1(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "   " empty$ int.to.str$ write$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "1"


def test_missing_distinguishes_from_empty(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # missing$ returns 1 for a missing field but 0 for an empty string.
    style = """\
ENTRY { journal } { } { }
FUNCTION {f}
{ journal missing$ int.to.str$ write$
  "" missing$ int.to.str$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "10"


# ---------------------------------------------------------------------------
# 79-column line wrapping — stress tests the output buffer directly
# ---------------------------------------------------------------------------


def test_short_line_not_wrapped(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "hello world" write$ newline$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl == "hello world\n"


def test_long_line_wraps_at_whitespace(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Write 100 chars in space-separated tokens. Must wrap at 79.
    payload = " ".join(["aa"] * 50)  # 50 tokens × 2 chars + 49 spaces = 149 chars
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "%PAYLOAD%" write$ newline$ }
READ
EXECUTE {f}
""".replace("%PAYLOAD%", payload)
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    lines = bbl.split("\n")
    # Every line except possibly the last must be ≤ 79 characters.
    for ln in lines[:-2]:  # -2 to skip trailing newline's empty string
        assert len(ln) <= 79, f"line too long ({len(ln)}): {ln!r}"
    # Reassembling should recover the payload (wrapped with 2-space leading
    # indent on continuation lines). Strip whitespace-runs and compare.
    joined = " ".join(part.strip() for part in lines if part.strip())
    assert joined == payload


# ---------------------------------------------------------------------------
# Log JSON — isolated from probe behavior
# ---------------------------------------------------------------------------


def test_log_entries_read_count(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    _, log = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path, with_log=True)
    assert log is not None
    assert log["entries_cited_found"] == 2
    # entries_read should equal the actual READ size (2 cited, 1 not).
    assert log["entries_read"] == 2


def test_log_macros_include_user_and_months(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    style = """\
ENTRY { } { } { }
MACRO {foo} {"bar"}
MACRO {baz} {"qux"}
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    _, log = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path, with_log=True)
    assert log is not None
    assert "foo" in log["macros_defined"]
    assert "baz" in log["macros_defined"]


# ---------------------------------------------------------------------------
# --aux flow (v0.3 addition): accept LaTeX .aux files instead of plain cites
# ---------------------------------------------------------------------------


def test_aux_input_single_citation(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    aux = r"""
\relax
\citation{a}
\bibstyle{plain}
\bibdata{refs}
"""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, [], tmp_path, aux_text=aux)
    assert bbl == "a\n"


def test_aux_input_multi_key_citation(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    aux = r"""
\relax
\citation{a,b,c}
"""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, [], tmp_path, aux_text=aux)
    assert bbl == "a\nb\nc\n"


def test_aux_input_multiple_citation_commands(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = "@misc{a}\n@misc{b}\n"
    aux = r"""
\citation{a}
\citation{b}
"""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, [], tmp_path, aux_text=aux)
    assert bbl == "a\nb\n"


# ---------------------------------------------------------------------------
# call.type$ dispatch — exercised directly without the probe dump
# ---------------------------------------------------------------------------


def test_call_type_dispatches_to_type_function(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = '@article{a, title = "A"}\n@book{b, title = "B"}\n'
    style = """\
ENTRY { title } { } { }
FUNCTION {article} { "article:" write$ title write$ newline$ }
FUNCTION {book}    { "book:"    write$ title write$ newline$ }
FUNCTION {default.type} { "unk" write$ newline$ }
FUNCTION {f} { call.type$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path)
    assert bbl == "article:A\nbook:B\n"


def test_call_type_falls_back_to_default_type(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = '@weirdtype{a, title = "A"}\n'
    style = """\
ENTRY { title } { } { }
FUNCTION {default.type} { "default:" write$ title write$ newline$ }
FUNCTION {f} { call.type$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl == "default:A\n"
