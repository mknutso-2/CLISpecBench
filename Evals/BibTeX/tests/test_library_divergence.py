"""Adversarial fixtures targeting corners where public .bib parsers and
.bst interpreters are known to diverge:

- Author-name grammar under multi-comma / brace-protected / tied-name inputs.
- @string macro resolution order and case handling.
- Crossref with case-folding and preservation of parent key casing.
- format.name$ abbreviation rules (`f.` initial + period, `~` tie).
- purify$ on LaTeX accent macros vs plain braces.
- change.case$ with brace-protected ALL-CAPS acronyms.
- Comparison operators on mixed-type stack values.

Each test is a standalone .bst fragment so a regression in one area does
not cascade into the others.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex


def _exec(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    bib: str,
    body: str,
    extra_entry: str = "{ }",
) -> str:
    """Build a style that EXECUTEs `body` (no ITERATE) and returns the .bbl."""
    style = f"""\
ENTRY {{ author title }} {{ }} {extra_entry}
FUNCTION {{f}} {{ {body} }}
READ
EXECUTE {{f}}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    return bbl


# ---------------------------------------------------------------------------
# Name grammar divergences
# ---------------------------------------------------------------------------


def test_name_with_brace_protected_von_is_treated_as_uppercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # "{von} der Pol" — the brace-protected "{von}" is UPPERCASE-ish per §2.1,
    # so "der" becomes the (single) von, "Pol" is Last, "{von}" is First.
    # bibtexparser, pybtex, and BiBTeXML have historically disagreed on this.
    bib = '@article{a, author = "{von} der Pol"}\n'
    style = """\
ENTRY { author } { } { }
FUNCTION {f}
{ author #1 "{ff}" format.name$ write$ "/" write$
  author #1 "{vv}" format.name$ write$ "/" write$
  author #1 "{ll}" format.name$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "{von}/der/Pol"


def test_name_tied_tokens_preserved_as_separate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Tie character ~ separates tokens for the grammar. "John~Paul Smith"
    # tokenizes as ["John", "Paul", "Smith"]. Form 1 with no lowercase:
    # First = "John Paul", Last = "Smith".
    bib = '@article{a, author = "John~Paul Smith"}\n'
    style = """\
ENTRY { author } { } { }
FUNCTION {f}
{ author #1 "{ff}" format.name$ write$ "/" write$
  author #1 "{ll}" format.name$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "John Paul/Smith"


def test_num_names_treats_brace_group_and_as_literal(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """num.names$ counts top-level `and` separators but treats `and`
    inside brace groups as part of a single name. Three top-level
    `and`s would be 4 names; two top-level `and`s with a third `and`
    inside `{Brown and Green}` yields 3 names."""
    bib = '@article{a, author = "Smith and Jones and {Brown and Green}"}\n'
    style = """\
ENTRY { author } { } { }
FUNCTION {f} { author num.names$ int.to.str$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "3"


# ---------------------------------------------------------------------------
# @string macro divergences
# ---------------------------------------------------------------------------


def test_string_macro_redefinition_last_wins(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = '@string{pub = "first"}\n@string{pub = "second"}\n@article{a, publisher = pub}\n'
    style = """\
ENTRY { publisher } { } { }
FUNCTION {f} { publisher write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "second"


def test_string_macro_forward_reference_fails(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Using a macro before it's defined yields an unresolved_macro warning
    # and an empty expansion.
    bib = '@article{a, publisher = pub}\n@string{pub = "late"}\n'
    style = """\
ENTRY { publisher } { } { }
FUNCTION {f}
{ publisher empty$ { "yes-empty" write$ } { "no" write$ } if$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "yes-empty"


# ---------------------------------------------------------------------------
# Crossref divergences
# ---------------------------------------------------------------------------


def test_crossref_preserves_parent_key_case_in_child_crossref_value(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # The child's resolved crossref in the log should reflect the parent's
    # declared casing (MixedCase), even though lookup was case-insensitive.
    bib = """
@proceedings{MixedCase, year = 2020}
@inproceedings{child, crossref = "mixedcase"}
"""
    style = """\
ENTRY { year } { } { }
FUNCTION {f} { year write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["child"], tmp_path)
    assert bbl.strip() == "2020"


# ---------------------------------------------------------------------------
# format.name$ divergences
# ---------------------------------------------------------------------------


def test_format_name_with_literal_glue(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # "{f. }{vv }{ll}{, jj}" with a name that has First and Last but no von or Jr.
    # The `{vv }` and `{, jj}` groups should collapse (empty part = suppress unit).
    bib = '@article{a, author = "John Smith"}\n'
    style = """\
ENTRY { author } { } { }
FUNCTION {f}
{ author #1 "{f. }{vv }{ll}{, jj}" format.name$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    # Expected: "J. Smith" (f. + space, no von, Smith, no Jr segment).
    assert "J." in bbl and "Smith" in bbl
    assert ", " not in bbl  # Jr segment should collapse


# ---------------------------------------------------------------------------
# purify$ / change.case$ on adversarial inputs
# ---------------------------------------------------------------------------


def test_purify_strips_punctuation(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bbl = _exec(
        submission_command,
        tmp_path,
        '@article{a, title = "x"}\n',
        '"Hello, World! (2024)" purify$ write$',
    )
    assert bbl.strip() == "Hello World 2024"


def test_change_case_brace_protected_acronym(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # "The {USA} Story" change.case$ "l" → "the {USA} story" (USA preserved).
    bbl = _exec(
        submission_command,
        tmp_path,
        '@article{a, title = "x"}\n',
        '"The {USA} Story" "l" change.case$ write$',
    )
    assert bbl.strip() == "the {USA} story"


def test_change_case_title_mode(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # "t" mode: first letter uppercase, rest lowercase, respecting braces.
    bbl = _exec(
        submission_command,
        tmp_path,
        '@article{a, title = "x"}\n',
        '"HELLO {World}" "t" change.case$ write$',
    )
    assert bbl.strip() == "Hello {World}"


# ---------------------------------------------------------------------------
# Comparison / stack divergences
# ---------------------------------------------------------------------------


def test_equal_returns_0_for_cross_type_compare(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Comparing integer 1 == string "1" should yield 0 (different types).
    bbl = _exec(
        submission_command, tmp_path, '@article{a, title = "x"}\n', '#1 "1" = int.to.str$ write$'
    )
    assert bbl.strip() == "0"


def test_text_length_of_string_with_brace_group_content(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # "a{bc}d" has text.length$ = 4 (a + b + c + d, braces themselves are 0).
    bbl = _exec(
        submission_command,
        tmp_path,
        '@article{a, title = "x"}\n',
        '"a{bc}d" text.length$ int.to.str$ write$',
    )
    assert bbl.strip() == "4"


def test_text_length_of_control_sequence_is_one(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Per spec §8.4: a brace group beginning with \ contributes 1.
    bbl = _exec(
        submission_command,
        tmp_path,
        '@article{a, title = "x"}\n',
        '"{\\TeX}" text.length$ int.to.str$ write$',
    )
    assert bbl.strip() == "1"
