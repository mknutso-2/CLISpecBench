"""Dedicated CLI coverage for core geometric/value entities."""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from iges_support import (
    assert_semantic_equal,
    direction_document,
    evaluate_entity,
    fixture_iges_from_json,
    make_entity,
    semantic_roundtrip_json,
    wrap_entities,
)


def _roundtrip_single(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=entity_type,
                form=form,
                data=data,
            ),
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    entity = reparsed["entities"][0]["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def test_circular_arc_eval_start_point_lands_in_zt_plane(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = {
        "zt": 7.5,
        "x1": 0.0,
        "y1": 0.0,
        "x2": 1.0,
        "y2": 0.0,
        "x3": 0.0,
        "y3": 1.0,
    }
    iges_path = fixture_iges_from_json(
        submission_command,
        wrap_entities([make_entity(de_index=1, entity_type=100, data=data)]),
        tmp_path,
        name="circular-arc",
    )
    _, payload = evaluate_entity(
        submission_command,
        iges_path,
        1,
        0.0,
        tmp_path,
        name="circular-arc-eval",
    )
    assert payload.get("point") == pytest.approx([1.0, 0.0, 7.5], rel=1e-9, abs=1e-12)


def test_direction_roundtrips_non_unit_ratios_without_normalizing(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    result = semantic_roundtrip_json(
        submission_command, direction_document({"x": 1.0, "y": 2.0, "z": 3.0}), tmp_path
    )
    data = result["entities"][0]["entity"]["data"]
    assert_semantic_equal(data, {"x": 1.0, "y": 2.0, "z": 3.0})


def test_transformation_matrix_roundtrips_rotation_and_translation(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=124,
        data={
            "rotation": [
                [0.0, 0.0, 1.0],
                [0.0, 1.0, 0.0],
                [-1.0, 0.0, 0.0],
            ],
            "translation": [10.0, 20.0, 30.0],
        },
    )
    assert data["rotation"][0][2] == pytest.approx(1.0, rel=1e-12, abs=1e-15)
    assert data["rotation"][2][0] == pytest.approx(-1.0, rel=1e-12, abs=1e-15)
    assert data["translation"] == pytest.approx([10.0, 20.0, 30.0], rel=1e-12, abs=1e-15)
