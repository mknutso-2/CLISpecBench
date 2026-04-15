"""Reference fixture tests — parse the three real-world IGES files.

Ports ``Evals/IGES-SDK/tests/integration/test_reference_files.cpp`` to drive
the ``iges parse`` CLI. ex1/ex2/ex3 are Burkardt-collection files from the
IGES 5.3 appendices; together they exercise most of the spec surface.

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

from iges_support import parse_iges_to_json

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


# -----------------------------------------------------------------
# ex1.iges — IC library cell (subfigures, copious data, connect points)
# -----------------------------------------------------------------
def test_ex1_parses_with_expected_global_and_entity_count(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    parsed = parse_iges_to_json(submission_command, FIXTURES / "ex1.iges", tmp_path)

    start = parsed["start_lines"]
    assert isinstance(start, list)
    assert len(start) == 2

    g = parsed["global"]
    assert isinstance(g, dict)
    assert g["product_id_sender"] == "5MICRONLIB"
    assert g["file_name"] == "PADIN"
    # Unit flag 9 in the spec maps to "microns".
    assert g["units"] == "microns"

    entities = parsed["entities"]
    assert isinstance(entities, list)
    assert len(entities) == 21


def test_ex1_entity_type_mix(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    parsed = parse_iges_to_json(submission_command, FIXTURES / "ex1.iges", tmp_path)
    counts = _entity_type_counts(parsed)

    assert counts[308] == 2      # Subfigure Definition (PADBLK, CONTACT)
    assert counts[106] >= 10     # Copious Data
    assert counts[406] == 1      # LINWIDTH Property
    # Regression: ex1 contains Connect Point (132), Network Subfigure
    # Definition (320), and Rectangular Array (412) entities with
    # defaulted fields — the three parsers fixed 2026-04-14.
    assert counts[132] >= 1
    assert counts[320] >= 1
    assert counts[412] >= 1


# -----------------------------------------------------------------
# ex2.iges — Mechanical part with dimensions and annotations
# -----------------------------------------------------------------
def test_ex2_parses_with_expected_global(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    parsed = parse_iges_to_json(submission_command, FIXTURES / "ex2.iges", tmp_path)

    g = parsed["global"]
    assert isinstance(g, dict)
    assert g["product_id_sender"] == "PANEL123"

    entities = parsed["entities"]
    assert isinstance(entities, list)
    assert len(entities) > 20


def test_ex2_contains_geometry_and_annotation(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    parsed = parse_iges_to_json(submission_command, FIXTURES / "ex2.iges", tmp_path)
    counts = _entity_type_counts(parsed)

    assert counts[110] > 0                              # Lines
    assert counts[100] > 0                              # Circular arcs
    assert counts[116] > 0                              # Points
    assert counts[212] > 0                              # General Notes
    assert counts[214] > 0                              # Leader Arrows
    assert counts[216] + counts[218] + counts[222] > 0  # Dimensions


# -----------------------------------------------------------------
# ex3.iges — View/Drawing with transformation matrices
# -----------------------------------------------------------------
def test_ex3_parses_with_expected_global(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    parsed = parse_iges_to_json(submission_command, FIXTURES / "ex3.iges", tmp_path)

    g = parsed["global"]
    assert isinstance(g, dict)
    assert g["product_id_sender"] == "VIEWDWG2"

    entities = parsed["entities"]
    assert isinstance(entities, list)
    assert len(entities) > 10


def test_ex3_contains_view_drawing_and_xform(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    parsed = parse_iges_to_json(submission_command, FIXTURES / "ex3.iges", tmp_path)
    counts = _entity_type_counts(parsed)

    assert counts[410] > 0   # View
    assert counts[404] > 0   # Drawing
    assert counts[124] > 0   # Transformation Matrix
