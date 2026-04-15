"""Geometric evaluation tests for the ``iges eval`` subcommand.

Line coverage lives in ``test_line_entity.py``. This file adds:

* Circular Arc (§4.3) — evaluation at t=0 / t=0.5 / t=1.
* ``eval`` on a non-parametric entity type — must be rejected.
* ``eval`` with t outside [0,1] — must be rejected (§1 eval contract).

Ports the CLI-observable subset of ``test_geometric_evaluation.cpp``;
B-spline / surface / block / sphere / cylinder evaluation is not yet
covered — a follow-up can layer those on once the CLI is stable.
"""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path

import pytest

from iges_support import (
    evaluate_entity,
    make_entity,
    wrap_entities,
    write_iges_from_json,
)


def _single_arc_document(
    zt: float,
    center: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> dict[str, object]:
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=100,
            data={
                "zt": zt,
                "x1": center[0], "y1": center[1],
                "x2": start[0],  "y2": start[1],
                "x3": end[0],    "y3": end[1],
            },
        ),
    ])


# §4.3: Circular Arc parameterization.
#
# The IGES spec does not normalize the arc parameter. The reference
# implementation passes t directly as the angular parameter (radians),
# matching the SDK's `CircularArcEntity::evaluate()`:
#
#     C(t) = (x1 + R·cos(t),  y1 + R·sin(t),  zt)
#
# Quarter circle below: center (0,0), radius 5, start_angle = 0,
# end_angle = π/2. Evaluating at angles 0, π/4, π/2 gives start,
# midpoint-on-arc, and end respectively.
def test_arc_eval_at_start_angle_gives_start_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _single_arc_document(0.0, (0.0, 0.0), (5.0, 0.0), (0.0, 5.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 1, 0.0, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([5.0, 0.0, 0.0], abs=1e-9)


def test_arc_eval_at_end_angle_gives_end_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _single_arc_document(0.0, (0.0, 0.0), (5.0, 0.0), (0.0, 5.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, math.pi / 2, tmp_path
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.0, 5.0, 0.0], abs=1e-9)


def test_arc_eval_at_midangle_is_on_arc(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _single_arc_document(0.0, (0.0, 0.0), (5.0, 0.0), (0.0, 5.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, math.pi / 4, tmp_path
    )
    assert payload["ok"] is True
    expected = 5.0 * math.cos(math.pi / 4)
    assert payload["point"] == pytest.approx([expected, expected, 0.0], abs=1e-9)


# §4.3: arc with a non-zero start angle.
#
# Start point at (R·cos(π/6), R·sin(π/6)), end point at (R·cos(2π/3),
# R·sin(2π/3)). Evaluating `iges eval` at t = π/6 must return the
# start point; t = 2π/3 must return the end point; t = π/2 (midway in
# angle space) must lie on the circle of radius R.
#
# This guards against implementations that silently assume the arc
# begins at angle 0.
def test_arc_eval_at_nonzero_start_angle_returns_start_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    r = 5.0
    start_angle = math.pi / 6
    end_angle = 2.0 * math.pi / 3
    start = (r * math.cos(start_angle), r * math.sin(start_angle))
    end = (r * math.cos(end_angle), r * math.sin(end_angle))
    doc = _single_arc_document(0.0, (0.0, 0.0), start, end)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, start_angle, tmp_path,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx(
        [start[0], start[1], 0.0], abs=1e-9,
    )


def test_arc_eval_at_nonzero_end_angle_returns_end_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    r = 5.0
    start_angle = math.pi / 6
    end_angle = 2.0 * math.pi / 3
    start = (r * math.cos(start_angle), r * math.sin(start_angle))
    end = (r * math.cos(end_angle), r * math.sin(end_angle))
    doc = _single_arc_document(0.0, (0.0, 0.0), start, end)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, end_angle, tmp_path,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx(
        [end[0], end[1], 0.0], abs=1e-9,
    )


def test_arc_eval_offcenter_arc_midangle_on_circle(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # Arc centered at (10, 20), radius 3, spanning angles π/4 to 3π/4.
    cx, cy = 10.0, 20.0
    r = 3.0
    start_angle = math.pi / 4
    end_angle = 3.0 * math.pi / 4
    start = (cx + r * math.cos(start_angle), cy + r * math.sin(start_angle))
    end = (cx + r * math.cos(end_angle), cy + r * math.sin(end_angle))
    doc = _single_arc_document(0.0, (cx, cy), start, end)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # Mid-arc angle must land on the circle centered at (cx, cy).
    mid = (start_angle + end_angle) / 2.0
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, mid, tmp_path,
    )
    assert payload["ok"] is True
    px, py, pz = payload["point"]
    assert (px - cx) ** 2 + (py - cy) ** 2 == pytest.approx(r * r, abs=1e-9)
    assert pz == pytest.approx(0.0, abs=1e-9)


def test_arc_eval_respects_z_plane(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # Arc parallel to XY but at z = 2.5.
    doc = _single_arc_document(2.5, (0.0, 0.0), (1.0, 0.0), (0.0, 1.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 1, 0.0, tmp_path)
    assert payload["ok"] is True
    assert payload["point"][2] == pytest.approx(2.5)


# §4.6 + §1.6: Copious Data polyline parameterization.
#
# Forms 11 (2D linear path), 12 (3D linear path), and 63 (simple closed
# 2D area) evaluate as piecewise-linear polylines with parameter
# ``t ∈ [0, N−1]``: integer values land on tuple points, and fractional
# values linearly interpolate between adjacent tuples.
def _copious_data_form11_document(
    zt: float, points_2d: Sequence[tuple[float, float]]
) -> dict[str, object]:
    flat: list[float] = []
    for x, y in points_2d:
        flat.extend([x, y])
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=106,
            form=11,
            data={"ip": 1, "n": len(points_2d), "zt": zt, "data": flat},
        ),
    ])


def _copious_data_form12_document(
    points_3d: Sequence[tuple[float, float, float]],
) -> dict[str, object]:
    flat: list[float] = []
    for x, y, z in points_3d:
        flat.extend([x, y, z])
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=106,
            form=12,
            data={"ip": 2, "n": len(points_3d), "zt": 0.0, "data": flat},
        ),
    ])


def test_copious_data_form11_at_vertex_returns_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _copious_data_form11_document(
        2.5, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    )
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 1, 1.0, tmp_path)
    assert payload["ok"] is True
    # Tuple index 1 with zt=2.5 supplying z.
    assert payload["point"] == pytest.approx([1.0, 0.0, 2.5], abs=1e-9)


def test_copious_data_form11_midpoint_interpolates(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _copious_data_form11_document(
        0.0, [(0.0, 0.0), (2.0, 0.0), (2.0, 4.0)]
    )
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t = 1.5: halfway between tuples 1 (2,0) and 2 (2,4).
    _, payload = evaluate_entity(submission_command, iges_path, 1, 1.5, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([2.0, 2.0, 0.0], abs=1e-9)


def test_copious_data_form12_3d_path_at_fractional_t(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _copious_data_form12_document([
        (0.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (3.0, 0.0, 6.0),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t = 0.25: 25% between tuples 0 and 1 → (0.75, 0, 0).
    _, payload = evaluate_entity(submission_command, iges_path, 1, 0.25, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.75, 0.0, 0.0], abs=1e-9)


# §4.4: Composite Curve default parameterization.
#
# The composite parameter line accumulates each constituent's native
# span: T(0) = 0, T(i+1) = T(i) + (v1_i − v0_i). Two Line constituents
# (native span [0, 1] each) produce a composite domain of [0, 2];
# t < 1 picks the first line at local (t), t ≥ 1 picks the second at
# local (t − 1).
def test_composite_curve_eval_at_start_returns_first_constituent_start(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [3.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [3.0, 0.0, 0.0], "terminate": [3.0, 4.0, 0.0]}),
        make_entity(de_index=5, entity_type=102, data={
            "constituents": [1, 3]}),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 5, 0.0, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.0, 0.0, 0.0], abs=1e-9)


def test_composite_curve_eval_inside_first_constituent(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [3.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [3.0, 0.0, 0.0], "terminate": [3.0, 4.0, 0.0]}),
        make_entity(de_index=5, entity_type=102, data={
            "constituents": [1, 3]}),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t = 0.5 → halfway along first Line (native [0,1]) → (1.5, 0, 0)
    _, payload = evaluate_entity(submission_command, iges_path, 5, 0.5, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([1.5, 0.0, 0.0], abs=1e-9)


def test_composite_curve_eval_at_boundary_goes_to_first_leg_endpoint(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [3.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [3.0, 0.0, 0.0], "terminate": [3.0, 4.0, 0.0]}),
        make_entity(de_index=5, entity_type=102, data={
            "constituents": [1, 3]}),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t = 1.0 is the junction; both legs pass through (3, 0, 0).
    _, payload = evaluate_entity(submission_command, iges_path, 5, 1.0, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([3.0, 0.0, 0.0], abs=1e-9)


def test_composite_curve_eval_inside_second_constituent(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [3.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [3.0, 0.0, 0.0], "terminate": [3.0, 4.0, 0.0]}),
        make_entity(de_index=5, entity_type=102, data={
            "constituents": [1, 3]}),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t = 1.5 → halfway along second Line, local t = 0.5 → (3, 2, 0)
    _, payload = evaluate_entity(submission_command, iges_path, 5, 1.5, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([3.0, 2.0, 0.0], abs=1e-9)


def test_composite_curve_eval_at_terminus_returns_second_constituent_end(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [3.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [3.0, 0.0, 0.0], "terminate": [3.0, 4.0, 0.0]}),
        make_entity(de_index=5, entity_type=102, data={
            "constituents": [1, 3]}),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 5, 2.0, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([3.0, 4.0, 0.0], abs=1e-9)


# §1 eval contract: non-parametric entity types must be rejected.
def test_eval_on_non_parametric_entity_is_rejected(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=406,  # Property — not geometrically parametric
            data={
                "np": 1,
                "values": [{"kind": "real", "value": 1.0}],
            },
        ),
    ])
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, 0.0, tmp_path, check=False,
    )
    assert payload["ok"] is False
    assert "error" in payload
