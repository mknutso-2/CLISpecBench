"""Conforming, test-owned topology contexts for focused entity observations.

IGES §§4.143–4.147 require real edge/face parents and Form 1 topology;
an independent Open Shell (514/2) is explicitly permitted by §4.147.
The solid fixture additionally satisfies §4.49 with two disjoint, closed,
outward-oriented tetrahedral shells: the inner shell is a reversed void use.
"""

from __future__ import annotations

import copy
import math
from typing import Any

from iges_support import make_entity, wrap_entities

Vertex = tuple[float, float, float]
Document = dict[str, Any]


def _dependent_status() -> dict[str, str]:
    # 00010001: physically dependent, with hierarchy deferred to the parent.
    return {
        "blank": "visible",
        "subordinate": "physically_dependent",
        "entity_use": "geometry",
        "hierarchy": "global_defer",
    }


def _append_entity(
    document: Document,
    entity_type: int,
    data: Document,
    *,
    form: int = 0,
    dependent: bool = True,
) -> int:
    entities: list[Document] = document["entities"]
    index = max((int(entity["de_index"]) for entity in entities), default=-1) + 2
    entities.append(
        make_entity(
            de_index=index,
            entity_type=entity_type,
            form=form,
            data=data,
            directory_entry_overrides={"status": _dependent_status()} if dependent else None,
        )
    )
    return index


def _append_face(
    document: Document,
    surface_de: int,
    edge_list: int,
    edge_uses: list[tuple[int, bool]],
) -> tuple[int, int]:
    loop = _append_entity(
        document,
        508,
        {
            "n": len(edge_uses),
            "edge_uses": [
                {
                    "type": 0,
                    "edge": edge_list,
                    "ndx": index,
                    "orientation": forward,
                    "k": 0,
                    "param_curves": [],
                }
                for index, forward in edge_uses
            ],
        },
        form=1,
    )
    face = _append_entity(
        document,
        510,
        {"surf": surface_de, "n": 1, "outer_loop_flag": True, "loops": [loop]},
        form=1,
    )
    return loop, face


def attach_open_shell(
    document: Document,
    *,
    surface_de: int,
    boundary_vertices: list[Vertex],
    boundary_curve_indices: list[int],
    boundary_forward: list[bool] | None = None,
) -> tuple[Document, dict[str, int]]:
    """Bound an existing surface by a closed ordered perimeter.

    Vertices follow the boundary with the face interior to its left (§4.145).
    Each curve connects vertex i to i+1, cyclically, in the indicated natural
    direction. The caller owns the analytic geometry; this helper supplies
    actual Form 1 parents rather than meaningless dangling pointer values.
    """
    document = copy.deepcopy(document)
    count = len(boundary_vertices)
    assert count >= 3 and len(boundary_curve_indices) == count
    if boundary_forward is None:
        boundary_forward = [True] * count
    assert len(boundary_forward) == count
    subjects = {surface_de, *boundary_curve_indices}
    for entity in document["entities"]:
        if entity["de_index"] in subjects:
            entity["directory_entry"]["status"] = _dependent_status()
    vertex_list = _append_entity(
        document,
        502,
        {"n": count, "vertices": [list(v) for v in boundary_vertices]},
        form=1,
    )
    edges: list[Document] = []
    for i, (curve, forward) in enumerate(
        zip(boundary_curve_indices, boundary_forward, strict=True)
    ):
        start, end = i + 1, (i + 1) % count + 1
        if not forward:
            start, end = end, start
        edges.append(
            {"curve": curve, "svp": vertex_list, "sv": start, "tvp": vertex_list, "tv": end}
        )
    edge_list = _append_entity(document, 504, {"n": count, "edges": edges}, form=1)
    loop, face = _append_face(
        document,
        surface_de,
        edge_list,
        [(i + 1, forward) for i, forward in enumerate(boundary_forward)],
    )
    shell = _append_entity(
        document,
        514,
        {"n": 1, "faces": [{"face": face, "orientation": True}]},
        form=2,
        dependent=False,
    )
    return document, {
        "vertex_list": vertex_list,
        "edge_list": edge_list,
        "loop": loop,
        "face": face,
        "shell": shell,
    }


def _append_plane(document: Document, a: Vertex, b: Vertex, c: Vertex) -> int:
    u = tuple(b[i] - a[i] for i in range(3))
    v = tuple(c[i] - a[i] for i in range(3))
    normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    assert math.fsum(value * value for value in normal) > 0
    location = _append_entity(document, 116, {"coords": list(a), "display_symbol": 0})
    normal_de = _append_entity(document, 123, dict(zip(("x", "y", "z"), normal, strict=True)))
    direction_de = _append_entity(document, 123, dict(zip(("x", "y", "z"), u, strict=True)))
    return _append_entity(
        document,
        190,
        {"deloc": location, "denrml": normal_de, "derefd": direction_de},
        form=1,
    )


def open_triangle_document() -> tuple[Document, dict[str, int]]:
    """A unit XY triangle, including a reversed edge and a parameter curve."""
    vertices: list[Vertex] = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    document = wrap_entities([])
    plane = _append_plane(document, *vertices)
    curves = [
        _append_entity(document, 110, {"start": list(vertices[a]), "terminate": list(vertices[b])})
        for a, b in [(0, 1), (1, 2), (0, 2)]
    ]
    # A separate 2D parameter-space curve for the first edge preserves the
    # nonempty K/ISOP/CURV data shape (§4.145). This plane's basis is XY.
    parameter = _append_entity(
        document,
        110,
        {"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
    )
    document["entities"][-1]["directory_entry"]["status"]["entity_use"] = "parametric_2d"
    document, ids = attach_open_shell(
        document,
        surface_de=plane,
        boundary_vertices=vertices,
        boundary_curve_indices=curves,
        boundary_forward=[True, True, False],
    )
    loop = next(entity for entity in document["entities"] if entity["de_index"] == ids["loop"])
    loop["entity"]["data"]["edge_uses"][0].update(
        {"k": 1, "param_curves": [{"isoparametric": True, "curve": parameter}]}
    )
    return document, ids


def _append_tetrahedron(document: Document, vertices: list[Vertex]) -> int:
    # These oriented face cycles point outward for the positive coordinate
    # tetrahedron. Every undirected edge occurs twice, in opposite directions.
    faces = [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    vertex_list = _append_entity(
        document,
        502,
        {"n": 4, "vertices": [list(v) for v in vertices]},
        form=1,
    )
    curves = [
        _append_entity(document, 110, {"start": list(vertices[a]), "terminate": list(vertices[b])})
        for a, b in pairs
    ]
    edge_list = _append_entity(
        document,
        504,
        {
            "n": 6,
            "edges": [
                {"curve": curve, "svp": vertex_list, "sv": a + 1, "tvp": vertex_list, "tv": b + 1}
                for (a, b), curve in zip(pairs, curves, strict=True)
            ],
        },
        form=1,
    )
    face_uses: list[Document] = []
    for cycle in faces:
        plane = _append_plane(document, *(vertices[index] for index in cycle))
        uses: list[tuple[int, bool]] = []
        for a, b in zip(cycle, (*cycle[1:], cycle[0]), strict=True):
            uses.append((pairs.index((min(a, b), max(a, b))) + 1, a < b))
        _, face = _append_face(document, plane, edge_list, uses)
        face_uses.append({"face": face, "orientation": True})
    return _append_entity(document, 514, {"n": 4, "faces": face_uses}, form=1)


def solid_with_void_document() -> tuple[Document, int]:
    """A closed tetrahedron containing a smaller, disjoint tetrahedral void."""
    document = wrap_entities([])
    outer = _append_tetrahedron(
        document,
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)],
    )
    inner = _append_tetrahedron(
        document,
        [(0.1, 0.1, 0.1), (0.2, 0.1, 0.1), (0.1, 0.2, 0.1), (0.1, 0.1, 0.2)],
    )
    solid = _append_entity(
        document,
        186,
        {"shell": outer, "sof": True, "n": 1, "voids": [{"shell": inner, "orientation": False}]},
        dependent=False,
    )
    return document, solid
