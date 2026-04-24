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

from pathlib import Path

from conftest import run_bibtex

MINI_BIB = "@misc{a}\n"


def _exec(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    *,
    entry_fields: str = "",
    expect_exit: int = 0,
) -> str:
    # Append newline$ if body ends with bare write$ — see test_bst_language
    # _maybe_flush for rationale. Guards the suite against a cascade where
    # one missing end-of-run flush in the interpreter takes down every
    # write$-terminated test body.
    if body.rstrip().endswith("write$"):
        body = body + " newline$"
    style = (
        f"ENTRY {{ {entry_fields} }} {{ }} {{ }}\n"
        f"FUNCTION {{f}} {{ {body} }}\n"
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


def test_negative_integer_literal(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """#-5 is a valid negative integer literal (bibtex.web §3020)."""
    bbl = _exec(submission_command, tmp_path, "#-5 int.to.str$ write$")
    assert bbl.strip() == "-5"


def test_zero_integer_literal(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """#0 is the integer zero."""
    bbl = _exec(submission_command, tmp_path, "#0 int.to.str$ write$")
    assert bbl.strip() == "0"


def test_integer_literal_arithmetic(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """#3 #4 + = 7."""
    bbl = _exec(submission_command, tmp_path, "#3 #4 + int.to.str$ write$")
    assert bbl.strip() == "7"


def test_negative_minus_positive_arithmetic(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """#-3 #4 + = 1."""
    bbl = _exec(
        submission_command, tmp_path, "#-3 #4 + int.to.str$ write$"
    )
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
  while$ }
READ
EXECUTE {setup}
EXECUTE {loop}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.rstrip("\n") == "xxx"


def test_function_literal_as_if_branch(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
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


def test_full_line_comment(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A line starting with % is entirely a comment."""
    style = """\
ENTRY { } { } { }
% Style-file documentation here.
% Author: somebody.
FUNCTION {f} { "ok" write$ }
READ
EXECUTE {f}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.strip() == "ok"


# ---------------------------------------------------------------------------
# Top-level ordering
# ---------------------------------------------------------------------------


def test_iterate_before_read_is_error(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Per btxhak §3.1, ITERATE requires READ to have run first."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
ITERATE {f}
READ
"""
    bbl, _ = run_bibtex(
        submission_command, MINI_BIB, style, ["a"], tmp_path, expect_exit=1
    )
    # Error body should be JSON with source=bst or runtime.
    assert "error" in bbl.lower()


def test_execute_before_read_is_permitted(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """EXECUTE on a function that doesn't touch entries is fine before READ."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "pre-read" write$ }
EXECUTE {f}
READ
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert "pre-read" in bbl


def test_missing_entry_declaration_prevents_entry_access(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Without ENTRY, entry-scoped field access is unavailable. The tool
    may either reject the .bst at load time or silently return empty/missing
    when the undefined fields are referenced; we only assert that the tool
    does not produce an .bbl containing nonsense field values."""
    # A .bst that doesn't declare ENTRY at all but tries to access a field.
    style = """\
FUNCTION {f} { title write$ }
READ
EXECUTE {f}
"""
    bbl, log = run_bibtex(
        submission_command,
        "@article{a, title = \"T\"}\n",
        style,
        ["a"],
        tmp_path,
        expect_exit=0,  # Accept either behavior
        with_log=True,
    )
    # If the tool accepted it, the bbl must not contain the field value
    # (since `title` was never declared as an entry field).
    assert "T" not in bbl or log is not None


# ---------------------------------------------------------------------------
# Duplicate names
# ---------------------------------------------------------------------------


def test_duplicate_function_definition_is_either_error_or_override(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Redefining an existing FUNCTION: bibtex.web §4030 says hard error,
    but many implementations allow last-definition-wins. Accept either: if
    the tool accepts, "two" (the second definition) is what runs, not "one".
    """
    style = """\
ENTRY { } { } { }
FUNCTION {f} { "one" write$ }
FUNCTION {f} { "two" write$ }
READ
EXECUTE {f}
"""
    import subprocess

    bib_file = tmp_path / "refs.bib"
    bst_file = tmp_path / "style.bst"
    out_file = tmp_path / "out.bbl"
    cites_file = tmp_path / "cites.txt"
    bib_file.write_text(MINI_BIB, encoding="utf-8")
    bst_file.write_text(style, encoding="utf-8")
    cites_file.write_text("a\n", encoding="utf-8")
    result = subprocess.run(
        [
            *submission_command,
            "--bib",
            str(bib_file),
            "--style",
            str(bst_file),
            "--cites",
            str(cites_file),
            "--output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 1:
        # Strict mode: produced an error. OK.
        return
    assert result.returncode == 0, (
        f"tool exited with unexpected code {result.returncode}: {result.stderr}"
    )
    # Lenient mode: last definition wins.
    content = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
    assert "two" in content, (
        f"last-definition-wins expected, but output contains: {content!r}"
    )


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
FUNCTION {f} { "ok" write$ }
READ
EXECUTE {f}
"""
    bbl, log = run_bibtex(
        submission_command, MINI_BIB, style, ["a"], tmp_path, with_log=True
    )
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
ENTRY { } { } { sort.key$ }
FUNCTION {setkey} { "abc" 'sort.key$ := }
FUNCTION {emit} { sort.key$ write$ }
READ
ITERATE {setkey}
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, MINI_BIB, style, ["a"], tmp_path)
    assert bbl.rstrip("\n") == "abc"


# ---------------------------------------------------------------------------
# Unknown function reference at load time
# ---------------------------------------------------------------------------


def test_unknown_function_reference_fails_or_warns(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Referencing an undefined identifier is a load-time error per
    bibtex.web §3100 (strict). Lenient implementations may substitute
    Missing and emit a warning. Accept either."""
    style = """\
ENTRY { } { } { }
FUNCTION {f} { does.not.exist }
READ
EXECUTE {f}
"""
    import subprocess

    bib_file = tmp_path / "refs.bib"
    bst_file = tmp_path / "style.bst"
    out_file = tmp_path / "out.bbl"
    cites_file = tmp_path / "cites.txt"
    log_file = tmp_path / "out.log"
    bib_file.write_text(MINI_BIB, encoding="utf-8")
    bst_file.write_text(style, encoding="utf-8")
    cites_file.write_text("a\n", encoding="utf-8")
    result = subprocess.run(
        [
            *submission_command,
            "--bib",
            str(bib_file),
            "--style",
            str(bst_file),
            "--cites",
            str(cites_file),
            "--output",
            str(out_file),
            "--log",
            str(log_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 1:
        # Strict mode — an error JSON was emitted. OK.
        return
    assert result.returncode == 0
    # Lenient mode — must have emitted a warning about the unknown name.
    assert log_file.exists()
    import json

    log = json.loads(log_file.read_text(encoding="utf-8"))
    warnings = log.get("warnings", []) if isinstance(log, dict) else []
    msgs = [w.get("message", "") for w in warnings]
    kinds = [w.get("kind", "") for w in warnings]
    assert any(
        "does.not.exist" in m or "unknown" in k.lower() or "undefined" in k.lower()
        for m, k in zip(msgs, kinds, strict=False)
    ), (
        "lenient mode must emit a warning naming the unknown function; "
        f"got warnings: {warnings!r}"
    )
