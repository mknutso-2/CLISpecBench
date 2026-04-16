"""Dedicated CLI coverage for structure, property, and view entities."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from iges_support import make_entity, semantic_roundtrip_json, wrap_entities


def _roundtrip_single(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    doc = wrap_entities([
        make_entity(
            de_index=1, entity_type=entity_type, form=form, data=data,
        ),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    entity = reparsed["entities"][0]["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def test_subfigure_definition_roundtrips_empty_member_list(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=308,
        data={"depth": 0, "name": "EMPTY", "n": 0, "entities": []},
    )
    assert data == {"depth": 0, "name": "EMPTY", "n": 0, "entities": []}


def test_property_roundtrips_string_payload(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=406,
        data={"np": 1, "values": [{"kind": "string", "value": "Label"}]},
    )
    assert data == {"np": 1, "values": [{"kind": "string", "value": "Label"}]}


def test_drawing_form_one_roundtrips_angles_and_annotations(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=404,
        form=1,
        data={
            "n": 2,
            "views": [
                {"view": 1, "x_origin": 0.0, "y_origin": 0.0, "angle": 0.0},
                {"view": 3, "x_origin": 5.0, "y_origin": 10.0, "angle": 1.5708},
            ],
            "m": 1,
            "annotations": [9],
        },
    )
    assert data["views"][1]["view"] == 3
    assert data["views"][1]["angle"] == pytest.approx(1.5708)
    assert data["annotations"] == [9]


def test_subfigure_instance_roundtrips_unit_scale(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=408,
        data={"de": 5, "translation": [10.0, 20.0, 30.0], "scale": 1.0},
    )
    assert data["de"] == 5
    assert data["translation"] == pytest.approx([10.0, 20.0, 30.0])
    assert data["scale"] == pytest.approx(1.0)


def test_view_form_one_roundtrips_perspective_fields(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=410,
        form=1,
        data={
            "form": 1,
            "view_number": 2,
            "scale": 0.5,
            "clip_planes": [],
            "view_plane_normal": [0.0, 0.0, 1.0],
            "view_reference_point": [1.0, 2.0, 3.0],
            "center_of_projection": [0.0, 0.0, 100.0],
            "view_up_vector": [0.0, 1.0, 0.0],
            "view_plane_distance": 50.0,
            "umin": -10.0,
            "umax": 10.0,
            "vmin": -5.0,
            "vmax": 5.0,
            "depth_clipping": 1,
            "wmin": -200.0,
            "wmax": 200.0,
        },
    )
    assert data["view_number"] == 2
    assert data["center_of_projection"][2] == pytest.approx(100.0)
    assert data["view_plane_distance"] == pytest.approx(50.0)
    assert data["wmax"] == pytest.approx(200.0)


def test_rectangular_array_roundtrips_do_dont_list(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=412,
        data={
            "de": 5,
            "s": 2.0,
            "position": [1.0, 2.0, 0.0],
            "nc": 3,
            "nr": 4,
            "dx": 10.0,
            "dy": 15.0,
            "ax": 0.5,
            "lc": 2,
            "ddf": 0,
            "positions": [1, 4],
        },
    )
    assert data["nc"] == 3
    assert data["nr"] == 4
    assert data["ddf"] == 0
    assert data["positions"] == [1, 4]


def test_circular_array_roundtrips_do_dont_list(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=414,
        data={
            "de": 7,
            "ne": 8,
            "center": [1.0, 2.0, 0.0],
            "r": 15.0,
            "as": 0.5,
            "ad": 0.7854,
            "lc": 1,
            "ddf": 0,
            "positions": [3],
        },
    )
    assert data["ne"] == 8
    assert data["r"] == pytest.approx(15.0)
    assert data["ad"] == pytest.approx(0.7854)
    assert data["positions"] == [3]
