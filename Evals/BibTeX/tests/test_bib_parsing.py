"""Tests for `.bib` parsing observed via a probe .bst style.

A minimal style file (PROBE_STYLE_FIELDS) dumps each cited entry's fields as
`key=value` lines, so we can assert on the .bbl output."""

from __future__ import annotations

from pathlib import Path

from conftest import PROBE_STYLE_FIELDS, parse_dump, run_bibtex


def _entries(bbl: str) -> dict[str, dict[str, str]]:
    return {r["key"]: r for r in parse_dump(bbl)}


def test_simple_article(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{k, author = "Smith", title = "Hello", year = 2024}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _entries(bbl)["k"]
    assert rec["type"] == "article"
    assert rec["author"] == "Smith"
    assert rec["title"] == "Hello"
    assert rec["year"] == "2024"


def test_entry_type_case_insensitive(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@ARTICLE{k, title = "X"}\n@Book{b, title = "Y"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k", "b"], tmp_path)
    e = _entries(bbl)
    assert e["k"]["type"] == "article"
    assert e["b"]["type"] == "book"


def test_key_case_preserved(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{MixedKey99, title = "X"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["MixedKey99"], tmp_path)
    assert "key=MixedKey99" in bbl


def test_field_name_case_insensitive(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{k, Title = "X", AUTHOR = "A"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _entries(bbl)["k"]
    assert rec.get("title") == "X"
    assert rec.get("author") == "A"


def test_paren_delimited_entry(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article(k, title = "X")\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["title"] == "X"


def test_braced_field_value(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = "@article{k, title = {Hello World}}\n"
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["title"] == "Hello World"


def test_number_field_value(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = "@article{k, year = 2024}\n"
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["year"] == "2024"


def test_non_entry_text_before_at_ignored(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = 'Random preamble.\n\n@article{k, title = "X"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["title"] == "X"


def test_trailing_comma_accepted(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{k, title = "X", year = 2024,}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["year"] == "2024"


def test_string_macro_resolution(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@string{pub = "IEEE"}\n@article{k, publisher = pub}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["publisher"] == "IEEE"


def test_string_macro_case_insensitive(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@STRING{Pub = "IEEE"}\n@article{k, publisher = PUB}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["publisher"] == "IEEE"


def test_string_concatenation_hash(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@string{yr = "2024"}\n@article{k, year = yr # "-11"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["year"] == "2024-11"


def test_predefined_month_jan(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = "@article{k, month = jan}\n"
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["month"] == "January"


def test_string_macro_overrides_month(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@string{may = "Mai"}\n@article{k, month = may}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    assert _entries(bbl)["k"]["month"] == "Mai"


def test_crossref_inheritance(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = """
@proceedings{parent, title = "Proc Volume", year = 2020, publisher = "ACM"}
@inproceedings{child, author = "Jones", title = "Paper X", crossref = "parent"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["child"], tmp_path)
    rec = _entries(bbl)["child"]
    assert rec["year"] == "2020"
    assert rec["publisher"] == "ACM"
    assert rec["title"] == "Paper X"  # child's own wins


def test_crossref_case_insensitive_lookup(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = (
        "@proceedings{Parent, year = 2020}\n"
        '@inproceedings{child, crossref = "PARENT", title = "x"}\n'
    )
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["child"], tmp_path)
    assert _entries(bbl)["child"]["year"] == "2020"
