"""Analytic surfaces with legal, finite Face510/OpenShell514 contexts.

The §4.51–4.54 surfaces cannot appear independently. Each fixture restricts
one to a nondegenerate rectangular patch. Its four exact circular/linear
model-space boundary curves are backed by actual edge/vertex/loop records.
Rational quadratic arcs follow §4.23 (middle weight cos(half sweep)); no
submission or reference evaluator supplies their geometry.
"""

from __future__ import annotations

import math
from typing import Any

from iges_support import make_entity, wrap_entities
from topology_support import Vertex, attach_open_shell


def _arc(
    center: Vertex, x: Vertex, y: Vertex, radius: float, start: float, end: float
) -> dict[str, Any]:
    a, b = math.radians(start), math.radians(end)
    midpoint = (a + b) / 2
    weight = math.cos((b - a) / 2)
    assert weight > 0
    controls = [
        [center[i] + radius * (math.cos(t) * x[i] + math.sin(t) * y[i]) / w for i in range(3)]
        for t, w in [(a, 1.0), (midpoint, weight), (b, 1.0)]
    ]
    normal = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
    return {
        "K": 2,
        "M": 2,
        "prop1": 1,
        "prop2": 0,
        "prop3": 0,
        "prop4": 0,
        "knots": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
        "weights": [1.0, weight, 1.0],
        "control_points": controls,
        "v0": 0.0,
        "v1": 1.0,
        "plane_normal": normal,
    }


def analytic_surface_document(
    kind: int, form: int, data: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    """Keep the target's canonical data and add its required topology parent."""
    records = [
        make_entity(
            de_index=1, entity_type=116, data={"coords": [0.0, 0.0, 0.0], "display_symbol": 0}
        )
    ]
    if data.get("deaxis"):
        records.append(
            make_entity(de_index=3, entity_type=123, data={"x": 0.0, "y": 0.0, "z": 1.0})
        )
    if data.get("derefd"):
        records.append(
            make_entity(de_index=5, entity_type=123, data={"x": 1.0, "y": 0.0, "z": 0.0})
        )
    surface_de = 2 * len(records) + 1
    records.append(make_entity(de_index=surface_de, entity_type=kind, form=form, data=data))
    curves: list[tuple[int, dict[str, Any]]] = []
    x, y, z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    if kind in (192, 194):
        r = float(data["radius"])
        top_r = r + (math.tan(math.radians(data["sangle"])) if kind == 194 else 0)
        curves = [
            (126, _arc((0.0, 0.0, 0.0), x, y, r, 0, 90)),
            (110, {"start": [0.0, r, 0.0], "terminate": [0.0, top_r, 1.0]}),
            (126, _arc((0.0, 0.0, 1.0), x, y, top_r, 90, 0)),
            (110, {"start": [top_r, 0.0, 1.0], "terminate": [r, 0.0, 0.0]}),
        ]
    elif kind == 196:
        r = float(data["radius"])
        curves = [
            (126, _arc((0.0, 0.0, 0.0), x, y, r, 0, 90)),
            (126, _arc((0.0, 0.0, 0.0), y, z, r, 0, 30)),
            (126, _arc((0.0, 0.0, r / 2), x, y, r * math.sqrt(3) / 2, 90, 0)),
            (126, _arc((0.0, 0.0, 0.0), x, z, r, 30, 0)),
        ]
    elif kind == 198:
        r, major = float(data["minrad"]), float(data["majrad"])
        # §4.54 uses cos(v)*x - sin(v)*y, with u the minor-circle angle.
        minus_y = (0.0, -1.0, 0.0)
        curves = [
            (126, _arc((0.0, -major, 0.0), minus_y, z, r, 0, 90)),
            (126, _arc((0.0, 0.0, r), x, minus_y, major, 90, 180)),
            (126, _arc((-major, 0.0, 0.0), (-1.0, 0.0, 0.0), z, r, 90, 0)),
            (126, _arc((0.0, 0.0, 0.0), x, minus_y, major + r, 180, 90)),
        ]
    else:
        raise AssertionError(f"unsupported fixture surface {kind}")
    vertices: list[Vertex] = []
    ends: list[Vertex] = []
    indices: list[int] = []
    for curve_kind, curve in curves:
        index = 2 * len(records) + 1
        indices.append(index)
        start = curve["control_points"][0] if curve_kind == 126 else curve["start"]
        end = curve["control_points"][-1] if curve_kind == 126 else curve["terminate"]
        vertices.append((start[0], start[1], start[2]))
        ends.append((end[0], end[1], end[2]))
        records.append(make_entity(de_index=index, entity_type=curve_kind, data=curve))
    # Check closure independently of the code being evaluated (§4.145).
    for i, end in enumerate(ends):
        assert math.dist(end, vertices[(i + 1) % 4]) < 1e-12
    document, _ = attach_open_shell(
        wrap_entities(records),
        surface_de=surface_de,
        boundary_vertices=vertices,
        boundary_curve_indices=indices,
    )
    return document, surface_de
