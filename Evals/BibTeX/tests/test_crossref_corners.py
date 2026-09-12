"""Exhaustive crossref tests covering btxdoc §3.1 and summary §1.6.

Crossref rules (from ``btxdoc.tex`` and the summary spec):

- A ``crossref`` field's value (case-insensitive) matches another entry's
  key. The child inherits every field of the parent that the child does
  not itself define. Inherited fields come *after* the child's own
  fields in declaration order (summary §1.6).
- Cross-reference chains are **not** followed transitively. A ``crossref``
  target that itself has a ``crossref`` must not cause grandparent
  fields to be inherited (btxdoc: "you may not reliably nest cross
  references").
- A missing crossref target emits an ``unresolved_crossref`` warning
  (spec §5.3) and the child's fields remain as declared.
- An immediate 2-entry ``crossref`` cycle emits a ``crossref_cycle``
  warning and MUST NOT hang (spec §5.3).
- Lookup is case-insensitive on the key, but the parent's declared
  key casing is preserved elsewhere.
- Child-defined fields override inherited values.

Each test writes its own ``.bst`` and asserts the ``.bbl`` output or
the ``--log`` JSON directly.
"""

from __future__ import annotations

# btxdoc lines 173–178: every cross-referenced parent follows its children.
from pathlib import Path
from typing import Any

import pytest

from conftest import run_bibtex

# A minimal probe that dumps one field per line for one entry. Shared here
# because crossref inheritance is a preparation-phase concern — once the
# field landscape is fixed, our assertion is a simple field value check.
PROBE_SINGLE_ENTRY = """\
ENTRY {
    author title booktitle editor year publisher journal note
    organization series volume number pages month
} { } { }
FUNCTION {dump}
{ "author=" write$ author write$ newline$
  "title=" write$ title write$ newline$
  "booktitle=" write$ booktitle write$ newline$
  "editor=" write$ editor write$ newline$
  "year=" write$ year write$ newline$
  "publisher=" write$ publisher write$ newline$
  "journal=" write$ journal write$ newline$
}
READ
ITERATE {dump}
"""


def _parse_single_dump(bbl: str) -> dict[str, str]:
    """Parse ``key=value`` lines, last occurrence wins."""
    out: dict[str, str] = {}
    for line in bbl.split("\n"):
        if "=" in line:
            k, _, v = line.partition("=")
            out[k] = v
    return out


def _find_warning(log: dict[str, Any] | None, kind: str) -> list[dict[str, Any]]:
    if log is None:
        return []
    return [w for w in log.get("warnings", []) if w.get("kind") == kind]


# ---------------------------------------------------------------------------
# Basic inheritance: child inherits only fields it does NOT define
# ---------------------------------------------------------------------------


def test_child_inherits_missing_fields(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Child missing ``year`` and ``publisher`` inherits them from parent."""
    bib = """
@inproceedings{child, author = "Jones", title = "Paper X", crossref = "parent"}
@proceedings{parent, title = "Proc Vol", year = "2020", publisher = "ACM"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["year"] == "2020"
    assert rec["publisher"] == "ACM"


def test_child_own_field_overrides_inherited(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Child's own field wins when both child and parent define it."""
    bib = """
@inproceedings{child, title = "Child Title", crossref = "parent"}
@proceedings{parent, title = "Parent Title", year = "2020"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["title"] == "Child Title"
    # But still inherited fields the child did not define.
    assert rec["year"] == "2020"


def test_child_without_inheritable_parent_field_is_missing(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """If neither child nor parent defines a field, it stays missing (empty probe output)."""
    bib = """
@inproceedings{child, crossref = "parent"}
@proceedings{parent, title = "T"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    # publisher was defined on neither → missing → empty dump value.
    assert rec["publisher"] == ""


# ---------------------------------------------------------------------------
# Case sensitivity
# ---------------------------------------------------------------------------


def test_crossref_lookup_is_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``crossref = "PARENT"`` matches ``@article{parent, ...}`` (summary §1.6)."""
    bib = """
@article{child, crossref = "PARENT"}
@article{parent, year = "1999"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["year"] == "1999"


def test_crossref_lookup_case_insensitive_other_direction(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """``crossref = "parent"`` also matches ``@article{PARENT, ...}``."""
    bib = """
@article{child, crossref = "parent"}
@article{PARENT, year = "1999"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["year"] == "1999"


def test_crossref_mixed_case_parent_key(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Lookup is case-insensitive with MixedCase keys too."""
    bib = """
@inproceedings{child, crossref = "MIXEDPARENT"}
@proceedings{MixedParent, year = "2020"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["year"] == "2020"


# ---------------------------------------------------------------------------
# Missing target
# ---------------------------------------------------------------------------


def test_unresolved_crossref_emits_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A crossref to a non-existent key emits ``unresolved_crossref`` (spec §5.3)."""
    bib = '@article{child, title = "kept", crossref = "ghost"}\n'
    _, log = run_bibtex(
        submission_command,
        bib,
        PROBE_SINGLE_ENTRY,
        ["child"],
        tmp_path,
        with_log=True,
    )
    warnings = _find_warning(log, "unresolved_crossref")
    assert len(warnings) >= 1


def test_unresolved_crossref_does_not_lose_child_fields(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """With a ghost crossref target, the child's own fields are still present."""
    bib = '@article{child, title = "kept", crossref = "ghost"}\n'
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["title"] == "kept"


# ---------------------------------------------------------------------------
# Cycle detection (spec §5.3 ``crossref_cycle``)
# ---------------------------------------------------------------------------


def test_two_entry_cycle_emits_cycle_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A ↔ B cycle must emit ``crossref_cycle`` and must NOT hang (spec §5.3)."""
    bib = """
@article{a, title = "A", crossref = "b"}
@article{b, title = "B", crossref = "a"}
"""
    # 10s timeout: real hangs become test failures via subprocess timeout.
    _, log = run_bibtex(
        submission_command,
        bib,
        PROBE_SINGLE_ENTRY,
        ["a"],
        tmp_path,
        with_log=True,
        timeout=10,
    )
    cycles = _find_warning(log, "crossref_cycle")
    assert len(cycles) >= 1


def test_cycle_does_not_prevent_output(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Even under a cycle, the child's .bbl output is still produced."""
    bib = """
@article{a, title = "A", crossref = "b"}
@article{b, title = "B", crossref = "a"}
"""
    bbl, _ = run_bibtex(
        submission_command,
        bib,
        PROBE_SINGLE_ENTRY,
        ["a"],
        tmp_path,
        timeout=10,
    )
    rec = _parse_single_dump(bbl)
    # Child's own title remains accessible.
    assert rec["title"] == "A"


# ---------------------------------------------------------------------------
# Non-transitive chain (btxdoc §3.1 + summary §1.6)
# ---------------------------------------------------------------------------


def test_chain_does_not_inherit_from_grandparent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A → B → C: A inherits ONLY B's fields, not C's (spec §1.6, btxdoc)."""
    bib = """
@misc{a, title = "A", crossref = "b"}
@misc{b, year = "2020", crossref = "c"}
@misc{c, publisher = "GRANDPA"}
"""
    bbl, _ = run_bibtex(
        submission_command,
        bib,
        PROBE_SINGLE_ENTRY,
        ["a"],
        tmp_path,
    )
    rec = _parse_single_dump(bbl)
    # B's `year` IS inherited (one level up).
    assert rec["year"] == "2020"
    # C's `publisher` is NOT inherited (transitivity blocked).
    assert rec["publisher"] == ""


def test_chain_child_own_fields_still_present(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """In a 3-entry chain, the child's own fields are preserved."""
    bib = """
@misc{a, title = "MyTitle", crossref = "b"}
@misc{b, year = "2020", crossref = "c"}
@misc{c, publisher = "X"}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["a"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["title"] == "MyTitle"


# ---------------------------------------------------------------------------
# Interaction with @string macros in inherited fields
# ---------------------------------------------------------------------------


def test_inherited_macro_field_is_expanded(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An inherited field whose value is a macro-reference must still be
    expanded via @string resolution (spec §1.5 + §1.6 interaction)."""
    bib = """
@string{pub = "IEEE"}
@inproceedings{child, crossref = "parent"}
@proceedings{parent, publisher = pub}
"""
    bbl, _ = run_bibtex(submission_command, bib, PROBE_SINGLE_ENTRY, ["child"], tmp_path)
    rec = _parse_single_dump(bbl)
    assert rec["publisher"] == "IEEE"


@pytest.mark.parametrize("children", [1, 2])
def test_crossref_parent_inclusion_threshold(
    submission_command: tuple[str, ...], tmp_path: Path, children: int
) -> None:
    # btxdoc lines 163–175 and bibtex.web min_crossrefs=2: an uncited
    # parent is included only after two cited children refer to it. For a
    # single child, inheritance survives but its crossref pointer is removed.
    # Canonical parity corpora use explicit fields so this one rule cannot
    # mask eight independent style executions.
    bib = "".join(f'@misc{{c{i}, crossref = "p"}}\n' for i in range(children))
    bib += '@misc{p, year = "2020"}\n'
    style = r"""
ENTRY { year } { } { }
FUNCTION {emit}
{ cite$ write$ ":" write$
  crossref missing$ { "none" } { crossref } if$ write$
  ":" write$ year write$ newline$
}
READ
ITERATE {emit}
"""
    bbl, _ = run_bibtex(
        submission_command, bib, style, [f"c{i}" for i in range(children)], tmp_path
    )
    expected = ["c0:none:2020"] if children == 1 else ["c0:p:2020", "c1:p:2020", "p:none:2020"]
    assert bbl.splitlines() == expected
