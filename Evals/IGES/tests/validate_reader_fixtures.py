"""Unscored maintenance check for the frozen input corpus (run as a script).

This intentionally imports neither a submission nor a reference implementation.
Physical records follow §2.2.4; parameter ordering follows the cited §4 tables.
The scored tests separately check independently calculated geometric outcomes.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

# Parameter Data tables in §§4.3, 4.5, 4.17–4.21, 4.25, 4.30, 4.50–4.54.
_SCALARS = {
    100: "zt x1 y1 x2 y2 x3 y3",
    104: "A B C D E F zt x1 y1 x2 y2",
    118: "de1 de2 dirflg devflg",
    120: "l c sa ta",
    123: "x y z",
    130: "de1 flag de2 ndim ptype d1 td1 d2 td2 vx vy vz tt1 tt2",
    140: "nx ny nz d de",
    190: "deloc denrml derefd",
    192: "deloc deaxis radius derefd",
    194: "deloc deaxis radius sangle derefd",
    196: "deloc radius deaxis derefd",
    198: "deloc deaxis majrad minrad derefd",
}


def _flatten(rows: list[list[float]]) -> list[float]:
    return [v for row in rows for v in row]


def _parameters(entity_type: int, data: dict[str, Any]) -> list[float]:
    if entity_type in _SCALARS:
        return [data[k] for k in _SCALARS[entity_type].split()]
    if entity_type == 102:  # §4.4
        return [len(data["constituents"]), *data["constituents"]]
    if entity_type == 106:  # §4.6, zT exists only for IP=1.
        return [data["ip"], data["n"], *([data["zt"]] if data["ip"] == 1 else []), *data["data"]]
    if entity_type == 110:  # §4.13
        return [*data["start"], *data["terminate"]]
    if entity_type == 112:  # §4.14: each segment is X/Y/Z, cubic coefficients.
        values: list[float] = [
            data["ctype"],
            data["H"],
            data["ndim"],
            len(data["segments"]),
            *data["breakpoints"],
        ]
        for segment in data["segments"]:
            values += [segment[c + axis] for axis in "xyz" for c in "abcd"]
        return values + [data[f"tp{axis}{i}"] for axis in "xyz" for i in range(4)]
    if entity_type == 116:  # §4.16
        return [*data["coords"], data["display_symbol"]]
    if entity_type == 122:  # §4.19
        return [data["de"], *data["terminate_point"]]
    if entity_type == 124:  # §4.21: translation is interleaved after each row.
        return [
            v
            for row, t in zip(data["rotation"], data["translation"], strict=True)
            for v in [*row, t]
        ]
    if entity_type == 126:  # §4.23
        return [data[k] for k in "K M prop1 prop2 prop3 prop4".split()] + [
            *data["knots"],
            *data["weights"],
            *_flatten(data["control_points"]),
            data["v0"],
            data["v1"],
            *data["plane_normal"],
        ]
    if entity_type == 128:  # §4.24
        return [data[k] for k in "K1 K2 M1 M2 prop1 prop2 prop3 prop4 prop5".split()] + [
            *data["knots_u"],
            *data["knots_v"],
            *data["weights"],
            *_flatten(data["control_points"]),
            data["u0"],
            data["u1"],
            data["v0"],
            data["v1"],
        ]
    if entity_type == 502:  # §4.143
        return [data["n"], *_flatten(data["vertices"])]
    if entity_type == 504:  # §4.144
        return [
            data["n"],
            *[edge[k] for edge in data["edges"] for k in ("curve", "svp", "sv", "tvp", "tv")],
        ]
    if entity_type == 508:  # §4.145; this corpus uses legal optional K=0.
        return [
            data["n"],
            *[
                edge[k]
                for edge in data["edge_uses"]
                for k in ("type", "edge", "ndx", "orientation", "k")
            ],
        ]
    if entity_type == 510:  # §4.146
        return [data["surf"], data["n"], data["outer_loop_flag"], *data["loops"]]
    if entity_type == 514:  # §4.147
        return [data["n"], *[face[k] for face in data["faces"] for k in ("face", "orientation")]]
    if entity_type == 406:  # §4.124, numeric property used by the rejection probe.
        return [data["np"], *[v["value"] for v in data["values"]]]
    raise AssertionError(f"Add an independent Parameter Data check for type {entity_type}")


def _same_numbers(actual: list[float], expected: list[float]) -> None:
    assert len(actual) == len(expected), (len(actual), len(expected))
    assert all(
        math.isclose(a, b, rel_tol=2e-12, abs_tol=1e-12)
        for a, b in zip(actual, expected, strict=True)
    ), (actual, expected)


def _curve_point(entity: dict[str, Any], t: float) -> tuple[float, float, float]:
    data = entity["entity"]["data"]
    if entity["entity"]["type"] == 110:
        return tuple(data["start"][i] * (1 - t) + data["terminate"][i] * t for i in range(3))  # type: ignore[return-value]
    # All new circular boundary curves are degree2 rational Bezier spans.
    assert entity["entity"]["type"] == 126 and data["K"] == data["M"] == 2
    weights = [
        data["weights"][0] * (1 - t) ** 2,
        data["weights"][1] * 2 * t * (1 - t),
        data["weights"][2] * t**2,
    ]
    return tuple(
        sum(weights[j] * data["control_points"][j][i] for j in range(3)) / sum(weights)
        for i in range(3)
    )  # type: ignore[return-value]


def _validate_analytic_context(document: dict[str, Any]) -> None:
    """Check new patches against implicit equations, using no fixture builder.

    Physical PD order alone cannot establish semantic legality. These checks
    independently verify reference types, closed boundaries, and that sampled
    actual rational curves lie on their claimed §4.51–4.54 analytic surfaces.
    """
    entities = {e["de_index"]: e for e in document["entities"]}
    for de, surface in entities.items():
        kind = surface["entity"]["type"]
        if kind not in (192, 194, 196, 198):
            continue
        data = surface["entity"]["data"]
        assert surface["directory_entry"]["status"]["subordinate"] == "physically_dependent"
        assert entities[data["deloc"]]["entity"]["type"] == 116
        assert entities[data["deaxis"]]["entity"]["type"] == 123
        assert entities[data["derefd"]]["entity"]["type"] == 123
        faces = [
            e
            for e in entities.values()
            if e["entity"]["type"] == 510 and e["entity"]["data"]["surf"] == de
        ]
        assert len(faces) == 1
        face = faces[0]
        assert face["entity"]["form"] == 1 and face["entity"]["data"]["n"] == 1
        shells = [e for e in entities.values() if e["entity"]["type"] == 514]
        assert len(shells) == 1 and shells[0]["entity"]["form"] == 2
        assert shells[0]["entity"]["data"]["faces"] == [
            {"face": face["de_index"], "orientation": True}
        ]
        loop = entities[face["entity"]["data"]["loops"][0]]
        assert loop["entity"]["type"] == 508 and loop["entity"]["form"] == 1
        uses = loop["entity"]["data"]["edge_uses"]
        starts: list[list[float]] = []
        ends: list[list[float]] = []
        for use in uses:
            edge_list = entities[use["edge"]]
            assert edge_list["entity"]["type"] == 504 and edge_list["entity"]["form"] == 1
            edge = edge_list["entity"]["data"]["edges"][use["ndx"] - 1]
            curve = entities[edge["curve"]]
            vertex_list = entities[edge["svp"]]
            assert edge["svp"] == edge["tvp"] and vertex_list["entity"]["type"] == 502
            assert vertex_list["entity"]["form"] == 1
            vertices = vertex_list["entity"]["data"]["vertices"]
            start, end = vertices[edge["sv"] - 1], vertices[edge["tv"] - 1]
            assert math.dist(_curve_point(curve, 0), start) < 1e-12
            assert math.dist(_curve_point(curve, 1), end) < 1e-12
            assert use["orientation"] and use["k"] == 0
            starts.append(start)
            ends.append(end)
            for t in (0, 0.25, 0.5, 0.75, 1):
                x, y, z = _curve_point(curve, t)
                if kind == 192:
                    residual = x * x + y * y - data["radius"] ** 2
                elif kind == 194:
                    residual = (
                        x * x
                        + y * y
                        - (data["radius"] + z * math.tan(math.radians(data["sangle"]))) ** 2
                    )
                elif kind == 196:
                    residual = x * x + y * y + z * z - data["radius"] ** 2
                else:
                    residual = (
                        (math.hypot(x, y) - data["majrad"]) ** 2 + z * z - data["minrad"] ** 2
                    )
                assert abs(residual) < 1e-10, (kind, t, residual)
        assert all(
            math.dist(end, starts[(i + 1) % len(starts)]) < 1e-12 for i, end in enumerate(ends)
        )
        assert len(starts) == 4 and math.dist(starts[0], starts[2]) > 0.1


def validate(path: Path) -> tuple[int, int]:
    fixtures: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    entities_checked = 0
    for key, fixture in fixtures.items():
        document = fixture["document"]
        _validate_analytic_context(document)
        assert (
            key
            == hashlib.sha256(
                json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        )
        lines = fixture["iges"].splitlines()
        assert all(len(line) == 80 for line in lines)
        grouped = {s: [line for line in lines if line[72] == s] for s in "SGDPT"}
        assert lines == [line for s in "SGDPT" for line in grouped[s]]
        for group in grouped.values():
            assert [int(line[73:80]) for line in group] == list(range(1, len(group) + 1))
        assert len(grouped["T"]) == 1
        assert grouped["T"][0][:32] == "".join(f"{s}{len(grouped[s]):7d}" for s in "SGDP")
        assert [line[:72].rstrip() for line in grouped["S"]] == document["start_lines"]
        assert len(grouped["D"]) == len(document["entities"]) * 2
        for i, entity in enumerate(document["entities"]):
            first, second = grouped["D"][i * 2 : i * 2 + 2]
            kind = entity["entity"]["type"]
            status = entity["directory_entry"]["status"]
            subordinate = {
                "independent": "00",
                "physically_dependent": "01",
                "logically_dependent": "02",
                "both": "03",
            }
            assert first[66:68] == subordinate[status["subordinate"]]
            if kind == 123:
                assert status["subordinate"] == "physically_dependent"
                assert any(
                    entity["de_index"] == parent["entity"]["data"].get(field)
                    for parent in document["entities"]
                    for field in ("denrml", "deaxis", "derefd")
                )
            assert int(first[:8]) == int(second[:8]) == kind
            assert int(second[32:40]) == entity["entity"]["form"]
            assert int(first[73:80]) == entity["de_index"]
            begin, count = int(first[8:16]), int(second[24:32])
            records = grouped["P"][begin - 1 : begin - 1 + count]
            assert len(records) == count and count > 0
            assert all(
                line[64] == " " and int(line[65:72]) == entity["de_index"] for line in records
            )
            pd = "".join(line[:64] for line in records).strip()
            assert pd.endswith(";")
            actual = [float(token.strip().replace("D", "E") or "0") for token in pd[:-1].split(",")]
            assert actual[0] == kind
            data = entity["entity"]["data"]
            if kind == 114:
                # The frozen corpus explicitly supplies (M+1)*(N+1) blocks.
                # §2.2.3 also permits terminating trailing default slots; the
                # scored writer check only constrains real/interleaved slots.
                prefix = [data[k] for k in ("ctype", "ptype", "M", "N")] + [
                    *data["tu"],
                    *data["tv"],
                ]
                _same_numbers(actual[1 : 1 + len(prefix)], prefix)
                blocks = actual[1 + len(prefix) :]
                assert len(blocks) == (data["M"] + 1) * (data["N"] + 1) * 48
                for row in range(data["M"]):
                    for column in range(data["N"]):
                        patch = data["patches"][row * data["N"] + column]
                        start = (row * (data["N"] + 1) + column) * 48
                        _same_numbers(
                            blocks[start : start + 48],
                            [*patch["coeff_x"], *patch["coeff_y"], *patch["coeff_z"]],
                        )
            else:
                _same_numbers(actual[1:], _parameters(kind, data))
            entities_checked += 1
    return len(fixtures), entities_checked


if __name__ == "__main__":
    print(
        "Validated fixture and entity counts:",
        validate(Path(__file__).parent / "data" / "reader-fixtures.json"),
    )
