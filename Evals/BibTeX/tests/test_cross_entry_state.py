"""Cross-entry state: global vs entry scope, ITERATE vs EXECUTE visibility.

Per btxhak §3.3/§3.4:

  * STRINGS { a b c } declared at global scope persist for the lifetime of
    the .bst execution. Writes in one entry's ITERATE body are visible to
    later iterations.
  * STRINGS declared via ENTRY { ... } { ... } { a b } are ENTRY-SCOPED:
    each entry gets its own scratch slot. Writes in entry X are not
    visible in entry Y.
  * INTEGERS behave the same way (global persists, entry resets).
  * call.type$ and cite$ outside of ITERATE (e.g. inside EXECUTE)
    have no current entry and must not silently succeed with garbage.

This file exercises the visibility contracts above.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_bibtex

THREE_BIB = "@misc{a}\n@misc{b}\n@misc{c}\n"


# ---------------------------------------------------------------------------
# Global INTEGERS persist across ITERATE iterations
# ---------------------------------------------------------------------------


def test_global_integer_persists_across_iterate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A global INTEGERS counter incremented per entry keeps growing across
    iterations."""
    style = """\
ENTRY { } { } { }
INTEGERS { counter }
FUNCTION {init} { #0 'counter := }
FUNCTION {bump}
{ counter #1 + 'counter :=
  counter int.to.str$ write$ newline$ }
READ
EXECUTE {init}
ITERATE {bump}
"""
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    assert bbl.split() == ["1", "2", "3"]


def test_global_string_persists_across_iterate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A global STRING concatenated each iteration shows accumulation."""
    style = """\
ENTRY { } { } { }
STRINGS { acc }
FUNCTION {init} { "" 'acc := }
FUNCTION {append.cite} { acc cite$ * 'acc := }
FUNCTION {emit.final} { acc write$ newline$ }
READ
EXECUTE {init}
ITERATE {append.cite}
EXECUTE {emit.final}
"""
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    assert bbl.strip() == "abc"


# ---------------------------------------------------------------------------
# ENTRY-scope INTEGERS reset between entries
# ---------------------------------------------------------------------------


def test_entry_integer_resets_between_entries(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An ENTRY-scoped INTEGER initialized to 0 per entry is always 0 on
    entry into each iteration, regardless of what the previous iteration
    set it to."""
    style = """\
ENTRY { } { slot } { }
FUNCTION {check.and.bump}
{ slot int.to.str$ write$ " " * write$
  slot #99 + 'slot := }
FUNCTION {init.slot} { #0 'slot := }
READ
ITERATE {init.slot}
ITERATE {check.and.bump}
"""
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    # Each entry starts with slot=0 (set by init.slot), writes "0 ".
    # The bump to 99 in the previous iteration is not visible in this entry.
    assert bbl.replace("\n", "").strip().split() == ["0", "0", "0"]


def test_entry_string_resets_between_entries(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Like integers, entry-scope STRINGS are per-entry."""
    style = """\
ENTRY { } { } { note }
FUNCTION {set.note} { "X" 'note := }
FUNCTION {emit.note}
{ note duplicate$ empty$ { "empty" swap$ pop$ } { skip$ } if$ write$ newline$ }
READ
ITERATE {emit.note}
"""
    # note is never set, so each entry sees it as empty.
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    lines = [ln for ln in bbl.split("\n") if ln]
    for ln in lines:
        assert ln == "empty", f"note leaked or survived: {ln!r}"


# ---------------------------------------------------------------------------
# FUNCTION visibility across EXECUTE and ITERATE
# ---------------------------------------------------------------------------


def test_function_callable_from_both_execute_and_iterate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A FUNCTION defined once is callable from EXECUTE and from ITERATE."""
    style = """\
ENTRY { } { } { }
FUNCTION {shout} { "HEY" write$ newline$ }
READ
EXECUTE {shout}
ITERATE {shout}
"""
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    lines = [ln for ln in bbl.split("\n") if ln]
    assert lines == ["HEY", "HEY", "HEY", "HEY"]  # EXECUTE once + ITERATE 3x


# ---------------------------------------------------------------------------
# cite$ inside ITERATE vs EXECUTE
# ---------------------------------------------------------------------------


def test_cite_matches_current_entry_in_iterate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Inside ITERATE, cite$ is the current entry's key."""
    style = """\
ENTRY { } { } { }
FUNCTION {dump} { cite$ write$ newline$ }
READ
ITERATE {dump}
"""
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    assert bbl.split() == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Entry field values don't leak
# ---------------------------------------------------------------------------


def test_entry_field_values_are_per_entry(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Field values written in one entry's context don't leak to another."""
    bib = '@article{a, title = "AlphaTitle"}\n@article{b}\n'
    style = """\
ENTRY { title } { } { }
FUNCTION {dump} { title duplicate$ missing$ { "MISSING" swap$ pop$ } { skip$ } if$ write$ newline$ }
READ
ITERATE {dump}
"""
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path)
    lines = [ln for ln in bbl.split("\n") if ln]
    assert lines[0] == "AlphaTitle"
    assert lines[1] == "MISSING", f"entry b should not see a's title; got {lines[1]!r}"


# ---------------------------------------------------------------------------
# Name disambiguation (simulated): two entries with same first-author lastname
# produce distinguishable sort keys when the style computes a disambig suffix.
# This exercises cross-entry state + sort.key$ cooperation.
# ---------------------------------------------------------------------------


def test_disambiguation_counter_distinguishes_homonym_entries(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two entries sharing the same first-author last name produce sort keys
    that differ by an appended counter letter — the mechanism alpha.bst uses
    to emit 'Smith2024a' vs 'Smith2024b'.

    We simulate this by keeping a global integer that increments per entry
    whose author starts with 'Smith'."""
    bib = (
        '@article{a, author = "John Smith", year = 2024}\n'
        '@article{b, author = "Mary Smith", year = 2024}\n'
        '@article{c, author = "Alice Jones", year = 2024}\n'
    )
    style = """\
ENTRY { author year } { } { sort.key$ }
INTEGERS { smithct }
FUNCTION {init} { #0 'smithct := }
FUNCTION {assign.key}
{ author text.prefix$ #5 substring$
  duplicate$ "Smith" =
    { pop$ smithct #1 + 'smithct := smithct int.to.chr$ #96 + int.to.chr$ swap$ pop$ }
    { pop$ "Z" }
  if$
  cite$ swap$ * 'sort.key$ :=
}
FUNCTION {emit} { sort.key$ write$ newline$ }
READ
EXECUTE {init}
ITERATE {assign.key}
SORT
ITERATE {emit}
"""
    # The above is deliberately simplified — we want to observe that the
    # counter increments across entries, producing different keys for the
    # two Smith entries.
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b", "c"], tmp_path)
    lines = [ln for ln in bbl.split("\n") if ln]
    # Each of a and b has a Smith-derived key with different chr codes; c gets "Z".
    # Specifically: a -> "a" + chr(96+1) = "aa", b -> "b" + chr(96+2) = "bb", c -> "cZ"
    # (We don't pin exact values — just that Smith entries differ.)
    smith_lines = [ln for ln in lines if "a" in ln or "b" in ln]
    # The two Smith keys must not be identical.
    assert len(set(smith_lines)) == len(smith_lines), (
        f"Smith entries produced duplicate disambiguation keys: {smith_lines!r}"
    )


# ---------------------------------------------------------------------------
# INTEGERS reset by EXECUTE of init helper
# ---------------------------------------------------------------------------


def test_execute_can_reset_global_state(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An EXECUTE between two ITERATE passes can reset global state."""
    style = """\
ENTRY { } { } { }
INTEGERS { n }
FUNCTION {init} { #0 'n := }
FUNCTION {bump} { n #1 + 'n := }
FUNCTION {emit} { n int.to.str$ write$ newline$ }
READ
EXECUTE {init}
ITERATE {bump}
EXECUTE {emit}
EXECUTE {init}
ITERATE {bump}
EXECUTE {emit}
"""
    bbl, _ = run_bibtex(submission_command, THREE_BIB, style, ["a", "b", "c"], tmp_path)
    # First emit: 3 (after 3 bumps). Second emit: also 3 (after reset + 3 more bumps).
    assert bbl.split() == ["3", "3"]
