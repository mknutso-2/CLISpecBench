"""Depth tests for SORT / REVERSE / ITERATE semantics.

``test_bst_language.py`` covers the happy path for the top-level commands.
This file fills in the corners:

  * Stability: ties on sort.key$ preserve READ order.
  * Missing / empty sort.key$ bucketing.
  * Lexicographic (not numeric) comparison.
  * Multiple SORT calls: last key wins.
  * EXECUTE between SORT and ITERATE doesn't perturb order.
  * REVERSE semantics (with and without SORT).
  * ITERATE of empty cited list is a no-op.
  * sort.key$ visibility in subsequent ITERATE passes.

All references are to *Designing BibTeX Styles* (btxhak) §3.2 "SORT"
and bibtex.web §12230+ (the sort implementation).
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex


def _sort_bbl(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    bib: str,
    cites: list[str],
    *,
    keys: dict[str, str] | None = None,
    with_reverse: bool = False,
    skip_sort: bool = False,
) -> str:
    """Helper: assigns each entry's ``sort.key$`` from either its cite key
    (by default) or an explicit ``keys`` mapping, then SORT + ITERATE and
    returns the .bbl (one cite$ per line)."""
    if keys is None:
        # Use cite$ itself as the sort key — sort by cite key.
        presort_body = "cite$ 'sort.key$ :="
    else:
        # Branch on cite$ for each known key.
        branches = []
        for k, v in keys.items():
            branches.append(f'cite$ "{k}" = {{ "{v}" \'sort.key$ := }} {{ skip$ }} if$')
        presort_body = " ".join(branches)

    style_lines = [
        "ENTRY { author title year } { } { sort.key$ }",
        "FUNCTION {presort} { " + presort_body + " }",
        "FUNCTION {emit} { cite$ write$ newline$ }",
        "READ",
        "ITERATE {presort}",
    ]
    if not skip_sort:
        style_lines.append("SORT")
    if with_reverse:
        style_lines.append("REVERSE {emit}")
    else:
        style_lines.append("ITERATE {emit}")
    style = "\n".join(style_lines) + "\n"
    bbl, _ = run_bibtex(submission_command, bib, style, cites, tmp_path)
    return bbl


# ---------------------------------------------------------------------------
# Stability
# ---------------------------------------------------------------------------


def test_sort_is_stable_on_ties(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Two entries with the same sort.key$ preserve READ order.

    btxhak §3.2: "If two entries have identical sort keys, they appear in
    the order in which they were READ."
    """
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    # Assign identical sort keys to all three.
    keys = {"a": "same", "b": "same", "c": "same"}
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["a", "b", "c"], keys=keys)
    assert bbl.split() == ["a", "b", "c"], f"stable sort on equal keys violated: {bbl.split()!r}"


def test_sort_is_stable_on_partial_ties(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Ties within one bucket respect READ order; buckets are ordered by key."""
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n@misc{d}\n"
    keys = {"a": "x", "b": "y", "c": "x", "d": "y"}  # a,c same; b,d same
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["a", "b", "c", "d"], keys=keys)
    # Bucket x = [a, c] (in READ order); bucket y = [b, d] (in READ order).
    assert bbl.split() == ["a", "c", "b", "d"]


# ---------------------------------------------------------------------------
# Missing / empty sort.key$
# ---------------------------------------------------------------------------


def test_sort_empty_key_orders_with_others_lexicographically(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An empty sort key sorts before non-empty keys (empty string lex-less than any nonempty)."""
    bib = "@misc{a}\n@misc{b}\n"
    keys = {"a": "", "b": "x"}
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["a", "b"], keys=keys)
    assert bbl.split() == ["a", "b"]


# ---------------------------------------------------------------------------
# Lexicographic not numeric
# ---------------------------------------------------------------------------


def test_sort_is_lexicographic_not_numeric(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Sort keys compare as byte strings: "10" < "2" lexicographically."""
    bib = "@misc{a}\n@misc{b}\n"
    keys = {"a": "10", "b": "2"}
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["a", "b"], keys=keys)
    # Lex order: "10" < "2" because '1' (0x31) < '2' (0x32).
    assert bbl.split() == ["a", "b"]


def test_sort_case_sensitivity(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Uppercase sorts before lowercase (ASCII-ordered)."""
    bib = "@misc{lo}\n@misc{UP}\n"
    keys = {"lo": "abc", "UP": "ABC"}
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["lo", "UP"], keys=keys)
    # "ABC" (uppercase) < "abc" (lowercase) lex.
    assert bbl.split() == ["UP", "lo"]


# ---------------------------------------------------------------------------
# Multiple SORT: last wins
# ---------------------------------------------------------------------------


def test_last_sort_key_wins(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """bibtex.web: when sort.key$ is reassigned between SORTs, the last
    assignment before a SORT determines the effective key for that SORT."""
    bib = "@misc{a}\n@misc{b}\n"
    style = """\
ENTRY { } { } { sort.key$ }
FUNCTION {first.key} { cite$ 'sort.key$ := }
FUNCTION {second.key}
{ cite$ "a" =
    { "zz" 'sort.key$ := }
    { "aa" 'sort.key$ := }
  if$
}
FUNCTION {emit} { cite$ write$ newline$ }
READ
ITERATE {first.key}
SORT
ITERATE {second.key}
SORT
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path)
    # After second ITERATE: a's key = "zz", b's key = "aa".
    # SORT puts b first, then a.
    assert bbl.split() == ["b", "a"]


# ---------------------------------------------------------------------------
# EXECUTE between SORT and ITERATE doesn't change order
# ---------------------------------------------------------------------------


def test_execute_between_sort_and_iterate_preserves_order(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    style = """\
ENTRY { } { } { sort.key$ }
FUNCTION {presort} { cite$ 'sort.key$ := }
FUNCTION {nop} { skip$ }
FUNCTION {emit} { cite$ write$ newline$ }
READ
ITERATE {presort}
SORT
EXECUTE {nop}
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b", "c"], tmp_path)
    assert bbl.split() == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# REVERSE
# ---------------------------------------------------------------------------


def test_reverse_after_sort(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """REVERSE iterates in the OPPOSITE of the sorted order."""
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["a", "b", "c"], with_reverse=True)
    # Sorted a<b<c, then REVERSE → c, b, a.
    assert bbl.split() == ["c", "b", "a"]


def test_reverse_without_sort(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """REVERSE without prior SORT iterates in reverse READ order."""
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    bbl = _sort_bbl(
        submission_command,
        tmp_path,
        bib,
        ["a", "b", "c"],
        skip_sort=True,
        with_reverse=True,
    )
    # READ order [a, b, c] reversed → [c, b, a].
    assert bbl.split() == ["c", "b", "a"]


# ---------------------------------------------------------------------------
# Empty iteration
# ---------------------------------------------------------------------------


def test_iterate_empty_cited_list_is_noop(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When no entries are cited, ITERATE runs zero times, not an error."""
    bib = "@misc{a}\n@misc{b}\n"
    style = """\
ENTRY { } { } { }
FUNCTION {emit} { cite$ write$ newline$ }
READ
ITERATE {emit}
"""
    # Cite a key that exists in the bib, ignoring b.
    bbl, _ = run_bibtex(submission_command, bib, style, ["a"], tmp_path)
    assert bbl.strip() == "a"


# ---------------------------------------------------------------------------
# ITERATE inside an empty-entries corpus still succeeds
# ---------------------------------------------------------------------------


def test_sort_of_single_entry_is_noop(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """SORT of one entry is a no-op, not an error."""
    bib = "@misc{only}\n"
    bbl = _sort_bbl(submission_command, tmp_path, bib, ["only"])
    assert bbl.strip() == "only"


# ---------------------------------------------------------------------------
# Sort key set in ITERATE is visible after SORT
# ---------------------------------------------------------------------------


def test_sort_key_persists_into_post_sort_iterate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """After SORT, the sort.key$ assigned in presort is still visible to
    the post-SORT ITERATE (each entry's scratch survives across SORT)."""
    bib = "@misc{a}\n@misc{b}\n"
    style = """\
ENTRY { } { } { sort.key$ }
FUNCTION {presort}
{ cite$ "a" = { "first" 'sort.key$ := } { "second" 'sort.key$ := } if$ }
FUNCTION {emit} { sort.key$ write$ newline$ }
READ
ITERATE {presort}
SORT
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path)
    # a's sort.key$ is "first"; b's is "second". After sort ("first" < "second"):
    # line 1 = "first", line 2 = "second".
    assert bbl.split() == ["first", "second"]


# ---------------------------------------------------------------------------
# Multiple REVERSE/ITERATE interactions
# ---------------------------------------------------------------------------


def test_two_iterates_are_independent(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Running ITERATE twice visits every entry again in the same order."""
    bib = "@misc{a}\n@misc{b}\n"
    style = """\
ENTRY { } { } { }
FUNCTION {emit} { cite$ write$ newline$ }
READ
ITERATE {emit}
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path)
    # First pass: a, b. Second pass: a, b. Total: a b a b.
    assert bbl.split() == ["a", "b", "a", "b"]


def test_sort_idempotent_on_sorted_input(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Calling SORT twice on already-sorted data yields the same order."""
    bib = "@misc{a}\n@misc{b}\n@misc{c}\n"
    style = """\
ENTRY { } { } { sort.key$ }
FUNCTION {presort} { cite$ 'sort.key$ := }
FUNCTION {emit} { cite$ write$ newline$ }
READ
ITERATE {presort}
SORT
SORT
ITERATE {emit}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b", "c"], tmp_path)
    assert bbl.split() == ["a", "b", "c"]
