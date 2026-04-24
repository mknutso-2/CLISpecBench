"""Tests for the .bst style-file language: top-level commands and built-ins."""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex

MINI_BIB = '@article{a, author = "Smith", title = "TA", year = 2024}\n'


def _run_with_body(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    bib: str = MINI_BIB,
    cites: list[str] | None = None,
) -> str:
    """Run a .bst containing a single ITERATE-able function called `f` with
    the given body. Returns the .bbl text."""
    style = f"""\
ENTRY {{ author title year }} {{ }} {{ }}
FUNCTION {{f}} {{ {body} }}
READ
ITERATE {{f}}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, cites or ["a"], tmp_path)
    return bbl


def _run_with_execute(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    bib: str = MINI_BIB,
) -> str:
    """Run EXECUTE on a function body (no current entry)."""
    style = f"""\
ENTRY {{ author }} {{ }} {{ }}
FUNCTION {{f}} {{ {body} }}
READ
EXECUTE {{f}}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    return bbl


# --- Arithmetic / comparison ---


def test_add(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#3 #4 + int.to.str$ write$")
    assert bbl.strip() == "7"


def test_sub(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#10 #3 - int.to.str$ write$")
    assert bbl.strip() == "7"


def test_greater_than(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#5 #3 > int.to.str$ write$")
    assert bbl.strip() == "1"


def test_less_than(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#5 #3 < int.to.str$ write$")
    assert bbl.strip() == "0"


def test_equal_int(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#5 #5 = int.to.str$ write$")
    assert bbl.strip() == "1"


def test_equal_string(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"foo" "foo" = int.to.str$ write$')
    assert bbl.strip() == "1"


def test_string_concat(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"foo" "bar" * write$')
    assert bbl.strip() == "foobar"


# --- Stack ops ---


def test_pop(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"keep" "drop" pop$ write$')
    assert bbl.strip() == "keep"


def test_swap(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"A" "B" swap$ write$ write$')
    assert bbl.strip() == "AB"


def test_duplicate(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"X" duplicate$ write$ write$')
    assert bbl.strip() == "XX"


# --- Control flow ---


def test_if_true_branch(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '#1 { "yes" write$ } { "no" write$ } if$')
    assert bbl.strip() == "yes"


def test_if_false_branch(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '#0 { "yes" write$ } { "no" write$ } if$')
    assert bbl.strip() == "no"


def test_while_loop(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { i } { }
FUNCTION {f}
{ #3 'i :=
  { i #0 > }
    { i int.to.str$ write$ i #1 - 'i := }
  while$ }
READ
ITERATE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "321"


def test_skip_is_noop(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"A" skip$ write$')
    assert bbl.strip() == "A"


# --- String built-ins ---


def test_add_period(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"hello" add.period$ write$')
    assert bbl.strip() == "hello."


def test_add_period_preserves_final_punct(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"hi?" add.period$ write$')
    assert bbl.strip() == "hi?"


def test_chr_to_int(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"A" chr.to.int$ int.to.str$ write$')
    assert bbl.strip() == "65"


def test_int_to_chr(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#66 int.to.chr$ write$")
    assert bbl.strip() == "B"


def test_int_to_str(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "#42 int.to.str$ write$")
    assert bbl.strip() == "42"


def test_substring(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"abcdefg" #2 #3 substring$ write$')
    assert bbl.strip() == "bcd"


def test_text_length(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"abcde" text.length$ int.to.str$ write$')
    assert bbl.strip() == "5"


def test_text_length_brace_group_counts_contents(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Brace contents that are not a `\foo` control sequence count individually:
    # "{abc}def" is 6 text characters.
    bbl = _run_with_execute(
        submission_command, tmp_path, '"{abc}def" text.length$ int.to.str$ write$'
    )
    assert bbl.strip() == "6"


def test_text_prefix(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"hello world" #5 text.prefix$ write$')
    assert bbl.strip() == "hello"


def test_change_case_lower(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"Hello World" "l" change.case$ write$')
    assert bbl.strip() == "hello world"


def test_change_case_upper(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"Hello World" "u" change.case$ write$')
    assert bbl.strip() == "HELLO WORLD"


def test_change_case_title(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"HELLO WORLD" "t" change.case$ write$')
    assert bbl.strip() == "Hello world"


def test_change_case_protects_braces(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # {USA} is brace-protected; its interior is preserved.
    bbl = _run_with_execute(
        submission_command, tmp_path, '"The {USA} story" "l" change.case$ write$'
    )
    assert bbl.strip() == "the {USA} story"


def test_purify_strips_punctuation(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, '"Hello, World!" purify$ write$')
    assert bbl.strip() == "Hello World"


def test_quote_pushes_double_quote(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_execute(submission_command, tmp_path, "quote$ write$")
    assert bbl.strip() == '"'


# --- Entry-scope built-ins ---


def test_cite_in_iterate(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_body(submission_command, tmp_path, "cite$ write$")
    assert bbl.strip() == "a"


def test_type_in_iterate(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_body(submission_command, tmp_path, "type$ write$")
    assert bbl.strip() == "article"


def test_empty_on_missing_field(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_body(submission_command, tmp_path, "journal empty$ int.to.str$ write$")
    assert bbl.strip() == "1"


def test_empty_on_nonempty_string(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_body(submission_command, tmp_path, "author empty$ int.to.str$ write$")
    assert bbl.strip() == "0"


def test_missing_on_missing(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _run_with_body(submission_command, tmp_path, "journal missing$ int.to.str$ write$")
    assert bbl.strip() == "1"


def test_preamble(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@preamble{"hi"}\n@article{a, title = "T"}\n'
    style = """\
ENTRY { } { } { }
FUNCTION {f} { preamble$ write$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "hi"


# --- Variables and :=  ---


def test_assign_global_integer(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
INTEGERS { counter }
FUNCTION {f}
{ #42 'counter :=
  counter int.to.str$ write$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "42"


def test_assign_global_string(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
STRINGS { label }
FUNCTION {f}
{ "hello" 'label :=
  label write$ }
READ
EXECUTE {f}
"""
    bib = "@misc{a}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "hello"


# --- num.names$ / format.name$ ---


def test_num_names(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { author } { } { }
FUNCTION {f} { author num.names$ int.to.str$ write$ }
READ
ITERATE {f}
"""
    bib = '@article{a, author = "Smith and Jones and Doe"}\n'
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "3"


def test_format_name_first_last(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { author } { } { }
FUNCTION {f}
{ author #1 "{ll}" format.name$ write$ newline$
  author #1 "{ff}" format.name$ write$ }
READ
ITERATE {f}
"""
    bib = '@article{a, author = "John Smith"}\n'
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    lines = bbl.strip().split("\n")
    assert lines[0] == "Smith"
    assert lines[1] == "John"


# --- SORT ---


def test_sort_by_sort_key(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { author } { } { sort.key$ }
FUNCTION {init.key} { author 'sort.key$ := }
FUNCTION {dump} { cite$ write$ newline$ }
READ
ITERATE {init.key}
SORT
ITERATE {dump}
"""
    bib = """
@article{c, author = "Charlie"}
@article{a, author = "Alice"}
@article{b, author = "Bob"}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["c", "a", "b"], tmp_path)
    assert bbl.strip().split("\n") == ["a", "b", "c"]


# --- REVERSE ---


def test_reverse_iterates_backward(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
REVERSE {f}
"""
    bib = "@misc{x}\n@misc{y}\n@misc{z}\n"
    bbl, _ = run_bibtex(submission_command, bib, style, ["x", "y", "z"], tmp_path)
    assert bbl.strip().split("\n") == ["z", "y", "x"]


# --- Log output ---


def test_log_records_iterations(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    bib = "@misc{a}\n@misc{b}\n"
    _, log = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path, with_log=True)
    assert log is not None
    assert log["entries_read"] == 2
    assert log["iterations"] == 1


def test_log_records_missing_cite(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    bib = "@misc{a}\n"
    _, log = run_bibtex(submission_command, bib, style, ["a", "ghost"], tmp_path, with_log=True)
    assert log is not None
    assert "ghost" in log["entries_cited_missing"]


def test_log_records_macros(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
MACRO {jan} {"January"}
MACRO {feb} {"February"}
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""
    bib = "@misc{a}\n"
    _, log = run_bibtex(submission_command, bib, style, ["a"], tmp_path, with_log=True)
    assert log is not None
    assert "jan" in log["macros_defined"]
    assert "feb" in log["macros_defined"]
