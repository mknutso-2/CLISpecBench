"""Geometric evaluation tests for the ``iges eval`` subcommand.

Line coverage lives in ``test_line_entity.py``. This file covers the
parametric entity types enumerated in §1.6 of the agent contract —
Circular Arc (§4.3), Copious Data (§4.6), Composite Curve (§4.4),
Offset Curve (§4.25), Ruled Surface (§4.17), Surface of Revolution
(§4.18), and the B-Spline curve/surface types — using each entity's
**native** parameter domain (not a normalized `[0, 1]`). Also exercises:

* ``eval`` on a non-parametric entity type — must be rejected.
* Curve ``eval`` with ``--s`` supplied — must be rejected.
* Surface ``eval`` without ``--s`` — must be rejected.
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


# §4.25: Offset Curve (FLAG=1 uniform offset).
#
# Given a base Line from (0,0,0) to (10,0,0) with native t ∈ [0, 1],
# offset by d1 = 2 along the +Y unit normal, the offset curve at
# parameter t_in_base is (10*t_in_base, 2, 0). The offset curve uses
# the base curve's parameter [TT1, TT2] = [0, 1].
def _offset_curve_over_line_doc(d1: float) -> dict[str, object]:
    return wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [10.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=130, data={
            "de1": 1,
            "flag": 1,    # uniform offset
            "de2": 0,
            "ndim": 0,
            "ptype": 2,   # parameter
            "d1": d1, "td1": 0.0, "d2": 0.0, "td2": 0.0,
            "vx": 0.0, "vy": 1.0, "vz": 0.0,  # +Y unit normal
            "tt1": 0.0, "tt2": 1.0,
        }),
    ])


def test_offset_curve_eval_at_start_is_displaced_base_start(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _offset_curve_over_line_doc(d1=2.0)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 3, 0.0, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.0, 2.0, 0.0], abs=1e-9)


def test_offset_curve_eval_at_midparam_follows_base(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _offset_curve_over_line_doc(d1=2.0)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 3, 0.5, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([5.0, 2.0, 0.0], abs=1e-9)


def test_offset_curve_eval_nonzero_offset_follows_base(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # Ensure the offset displacement actually scales with d1.
    doc = _offset_curve_over_line_doc(d1=5.0)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(submission_command, iges_path, 3, 0.25, tmp_path)
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([2.5, 5.0, 0.0], abs=1e-9)


# §4.17: Ruled Surface (Type 118).
#
# Two parallel line segments bound a flat ruled surface:
#   Curve 1: (0,0,0) → (10,0,0)
#   Curve 2: (0,5,0) → (10,5,0)
# Form 0: t ∈ [0, 1] along curves, s ∈ [0, 1] across the rule.
# At (t, s) = (0.3, 0.4): point = (3, 2, 0).
def _ruled_surface_two_lines_doc(
    dirflg: int = 0, form: int = 0
) -> dict[str, object]:
    return wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [10.0, 0.0, 0.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [0.0, 5.0, 0.0], "terminate": [10.0, 5.0, 0.0]}),
        make_entity(de_index=5, entity_type=118, form=form, data={
            "de1": 1, "de2": 3, "dirflg": dirflg, "devflg": 0}),
    ])


def test_ruled_surface_eval_interior_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _ruled_surface_two_lines_doc()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 0.3, tmp_path, s=0.4,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([3.0, 2.0, 0.0], abs=1e-9)


def test_ruled_surface_eval_on_first_curve_returns_curve1_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _ruled_surface_two_lines_doc()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 0.5, tmp_path, s=0.0,
    )
    assert payload["ok"] is True
    # s=0 is on curve 1 at u=0.5 → (5, 0, 0)
    assert payload["point"] == pytest.approx([5.0, 0.0, 0.0], abs=1e-9)


def test_ruled_surface_eval_on_second_curve_returns_curve2_point(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _ruled_surface_two_lines_doc()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 0.5, tmp_path, s=1.0,
    )
    assert payload["ok"] is True
    # s=1 is on curve 2 at u=0.5 → (5, 5, 0)
    assert payload["point"] == pytest.approx([5.0, 5.0, 0.0], abs=1e-9)


def test_ruled_surface_eval_dirflg_reverses_second_curve(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # dirflg=1 matches curve 1 start to curve 2 end. At t=0, s=1 we end
    # up at the *end* of curve 2, which is (10, 5, 0).
    doc = _ruled_surface_two_lines_doc(dirflg=1)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 0.0, tmp_path, s=1.0,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([10.0, 5.0, 0.0], abs=1e-9)


# §4.18: Surface of Revolution (Type 120).
#
# Axis: Z-axis (Line from (0,0,0) to (0,0,1)).
# Generatrix: Line from (2,0,0) to (2,0,3) (vertical line at x=2 in the
#   XZ plane). Revolving it produces a cylinder of radius 2 and height
#   3. At (t, s) on the surface, the point is
#       (2·cos(s), 2·sin(s), 3·t_fraction_along_generatrix_in_z).
# Line native param t ∈ [0, 1], so at t=0.5 the generatrix point is
# (2, 0, 1.5).
def _cylinder_via_surface_of_revolution(
    sa: float, ta: float,
) -> dict[str, object]:
    return wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [0.0, 0.0, 0.0], "terminate": [0.0, 0.0, 1.0]}),
        make_entity(de_index=3, entity_type=110, data={
            "start": [2.0, 0.0, 0.0], "terminate": [2.0, 0.0, 3.0]}),
        make_entity(de_index=5, entity_type=120, data={
            "l": 1, "c": 3, "sa": sa, "ta": ta}),
    ])


def test_surface_of_revolution_eval_at_start_angle(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # Pad the angle range slightly on both sides — IGES real literals
    # use %.15g and round the last bit of π, which would put s=π
    # epsilon-past ta=π. The geometric assertion is unaffected.
    doc = _cylinder_via_surface_of_revolution(sa=-0.1, ta=math.pi + 0.1)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t=0 → generatrix start (2, 0, 0); s=0 → no rotation.
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 0.0, tmp_path, s=0.0,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([2.0, 0.0, 0.0], abs=1e-9)


def test_surface_of_revolution_eval_quarter_rotation(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _cylinder_via_surface_of_revolution(sa=-0.1, ta=math.pi + 0.1)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t=0.5 → generatrix point (2, 0, 1.5); s=π/2 → rotate 90° about Z
    # → (0, 2, 1.5).
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 0.5, tmp_path, s=math.pi / 2,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.0, 2.0, 1.5], abs=1e-9)


def test_surface_of_revolution_eval_half_rotation(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _cylinder_via_surface_of_revolution(sa=-0.1, ta=math.pi + 0.1)
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    # t=1 → generatrix end (2, 0, 3); s=π → rotate 180° → (−2, 0, 3).
    _, payload = evaluate_entity(
        submission_command, iges_path, 5, 1.0, tmp_path, s=math.pi,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([-2.0, 0.0, 3.0], abs=1e-9)


# §4.19: Tabulated Cylinder (Type 122).
#
# The directrix supplies the varying surface point; the generatrix
# direction is fixed by the vector from the directrix start point to the
# entity's terminate point. `s` runs from the directrix (`s=0`) to the
# terminate point (`s=1`) along that fixed vector.
def _tabulated_cylinder_over_line_doc() -> dict[str, object]:
    return wrap_entities([
        make_entity(de_index=1, entity_type=110, data={
            "start": [1.0, 2.0, 3.0], "terminate": [5.0, 2.0, 3.0]}),
        make_entity(de_index=3, entity_type=122, data={
            "de": 1, "terminate_point": [1.0, 2.0, 7.0]}),
    ])


def _tabulated_cylinder_over_arc_doc() -> dict[str, object]:
    return wrap_entities([
        make_entity(de_index=1, entity_type=100, data={
            "zt": 1.0,
            "x1": 0.0, "y1": 0.0,
            "x2": 2.0, "y2": 0.0,
            "x3": 0.0, "y3": 2.0,
        }),
        make_entity(de_index=3, entity_type=122, data={
            "de": 1, "terminate_point": [3.0, 0.0, 4.0]}),
    ])


def test_tabulated_cylinder_over_line_interpolates_along_generatrix(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _tabulated_cylinder_over_line_doc()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 3, 0.25, tmp_path, s=0.5,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([2.0, 2.0, 5.0], abs=1e-9)


def test_tabulated_cylinder_over_arc_keeps_generatrix_parallel(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = _tabulated_cylinder_over_arc_doc()
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    _, payload = evaluate_entity(
        submission_command, iges_path, 3, math.pi / 2, tmp_path, s=1.0,
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([1.0, 2.0, 4.0], abs=1e-9)


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
