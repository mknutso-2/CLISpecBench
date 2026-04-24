"""Author-name grammar tests, observed via format.name$ with full-form format units."""

from __future__ import annotations

from pathlib import Path

from conftest import PROBE_STYLE_NAMES, parse_name_dump, run_bibtex


def _one_name(submission_command: tuple[str, ...], tmp_path: Path, literal: str) -> dict[str, str]:
    bib = f'@article{{k, author = "{literal}"}}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_NAMES, ["k"], tmp_path)
    entries = parse_name_dump(bbl)
    assert len(entries) == 1
    assert entries[0]["key"] == "k"
    assert len(entries[0]["names"]) == 1
    return entries[0]["names"][0]


def _names(
    submission_command: tuple[str, ...], tmp_path: Path, literal: str
) -> list[dict[str, str]]:
    bib = f'@article{{k, author = "{literal}"}}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_NAMES, ["k"], tmp_path)
    entries = parse_name_dump(bbl)
    return entries[0]["names"]


# --- Form 1: no commas ---


def test_form1_simple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "John Smith")
    assert n["first"] == "John"
    assert n["last"] == "Smith"


def test_form1_with_von(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "John van der Pol")
    assert n["first"] == "John"
    assert n["von"] == "van der"
    assert n["last"] == "Pol"


def test_form1_von_without_first(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "van der Pol")
    assert n["first"] == ""
    assert n["von"] == "van der"
    assert n["last"] == "Pol"


def test_form1_all_lowercase(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "van de")
    # All-lowercase head: von emptied, last absorbs.
    assert n["first"] == ""
    assert n["von"] == ""
    assert n["last"] == "van de"


def test_form1_single_token(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "Plato")
    assert n["last"] == "Plato"


def test_form1_brace_protected_is_uppercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    n = _one_name(submission_command, tmp_path, "{van der} Pol")
    # {van der} is a single uppercase-like token before the last token.
    assert n["first"] == "{van der}"
    assert n["last"] == "Pol"


# --- Form 2: one comma ---


def test_form2_simple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "Smith, John")
    assert n["first"] == "John"
    assert n["last"] == "Smith"


def test_form2_with_von(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "van der Pol, Balthasar")
    assert n["first"] == "Balthasar"
    assert n["von"] == "van der"
    assert n["last"] == "Pol"


def test_form2_leading_caps_prepend_to_last(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    n = _one_name(submission_command, tmp_path, "Foo van der Pol, Charles")
    assert n["first"] == "Charles"
    assert n["von"] == "van der"
    assert n["last"] == "Foo Pol"


# --- Form 3: two commas ---


def test_form3_simple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "Ford, Jr., Henry")
    assert n["first"] == "Henry"
    assert n["last"] == "Ford"
    assert n["jr"] == "Jr."


def test_form3_with_von(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    n = _one_name(submission_command, tmp_path, "van der Berg, III, Johann")
    assert n["first"] == "Johann"
    assert n["von"] == "van der"
    assert n["last"] == "Berg"
    assert n["jr"] == "III"


# --- And-separator ---


def test_multiple_authors(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    names = _names(submission_command, tmp_path, "John Smith and Jane Doe")
    assert len(names) == 2
    assert names[0]["last"] == "Smith"
    assert names[1]["last"] == "Doe"


def test_and_inside_braces_is_literal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    names = _names(submission_command, tmp_path, "{Smith and Smith}")
    assert len(names) == 1


def test_and_case_insensitive(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    names = _names(submission_command, tmp_path, "John Smith AND Jane Doe")
    assert len(names) == 2


def test_three_authors_mixed_forms(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    names = _names(
        submission_command,
        tmp_path,
        "Smith, Jane and {Von Neumann}, John and Watson, Jr., James D.",
    )
    assert len(names) == 3
    assert names[0]["first"] == "Jane" and names[0]["last"] == "Smith"
    assert "Von Neumann" in names[1]["last"]
    assert names[2]["jr"] == "Jr." and names[2]["first"] == "James D."
