"""Annotation and dimension entity tests for IGES §§4.55-4.68.

These tests port a focused subset of the SDK's Catch2 entity-spec cases
to the eval's CLI surface. Each case writes canonical IGES-JSON through
``iges write`` and reparses it with ``iges parse`` so the assertions
exercise the buildable submission contract rather than library internals.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import math
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
                directory_entry_overrides={"status": _status(False)},
            ),
            *supporting,
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    # Only the named target is scored; supporting annotations are prerequisites.
    entity = next(e for e in reparsed["entities"] if e["de_index"] == 1)["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def _status(dependent: bool = True) -> dict[str, str]:
    # §3.2.3 Table 4 and §§4.55–4.60: annotation use, physical children.
    return {
        "blank": "visible",
        "subordinate": "physically_dependent" if dependent else "independent",
        "entity_use": "annotation",
        "hierarchy": "global_top_down",
    }


def _support(index: int, kind: int, data: Mapping[str, Any], *, form: int = 0) -> dict[str, Any]:
    return make_entity(
        de_index=index,
        entity_type=kind,
        form=form,
        data=data,
        directory_entry_overrides={"status": _status()},
    )


def _note(index: int) -> dict[str, Any]:
    # §4.60: positive width/height, ASCII font, and an upright single string.
    return _support(
        index,
        212,
        {
            "ns": 1,
            "strings": [
                {
                    "nc": 1,
                    "wc": 1.0,
                    "hc": 1.0,
                    "fc": 1,
                    "slant": math.pi / 2,
                    "angle": 0.0,
                    "mirror": 0,
                    "vh": 0,
                    "start": [0.0, 0.0, 0.0],
                    "text": "A",
                }
            ],
        },
    )


def _leader(
    index: int, head: tuple[float, float] = (1.0, 0.0), tail: tuple[float, float] = (2.0, 0.0)
) -> dict[str, Any]:
    # Public Type214 schema: one nonzero segment, positive arrow dimensions.
    return _support(
        index,
        214,
        {
            "n": 1,
            "ad1": 0.2,
            "ad2": 0.1,
            "zt": 0.0,
            "xh": head[0],
            "yh": head[1],
            "segments": [{"x": tail[0], "y": tail[1]}],
        },
        form=1,
    )


def _witness(index: int, *, x: float = 0.0) -> dict[str, Any]:
    # §4.10: IP1, odd N>=3, collinear points and alternating gap/visible segment.
    return _support(
        index, 106, {"ip": 1, "n": 3, "zt": 0.0, "data": [x, 0.0, x, 0.2, x, 2.0]}, form=40
    )


def _circle(index: int, *, x: float = 0.0, y: float = 0.0, radius: float = 1.0) -> dict[str, Any]:
    # §4.1: coincident start/end gives a closed, simple, coplanar circle.
    return _support(
        index,
        100,
        {"zt": 0.0, "x1": x, "y1": y, "x2": x + radius, "y2": y, "x3": x + radius, "y3": y},
    )


def test_angular_dimension_roundtrip(submission_command: Sequence[str], tmp_path: Path) -> None:
    # §4.55: both leaders are circular arcs about (10,20), radius15.
    # Their endpoints define respectively counterclockwise and clockwise arcs.
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=202,
        data={
            "denote": 3,
            "dewit1": 5,
            "dewit2": 7,
            "xt": 10.0,
            "yt": 20.0,
            "radius": 15.0,
            "dearrw1": 9,
            "dearrw2": 11,
        },
        supporting=[
            _note(3),
            _support(
                5,
                106,
                {"ip": 1, "n": 3, "zt": 0.0, "data": [10.0, 20.0, 24.0, 20.0, 26.0, 20.0]},
                form=40,
            ),
            _support(
                7,
                106,
                {"ip": 1, "n": 3, "zt": 0.0, "data": [10.0, 20.0, -4.0, 20.0, -6.0, 20.0]},
                form=40,
            ),
            _leader(9, (25.0, 20.0), (10.0, 35.0)),
            _leader(11, (-5.0, 20.0), (10.0, 35.0)),
        ],
    )
    assert data["denote"] == 3
    assert data["dewit2"] == 7
    assert data["xt"] == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert data["radius"] == pytest.approx(15.0, rel=1e-12, abs=1e-15)
    assert data["dearrw2"] == 11


def test_curve_dimension_roundtrip(submission_command: Sequence[str], tmp_path: Path) -> None:
    # §4.56: two curved entities, leaders at first start/second terminate,
    # and valid witness lines. No self/dangling pointers or two-line shortcut.
    expected = {
        "denote": 3,
        "decurv1": 5,
        "decurv2": 7,
        "dearr1": 9,
        "dearr2": 11,
        "dewit1": 13,
        "dewit2": 15,
    }
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=204,
        data=expected,
        supporting=[
            _note(3),
            _circle(5),
            _circle(7, x=4.0),
            _leader(9),
            _leader(11, (5.0, 0.0), (6.0, 0.0)),
            _witness(13, x=1.0),
            _witness(15, x=5.0),
        ],
    )
    assert data == expected


def test_diameter_dimension_allows_single_leader(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=206,
        supporting=[_note(3), _leader(5)],
        data={
            "denote": 3,
            "dearrw1": 5,
            "dearrw2": 0,
            "xt": 5.0,
            "yt": 5.0,
        },
    )
    assert data["dearrw2"] == 0
    assert data["xt"] == pytest.approx(5.0, rel=1e-12, abs=1e-15)
    assert data["yt"] == pytest.approx(5.0, rel=1e-12, abs=1e-15)


def test_flag_note_zero_leaders_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=208,
        supporting=[_note(3)],
        data={
            "xt": 0.0,
            "yt": 0.0,
            "zt": 0.0,
            "angle": 3.14159265358979,
            "denote": 3,
            "n": 0,
            "leaders": [],
        },
    )
    assert data["angle"] == pytest.approx(3.14159265358979, rel=1e-12, abs=1e-15)
    assert data["n"] == 0
    assert data["leaders"] == []


def test_general_label_with_leader_roundtrip(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # §4.59 explicitly requires one or more leaders; unlike FlagNote208,
    # an empty leader list was not a legal positive GeneralLabel fixture.
    expected = {"denote": 3, "n": 1, "leaders": [5]}
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=210,
        data=expected,
        supporting=[_note(3), _leader(5)],
    )
    assert data == expected


def test_general_note_multiple_strings_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=212,
        data={
            "ns": 2,
            "strings": [
                {
                    "nc": 2,
                    "wc": 1.0,
                    "hc": 1.0,
                    "fc": 1,
                    "slant": math.pi / 2,
                    "angle": 0.0,
                    "mirror": 0,
                    "vh": 0,
                    "start": [0.0, 0.0, 0.0],
                    "text": "Hi",
                },
                {
                    "nc": 3,
                    "wc": 1.0,
                    "hc": 1.0,
                    "fc": 1,
                    "slant": math.pi / 2,
                    "angle": 0.0,
                    "mirror": 0,
                    "vh": 0,
                    "start": [5.0, 0.0, 0.0],
                    "text": "Bye",
                },
            ],
        },
    )
    assert data["ns"] == 2
    assert data["strings"][0]["text"] == "Hi"
    assert data["strings"][1]["start"] == pytest.approx([5.0, 0.0, 0.0], rel=1e-12, abs=1e-15)
    assert data["strings"][1]["text"] == "Bye"


def test_new_general_note_multiple_strings_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=213,
        data={
            "txtcw": 20.0,
            "txtch": 10.0,
            "justcd": 1,
            "txtcx": 0.0,
            "txtcy": 0.0,
            "txtcz": 0.0,
            "txtag": 0.0,
            "baselx": 0.0,
            "basely": 5.0,
            "baselz": 0.0,
            "nils": 2.0,
            "ns": 2,
            "strings": [
                {
                    "fixvar": 0,
                    "chrwid": 0.7,
                    "chrhgt": 1.0,
                    "cspace": 0.1,
                    "lspace": 0.0,
                    "font": 1,
                    "chrang": 0.0,
                    "cctext": "BL",
                    "nc": 5,
                    "wt": 4.0,
                    "ht": 1.2,
                    "chrset": 1,
                    "sl": 1.5708,
                    "a": 0.0,
                    "m": 0,
                    "vh": 0,
                    "xs": 0.0,
                    "ys": 5.0,
                    "zs": 0.0,
                    "text": "FIRST",
                },
                {
                    "fixvar": 1,
                    "chrwid": 0.5,
                    "chrhgt": 0.8,
                    "cspace": 0.2,
                    "lspace": 2.0,
                    "font": 3,
                    "chrang": 0.0,
                    "cctext": "NL",
                    "nc": 6,
                    "wt": 3.5,
                    "ht": 1.0,
                    "chrset": 1,
                    "sl": 1.5708,
                    "a": 0.0,
                    "m": 0,
                    "vh": 0,
                    "xs": 0.0,
                    "ys": 3.0,
                    "zs": 0.0,
                    "text": "SECOND",
                },
            ],
        },
    )
    assert data["justcd"] == 1
    assert data["ns"] == 2
    assert data["strings"][0]["text"] == "FIRST"
    assert data["strings"][1]["font"] == 3
    assert data["strings"][1]["cctext"] == "NL"
    assert data["strings"][1]["text"] == "SECOND"


def test_leader_arrow_multiple_segments_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=214,
        form=1,
        data={
            "n": 3,
            "ad1": 0.8,
            "ad2": 0.4,
            "zt": 1.5,
            "xh": 10.0,
            "yh": 20.0,
            "segments": [
                {"x": 5.0, "y": 10.0},
                {"x": 5.0, "y": 15.0},
                {"x": 8.0, "y": 15.0},
            ],
        },
    )
    assert data["n"] == 3
    assert data["ad1"] == pytest.approx(0.8, rel=1e-12, abs=1e-15)
    assert data["segments"][2] == pytest.approx({"x": 8.0, "y": 15.0}, rel=1e-12, abs=1e-15)


def test_linear_dimension_allows_null_witness_lines(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=216,
        # Public Type216 schema has five pointers only, no xt/yt fields.
        supporting=[_note(3), _leader(5), _leader(7, (-1.0, 0.0), (-2.0, 0.0))],
        data={
            "denote": 3,
            "dearrw1": 5,
            "dearrw2": 7,
            "dewit1": 0,
            "dewit2": 0,
        },
    )
    assert data["dewit1"] == 0
    assert data["dewit2"] == 0
    assert data["dearrw2"] == 7


def test_ordinate_dimension_form_zero_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=218,
        form=0,
        supporting=[_note(3), _witness(5)],
        data={
            "form": 0,
            "denote": 3,
            "dewit": 5,
            "deord": 0,
            "desupp": 0,
        },
    )
    assert data["form"] == 0
    assert data["dewit"] == 5
    assert data["deord"] == 0
    assert data["desupp"] == 0


def test_ordinate_dimension_form_one_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=218,
        form=1,
        supporting=[_note(3), _leader(5), _leader(7, (2.0, 0.0), (2.0, 1.0))],
        data={
            "form": 1,
            "denote": 3,
            "dewit": 0,
            "deord": 5,
            "desupp": 7,
        },
    )
    assert data["form"] == 1
    assert data["deord"] == 5
    assert data["desupp"] == 7


def test_point_dimension_roundtrip(submission_command: Sequence[str], tmp_path: Path) -> None:
    # Public Type220 requires actual note, leader and enclosing geometry DEs.
    expected = {"denote": 3, "dearrw": 5, "degeom": 7}
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=220,
        data=expected,
        supporting=[_note(3), _leader(5), _circle(7, radius=3.0)],
    )
    assert data == expected


def test_radius_dimension_form_one_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=222,
        form=1,
        supporting=[
            _note(3),
            _leader(5, (25.0, 20.0), (20.0, 20.0)),
            _leader(7, (20.0, 20.0), (10.0, 20.0)),
        ],
        data={
            "form": 1,
            "denote": 3,
            "dearrw": 5,
            "xt": 10.0,
            "yt": 20.0,
            "dearrw2": 7,
        },
    )
    assert data["form"] == 1
    assert data["xt"] == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert data["yt"] == pytest.approx(20.0, rel=1e-12, abs=1e-15)
    assert data["dearrw2"] == 7


def test_general_symbol_roundtrip(submission_command: Sequence[str], tmp_path: Path) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=228,
        data={"denote": 3, "n": 2, "geometries": [5, 7], "l": 2, "leaders": [9, 11]},
        supporting=[
            _note(3),
            _circle(5),
            _circle(7, radius=2.0),
            _leader(9),
            _leader(11, (2.0, 0.0), (3.0, 0.0)),
        ],
    )
    assert data["denote"] == 3
    assert data["geometries"] == [5, 7]
    assert data["l"] == 2
    assert data["leaders"] == [9, 11]


def test_sectioned_area_multiple_islands_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=230,
        # Closed outer circle contains two disjoint interior circles; §3.2.3
        # makes all boundary curves physical children of the sectioned area.
        supporting=[
            _circle(3, x=10.0, y=20.0, radius=10.0),
            _circle(5, x=7.0, y=20.0),
            _circle(7, x=13.0, y=20.0),
        ],
        data={
            "bndp": 3,
            "patrn": 5,
            "xt": 10.0,
            "yt": 20.0,
            "zt": 0.0,
            "dist": 3.5,
            "angle": 1.047,
            "n": 2,
            "islands": [5, 7],
        },
    )
    assert data["bndp"] == 3
    assert data["patrn"] == 5
    assert data["dist"] == pytest.approx(3.5, rel=1e-12, abs=1e-15)
    assert data["angle"] == pytest.approx(1.047, rel=1e-12, abs=1e-15)
    assert data["islands"] == [5, 7]
