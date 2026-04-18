"""Semantic round-trip tests for a breadth of entity types.

Each test builds a minimal canonical IGES-JSON document containing one
entity, runs ``iges write`` → ``iges parse``, and asserts the reparsed
``entity.data`` block matches the input field-for-field.

These are the CLI-observable equivalent of the SDK's Catch2 round-trip
tests (``test_writer_roundtrip.cpp`` / ``test_writer_roundtrip_batch2.cpp``),
which exercised library-internal parse/write functions. The eval only
owns the CLI surface, so we compare on the JSON payload after a full
write → read cycle.

Entities covered here were chosen for:

* schema simplicity (no form-dependent unions, no nested variants),
* presence in the three Burkardt fixtures (ex1/ex2/ex3), and
* coverage of each entity-data container shape (scalar, Vec3,
  Matrix3x3, DEIndex, DEIndex[], form-dependent).

Per-entity §4.X tests can layer additional behavioural checks on top.
"""
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
    record = reparsed["entities"][0]
    assert record["entity"]["type"] == entity_type
    assert record["entity"]["form"] == form
    return record["entity"]["data"]


# §4.1 Null Entity (Type 0) — empty data block
def test_null_entity_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=0, data={},
    )
    assert data == {}


# §4.3 Circular Arc (Type 100) — seven reals
def test_circular_arc_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "zt": 5.0,
        "x1": 1.0, "y1": 2.0,     # center
        "x2": 3.0, "y2": 4.0,     # start
        "x3": 5.0, "y3": 6.0,     # end
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=100, data=payload,
    )
    assert data == payload


# §4.4 Composite Curve (Type 102) — DE-pointer list
def test_composite_curve_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # A Composite Curve needs at least one referenced constituent, so
    # build two Lines plus the Composite that points at them.
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [1.0, 0.0, 0.0], "terminate": [1.0, 1.0, 0.0]}),
        make_entity(de_index=5, entity_type=102, data={
            "constituents": [1, 3]}),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    comp = reparsed["entities"][2]["entity"]
    assert comp["type"] == 102
    assert comp["data"]["constituents"] == [1, 3]


# §4.12 Plane (Type 108, form 0 = unbounded)
def test_plane_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "A": 0.0, "B": 0.0, "C": 1.0, "D": 0.0,
        "ptr": 0,
        "x": 0.0, "y": 0.0, "z": 0.0,
        "size": 0.0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=108, data=payload,
    )
    assert data == payload


# §4.16 Point (Type 116)
def test_point_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "coords": [1.5, 2.5, 3.5],
        "display_symbol": 0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=116, data=payload,
    )
    assert data["coords"] == pytest.approx([1.5, 2.5, 3.5])
    assert data["display_symbol"] == 0


# §4.20 Direction (Type 123) — unit vector
def test_direction_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"x": 1.0, "y": 0.0, "z": 0.0}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=123, data=payload,
    )
    assert data == payload


# §4.21 Transformation Matrix (Type 124) — 3x3 rotation + translation
def test_transformation_matrix_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "rotation": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "translation": [10.0, 20.0, 30.0],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=124, data=payload,
    )
    assert data["rotation"] == payload["rotation"]
    assert data["translation"] == pytest.approx([10.0, 20.0, 30.0])


# §4.21 — Non-identity rotation preserves off-diagonal terms.
def test_transformation_matrix_non_identity(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # 90° rotation about Z.
    payload = {
        "rotation": [
            [0.0, -1.0, 0.0],
            [1.0,  0.0, 0.0],
            [0.0,  0.0, 1.0],
        ],
        "translation": [0.0, 0.0, 0.0],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=124, data=payload,
    )
    assert data["rotation"][0][1] == pytest.approx(-1.0)
    assert data["rotation"][1][0] == pytest.approx(1.0)


# §4.5 Conic Arc (Type 104, form 1 = ellipse)
def test_conic_arc_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "A": -0.25, "B": 0.0, "C": -(1.0 / 9.0),
        "D": 0.0, "E": 0.0, "F": 1.0,
        "zt": 1.5,
        "x1": 2.0, "y1": 0.0,
        "x2": 0.0, "y2": 3.0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=104, form=1, data=payload,
    )
    for key, value in payload.items():
        if isinstance(value, float):
            assert data[key] == pytest.approx(value)
        else:
            assert data[key] == value


# §4.5 Copious Data (Type 106, form 12 = 3D linear path)
def test_copious_data_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "ip": 2,
        "n": 3,
        "zt": 0.0,
        "data": [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 3.0, 2.0, 1.0],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=106, form=12, data=payload,
    )
    assert data == payload


# §4.17 Ruled Surface (Type 118)
def test_ruled_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"de1": 1, "de2": 3, "dirflg": 0, "devflg": 1}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=118, data=payload,
    )
    assert data == payload


# §4.18 Surface of Revolution (Type 120)
def test_surface_of_revolution_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"l": 1, "c": 3, "sa": -0.1, "ta": 3.241592653589793}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=120, data=payload,
    )
    assert data["l"] == 1
    assert data["c"] == 3
    assert data["sa"] == pytest.approx(-0.1)
    assert data["ta"] == pytest.approx(payload["ta"])


# §4.19 Tabulated Cylinder (Type 122)
def test_tabulated_cylinder_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"de": 1, "terminate_point": [0.0, 0.0, 5.0]}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=122, data=payload,
    )
    assert data["de"] == 1
    assert data["terminate_point"] == pytest.approx([0.0, 0.0, 5.0])


# §4.22 Flash (Type 125)
def test_flash_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "x": 1.0,
        "y": 2.0,
        "dim1": 0.5,
        "dim2": 0.25,
        "rot": 0.0,
        "de": 0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=125, data=payload,
    )
    assert data == payload


# §4.25 Offset Curve (Type 130)
def test_offset_curve_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "de1": 1,
        "flag": 1,
        "de2": 0,
        "ndim": 3,
        "ptype": 1,
        "d1": 2.0,
        "td1": 0.0,
        "d2": 0.0,
        "td2": 0.0,
        "vx": 0.0,
        "vy": 0.0,
        "vz": 1.0,
        "tt1": 0.0,
        "tt2": 10.0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=130, data=payload,
    )
    assert data == payload


# §4.30 Offset Surface (Type 140)
def test_offset_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"nx": 0.0, "ny": 0.0, "nz": 1.0, "d": 2.5, "de": 7}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=140, data=payload,
    )
    assert data == payload


# §4.50 Plane Surface (Type 190, form 1)
def test_plane_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"deloc": 1, "denrml": 3, "derefd": 5}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=190, form=1, data=payload,
    )
    assert data == payload


# §4.50 Plane Surface (Type 190, form 0) — no reference direction
def test_plane_surface_form_zero_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"deloc": 1, "denrml": 3, "derefd": 0}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=190, form=0, data=payload,
    )
    assert data == payload


# §4.51 Cylindrical Surface (Type 192, form 1)
def test_cylindrical_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"deloc": 1, "deaxis": 3, "radius": 2.0, "derefd": 5}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=192, form=1, data=payload,
    )
    assert data == payload


# §4.51 Cylindrical Surface (Type 192, form 0) — no reference direction
def test_cylindrical_surface_form_zero_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"deloc": 1, "deaxis": 3, "radius": 2.0, "derefd": 0}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=192, form=0, data=payload,
    )
    assert data == payload


# §4.52 Conical Surface (Type 194, form 1)
def test_conical_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "deloc": 1,
        "deaxis": 3,
        "radius": 2.0,
        "sangle": 0.5235987755982988,
        "derefd": 5,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=194, form=1, data=payload,
    )
    assert data["deloc"] == 1
    assert data["deaxis"] == 3
    assert data["radius"] == pytest.approx(2.0)
    assert data["sangle"] == pytest.approx(payload["sangle"])
    assert data["derefd"] == 5


# §4.52 Conical Surface (Type 194, form 0) — no reference direction
def test_conical_surface_form_zero_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "deloc": 1,
        "deaxis": 3,
        "radius": 2.0,
        "sangle": 0.5235987755982988,
        "derefd": 0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=194, form=0, data=payload,
    )
    assert data["deloc"] == 1
    assert data["deaxis"] == 3
    assert data["radius"] == pytest.approx(2.0)
    assert data["sangle"] == pytest.approx(payload["sangle"])
    assert data["derefd"] == 0


# §4.53 Spherical Surface (Type 196, form 1)
def test_spherical_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"deloc": 1, "radius": 3.5, "deaxis": 3, "derefd": 5}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=196, form=1, data=payload,
    )
    assert data == payload


# §4.53 Spherical Surface (Type 196, form 0) — no axis or reference direction
def test_spherical_surface_form_zero_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"deloc": 1, "radius": 3.5, "deaxis": 0, "derefd": 0}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=196, form=0, data=payload,
    )
    assert data == payload


# §4.54 Toroidal Surface (Type 198, form 1)
def test_toroidal_surface_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "deloc": 1,
        "deaxis": 3,
        "majrad": 6.0,
        "minrad": 1.5,
        "derefd": 5,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=198, form=1, data=payload,
    )
    assert data == payload


# §4.54 Toroidal Surface (Type 198, form 0) — no reference direction
def test_toroidal_surface_form_zero_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "deloc": 1,
        "deaxis": 3,
        "majrad": 6.0,
        "minrad": 1.5,
        "derefd": 0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=198, form=0, data=payload,
    )
    assert data == payload


# §4.92 Subfigure Definition (Type 308)
def test_subfigure_definition_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        # A single constituent.
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [1.0, 1.0, 0.0]}),
        make_entity(de_index=3, entity_type=308, data={
            "depth": 0,
            "name": "MYSUB",
            "n": 1,
            "entities": [1],
        }),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    sub = reparsed["entities"][1]["entity"]
    assert sub["type"] == 308
    assert sub["data"]["name"] == "MYSUB"
    assert sub["data"]["entities"] == [1]


# §4.133 Subfigure Instance (Type 408)
def test_subfigure_instance_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=308, data={
            "depth": 0, "name": "SUB", "n": 1, "entities": [1]}),
        make_entity(de_index=5, entity_type=408, data={
            "de": 3,
            "translation": [5.0, 5.0, 0.0],
            "scale": 2.0,
        }),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    inst = reparsed["entities"][2]["entity"]
    assert inst["type"] == 408
    assert inst["data"]["de"] == 3
    assert inst["data"]["translation"] == pytest.approx([5.0, 5.0, 0.0])
    assert inst["data"]["scale"] == pytest.approx(2.0)


# §4.137 Circular Array (Type 414)
def test_circular_array_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=116, data={
            "coords": [0.0, 0.0, 0.0], "display_symbol": 0}),
        make_entity(de_index=3, entity_type=414, data={
            "de": 1,
            "ne": 6,
            "center": [0.0, 0.0, 0.0],
            "r": 5.0,
            "as": 0.0,
            "ad": 1.0472,   # ≈ 60°
            "lc": 0,
            "ddf": 0,
            "positions": [],
        }),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    arr = reparsed["entities"][1]["entity"]
    assert arr["type"] == 414
    assert arr["data"]["ne"] == 6
    assert arr["data"]["r"] == pytest.approx(5.0)


# §4.97 Property (Type 406) — FieldValue variant serialization
def test_property_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # FieldValue variant — tagged with {"kind", "value"}.
    payload = {
        "np": 3,
        "values": [
            {"kind": "int",    "value": 42},
            {"kind": "real",   "value": 3.14},
            {"kind": "string", "value": "LINWIDTH"},
        ],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=406, data=payload,
    )
    assert data["np"] == 3
    assert len(data["values"]) == 3
    kinds = [v["kind"] for v in data["values"]]
    assert kinds == ["int", "real", "string"]
    assert data["values"][0]["value"] == 42
    assert data["values"][2]["value"] == "LINWIDTH"


# §4.131 Drawing (Type 404, form 0 = no angle per DrawingView)
def test_drawing_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=410, data={
            "form": 0, "view_number": 1, "scale": 1.0,
            "clip_planes": [0, 0, 0, 0, 0, 0],
            "view_plane_normal": [0.0, 0.0, 1.0],
            "view_reference_point": [0.0, 0.0, 0.0],
            "center_of_projection": [0.0, 0.0, 0.0],
            "view_up_vector": [0.0, 1.0, 0.0],
            "view_plane_distance": 0.0,
            "umin": 0.0, "umax": 0.0, "vmin": 0.0, "vmax": 0.0,
            "depth_clipping": 0, "wmin": 0.0, "wmax": 0.0,
        }),
        make_entity(de_index=3, entity_type=404, form=0, data={
            "n": 1,
            "views": [{"view": 1, "x_origin": 0.0, "y_origin": 0.0, "angle": 0.0}],
            "m": 0,
            "annotations": [],
        }),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    dr = reparsed["entities"][1]["entity"]
    assert dr["type"] == 404
    assert dr["data"]["n"] == 1
    assert dr["data"]["views"][0]["view"] == 1


# §4.134 View (Type 410, form 0) — clip plane DE list
def test_view_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "form": 0,
        "view_number": 7,
        "scale": 2.5,
        "clip_planes": [0, 0, 0, 0, 0, 0],
        "view_plane_normal": [0.0, 0.0, 1.0],
        "view_reference_point": [0.0, 0.0, 0.0],
        "center_of_projection": [0.0, 0.0, 0.0],
        "view_up_vector": [0.0, 1.0, 0.0],
        "view_plane_distance": 0.0,
        "umin": 0.0, "umax": 0.0, "vmin": 0.0, "vmax": 0.0,
        "depth_clipping": 0, "wmin": 0.0, "wmax": 0.0,
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=410, form=0, data=payload,
    )
    assert data["view_number"] == 7
    assert data["scale"] == pytest.approx(2.5)
    assert data["clip_planes"] == [0, 0, 0, 0, 0, 0]


# §4.143 Vertex List (Type 502)
def test_vertex_list_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "n": 2,
        "vertices": [[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=502, data=payload,
    )
    assert data["n"] == 2
    assert data["vertices"][1] == pytest.approx([1.0, 2.0, 3.0])


# §4.144 Edge List (Type 504)
def test_edge_list_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "n": 1,
        "edges": [{"curve": 1, "svp": 3, "sv": 1, "tvp": 3, "tv": 2}],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=504, data=payload,
    )
    assert data == payload


# §4.145 Loop (Type 508)
def test_loop_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "n": 1,
        "edge_uses": [{
            "type": 0,
            "edge": 1,
            "ndx": 1,
            "orientation": True,
            "k": 1,
            "param_curves": [{"isoparametric": False, "curve": 0}],
        }],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=508, data=payload,
    )
    assert data == payload


# §4.146 Face (Type 510)
def test_face_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"surf": 1, "n": 1, "outer_loop_flag": True, "loops": [3]}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=510, data=payload,
    )
    assert data == payload


# §4.147 Shell (Type 514)
def test_shell_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {"n": 1, "faces": [{"face": 1, "orientation": True}]}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=514, data=payload,
    )
    assert data == payload


# §4.49 MSBO (Type 186)
def test_msbo_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    payload = {
        "shell": 1,
        "sof": True,
        "n": 1,
        "voids": [{"shell": 3, "orientation": False}],
    }
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=186, data=payload,
    )
    assert data == payload
