"""Line Entity (Type 110) tests — §4.13 of the IGES 5.3 spec.

Ports the Catch2 tests from ``Evals/IGES-SDK/tests/spec/test_4_13_line_entity.cpp``
to drive the ``iges`` CLI instead of calling parse_line_entity directly.

Each test builds a minimal IGES file containing one Line entity (via
``iges write``) and then exercises the remaining subcommands against it.
"""
# pyright: reportUnknownMemberType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from iges_support import (
    evaluate_entity,
    parse_iges_to_json,
    query_entity,
    roundtrip_iges,
    semantic_roundtrip_json,
    single_line_document,
    write_iges_from_json,
)


# §4.13: "Parameters: X1,Y1,Z1 (start point), X2,Y2,Z2 (terminate point)"
def test_parse_line_from_pd(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path)

    assert parsed["entities"][0]["entity"]["data"]["start"] == [1.0, 2.0, 3.0]
    assert parsed["entities"][0]["entity"]["data"]["terminate"] == [4.0, 5.0, 6.0]


# §4.13: "Each end point is specified relative to the definition space by
# triple coordinates." Start at the origin, terminate elsewhere — §3.2.5
# forbids zero-length curves, so both endpoints cannot be the origin.
def test_line_starting_at_origin(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path)

    data = parsed["entities"][0]["entity"]["data"]
    assert data["start"] == [0.0, 0.0, 0.0]
    assert data["terminate"] == [1.0, 0.0, 0.0]


def test_line_with_negative_coordinates(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((-1.5, 2.5, -3.5), (4.5, -5.5, 6.5))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path)

    data = parsed["entities"][0]["entity"]["data"]
    assert data["start"] == pytest.approx([-1.5, 2.5, -3.5])
    assert data["terminate"] == pytest.approx([4.5, -5.5, 6.5])


# §4.13: "C(t) = P1 + t*(P2 - P1) for 0 <= t <= 1 ... C(0) = P1"
def test_evaluate_at_t_zero_yields_start_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)

    _, payload = evaluate_entity(submission_command, iges_path, 1, 0.0, tmp_path)
    assert payload.get("ok") is True
    assert payload.get("point") == pytest.approx([1.0, 2.0, 3.0])


# §4.13: "... C(1) = P2"
def test_evaluate_at_t_one_yields_terminate_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)

    _, payload = evaluate_entity(submission_command, iges_path, 1, 1.0, tmp_path)
    assert payload.get("ok") is True
    assert payload.get("point") == pytest.approx([4.0, 5.0, 6.0])


# §4.13: "... C(0.5) = midpoint"
def test_evaluate_at_midpoint(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((0.0, 0.0, 0.0), (10.0, 0.0, 0.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)

    _, payload = evaluate_entity(submission_command, iges_path, 1, 0.5, tmp_path)
    assert payload.get("ok") is True
    assert payload.get("point") == pytest.approx([5.0, 0.0, 0.0], abs=1e-12)

# Query subcommand — single-entity extract.
def test_query_returns_single_line_entity(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)

    result = query_entity(submission_command, iges_path, 1, tmp_path)
    assert result["entity"]["type"] == 110
    assert result["entity"]["form"] == 0
    assert result["entity"]["data"]["start"] == [1.0, 2.0, 3.0]
    assert result["entity"]["data"]["terminate"] == [4.0, 5.0, 6.0]
    assert result["de_index"] == 1


# Roundtrip — semantic equivalence (bytes may normalize).
def test_roundtrip_preserves_line_entity(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)

    original_data = doc["entities"][0]["entity"]["data"]
    reparsed_data = reparsed["entities"][0]["entity"]["data"]
    assert original_data == reparsed_data


def test_roundtrip_subcommand_reparses_cleanly(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    rt_path = roundtrip_iges(submission_command, iges_path, tmp_path)

    parsed = parse_iges_to_json(submission_command, rt_path, tmp_path)
    data = parsed["entities"][0]["entity"]["data"]
    assert data["start"] == [1.0, 2.0, 3.0]
    assert data["terminate"] == [4.0, 5.0, 6.0]
