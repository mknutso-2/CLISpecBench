"""CLI-level coverage for spline, NURBS, and FEA-oriented IGES entities."""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from iges_support import (
    evaluate_entity,
    make_entity,
    semantic_roundtrip_json,
    wrap_entities,
    write_iges_from_json,
)


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


def test_parametric_spline_curve_roundtrips_and_evaluates(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = {
        "ctype": 3,
        "H": 2,
        "ndim": 3,
        "breakpoints": [0.0, 1.0, 2.0],
        "segments": [
            {
                "ax": 0.0, "bx": 0.0, "cx": 0.0, "dx": 1.0,
                "ay": 0.0, "by": 0.0, "cy": 0.0, "dy": 0.0,
                "az": 0.0, "bz": 0.0, "cz": 0.0, "dz": 0.0,
            },
            {
                "ax": 1.0, "bx": 3.0, "cx": 3.0, "dx": 1.0,
                "ay": 0.0, "by": 0.0, "cy": 0.0, "dy": 0.0,
                "az": 0.0, "bz": 0.0, "cz": 0.0, "dz": 0.0,
            },
        ],
        "tpx0": 8.0, "tpx1": 12.0, "tpx2": 6.0, "tpx3": 1.0,
        "tpy0": 0.0, "tpy1": 0.0, "tpy2": 0.0, "tpy3": 0.0,
        "tpz0": 0.0, "tpz1": 0.0, "tpz2": 0.0, "tpz3": 0.0,
    }
    roundtripped = _roundtrip_single(
        submission_command, tmp_path, entity_type=112, data=data,
    )
    assert roundtripped["breakpoints"] == [0.0, 1.0, 2.0]
    assert roundtripped["segments"][1]["cx"] == pytest.approx(3.0)
    assert roundtripped["tpx1"] == pytest.approx(12.0)

    iges_path = write_iges_from_json(
        submission_command,
        wrap_entities([make_entity(de_index=1, entity_type=112, data=data)]),
        tmp_path,
        name="spline-curve",
    )
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, 0.5, tmp_path, name="spline-curve-eval",
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.125, 0.0, 0.0], abs=1e-9)


def test_parametric_spline_surface_roundtrips_and_evaluates(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    coeff_x = [0.0] * 16
    coeff_y = [0.0] * 16
    coeff_z = [0.0] * 16
    coeff_x[1] = 1.0
    coeff_y[4] = 1.0
    coeff_z[2] = 1.0
    data = {
        "ctype": 2,
        "ptype": 1,
        "M": 1,
        "N": 1,
        "tu": [0.0, 1.0],
        "tv": [0.0, 1.0],
        "patches": [{
            "coeff_x": coeff_x,
            "coeff_y": coeff_y,
            "coeff_z": coeff_z,
        }],
    }
    roundtripped = _roundtrip_single(
        submission_command, tmp_path, entity_type=114, data=data,
    )
    assert roundtripped["patches"][0]["coeff_x"][1] == pytest.approx(1.0)
    assert roundtripped["patches"][0]["coeff_y"][4] == pytest.approx(1.0)
    assert roundtripped["patches"][0]["coeff_z"][2] == pytest.approx(1.0)

    iges_path = write_iges_from_json(
        submission_command,
        wrap_entities([make_entity(de_index=1, entity_type=114, data=data)]),
        tmp_path,
        name="spline-surface",
    )
    _, payload = evaluate_entity(
        submission_command,
        iges_path,
        1,
        0.5,
        tmp_path,
        s=0.5,
        name="spline-surface-eval",
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.5, 0.5, 0.25], abs=1e-9)


def test_rational_bspline_curve_roundtrips_plane_normal_and_evaluates(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = {
        "K": 2,
        "M": 2,
        "prop1": 1,
        "prop2": 0,
        "prop3": 0,
        "prop4": 0,
        "knots": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
        "weights": [1.0, math.sqrt(0.5), 1.0],
        "control_points": [
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        "v0": 0.0,
        "v1": 1.0,
        "plane_normal": [0.0, 0.0, 1.0],
    }
    roundtripped = _roundtrip_single(
        submission_command, tmp_path, entity_type=126, data=data,
    )
    assert roundtripped["plane_normal"] == pytest.approx([0.0, 0.0, 1.0])
    assert roundtripped["weights"][1] == pytest.approx(math.sqrt(0.5))
    assert roundtripped["control_points"][2] == pytest.approx([0.0, 1.0, 0.0])

    iges_path = write_iges_from_json(
        submission_command,
        wrap_entities([make_entity(de_index=1, entity_type=126, data=data)]),
        tmp_path,
        name="bspline-curve",
    )
    _, payload = evaluate_entity(
        submission_command, iges_path, 1, 0.5, tmp_path, name="bspline-curve-eval",
    )
    assert payload["ok"] is True
    x, y, z = payload["point"]
    assert z == pytest.approx(0.0, abs=1e-9)
    assert x == pytest.approx(y, abs=1e-9)
    assert x * x + y * y == pytest.approx(1.0, abs=1e-9)


def test_rational_bspline_curve_nonplanar_still_roundtrips_plane_normal_field(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=126,
        data={
            "K": 1,
            "M": 1,
            "prop1": 0,
            "prop2": 0,
            "prop3": 1,
            "prop4": 0,
            "knots": [0.0, 0.0, 1.0, 1.0],
            "weights": [1.0, 1.0],
            "control_points": [[0.0, 0.0, 0.0], [1.0, 0.0, 1.0]],
            "v0": 0.0,
            "v1": 1.0,
            "plane_normal": [0.0, 0.0, 0.0],
        },
    )
    assert data["prop1"] == 0
    assert data["plane_normal"] == pytest.approx([0.0, 0.0, 0.0])


def test_rational_bspline_surface_roundtrips_ranges_and_evaluates(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = {
        "K1": 1,
        "K2": 1,
        "M1": 1,
        "M2": 1,
        "prop1": 0,
        "prop2": 0,
        "prop3": 1,
        "prop4": 0,
        "prop5": 0,
        "knots_u": [0.0, 0.0, 1.0, 1.0],
        "knots_v": [0.0, 0.0, 1.0, 1.0],
        "weights": [1.0, 1.0, 1.0, 1.0],
        "control_points": [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
        ],
        "u0": 0.0,
        "u1": 1.0,
        "v0": 0.0,
        "v1": 1.0,
    }
    roundtripped = _roundtrip_single(
        submission_command, tmp_path, entity_type=128, data=data,
    )
    assert roundtripped["u1"] == pytest.approx(1.0)
    assert roundtripped["v1"] == pytest.approx(1.0)
    assert roundtripped["control_points"][3] == pytest.approx([1.0, 1.0, 0.0])

    iges_path = write_iges_from_json(
        submission_command,
        wrap_entities([make_entity(de_index=1, entity_type=128, data=data)]),
        tmp_path,
        name="bspline-surface",
    )
    _, payload = evaluate_entity(
        submission_command,
        iges_path,
        1,
        0.5,
        tmp_path,
        s=0.5,
        name="bspline-surface-eval",
    )
    assert payload["ok"] is True
    assert payload["point"] == pytest.approx([0.5, 0.5, 0.0], abs=1e-9)


def test_connect_point_roundtrips_full_metadata_fields(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=132,
        data={
            "location": [10.0, 20.0, 30.0],
            "display_symbol": 3,
            "tf": 101,
            "ff": 1,
            "cid": "PIN1",
            "pttcid": 5,
            "cfn": "INPUT",
            "pttcfn": 7,
            "cpid": 42,
            "fc": 12,
            "sf": 1,
            "psfi": 9,
        },
    )
    assert data["location"] == pytest.approx([10.0, 20.0, 30.0])
    assert data["display_symbol"] == 3
    assert data["pttcid"] == 5
    assert data["cfn"] == "INPUT"
    assert data["psfi"] == 9


def test_finite_element_roundtrips_connectivity_and_zero_node_pointer(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=136,
        data={
            "itop": 17,
            "n": 8,
            "nodes": [1, 3, 5, 7, 9, 11, 13, 0],
            "etyp": "LSO",
        },
    )
    assert data["itop"] == 17
    assert data["n"] == 8
    assert data["nodes"] == [1, 3, 5, 7, 9, 11, 13, 0]
    assert data["etyp"] == "LSO"
