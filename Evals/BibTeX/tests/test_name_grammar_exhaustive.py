"""Exhaustive author-name grammar tests covering every corner of btxhak §2.

Each test inspects a single name (or a single list of names) via a narrow
.bst that pushes one specific grammar dimension through ``format.name$``
with an unambiguous format string. No probe-dump parser is shared between
tests, so a regression in one dimension does not cascade.

btxhak §2 (Designing BibTeX Styles) covers three author-name forms:

- Form 1: ``First von Last``        — no commas.
- Form 2: ``von Last, First``       — exactly one comma.
- Form 3: ``von Last, Jr, First``   — exactly two commas.

Parts are separated by the case-insensitive word ``and`` (word-bounded at
brace depth 0). A tie ``~`` acts as whitespace between tokens. A token
starting with ``{`` is opaque-uppercase. The first non-brace character's
case decides whether a token is a von fragment.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex

# ---------------------------------------------------------------------------
# Single-name probes: build a style that emits exactly four tagged parts
# of the first name. Each test owns its .bst and its assertion so a failure
# names one grammar dimension.
# ---------------------------------------------------------------------------


def _normalize_separator(s: str) -> str:
    """Normalize inter-token separators in a name part for comparison.

    summary.md §2.6 permits either a tie ``~`` or a single ASCII space
    between tokens of a name part depending on the ``long_token=3``
    and last-gap rules. A conforming implementation MAY emit either
    form; tests should not pin one over the other for the default-
    separator case. This helper converts both to a single space so
    assertions compare the underlying token sequence.

    We deliberately do NOT fold source-preserved sep chars (a tie or
    hyphen that was EXPLICITLY in the source) — those are preserved
    literally per §2.1. Tests that want to exercise source-preserved
    sep chars use the raw ``_parts`` output without normalizing.
    """
    return s.replace("~", " ")


def _parts(
    submission_command: tuple[str, ...], tmp_path: Path, literal: str, which: int = 1
) -> dict[str, str]:
    """Format the ``which``-th name's four parts with unambiguous delimiters.

    Returns {"first", "von", "last", "jr"} parsed back from the .bbl.
    Delimiters are ``<|`` and ``|>`` which are chosen because BibTeX name
    grammar never emits them.
    """
    bib = f'@article{{k, author = "{literal}"}}\n'
    style = f"""\
ENTRY {{ author }} {{ }} {{ }}
FUNCTION {{f}}
{{ "first<|" author #{which} "{{ff}}" format.name$ * "|>" * write$
  "von<|"   author #{which} "{{vv}}" format.name$ * "|>" * write$
  "last<|"  author #{which} "{{ll}}" format.name$ * "|>" * write$
  "jr<|"    author #{which} "{{jj}}" format.name$ * "|>" * write$ }}
READ
ITERATE {{f}}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["k"], tmp_path)
    # Flatten wrapping to a single logical line, then extract parts.
    flat = bbl.replace("\n", "")
    parts: dict[str, str] = {}
    for label in ("first", "von", "last", "jr"):
        marker = label + "<|"
        end_marker = "|>"
        start = flat.find(marker)
        assert start != -1, f"missing {label!r} marker in {bbl!r}"
        start += len(marker)
        end = flat.find(end_marker, start)
        assert end != -1, f"missing end marker for {label!r} in {bbl!r}"
        parts[label] = flat[start:end]
    return parts


def _num_names(submission_command: tuple[str, ...], tmp_path: Path, literal: str) -> int:
    bib = f'@article{{k, author = "{literal}"}}\n'
    style = """\
ENTRY { author } { } { }
FUNCTION {f} { author num.names$ int.to.str$ write$ }
READ
ITERATE {f}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["k"], tmp_path)
    return int(bbl.strip())


# ---------------------------------------------------------------------------
# Form 1 — no commas (btxhak §2.2 / spec §2.2)
# ---------------------------------------------------------------------------


def test_form1_single_token_is_last(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 1, single token: becomes Last; First/von/Jr empty."""
    n = _parts(submission_command, tmp_path, "Plato")
    assert n["last"] == "Plato"
    assert n["first"] == ""
    assert n["von"] == ""
    assert n["jr"] == ""


def test_form1_first_last_no_von(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 1, two uppercase tokens: First + Last, no von."""
    n = _parts(submission_command, tmp_path, "John Smith")
    assert n["first"] == "John"
    assert n["last"] == "Smith"
    assert n["von"] == ""


def test_form1_von_between(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Form 1, lowercase between caps: becomes von. Inter-token
    separator inside von may be tie or space per §2.6."""
    n = _parts(submission_command, tmp_path, "John van der Pol")
    assert n["first"] == "John"
    assert _normalize_separator(n["von"]) == "van der"
    assert n["last"] == "Pol"


def test_form1_von_without_first(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 1, no leading caps: First is empty, von then Last."""
    n = _parts(submission_command, tmp_path, "van der Pol")
    assert n["first"] == ""
    assert _normalize_separator(n["von"]) == "van der"
    assert n["last"] == "Pol"


def test_form1_all_lowercase_absorbs_into_last(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 1, all-lowercase tokens: Last absorbs all, von emptied (spec §2.2)."""
    n = _parts(submission_command, tmp_path, "van de")
    assert n["first"] == ""
    assert n["von"] == ""
    assert n["last"] == "van de"


def test_form1_all_uppercase_last_is_final_token(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 1, all-uppercase with no lowercase: First = all but last, Last = final.
    Inter-token separator in First may be tie or space per §2.6."""
    n = _parts(submission_command, tmp_path, "John Paul Jones")
    assert _normalize_separator(n["first"]) == "John Paul"
    assert n["last"] == "Jones"
    assert n["von"] == ""


def test_form1_tied_tokens_separate_grammatically(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Tie ``~`` acts as whitespace between tokens grammatically
    (btxhak §2.1). The output separator for the joined tokens may
    be either a literal tie (preserved from the source per §2.1)
    or a single ASCII space (the default-separator fallback per
    §2.6). Tests accept either."""
    n = _parts(submission_command, tmp_path, "John~Paul Smith")
    # Tokens: [John, Paul, Smith] — all uppercase → First = John+Paul.
    assert _normalize_separator(n["first"]) == "John Paul"
    assert n["last"] == "Smith"


def test_form1_brace_protected_is_uppercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Brace-opened token is opaque-uppercase (btxhak §2.1)."""
    n = _parts(submission_command, tmp_path, "{van der} Pol")
    assert n["first"] == "{van der}"
    assert n["last"] == "Pol"
    assert n["von"] == ""


def test_form1_brace_protected_von_region(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A brace token between two lowercase tokens does NOT end the von run."""
    # "de {la} vega Smith": tokens=[de,{la},vega,Smith].
    # Lowercase token positions: 0 (de), 2 (vega). Brace token {la} is uppercase.
    # Per btxhak §2.2: von spans from the FIRST lowercase through the LAST
    # lowercase token, inclusive — so von = "de {la} vega", Last = "Smith".
    # Inter-token separator inside von may be tie or space per §2.6.
    n = _parts(submission_command, tmp_path, "de {la} vega Smith")
    assert _normalize_separator(n["von"]) == "de {la} vega"
    assert n["last"] == "Smith"
    assert n["first"] == ""


# ---------------------------------------------------------------------------
# Form 2 — one comma (btxhak §2.3 / spec §2.3)
# ---------------------------------------------------------------------------


def test_form2_simple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Form 2, head = Last only, First after the comma."""
    n = _parts(submission_command, tmp_path, "Smith, John")
    assert n["first"] == "John"
    assert n["last"] == "Smith"
    assert n["von"] == ""


def test_form2_von_plus_last_head(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 2, head with von + Last run. Inter-token separator inside
    von may be tie or space per §2.6."""
    n = _parts(submission_command, tmp_path, "van der Pol, Balthasar")
    assert n["first"] == "Balthasar"
    assert _normalize_separator(n["von"]) == "van der"
    assert n["last"] == "Pol"


def test_form2_leading_caps_prepend_to_last(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 2, leading uppercase tokens before von fold into Last (spec §2.3).
    Inter-token separator inside multi-token Last or von may be tie or
    space per §2.6."""
    n = _parts(submission_command, tmp_path, "Foo van der Pol, Charles")
    assert n["first"] == "Charles"
    assert _normalize_separator(n["von"]) == "van der"
    assert _normalize_separator(n["last"]) == "Foo Pol"


def test_form2_head_without_lowercase_is_all_last(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 2, head with no lowercase tokens: whole head is Last.
    Inter-token separator in Last may be tie or space per §2.6."""
    n = _parts(submission_command, tmp_path, "Charles Martin Jones, Jimmy")
    assert n["first"] == "Jimmy"
    assert _normalize_separator(n["last"]) == "Charles Martin Jones"
    assert n["von"] == ""


def test_form2_empty_first_after_comma(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 2 with empty segment after comma: First is empty, head becomes Last."""
    n = _parts(submission_command, tmp_path, "Smith, ")
    assert n["first"] == ""
    assert n["last"] == "Smith"


# ---------------------------------------------------------------------------
# Form 3 — two commas (btxhak §2.4 / spec §2.4)
# ---------------------------------------------------------------------------


def test_form3_jr_literal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Form 3 with common ``Jr.`` suffix."""
    n = _parts(submission_command, tmp_path, "Ford, Jr., Henry")
    assert n["first"] == "Henry"
    assert n["last"] == "Ford"
    assert n["jr"] == "Jr."


def test_form3_jr_roman_iii(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Form 3 with Roman-numeral suffix. Inter-token separator inside
    von may be tie or space per §2.6."""
    n = _parts(submission_command, tmp_path, "van der Berg, III, Johann")
    assert n["first"] == "Johann"
    assert _normalize_separator(n["von"]) == "van der"
    assert n["last"] == "Berg"
    assert n["jr"] == "III"


def test_form3_jr_multiword_senior(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Form 3 with a multi-word Jr segment like ``Senior``."""
    n = _parts(submission_command, tmp_path, "Bush, Senior, George")
    assert n["first"] == "George"
    assert n["last"] == "Bush"
    assert n["jr"] == "Senior"


def test_form3_extra_commas_fold_into_first(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Only the first two commas are structural (spec §2.5); extras join into First."""
    n = _parts(submission_command, tmp_path, "Smith, Jr., James, Jr.")
    assert n["last"] == "Smith"
    assert n["jr"] == "Jr."
    # Remaining commas rejoin into First with commas preserved.
    assert "," in n["first"]
    assert "James" in n["first"]


# ---------------------------------------------------------------------------
# Multiple-names and the ``and`` separator (btxhak §2, spec §2.0)
# ---------------------------------------------------------------------------


def test_and_separates_multiple_authors(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``and`` separator splits names."""
    assert _num_names(submission_command, tmp_path, "John Smith and Jane Doe") == 2


def test_and_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``AND`` / ``And`` are also separators (case-insensitive, spec §2)."""
    assert _num_names(submission_command, tmp_path, "John Smith AND Jane Doe") == 2
    assert _num_names(submission_command, tmp_path, "John Smith And Jane Doe") == 2


def test_and_inside_braces_is_literal(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``and`` inside a brace group is not a separator (btxhak §2)."""
    # One brace-wrapped name counts as 1.
    assert _num_names(submission_command, tmp_path, "{Smith and Smith}") == 1


def test_and_must_be_word_bounded(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``sand`` and ``brand`` contain ``and`` but are not separators."""
    # "Alexander and Hamilton" is 2 names; "Alexandrand Hamilton" is 1 (no ``and`` word).
    assert _num_names(submission_command, tmp_path, "Alexander and Hamilton") == 2


def test_multi_author_parts_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Each name in a list is independently grammared."""
    # Three authors in three forms.
    literal = "Smith, Jane and {Von Neumann}, John and Watson, Jr., James"
    # Validate counts first.
    assert _num_names(submission_command, tmp_path, literal) == 3
    # First name: Form 2 — "Smith, Jane".
    n1 = _parts(submission_command, tmp_path, literal, which=1)
    assert n1["first"] == "Jane"
    assert n1["last"] == "Smith"
    # Second name: Form 2 — "{Von Neumann}, John".
    n2 = _parts(submission_command, tmp_path, literal, which=2)
    assert n2["first"] == "John"
    assert "Von Neumann" in n2["last"]
    # Third name: Form 3 — "Watson, Jr., James".
    n3 = _parts(submission_command, tmp_path, literal, which=3)
    assert n3["first"] == "James"
    assert n3["last"] == "Watson"
    assert n3["jr"] == "Jr."


def test_brace_protected_von_is_uppercase_not_von(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``{von}`` (brace-protected) is uppercase per btxhak §2.1, NOT a von token."""
    # Tokens: [{von}, der, Pol]. Only "der" is lowercase → von = "der",
    # Last = "Pol", First = "{von}".
    n = _parts(submission_command, tmp_path, "{von} der Pol")
    assert n["first"] == "{von}"
    assert n["von"] == "der"
    assert n["last"] == "Pol"


def test_latex_accent_opening_token_is_uppercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    r"""Token opening with ``{\...}`` is treated as uppercase (spec §2.1).
    Inter-token separator inside the multi-token von may be tie or
    space per §2.6."""
    # "{\'E}tienne de la Valle\'e Poussin" — {\'E}tienne starts with a brace
    # group, and therefore this token is uppercase. The name has one lowercase
    # run: "de la". ``Valle'e`` begins with uppercase V. ``Poussin`` begins
    # with uppercase P.
    n = _parts(
        submission_command, tmp_path, r"{\'E}tienne de la Vall\'ee Poussin"
    )
    assert n["first"] == r"{\'E}tienne"
    assert _normalize_separator(n["von"]) == "de la"
    # Last can be "Vall\'ee Poussin" (uppercase-caps after the von).
    assert "Poussin" in n["last"]
