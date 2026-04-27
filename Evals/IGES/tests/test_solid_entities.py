"""Solid and CSG entity tests for IGES §§4.37-4.48."""

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


def test_block_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=150,
        data={
            "lx": 10.0,
            "ly": 20.0,
            "lz": 30.0,
            "corner": [1.0, 2.0, 3.0],
            "x_axis": [1.0, 0.0, 0.0],
            "z_axis": [0.0, 0.0, 1.0],
        },
    )
    assert data["lx"] == pytest.approx(10.0)
    assert data["ly"] == pytest.approx(20.0)
    assert data["lz"] == pytest.approx(30.0)
    assert data["corner"] == pytest.approx([1.0, 2.0, 3.0])


def test_wedge_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=152,
        data={
            "lx": 10.0,
            "ly": 5.0,
            "lz": 3.0,
            "ltx": 4.0,
            "corner": [1.0, 2.0, 3.0],
            "x_axis": [1.0, 0.0, 0.0],
            "z_axis": [0.0, 0.0, 1.0],
        },
    )
    assert data["ly"] == pytest.approx(5.0)
    assert data["lz"] == pytest.approx(3.0)
    assert data["ltx"] == pytest.approx(4.0)
    assert data["corner"][0] == pytest.approx(1.0)


def test_right_circular_cylinder_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=154,
        data={
            "h": 10.0,
            "r": 5.0,
            "face_center": [0.0, 0.0, 0.0],
            "axis": [0.0, 0.0, 1.0],
        },
    )
    assert data["h"] == pytest.approx(10.0)
    assert data["axis"] == pytest.approx([0.0, 0.0, 1.0])


def test_cone_frustum_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=156,
        data={
            "h": 10.0,
            "r1": 5.0,
            "r2": 2.0,
            "face_center": [0.0, 0.0, 0.0],
            "axis": [0.0, 0.0, 1.0],
        },
    )
    assert data["r1"] == pytest.approx(5.0)
    assert data["r2"] == pytest.approx(2.0)


def test_sphere_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=158,
        data={"radius": 5.0, "center": [1.0, 2.0, 3.0]},
    )
    assert data["radius"] == pytest.approx(5.0)
    assert data["center"] == pytest.approx([1.0, 2.0, 3.0])


def test_torus_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=160,
        data={
            "r1": 10.0,
            "r2": 2.0,
            "center": [0.0, 0.0, 0.0],
            "axis": [0.0, 0.0, 1.0],
        },
    )
    assert data["r1"] == pytest.approx(10.0)
    assert data["axis"][2] == pytest.approx(1.0)


def test_solid_of_revolution_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=162,
        data={
            "ptr": 3,
            "f": 0.5,
            "axis_point": [0.0, 0.0, 0.0],
            "axis_dir": [0.0, 0.0, 1.0],
        },
    )
    assert data["ptr"] == 3
    assert data["f"] == pytest.approx(0.5)
    assert data["axis_dir"] == pytest.approx([0.0, 0.0, 1.0])


def test_solid_of_linear_extrusion_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=164,
        data={"ptr": 3, "length": 10.0, "direction": [0.0, 0.0, 1.0]},
    )
    assert data["ptr"] == 3
    assert data["length"] == pytest.approx(10.0)
    assert data["direction"] == pytest.approx([0.0, 0.0, 1.0])


def test_ellipsoid_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=168,
        data={
            "lx": 10.0,
            "ly": 8.0,
            "lz": 5.0,
            "center": [1.0, 2.0, 3.0],
            "x_axis": [1.0, 0.0, 0.0],
            "z_axis": [0.0, 0.0, 1.0],
        },
    )
    assert data["center"] == pytest.approx([1.0, 2.0, 3.0])
    assert data["ly"] == pytest.approx(8.0)
    assert data["lz"] == pytest.approx(5.0)


def test_boolean_tree_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=180,
        data={"n": 3, "entries": [-1, -3, 1]},
    )
    assert data == {"n": 3, "entries": [-1, -3, 1]}


def test_selected_component_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=182,
        data={"btree": 5, "sel_point": [1.0, 2.0, 3.0]},
    )
    assert data["btree"] == 5
    assert data["sel_point"] == pytest.approx([1.0, 2.0, 3.0])


def test_solid_assembly_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=184,
        data={"n": 2, "items": [3, 5], "transforms": [7, 9]},
    )
    assert data["items"] == [3, 5]
    assert data["transforms"] == [7, 9]
