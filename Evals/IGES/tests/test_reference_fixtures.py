"""One integration observation per appendix file: parse and stable roundtrip.

Ports ``Evals/IGES-SDK/tests/integration/test_reference_files.cpp`` to drive
the ``iges parse`` CLI. ex1/ex2/ex3 are Burkardt-collection files from the
IGES appendices. Hidden copies normalize status padding (§2.2.4.4.9) and
ignored positive structure values (§2.2.4.4.3) to avoid public-contract conflicts.

Keep each file's observations together: five separately scored cases used to
fail on the same initial parse, amplifying one defect fivefold. These are
deliberately integration cases; focused tests elsewhere isolate individual
entities, Global fields, physical writing and validation rules.

These fixtures are the regression fence for the three defaulted-field
parser fixes landed 2026-04-14 (Connect Point §4.26 cid/cfn, Network
Subfigure Definition §4.22 prd, Rectangular Array §4.41 ddf). ex1 in
particular would fail to parse before those fixes.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import pytest

from iges_support import assert_semantic_equal, parse_iges_to_json, roundtrip_iges

FIXTURES = Path(__file__).parent / "data"


def _entity_type_counts(parsed: dict[str, object]) -> Counter[int]:
    entities = parsed["entities"]
    assert isinstance(entities, list)
    counts: Counter[int] = Counter()
    for record in entities:
        assert isinstance(record, dict)
        entity = record["entity"]
        assert isinstance(entity, dict)
        t = entity["type"]
        assert isinstance(t, int)
        counts[t] += 1
    return counts


def _check_ex1(parsed: dict[str, object]) -> None:
    start = parsed["start_lines"]
    assert isinstance(start, list)
    assert len(start) == 2

    g = parsed["global"]
    assert isinstance(g, dict)
    assert g["product_id_sender"] == "5MICRONLIB"
    assert g["file_name"] == "PADIN"
    # Unit flag 9 in the spec maps to "microns".
    assert g["units"] == "microns"
    counts = _entity_type_counts(parsed)

    assert counts[308] == 2  # Subfigure Definition (PADBLK, CONTACT)
    assert counts[106] >= 10  # Copious Data
    assert counts[406] == 1  # LINWIDTH Property
    # Regression: ex1 contains Connect Point (132), Network Subfigure
    # Definition (320), and Rectangular Array (412) entities with
    # defaulted fields — the three parsers fixed 2026-04-14.
    assert counts[132] >= 1
    assert counts[320] >= 1
    assert counts[412] >= 1


def _check_ex2(parsed: dict[str, object]) -> None:
    g = parsed["global"]
    assert isinstance(g, dict)
    assert g["product_id_sender"] == "PANEL123"
    counts = _entity_type_counts(parsed)

    assert counts[110] > 0  # Lines
    assert counts[100] > 0  # Circular arcs
    assert counts[116] > 0  # Points
    assert counts[212] > 0  # General Notes
    assert counts[214] > 0  # Leader Arrows
    assert counts[216] + counts[218] + counts[222] > 0  # Dimensions


def _check_ex3(parsed: dict[str, object]) -> None:
    g = parsed["global"]
    assert isinstance(g, dict)
    assert g["product_id_sender"] == "VIEWDWG2"
    counts = _entity_type_counts(parsed)

    assert counts[410] > 0  # View
    assert counts[404] > 0  # Drawing
    assert counts[124] > 0  # Transformation Matrix


@pytest.mark.parametrize(
    ("name", "expected_count"),
    [("ex1.iges", 21), ("ex2.iges", 90), ("ex3.iges", 109)],
)
def test_appendix_file_parse_and_roundtrip(
    submission_command: Sequence[str], tmp_path: Path, name: str, expected_count: int
) -> None:
    # Technical requirements §1.2/§4: parse, preserve canonical entity data,
    # and produce a byte-stable normalized roundtrip. Retain every prior
    # appendix observation, but count this shared workflow only once per file.
    src = FIXTURES / name
    original = parse_iges_to_json(submission_command, src, tmp_path, name="original")
    {"ex1.iges": _check_ex1, "ex2.iges": _check_ex2, "ex3.iges": _check_ex3}[name](original)
    first = roundtrip_iges(submission_command, src, tmp_path, name="first")
    reparsed = parse_iges_to_json(submission_command, first, tmp_path, name="reparsed")
    assert len(original["entities"]) == expected_count
    assert len(reparsed["entities"]) == expected_count
    for orig, rt in zip(original["entities"], reparsed["entities"], strict=True):
        assert orig["entity"]["type"] == rt["entity"]["type"]
        assert orig["entity"]["form"] == rt["entity"]["form"]
        # §3 permits bounded real serialization error; discrete fields remain
        # exact. Use the same public tolerance as the focused semantic tests.
        assert_semantic_equal(rt["entity"]["data"], orig["entity"]["data"])
    second = roundtrip_iges(submission_command, first, tmp_path, name="second")
    assert first.read_bytes() == second.read_bytes()
