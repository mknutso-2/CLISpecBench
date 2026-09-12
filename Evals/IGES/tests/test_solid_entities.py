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
    supporting: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=entity_type,
                form=form,
                data=data,
                directory_entry_overrides={
                    "status": _status(
                        "definition"
                        if entity_type == 184
                        else "other"
                        if entity_type == 182
                        else "geometry"
                    )
                },
            ),
            *supporting,
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    # Observe only the named target, not the independent support payloads.
    entity = next(e for e in reparsed["entities"] if e["de_index"] == 1)["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def _status(use: str = "geometry", *, dependent: bool = False) -> dict[str, str]:
    return {
        "blank": "visible",
        "subordinate": "physically_dependent" if dependent else "independent",
        "entity_use": use,
        "hierarchy": "global_top_down",
    }


def _sphere(index: int, x: float) -> dict[str, Any]:
    return make_entity(
        de_index=index,
        entity_type=158,
        data={"radius": 1.0, "center": [x, 0.0, 0.0]},
        directory_entry_overrides={"status": _status(dependent=True)},
    )


def _transform(index: int, x: float) -> dict[str, Any]:
    # §4.21: a proper orthogonal matrix and finite translation.
    return make_entity(
        de_index=index,
        entity_type=124,
        data={
            "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "translation": [x, 0.0, 0.0],
        },
    )


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
    assert data["lx"] == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert data["ly"] == pytest.approx(20.0, rel=1e-12, abs=1e-15)
    assert data["lz"] == pytest.approx(30.0, rel=1e-12, abs=1e-15)
    assert data["corner"] == pytest.approx([1.0, 2.0, 3.0], rel=1e-12, abs=1e-15)


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
    assert data["ly"] == pytest.approx(5.0, rel=1e-12, abs=1e-15)
    assert data["lz"] == pytest.approx(3.0, rel=1e-12, abs=1e-15)
    assert data["ltx"] == pytest.approx(4.0, rel=1e-12, abs=1e-15)
    assert data["corner"][0] == pytest.approx(1.0, rel=1e-12, abs=1e-15)


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
    assert data["h"] == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert data["axis"] == pytest.approx([0.0, 0.0, 1.0], rel=1e-12, abs=1e-15)


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
    assert data["r1"] == pytest.approx(5.0, rel=1e-12, abs=1e-15)
    assert data["r2"] == pytest.approx(2.0, rel=1e-12, abs=1e-15)


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
    assert data["radius"] == pytest.approx(5.0, rel=1e-12, abs=1e-15)
    assert data["center"] == pytest.approx([1.0, 2.0, 3.0], rel=1e-12, abs=1e-15)


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
    assert data["r1"] == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert data["axis"][2] == pytest.approx(1.0, rel=1e-12, abs=1e-15)


def test_solid_of_revolution_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=162,
        # §4.43 Form0: open profile coplanar with the Z axis, never crossing
        # it; endpoint projections close a positive-area rectangle.
        supporting=[
            make_entity(
                de_index=3,
                entity_type=110,
                data={"start": [2.0, 0.0, 0.0], "terminate": [2.0, 0.0, 3.0]},
                directory_entry_overrides={"status": _status(dependent=True)},
            )
        ],
        data={
            "ptr": 3,
            "f": 0.5,
            "axis_point": [0.0, 0.0, 0.0],
            "axis_dir": [0.0, 0.0, 1.0],
        },
    )
    assert data["ptr"] == 3
    assert data["f"] == pytest.approx(0.5, rel=1e-12, abs=1e-15)
    assert data["axis_dir"] == pytest.approx([0.0, 0.0, 1.0], rel=1e-12, abs=1e-15)


def test_solid_of_linear_extrusion_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=164,
        # §4.44: a closed non-self-intersecting XY circle; the extrusion
        # direction is not coplanar with its bounding curve.
        supporting=[
            make_entity(
                de_index=3,
                entity_type=100,
                data={"zt": 0.0, "x1": 0.0, "y1": 0.0, "x2": 2.0, "y2": 0.0, "x3": 2.0, "y3": 0.0},
                directory_entry_overrides={"status": _status(dependent=True)},
            )
        ],
        data={"ptr": 3, "length": 10.0, "direction": [0.0, 0.0, 1.0]},
    )
    assert data["ptr"] == 3
    assert data["length"] == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert data["direction"] == pytest.approx([0.0, 0.0, 1.0], rel=1e-12, abs=1e-15)


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
    assert data["center"] == pytest.approx([1.0, 2.0, 3.0], rel=1e-12, abs=1e-15)
    assert data["ly"] == pytest.approx(8.0, rel=1e-12, abs=1e-15)
    assert data["lz"] == pytest.approx(5.0, rel=1e-12, abs=1e-15)


def test_boolean_tree_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=180,
        # §4.46: operands are real solid primitives, followed by union.
        supporting=[_sphere(3, 0.0), _sphere(5, 4.0)],
        data={"n": 3, "entries": [-3, -5, 1]},
    )
    assert data == {"n": 3, "entries": [-3, -5, 1]}


def test_selected_component_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=182,
        # §4.47: the point lies strictly inside one component of a disjoint
        # Boolean union. The tree and both operands exist and are acyclic.
        supporting=[
            make_entity(
                de_index=3,
                entity_type=180,
                data={"n": 3, "entries": [-5, -7, 1]},
                directory_entry_overrides={"status": _status(dependent=True)},
            ),
            _sphere(5, 0.0),
            _sphere(7, 4.0),
        ],
        data={"btree": 3, "sel_point": [0.0, 0.0, 0.0]},
    )
    assert data["btree"] == 3
    assert data["sel_point"] == pytest.approx([0.0, 0.0, 0.0], rel=1e-12, abs=1e-15)


def test_solid_assembly_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=184,
        # §4.48 Form0: actual solid primitives and actual Type124 transforms.
        supporting=[_sphere(3, 0.0), _sphere(5, 4.0), _transform(7, 1.0), _transform(9, -1.0)],
        data={"n": 2, "items": [3, 5], "transforms": [7, 9]},
    )
    assert data["items"] == [3, 5]
    assert data["transforms"] == [7, 9]
