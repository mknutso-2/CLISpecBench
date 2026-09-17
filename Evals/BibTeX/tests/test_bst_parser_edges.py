"""`.bst` parser edge cases not covered by `test_bst_language.py`.

Focus areas:
  * Integer literal syntax: negative numbers, zero, leading-zero.
  * Nested function literals.
  * Quoted function names passed by reference.
  * ``%`` comments embedded mid-expression and mid-body.
  * Top-level ordering errors (e.g. ``ITERATE`` before ``READ``).
  * Missing or malformed top-level declarations.
  * Duplicate top-level names.
  * ``MACRO`` redefinition.

References: btxhak §5 ("The lexical structure of style files") and
bibtex.web §3000+ (`.bst` lexer / parser).
"""

from __future__ import annotations

# bibtex.web lines 8141–8146 predefine the per-entry sort.key$ string;
# ENTRY must not redeclare it. These fixtures exercise its use directly.
from pathlib import Path

from conftest import run_bibtex

MINI_BIB = "@misc{a,}\n"


def _exec(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    *,
    entry_fields: str = "",
    expect_exit: int = 0,
) -> str:
    # Flush every semantic probe explicitly, including writes inside branches.
    style = (
        f"ENTRY {{ {entry_fields} }} {{ }} {{ }}\n"
        f"FUNCTION {{f}} {{ {body}\n newline$ }}\n"
        "READ\n"
        "EXECUTE {f}\n"
    )
    bbl, _ = run_bibtex(
        submission_command,
        MINI_BIB,
        style,
        ["a"],
        tmp_path,
        expect_exit=expect_exit,
    )
    return bbl


# ---------------------------------------------------------------------------
# Integer literals
# ---------------------------------------------------------------------------


def test_negative_integer_literal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """#-5 is a valid negative integer literal (bibtex.web §3020)."""
    bbl = _exec(submission_command, tmp_path, "#-5 int.to.str$ write$")
    assert bbl.strip() == "-5"


def test_zero_integer_literal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """#0 is the integer zero."""
    bbl = _exec(submission_command, tmp_path, "#0 int.to.str$ write$")
    assert bbl.strip() == "0"


def test_integer_literal_arithmetic(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """#3 #4 + = 7."""
    bbl = _exec(submission_command, tmp_path, "#3 #4 + int.to.str$ write$")
    assert bbl.strip() == "7"


def test_negative_minus_positive_arithmetic(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """#-3 #4 + = 1."""
    bbl = _exec(submission_command, tmp_path, "#-3 #4 + int.to.str$ write$")
    assert bbl.strip() == "1"


# ---------------------------------------------------------------------------
# Nested function literals
# ---------------------------------------------------------------------------


def test_nested_function_literal_via_while(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Function literals inside while$ arguments parse correctly."""
    # Decrement n from 3 to 0; at each step write "x".
    style = """\
ENTRY { } { } { }
INTEGERS { n }
FUNCTION {setup} { #3 'n := }
FUNCTION {loop}
{ { n #0 > }
  { "x" write$ n #1 - 'n := }
  while$ newline$ }
READ
EXECUTE {setup}
EXECUTE {loop}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.rstrip("\n") == "xxx"


def test_function_literal_as_if_branch(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """if$ takes two function literals as branches."""
    bbl = _exec(
        submission_command,
        tmp_path,
        '#1 #0 > { "yes" } { "no" } if$ write$',
    )
    assert bbl.rstrip("\n") == "yes"


def test_deeply_nested_function_literals(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Function literal inside function literal inside function literal."""
    bbl = _exec(
        submission_command,
        tmp_path,
        '#1 #0 > { #1 #0 > { "deep" write$ } { skip$ } if$ } { skip$ } if$',
    )
    assert bbl.rstrip("\n") == "deep"


# ---------------------------------------------------------------------------
# Comments (% and mid-body)
# ---------------------------------------------------------------------------


def test_comment_at_eol_after_expression(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A ``%`` comment to end-of-line is allowed mid-body."""
    style = """\
ENTRY { } { } { }
FUNCTION {f}
{ "hello" write$ % this is a comment
  newline$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "hello"


def test_full_line_comment(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """A line starting with % is entirely a comment."""
    style = """\
ENTRY { } { } { }
% Style-file documentation here.
% Author: somebody.
FUNCTION {f} { "ok" write$ newline$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "ok"


# ---------------------------------------------------------------------------
# Top-level ordering
# ---------------------------------------------------------------------------


def test_iterate_before_read_is_error(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Per btxhak §3.1, ITERATE requires READ to have run first."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
ITERATE {f}
READ
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path, expect_exit=1)
    # Error body should be JSON with source=bst or runtime.
    assert "error" in bbl.lower()


def test_execute_before_read_is_rejected(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # bibtex.web bst_execute_command rejects EXECUTE before READ even if
    # the function does not access entries. Technical requirements require
    # exit 1 and structured error JSON for a BST error.
    from test_errors import run_for_exit1

    style = 'ENTRY {} {} {}\nFUNCTION {f} { "pre-read" write$ }\nEXECUTE {f}\nREAD\n'
    out = run_for_exit1(submission_command, MINI_BIB, style, "a\n", tmp_path)
    assert isinstance(out.get("error"), dict)


def test_read_without_entry_declaration_is_rejected(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # bibtex.web bst_read_command requires ENTRY before READ. Keep the
    # function valid so an unrelated unknown identifier cannot earn credit.
    from test_errors import run_for_exit1

    style = 'FUNCTION {f} { "ok" write$ }\nREAD\nEXECUTE {f}\n'
    out = run_for_exit1(submission_command, MINI_BIB, style, "a\n", tmp_path)
    assert isinstance(out.get("error"), dict)


def test_duplicate_function_definition_is_rejected(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # bibtex.web bst_function_command / already_seen_function_print reject
    # reusing an identifier. A parse error must have the harness error JSON.
    from test_errors import run_for_exit1

    style = (
        'ENTRY {} {} {}\nFUNCTION {f} { "one" write$ }\n'
        'FUNCTION {f} { "two" write$ }\nREAD\nEXECUTE {f}\n'
    )
    out = run_for_exit1(submission_command, MINI_BIB, style, "a\n", tmp_path)
    assert isinstance(out.get("error"), dict)


# ---------------------------------------------------------------------------
# MACRO parsing in .bst
# ---------------------------------------------------------------------------


def test_bst_macro_definition_is_parsed(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """MACRO at .bst level is a valid top-level declaration and is recorded
    in the log (per technical-requirements-prompt.md)."""
    style = """\
ENTRY { } { } { }
MACRO {custommac} {"MyValue"}
FUNCTION {f} { "ok" write$ newline$ }
READ
EXECUTE {f}
"""
    bbl, log = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path, with_log=True)
    assert "ok" in bbl
    # If the log includes macros_defined, custommac should be present.
    if log is not None and "macros_defined" in log:
        assert "custommac" in log["macros_defined"]


# ---------------------------------------------------------------------------
# Quoted function reference
# ---------------------------------------------------------------------------


def test_quoted_name_assigns_function_by_reference(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'sort.key$ := pops the value and stores it into sort.key$."""
    style = """\
ENTRY { } { } { }
FUNCTION {setkey} { "abc" 'sort.key$ := }
FUNCTION {emit} { sort.key$ write$ newline$ }
READ
ITERATE {setkey}
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.rstrip("\n") == "abc"


# ---------------------------------------------------------------------------
# Unknown function reference at load time
# ---------------------------------------------------------------------------


def test_unknown_function_reference_is_load_error(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Technical requirements 'Exit codes' explicitly require exit 1 for an
    # unknown function at load time; a warning or bare crash cannot pass.
    from test_errors import run_for_exit1

    style = "ENTRY {} {} {}\nFUNCTION {f} { does.not.exist }\nREAD\nEXECUTE {f}\n"
    out = run_for_exit1(submission_command, MINI_BIB, style, "a\n", tmp_path)
    assert isinstance(out.get("error"), dict)


def test_macro_name_has_separate_database_namespace(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # bibtex.web bst_macro_command uses macro_ilk, distinct from the
    # bst_fn_ilk namespace containing the built-in crossref field.
    style = (
        'MACRO {crossref} {"value"}\nENTRY {title} {} {}\n'
        "FUNCTION {f} { title write$ newline$ }\nREAD\nITERATE {f}\n"
    )
    bbl, _ = run_bibtex(submission_command, "@misc{a, title = crossref}\n", style, ["a"], tmp_path)
    assert bbl == "value\n"


def test_database_macro_is_not_callable_bst_function(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # macro_ilk does not define a function in bst_fn_ilk. The technical
    # requirements require structured load-time rejection of unknown names.
    from test_errors import run_for_exit1

    style = (
        'MACRO {onlymacro} {"value"}\nENTRY {} {} {}\n'
        "FUNCTION {f} { onlymacro write$ }\nREAD\nEXECUTE {f}\n"
    )
    out = run_for_exit1(submission_command, MINI_BIB, style, "a\n", tmp_path)
    assert isinstance(out.get("error"), dict)
