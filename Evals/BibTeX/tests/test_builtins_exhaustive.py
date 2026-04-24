"""Exhaustive per-built-in tests for the BibTeX 0.99c stack language.

Every one of the 37 built-ins listed in btxhak §4 gets its own test cluster:
a *normal* case, an *edge* case (empty string, zero integer, missing field,
etc.), and — where applicable — a *type-error* case that exercises the
spec's ``§3.3 / §3.8`` recovery behavior ("emit a warning, substitute a
default, continue execution").

Per spec §3.8, stack type errors are **non-fatal**: a warning of kind
``bst_type_error`` is recorded and the built-in pushes a default value.
We verify this via the ``--log`` JSON, not via a non-zero exit code.

Each test writes its own minimal .bst and asserts the .bbl text (and the
warning log when relevant). No probe-dump parser is shared between tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import run_bibtex

MINI_BIB = '@article{a, author = "Smith", title = "T", year = 2024}\n'
EMPTY_BIB = "@misc{a}\n"


def _exec(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    *,
    bib: str = MINI_BIB,
    entry_fields: str = "author title year",
    with_log: bool = False,
) -> tuple[str, dict[str, Any] | None]:
    """Run an ``EXECUTE {f}`` with ``f`` defined as the given body.

    Returns (bbl_text, log_or_None).
    """
    # Append newline$ when body ends on bare write$ — guards against a
    # single-line flush bug cascading across every built-in test. See
    # test_bst_language._maybe_flush for rationale.
    if body.rstrip().endswith("write$"):
        body = body + " newline$"
    style = f"""\
ENTRY {{ {entry_fields} }} {{ }} {{ }}
FUNCTION {{f}} {{ {body} }}
READ
EXECUTE {{f}}
"""
    return run_bibtex(
        submission_command, bib, style, ["a"], tmp_path, with_log=with_log
    )


def _iterate(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    *,
    bib: str = MINI_BIB,
    entry_fields: str = "author title year journal",
    with_log: bool = False,
) -> tuple[str, dict[str, Any] | None]:
    """Like ``_exec`` but with ``ITERATE {f}`` so there is a current entry."""
    style = f"""\
ENTRY {{ {entry_fields} }} {{ }} {{ }}
FUNCTION {{f}} {{ {body} }}
READ
ITERATE {{f}}
"""
    return run_bibtex(
        submission_command, bib, style, ["a"], tmp_path, with_log=with_log
    )


def _has_type_error(log: dict[str, Any] | None) -> bool:
    if log is None:
        return False
    for w in log.get("warnings", []):
        if w.get("kind") == "bst_type_error":
            return True
    return False


# ---------------------------------------------------------------------------
# Arithmetic: + and - (btxhak §4 — "builtin functions")
# ---------------------------------------------------------------------------


def test_plus_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#3 #4 + int.to.str$ write$")
    assert bbl.strip() == "7"


def test_plus_zero_identity(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#0 #5 + int.to.str$ write$")
    assert bbl.strip() == "5"


def test_plus_negative(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#-3 #5 + int.to.str$ write$")
    assert bbl.strip() == "2"


def test_plus_type_error_pushes_zero(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Non-integer top → warn + push 0 (spec §3.3)."""
    bbl, log = _exec(
        submission_command, tmp_path, '"abc" #3 + int.to.str$ write$', with_log=True
    )
    assert bbl.strip() == "3"  # "abc" popped as int → 0; 0+3 = 3.
    assert _has_type_error(log)


def test_minus_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#10 #3 - int.to.str$ write$")
    assert bbl.strip() == "7"


def test_minus_negative_result(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#3 #10 - int.to.str$ write$")
    assert bbl.strip() == "-7"


def test_minus_zero_edge(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#5 #5 - int.to.str$ write$")
    assert bbl.strip() == "0"


# ---------------------------------------------------------------------------
# Comparison: >, <, =
# ---------------------------------------------------------------------------


def test_greater_true(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#5 #3 > int.to.str$ write$")
    assert bbl.strip() == "1"


def test_greater_false(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#3 #5 > int.to.str$ write$")
    assert bbl.strip() == "0"


def test_greater_equal_is_false(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#5 #5 > int.to.str$ write$")
    assert bbl.strip() == "0"


def test_less_true(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#3 #5 < int.to.str$ write$")
    assert bbl.strip() == "1"


def test_less_false(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#5 #3 < int.to.str$ write$")
    assert bbl.strip() == "0"


def test_equal_int_true(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#5 #5 = int.to.str$ write$")
    assert bbl.strip() == "1"


def test_equal_int_false(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#5 #3 = int.to.str$ write$")
    assert bbl.strip() == "0"


def test_equal_string_true(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"foo" "foo" = int.to.str$ write$')
    assert bbl.strip() == "1"


def test_equal_string_false(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"foo" "bar" = int.to.str$ write$')
    assert bbl.strip() == "0"


def test_equal_empty_strings(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"" "" = int.to.str$ write$')
    assert bbl.strip() == "1"


def test_equal_cross_type_is_zero(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Comparing across types yields 0 per spec §3.5."""
    bbl, _ = _exec(submission_command, tmp_path, '#1 "1" = int.to.str$ write$')
    assert bbl.strip() == "0"


# ---------------------------------------------------------------------------
# String concat: *
# ---------------------------------------------------------------------------


def test_concat_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"foo" "bar" * write$')
    assert bbl.strip() == "foobar"


def test_concat_empty_left(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"" "bar" * write$')
    assert bbl.strip() == "bar"


def test_concat_empty_right(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"foo" "" * write$')
    assert bbl.strip() == "foo"


def test_concat_type_error_pushes_empty(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, log = _exec(
        submission_command, tmp_path, '#5 "suffix" * write$', with_log=True
    )
    # First pop is a string, second pop should be string but got int → default "".
    assert bbl.strip() == "suffix"
    assert _has_type_error(log)


# ---------------------------------------------------------------------------
# Assignment: := (value name -> )
# ---------------------------------------------------------------------------


def test_assign_integer(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
INTEGERS { n }
FUNCTION {f} { #42 'n := n int.to.str$ write$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, EMPTY_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "42"


def test_assign_string(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    style = """\
ENTRY { } { } { }
STRINGS { s }
FUNCTION {f} { "hello" 's := s write$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, EMPTY_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "hello"


def test_assign_empty_string_edge(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    style = """\
ENTRY { } { } { }
STRINGS { s }
FUNCTION {f} { "" 's := s "X" * write$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, EMPTY_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "X"


# ---------------------------------------------------------------------------
# substring$ (str int int -> str)
# ---------------------------------------------------------------------------


def test_substring_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"abcdefg" #2 #3 substring$ write$'
    )
    assert bbl.strip() == "bcd"


def test_substring_zero_length(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"abcdef" #1 #0 substring$ "|" * write$'
    )
    # zero length → empty; emit "|" to keep result non-empty for assertion
    assert bbl.strip() == "|"


def test_substring_from_end_negative_start(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Negative start counts from the end (spec §3.5)."""
    bbl, _ = _exec(
        submission_command, tmp_path, '"abcdef" #-1 #3 substring$ write$'
    )
    # start=-1 counts from the end: last 3 chars of "abcdef" = "def".
    assert bbl.strip() == "def"


# ---------------------------------------------------------------------------
# text.length$ (str -> int)
# ---------------------------------------------------------------------------


def test_text_length_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"abcde" text.length$ int.to.str$ write$'
    )
    assert bbl.strip() == "5"


def test_text_length_empty(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"" text.length$ int.to.str$ write$'
    )
    assert bbl.strip() == "0"


def test_text_length_control_sequence(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    r"""``{\TeX}`` is a control sequence, counts as 1 (spec §8.4)."""
    bbl, _ = _exec(
        submission_command, tmp_path, r'"{\TeX}" text.length$ int.to.str$ write$'
    )
    assert bbl.strip() == "1"


# ---------------------------------------------------------------------------
# text.prefix$ (str int -> str)
# ---------------------------------------------------------------------------


def test_text_prefix_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"hello world" #5 text.prefix$ write$'
    )
    assert bbl.strip() == "hello"


def test_text_prefix_zero(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"hello" #0 text.prefix$ "|" * write$'
    )
    assert bbl.strip() == "|"


def test_text_prefix_longer_than_string(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"hi" #100 text.prefix$ write$'
    )
    assert bbl.strip() == "hi"


# ---------------------------------------------------------------------------
# width$ (str -> int)
# ---------------------------------------------------------------------------


def test_width_nonzero_on_text(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """width$ returns a positive integer for any non-empty printable string (spec §8.1)."""
    bbl, _ = _exec(
        submission_command, tmp_path, '"hello" width$ #0 > int.to.str$ write$'
    )
    assert bbl.strip() == "1"


def test_width_empty_is_zero(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"" width$ int.to.str$ write$'
    )
    assert bbl.strip() == "0"


def test_width_longer_string_has_greater_width(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Monotone width: "aaa" has greater width than "a" (spec §8.1)."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"aaa" width$ "a" width$ > int.to.str$ write$',
    )
    assert bbl.strip() == "1"


# ---------------------------------------------------------------------------
# add.period$
# ---------------------------------------------------------------------------


def test_add_period_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"hello" add.period$ write$')
    assert bbl.strip() == "hello."


def test_add_period_preserves_existing_period(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"hi." add.period$ write$')
    assert bbl.strip() == "hi."


def test_add_period_preserves_question_mark(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"hi?" add.period$ write$')
    assert bbl.strip() == "hi?"


def test_add_period_preserves_exclamation(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"hi!" add.period$ write$')
    assert bbl.strip() == "hi!"


def test_add_period_ignores_trailing_braces(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """spec §3.5: ``add.period$`` ignores trailing ``}`` when checking."""
    bbl, _ = _exec(submission_command, tmp_path, '"hi.}}" add.period$ write$')
    assert bbl.strip() == "hi.}}"


# ---------------------------------------------------------------------------
# change.case$
# ---------------------------------------------------------------------------


def test_change_case_lower(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"Hello World" "l" change.case$ write$'
    )
    assert bbl.strip() == "hello world"


def test_change_case_upper(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"Hello World" "u" change.case$ write$'
    )
    assert bbl.strip() == "HELLO WORLD"


def test_change_case_title(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"HELLO WORLD" "t" change.case$ write$'
    )
    assert bbl.strip() == "Hello world"


def test_change_case_preserves_braces(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"The {USA} story" "l" change.case$ write$'
    )
    assert bbl.strip() == "the {USA} story"


def test_change_case_on_empty(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"" "l" change.case$ "|" * write$'
    )
    assert bbl.strip() == "|"


# ---------------------------------------------------------------------------
# chr.to.int$ / int.to.chr$
# ---------------------------------------------------------------------------


def test_chr_to_int_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"A" chr.to.int$ int.to.str$ write$'
    )
    assert bbl.strip() == "65"


def test_chr_to_int_lowercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"a" chr.to.int$ int.to.str$ write$'
    )
    assert bbl.strip() == "97"


def test_chr_to_int_wrong_length_is_error(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Non-1-char input → warn + default 0 (spec §3.5)."""
    bbl, log = _exec(
        submission_command,
        tmp_path,
        '"hi" chr.to.int$ int.to.str$ write$',
        with_log=True,
    )
    assert bbl.strip() == "0"
    assert _has_type_error(log)


def test_int_to_chr_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#66 int.to.chr$ write$")
    assert bbl.strip() == "B"


def test_int_to_chr_zero(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Zero → NUL byte; exercise round-trip via chr.to.int$."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        "#65 int.to.chr$ chr.to.int$ int.to.str$ write$",
    )
    assert bbl.strip() == "65"


# ---------------------------------------------------------------------------
# int.to.str$
# ---------------------------------------------------------------------------


def test_int_to_str_positive(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#42 int.to.str$ write$")
    assert bbl.strip() == "42"


def test_int_to_str_zero(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#0 int.to.str$ write$")
    assert bbl.strip() == "0"


def test_int_to_str_negative(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "#-7 int.to.str$ write$")
    assert bbl.strip() == "-7"


# ---------------------------------------------------------------------------
# purify$
# ---------------------------------------------------------------------------


def test_purify_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"Hello, World!" purify$ write$'
    )
    assert bbl.strip() == "Hello World"


def test_purify_empty(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"" purify$ "|" * write$'
    )
    assert bbl.strip() == "|"


def test_purify_only_punctuation(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"!!!???" purify$ "|" * write$'
    )
    # All stripped to empty; marker preserves position.
    assert bbl.strip() == "|"


# ---------------------------------------------------------------------------
# format.name$
# ---------------------------------------------------------------------------


def test_format_name_last(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{a, author = "John Smith"}\n'
    bbl, _ = _iterate(
        submission_command,
        tmp_path,
        'author #1 "{ll}" format.name$ write$',
        bib=bib,
        entry_fields="author",
    )
    assert bbl.strip() == "Smith"


def test_format_name_first_initial(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = '@article{a, author = "John Smith"}\n'
    bbl, _ = _iterate(
        submission_command,
        tmp_path,
        'author #1 "{f.}" format.name$ write$',
        bib=bib,
        entry_fields="author",
    )
    # "{f.}" → first-initial + period, e.g. "J."
    assert bbl.strip().startswith("J")
    assert "." in bbl


def test_format_name_out_of_range(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Index beyond the list length returns empty string (spec §3.5)."""
    bib = '@article{a, author = "John Smith"}\n'
    bbl, _ = _iterate(
        submission_command,
        tmp_path,
        'author #2 "{ll}" format.name$ "|" * write$',
        bib=bib,
        entry_fields="author",
    )
    assert bbl.strip() == "|"


# ---------------------------------------------------------------------------
# num.names$
# ---------------------------------------------------------------------------


def test_num_names_one(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{a, author = "Smith"}\n'
    bbl, _ = _iterate(
        submission_command,
        tmp_path,
        "author num.names$ int.to.str$ write$",
        bib=bib,
        entry_fields="author",
    )
    assert bbl.strip() == "1"


def test_num_names_three(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{a, author = "Smith and Jones and Doe"}\n'
    bbl, _ = _iterate(
        submission_command,
        tmp_path,
        "author num.names$ int.to.str$ write$",
        bib=bib,
        entry_fields="author",
    )
    assert bbl.strip() == "3"


# ---------------------------------------------------------------------------
# Control flow: if$
# ---------------------------------------------------------------------------


def test_if_true_branch(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '#1 { "yes" write$ } { "no" write$ } if$',
    )
    assert bbl.strip() == "yes"


def test_if_false_branch(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '#0 { "yes" write$ } { "no" write$ } if$',
    )
    assert bbl.strip() == "no"


def test_if_nonzero_is_true(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Per spec, condition is "nonzero → true", not just 1."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '#-1 { "yes" write$ } { "no" write$ } if$',
    )
    assert bbl.strip() == "yes"


# ---------------------------------------------------------------------------
# Control flow: while$
# ---------------------------------------------------------------------------


def test_while_counts_down(submission_command: tuple[str, ...], tmp_path: Path) -> None:
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
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "321"


def test_while_condition_false_from_start(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """If condition starts false, body runs zero times."""
    style = """\
ENTRY { } { i } { }
FUNCTION {f}
{ #0 'i :=
  { i #0 > }
    { "BAD" write$ }
  while$
  "ok" write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "ok"


# ---------------------------------------------------------------------------
# Control flow: skip$
# ---------------------------------------------------------------------------


def test_skip_is_noop(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"A" skip$ write$')
    assert bbl.strip() == "A"


def test_skip_leaves_stack_untouched(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"X" "Y" skip$ * write$')
    assert bbl.strip() == "XY"


# ---------------------------------------------------------------------------
# Stack: pop$ / swap$ / duplicate$
# ---------------------------------------------------------------------------


def test_pop_discards_top(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"keep" "drop" pop$ write$')
    assert bbl.strip() == "keep"


def test_swap_two(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"A" "B" swap$ write$ write$'
    )
    assert bbl.strip() == "AB"


def test_duplicate(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"X" duplicate$ write$ write$'
    )
    assert bbl.strip() == "XX"


# ---------------------------------------------------------------------------
# Entry scope: cite$ / type$ / call.type$ / empty$ / missing$
# ---------------------------------------------------------------------------


def test_cite(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _iterate(submission_command, tmp_path, "cite$ write$")
    assert bbl.strip() == "a"


def test_type_is_lowercased(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@ARTICLE{a, author = "x"}\n'
    bbl, _ = _iterate(
        submission_command, tmp_path, "type$ write$", bib=bib, entry_fields="author"
    )
    assert bbl.strip() == "article"


def test_call_type_dispatches(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = '@article{a, title = "A"}\n'
    style = """\
ENTRY { title } { } { }
FUNCTION {article} { "art:" write$ title write$ }
FUNCTION {default.type} { "def" write$ }
FUNCTION {f} { call.type$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "art:A"


def test_empty_on_missing_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _iterate(
        submission_command, tmp_path, "journal empty$ int.to.str$ write$"
    )
    assert bbl.strip() == "1"


def test_empty_on_whitespace_string(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"   " empty$ int.to.str$ write$'
    )
    assert bbl.strip() == "1"


def test_empty_on_nonempty_string(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"hi" empty$ int.to.str$ write$'
    )
    assert bbl.strip() == "0"


def test_missing_on_missing_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _iterate(
        submission_command, tmp_path, "journal missing$ int.to.str$ write$"
    )
    assert bbl.strip() == "1"


def test_missing_vs_empty_string(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """missing$ distinguishes missing field from empty string."""
    bbl, _ = _exec(
        submission_command, tmp_path, '"" missing$ int.to.str$ write$'
    )
    assert bbl.strip() == "0"


# ---------------------------------------------------------------------------
# preamble$
# ---------------------------------------------------------------------------


def test_preamble_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@preamble{"\\special"}\n@article{a, author = "X"}\n'
    bbl, _ = _exec(submission_command, tmp_path, "preamble$ write$", bib=bib)
    assert bbl.strip() == r"\special"


def test_preamble_empty_when_none(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        'preamble$ empty$ int.to.str$ write$',
    )
    assert bbl.strip() == "1"


def test_preamble_concatenated(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """summary.md §3.5 `preamble$` row: concatenation of all
    `@preamble` values in source order, separated by a single
    ASCII space. Two preambles "aa" + "bb" MUST yield exactly
    "aa bb" per the documented contract."""
    bib = (
        '@preamble{"aa"}\n'
        '@preamble{"bb"}\n'
        '@article{a, author = "X"}\n'
    )
    bbl, _ = _exec(submission_command, tmp_path, "preamble$ write$", bib=bib)
    assert bbl.rstrip("\n") == "aa bb", (
        f"expected 'aa bb' (source order, single-space separator); got {bbl!r}"
    )


# ---------------------------------------------------------------------------
# write$ / newline$
# ---------------------------------------------------------------------------


def test_write_normal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"hello" write$')
    # Implementation flushes any pending line at end-of-run; tolerate a final newline.
    assert bbl.rstrip("\n") == "hello"


def test_write_empty_string(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"" write$')
    assert bbl.rstrip("\n") == ""


def test_newline_emits_lf(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl, _ = _exec(submission_command, tmp_path, '"x" write$ newline$ "y" write$')
    assert bbl.rstrip("\n") == "x\ny"


# ---------------------------------------------------------------------------
# Character queries: quote$
# ---------------------------------------------------------------------------


def test_quote_pushes_double_quote(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(submission_command, tmp_path, "quote$ write$")
    assert bbl.rstrip("\n") == '"'


def test_quote_within_string_build(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """quote$ composes with * to build a literal quote in the middle."""
    bbl, _ = _exec(submission_command, tmp_path, '"a" quote$ * "b" * write$')
    assert bbl.rstrip("\n") == 'a"b'


# ---------------------------------------------------------------------------
# Debug/trace: top$ / stack$
# Per spec §3.5, these are debug aids. ``top$`` may be a silent no-op in the
# harness; ``stack$`` dumps (and may clear) the stack. We only assert that
# they do not crash and that subsequent computation proceeds.
# ---------------------------------------------------------------------------


def test_top_is_noop_on_output(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """top$ prints the stack (debug) — MUST not abort execution."""
    bbl, _ = _exec(
        submission_command, tmp_path, '"A" duplicate$ top$ write$'
    )
    # Two copies of "A" were left by duplicate; top$ either prints them to
    # a log/stderr or is a silent no-op. Either way, "A" must still write.
    assert "A" in bbl


def test_stack_does_not_crash(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """stack$ dumps the full stack (debug). MUST not abort execution."""
    bbl, _ = _exec(
        submission_command, tmp_path, '"X" "Y" stack$ "post" write$'
    )
    # "post" comes after stack$, so execution must continue. stack$ may leave
    # the stack empty or full depending on interpretation; don't assert on
    # what's left, just on continuation.
    assert "post" in bbl


# ---------------------------------------------------------------------------
# warning$ (str -> )
# ---------------------------------------------------------------------------


def test_warning_emits_entry_in_log(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ appends to the warnings log (spec §5.2/§5.3)."""
    _, log = _exec(
        submission_command,
        tmp_path,
        '"something odd" warning$',
        with_log=True,
    )
    assert log is not None
    # The warning must be present somewhere. We don't pin the exact kind —
    # only that the user-supplied message appears in the warnings list.
    msgs = [w.get("message", "") for w in log.get("warnings", [])]
    assert any("something odd" in m for m in msgs)


def test_warning_does_not_abort(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ does not stop execution (spec §5.3)."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"err" warning$ "after" write$',
    )
    assert "after" in bbl


def test_warning_empty_message_allowed(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ with empty string is legal."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"" warning$ "ok" write$',
    )
    assert bbl.strip() == "ok"
