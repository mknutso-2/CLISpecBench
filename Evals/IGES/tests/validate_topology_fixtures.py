"""Maintenance audit of test-owned geometry, independent of reference parsers.

Run directly with Python. These checks are not scored submission tests.
The fixtures' conforming inputs follow §§4.20, 4.49 and 4.143–4.147;
checking graph closure and geometry prevents a permissive reference parser
from hiding a malformed positive-test prerequisite.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from topology_support import open_triangle_document, solid_with_void_document

Vec = tuple[float, float, float]


def vector(value: Any) -> Vec:
    return float(value[0]), float(value[1]), float(value[2])


def subtract(a: Vec, b: Vec) -> Vec:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def dot(a: Vec, b: Vec) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def unit(a: Vec) -> Vec:
    length = math.sqrt(dot(a, a))
    assert length > 0
    return a[0] / length, a[1] / length, a[2] / length


def validate(document: dict[str, Any]) -> None:
    rows: dict[int, Any] = {row["de_index"]: row for row in document["entities"]}
    assert len(rows) == len(document["entities"])
    assert list(rows) == list(range(1, 2 * len(rows), 2))

    def data(index: int, kind: int) -> dict[str, Any]:
        assert rows[index]["entity"]["type"] == kind
        return rows[index]["entity"]["data"]

    def direction(index: int) -> Vec:
        item = data(index, 123)
        return unit((item["x"], item["y"], item["z"]))

    def frame(index: int) -> tuple[Vec, Vec, Vec, Vec]:
        plane = data(index, 190)
        origin = vector(data(plane["deloc"], 116)["coords"])
        normal, x = direction(plane["denrml"]), direction(plane["derefd"])
        assert abs(dot(normal, x)) < 1e-12
        return origin, normal, x, cross(normal, x)

    loop_vertices: dict[int, list[Vec]] = {}
    loop_uses: dict[int, list[tuple[int, int, bool]]] = {}
    for index, row in rows.items():
        entity, directory = row["entity"], row["directory_entry"]
        kind = entity["type"]
        assert directory["entity_type"] == kind and directory["form"] == entity["form"]
        if kind in (123, 502, 504, 508, 510):
            assert directory["status"]["subordinate"] == "physically_dependent"
            assert directory["xform_matrix"] == 0
        if kind in (502, 504, 508, 510):
            assert entity["form"] == 1
            assert directory["status"]["hierarchy"] == "global_defer"
        if kind == 502:
            assert entity["data"]["n"] == len(entity["data"]["vertices"]) > 0
        if kind != 508:
            continue
        loop = data(index, 508)
        assert loop["n"] == len(loop["edge_uses"]) >= 3
        vertices: list[Vec] = []
        ends: list[Vec] = []
        uses: list[tuple[int, int, bool]] = []
        for use in loop["edge_uses"]:
            assert use["type"] == 0
            edge_list = data(use["edge"], 504)
            assert edge_list["n"] == len(edge_list["edges"]) > 0
            edge = edge_list["edges"][use["ndx"] - 1]
            start = vector(data(edge["svp"], 502)["vertices"][edge["sv"] - 1])
            end = vector(data(edge["tvp"], 502)["vertices"][edge["tv"] - 1])
            line = data(edge["curve"], 110)
            assert math.dist(start, vector(line["start"])) < 1e-12
            assert math.dist(end, vector(line["terminate"])) < 1e-12
            assert math.dist(start, end) > 0
            if not use["orientation"]:
                start, end = end, start
            vertices.append(start)
            ends.append(end)
            uses.append((use["edge"], use["ndx"], use["orientation"]))
            assert use["k"] == len(use["param_curves"])
        assert all(
            math.dist(a, b) < 1e-12 for a, b in zip(ends, vertices[1:] + vertices[:1], strict=True)
        )
        loop_vertices[index], loop_uses[index] = vertices, uses

    face_planes: dict[int, tuple[Vec, Vec]] = {}
    for index, row in rows.items():
        if row["entity"]["type"] != 510:
            continue
        face = data(index, 510)
        assert face["n"] == len(face["loops"]) == 1
        origin, normal, x, y = frame(face["surf"])
        face_planes[index] = origin, normal
        vertices = loop_vertices[face["loops"][0]]
        assert len(vertices) == 3
        assert all(abs(dot(subtract(p, origin), normal)) < 1e-12 for p in vertices)
        area = cross(subtract(vertices[1], vertices[0]), subtract(vertices[2], vertices[0]))
        assert dot(area, normal) > 0  # Nonzero area; material is left of the loop.
        for use in data(face["loops"][0], 508)["edge_uses"]:
            for parameter in use["param_curves"]:
                curve = data(parameter["curve"], 110)
                assert (
                    rows[parameter["curve"]]["directory_entry"]["status"]["entity_use"]
                    == "parametric_2d"
                )
                a, b = vector(curve["start"]), vector(curve["terminate"])
                assert a[2] == b[2] == 0
                assert parameter["isoparametric"] is (a[0] == b[0] or a[1] == b[1])
                edge = data(use["edge"], 504)["edges"][use["ndx"] - 1]
                line = data(edge["curve"], 110)
                for uv, point in [(a, vector(line["start"])), (b, vector(line["terminate"]))]:
                    mapped = tuple(origin[i] + uv[0] * x[i] + uv[1] * y[i] for i in range(3))
                    assert math.dist(mapped, point) < 1e-12

    shell_vertices: dict[int, list[Vec]] = {}
    for index, row in rows.items():
        if row["entity"]["type"] != 514:
            continue
        shell = data(index, 514)
        assert shell["n"] == len(shell["faces"]) > 0
        form = row["entity"]["form"]
        assert form in (1, 2)
        shell_uses: Counter[tuple[int, int, bool]] = Counter()
        vertices = []
        volume = 0.0
        for use in shell["faces"]:
            assert use["orientation"] is True
            face = data(use["face"], 510)
            for loop in face["loops"]:
                shell_uses.update(loop_uses[loop])
                a, b, c = loop_vertices[loop]
                vertices.extend((a, b, c))
                volume += dot(a, cross(b, c)) / 6
        if form == 1:
            assert volume > 0
            assert all(
                count == 1 and shell_uses[(edge, n, not orientation)] == 1
                for (edge, n, orientation), count in shell_uses.items()
            )
        else:
            assert all(count == 1 for count in shell_uses.values())
        shell_vertices[index] = vertices

    for row in rows.values():
        if row["entity"]["type"] != 186:
            continue
        solid = row["entity"]["data"]
        assert solid["sof"] is True and solid["n"] == len(solid["voids"]) == 1
        outer = data(solid["shell"], 514)
        assert rows[solid["shell"]]["entity"]["form"] == 1
        for void in solid["voids"]:
            assert void["orientation"] is False
            assert rows[void["shell"]]["entity"]["form"] == 1
            # All inner vertices lie strictly inside every outward outer
            # face half-space: this proves containment and disjoint shells.
            for use in outer["faces"]:
                origin, normal = face_planes[use["face"]]
                assert all(
                    dot(subtract(p, origin), normal) < -1e-12 for p in shell_vertices[void["shell"]]
                )


if __name__ == "__main__":
    for builder in (open_triangle_document, solid_with_void_document):
        document, _ = builder()
        validate(document)
        print(f"{builder.__name__}: {len(document['entities'])} entity records validated")
