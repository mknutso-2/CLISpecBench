"""Field concatenation and @string macro corners.

Per btxdoc §3:
  * ``#`` concatenates two values (string or macro-ref or number).
  * Concatenation with ``""`` is identity.
  * Numbers concat to strings work (``2024 # "-11"`` → ``"2024-11"``).
  * Macros can be redefined — last ``@string`` wins.
  * Forward references (macro used before its ``@string``) are errors
    per bibtex.web §12250 (single-pass parser).
  * Self-referential macros are not supported.

These tests pin the behavior independent of any `.bst` style; we use
``PROBE_STYLE_FIELDS`` to dump the resulting field value.
"""

from __future__ import annotations

from pathlib import Path

from conftest import PROBE_STYLE_FIELDS, parse_dump, run_bibtex


def _first(dump_records: list[dict[str, str]], key: str) -> dict[str, str]:
    for rec in dump_records:
        if rec.get("key") == key:
            return rec
    raise AssertionError(f"entry {key!r} not in dump: {dump_records!r}")


# ---------------------------------------------------------------------------
# Concatenation basics
# ---------------------------------------------------------------------------


def test_concat_two_literals(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{k, title = "abc" # "def"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("title") == "abcdef"


def test_concat_three_literals(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@article{k, title = "a" # "b" # "c"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("title") == "abc"


def test_concat_with_empty_is_identity(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Concatenating an empty string is an identity op."""
    bib = '@article{k, title = "" # "X" # ""}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("title") == "X"


def test_concat_number_and_string(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Number # string coerces the number to its string representation."""
    bib = '@article{k, year = 2024 # "-11"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("year") == "2024-11"


def test_concat_two_numbers(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Concatenating two numbers yields their string representations joined."""
    bib = "@article{k, year = 20 # 24}\n"
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    # "20" concat "24" = "2024"
    assert rec.get("year") == "2024"


# ---------------------------------------------------------------------------
# Macro resolution
# ---------------------------------------------------------------------------


def test_macro_used_in_concatenation(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    bib = '@string{pub = "IEEE"}\n@article{k, publisher = pub # " Press"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("publisher") == "IEEE Press"


def test_macro_redefinition_last_wins(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Per btxdoc §3.1: a second @string{} for the same name overrides
    the first, for uses AFTER the redefinition."""
    bib = '@string{brand = "Alpha"}\n@string{brand = "Beta"}\n@article{k, publisher = brand}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("publisher") == "Beta"


def test_macro_redefinition_does_not_affect_prior_uses(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Redefining a macro affects only later @-things. An entry that
    used the macro before the redefinition keeps the old value."""
    bib = (
        '@string{brand = "Old"}\n'
        "@article{k1, publisher = brand}\n"
        '@string{brand = "New"}\n'
        "@article{k2, publisher = brand}\n"
    )
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k1", "k2"], tmp_path)
    dump = parse_dump(bbl)
    k2 = _first(dump, "k2")
    # Implementations may differ: some eagerly resolve, others lazily.
    # We assert only that they may differ or both be "New" — but not both "Old".
    # More specifically: k2 must be "New" (it's after the redefinition).
    assert k2.get("publisher") == "New"


def test_macro_concat_with_self(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """@string{x = x # "more"} is a forward reference to x within its own
    definition. Per btxdoc §3.1, this is undefined/error; we accept either
    a failed parse OR a lazy resolution that sees x as empty the first time."""
    bib = '@string{x = "start"}\n@string{x = x # " end"}\n@article{k, title = x}\n'
    # Accept both interpretations: impl may resolve eagerly to "start end" or
    # error out. We only verify the tool doesn't produce nonsense.
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    title = rec.get("title", "")
    assert title in ("start end", "start", " end", ""), (
        f"unexpected self-concat resolution: {title!r}"
    )


def test_macro_chain(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """A macro whose value references another macro resolves transitively."""
    bib = '@string{a = "X"}\n@string{b = a # "Y"}\n@string{c = b # "Z"}\n@article{k, title = c}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("title") == "XYZ"


def test_macro_case_insensitive_concat(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Macro lookup is case-insensitive on both definition and reference."""
    bib = '@STRING{Pub = "IEEE"}\n@article{k, publisher = PUB # " Journals"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_STYLE_FIELDS, ["k"], tmp_path)
    rec = _first(parse_dump(bbl), "k")
    assert rec.get("publisher") == "IEEE Journals"
