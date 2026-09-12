"""CLI-level coverage for valid IGES surface-boundary/reference entities.

Pointers in a successful write/parse fixture resolve to real, correctly typed
geometry. §§4.31–4.34 require closed, nonintersecting boundaries on a regular
parametric surface; accepting a dangling or self-referential record is not a
condition of earning its field-preservation score.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from iges_support import make_entity, semantic_roundtrip_json, wrap_entities


def _dependent_entity(
    de_index: int,
    entity_type: int,
    data: Mapping[str, Any],
    *,
    form: int = 0,
    parametric: bool = False,
    logical: bool = False,
) -> dict[str, Any]:
    record = make_entity(de_index=de_index, entity_type=entity_type, form=form, data=data)
    # §2.2.4.4.9: referenced construction geometry is physically dependent;
    # group members are logically dependent. §4.32 marks parameter curves 05.
    status = record["directory_entry"]["status"]
    status["subordinate"] = "logically_dependent" if logical else "physically_dependent"
    status["entity_use"] = "parametric_2d" if parametric else "geometry"
    return record


def _surface() -> dict[str, Any]:
    # §4.24: degree-one, unit-weight tensor product gives S(u,v)=(u,v,0)
    # on [0,10]². It is regular, one-to-one and has positive +Z normal.
    return _dependent_entity(
        3,
        128,
        {
            "K1": 1,
            "K2": 1,
            "M1": 1,
            "M2": 1,
            "prop1": 0,
            "prop2": 0,
            "prop3": 1,
            "prop4": 0,
            "prop5": 0,
            "knots_u": [0.0, 0.0, 10.0, 10.0],
            "knots_v": [0.0, 0.0, 10.0, 10.0],
            "weights": [1.0, 1.0, 1.0, 1.0],
            "control_points": [
                [0.0, 0.0, 0.0],
                [10.0, 0.0, 0.0],
                [0.0, 10.0, 0.0],
                [10.0, 10.0, 0.0],
            ],
            "u0": 0.0,
            "u1": 10.0,
            "v0": 0.0,
            "v1": 10.0,
        },
    )


def _line(
    de_index: int, start: tuple[float, float], end: tuple[float, float], *, parametric: bool = False
) -> dict[str, Any]:
    return _dependent_entity(
        de_index, 110, {"start": [*start, 0.0], "terminate": [*end, 0.0]}, parametric=parametric
    )


def _path(
    de_index: int, points: Sequence[tuple[float, float]], *, parametric: bool = False
) -> dict[str, Any]:
    # §4.7: both forms represent the same polygon; the parameter-space form
    # is explicitly two-dimensional and is never silently scaled to model units.
    coords = [list(point) if parametric else [*point, 0.0] for point in points]
    return _dependent_entity(
        de_index,
        106,
        {
            "ip": 1 if parametric else 2,
            "n": len(points),
            "zt": 0.0,
            "data": [coordinate for point in coords for coordinate in point],
        },
        form=11 if parametric else 12,
        parametric=parametric,
    )


def _closed_boundaries(entity_type: int) -> list[dict[str, Any]]:
    # §§4.31 D6/D10 and 4.34: one CCW outer rectangle encloses two disjoint
    # CW holes. The active region is connected and lies left of every boundary.
    polygons = [
        [(1.0, 1.0), (9.0, 1.0), (9.0, 9.0), (1.0, 9.0), (1.0, 1.0)],
        [(2.0, 2.0), (2.0, 3.0), (3.0, 3.0), (3.0, 2.0), (2.0, 2.0)],
        [(6.0, 6.0), (6.0, 7.0), (7.0, 7.0), (7.0, 6.0), (6.0, 6.0)],
    ]
    records = [_surface()]
    for index, points in zip((5, 11, 17), polygons, strict=True):
        if entity_type == 141:
            data = {
                "type": 1,
                "pref": 2,
                "sptr": 3,
                "n": 1,
                "curves": [{"crvpt": index + 2, "sense": 1, "k": 1, "pscpt": [index + 4]}],
            }
        else:
            data = {"crtn": 0, "sptr": 3, "bptr": index + 4, "cptr": index + 2, "pref": 3}
        records.extend(
            [
                _dependent_entity(index, entity_type, data),
                _path(index + 2, points),
                _path(index + 4, points, parametric=True),
            ]
        )
    return records


def _roundtrip_single(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
    context: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    doc = wrap_entities(
        [make_entity(de_index=1, entity_type=entity_type, form=form, data=data), *context]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    entity = reparsed["entities"][0]["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def test_boundary_with_parameter_space_curve_collections_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §4.31 D12: the first model polyline is reproduced by two parameter
    # lines. Reversing the second model line (SENSE=2) closes the CCW triangle.
    a, b, c = (1.0, 1.0), (9.0, 1.0), (9.0, 9.0)
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=141,
        data={
            "type": 1,
            "pref": 2,
            "sptr": 3,
            "n": 2,
            "curves": [
                {"crvpt": 5, "sense": 1, "k": 2, "pscpt": [7, 9]},
                {"crvpt": 11, "sense": 2, "k": 1, "pscpt": [13]},
            ],
        },
        context=[
            _surface(),
            _path(5, [a, b, c]),
            _line(7, a, b, parametric=True),
            _line(9, b, c, parametric=True),
            _line(11, a, c),
            _line(13, c, a, parametric=True),
        ],
    )
    assert data["type"] == 1
    assert data["pref"] == 2
    assert data["sptr"] == 3
    assert data["curves"][0]["pscpt"] == [7, 9]
    assert data["curves"][1]["sense"] == 2


def test_curve_on_parametric_surface_roundtrips_creation_and_preference(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §4.32 CRTN=3: matching horizontal lines are a genuine v=2 isoparametric
    # curve of S(u,v)=(u,v,0), with the same orientation in both spaces.
    payload = {"crtn": 3, "sptr": 3, "bptr": 5, "cptr": 7, "pref": 3}
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=142,
        data=payload,
        context=[
            _surface(),
            _line(5, (1.0, 2.0), (9.0, 2.0), parametric=True),
            _line(7, (1.0, 2.0), (9.0, 2.0)),
        ],
    )
    assert data == payload


def test_bounded_surface_with_multiple_boundaries_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=143,
        data={"type": 1, "sptr": 3, "n": 3, "bdpt": [5, 11, 17]},
        context=_closed_boundaries(141),
    )
    assert data["type"] == 1
    assert data["sptr"] == 3
    assert data["n"] == 3
    assert data["bdpt"] == [5, 11, 17]


def test_trimmed_surface_with_default_outer_boundary_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    payload = {"pts": 3, "n1": 0, "n2": 0, "pto": 0, "pti": []}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=144, data=payload, context=[_surface()]
    )
    assert data == payload


def test_trimmed_surface_with_inner_boundaries_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=144,
        data={"pts": 3, "n1": 1, "n2": 2, "pto": 5, "pti": [11, 17]},
        context=_closed_boundaries(142),
    )
    assert data["pts"] == 3
    assert data["n1"] == 1
    assert data["pto"] == 5
    assert data["pti"] == [11, 17]


def test_associativity_instance_group_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §4.85 form7 has the same unordered member list without requiring the
    # additional back-pointer lists that the published JSON schema omits.
    members = [
        _dependent_entity(
            index, 116, {"coords": [float(index), 0.0, 0.0], "display_symbol": 0}, logical=True
        )
        for index in (3, 5, 7)
    ]
    payload = {"n": 3, "entries": [3, 5, 7]}
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=402, form=7, data=payload, context=members
    )
    assert data == payload


def test_associativity_instance_empty_group_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command, tmp_path, entity_type=402, form=1, data={"n": 0, "entries": []}
    )
    assert data == {"n": 0, "entries": []}


def test_external_reference_form_zero_roundtrips_filename_and_entity_name(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=416,
        form=0,
        data={"filename": "part.igs", "entity_name": "Block"},
    )
    assert data == {"filename": "part.igs", "entity_name": "Block"}


def test_external_reference_form_one_roundtrips_filename_only(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=416,
        form=1,
        data={"filename": "library.igs", "entity_name": ""},
    )
    assert data == {"filename": "library.igs", "entity_name": ""}


def test_external_reference_form_two_roundtrips_logical_reference(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=416,
        form=2,
        data={"filename": "assembly.igs", "entity_name": "Flange"},
    )
    assert data == {"filename": "assembly.igs", "entity_name": "Flange"}
