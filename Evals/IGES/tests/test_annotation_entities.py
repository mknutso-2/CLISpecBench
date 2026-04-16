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
    entity = reparsed["entities"][0]["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def test_angular_dimension_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=202,
        data={
            "denote": 1,
            "dewit1": 3,
            "dewit2": 5,
            "xt": 10.0,
            "yt": 20.0,
            "radius": 15.0,
            "dearrw1": 7,
            "dearrw2": 9,
        },
    )
    assert data["denote"] == 1
    assert data["dewit2"] == 5
    assert data["xt"] == pytest.approx(10.0)
    assert data["radius"] == pytest.approx(15.0)
    assert data["dearrw2"] == 9


def test_curve_dimension_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=204,
        data={
            "denote": 21,
            "decurv1": 23,
            "decurv2": 25,
            "dearr1": 27,
            "dearr2": 29,
            "dewit1": 31,
            "dewit2": 33,
        },
    )
    assert data == {
        "denote": 21,
        "decurv1": 23,
        "decurv2": 25,
        "dearr1": 27,
        "dearr2": 29,
        "dewit1": 31,
        "dewit2": 33,
    }


def test_diameter_dimension_allows_single_leader(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=206,
        data={
            "denote": 1,
            "dearrw1": 3,
            "dearrw2": 0,
            "xt": 5.0,
            "yt": 5.0,
        },
    )
    assert data["dearrw2"] == 0
    assert data["xt"] == pytest.approx(5.0)
    assert data["yt"] == pytest.approx(5.0)


def test_flag_note_zero_leaders_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=208,
        data={
            "xt": 0.0,
            "yt": 0.0,
            "zt": 0.0,
            "angle": 3.14159265358979,
            "denote": 5,
            "n": 0,
            "leaders": [],
        },
    )
    assert data["angle"] == pytest.approx(3.14159265358979)
    assert data["n"] == 0
    assert data["leaders"] == []


def test_general_label_zero_leaders_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=210,
        data={"denote": 1, "n": 0, "leaders": []},
    )
    assert data == {"denote": 1, "n": 0, "leaders": []}


def test_general_note_multiple_strings_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
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
                    "slant": 0.0,
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
                    "slant": 0.0,
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
    assert data["strings"][1]["start"] == pytest.approx([5.0, 0.0, 0.0])
    assert data["strings"][1]["text"] == "Bye"


def test_new_general_note_multiple_strings_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
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
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=214,
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
    assert data["ad1"] == pytest.approx(0.8)
    assert data["segments"][2] == pytest.approx({"x": 8.0, "y": 15.0})


def test_linear_dimension_allows_null_witness_lines(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=216,
        data={
            "denote": 1,
            "dearrw1": 3,
            "dearrw2": 5,
            "dewit1": 0,
            "dewit2": 0,
            "xt": 0.0,
            "yt": 0.0,
        },
    )
    assert data["dewit1"] == 0
    assert data["dewit2"] == 0
    assert data["dearrw2"] == 5


def test_ordinate_dimension_form_zero_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=218,
        form=0,
        data={
            "form": 0,
            "denote": 1,
            "dewit": 3,
            "deord": 0,
            "desupp": 0,
        },
    )
    assert data["form"] == 0
    assert data["dewit"] == 3
    assert data["deord"] == 0
    assert data["desupp"] == 0


def test_ordinate_dimension_form_one_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=218,
        form=1,
        data={
            "form": 1,
            "denote": 1,
            "dewit": 0,
            "deord": 3,
            "desupp": 5,
        },
    )
    assert data["form"] == 1
    assert data["deord"] == 3
    assert data["desupp"] == 5


def test_point_dimension_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=220,
        data={"denote": 51, "dearrw": 53, "degeom": 55},
    )
    assert data == {"denote": 51, "dearrw": 53, "degeom": 55}


def test_radius_dimension_form_one_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=222,
        form=1,
        data={
            "form": 1,
            "denote": 1,
            "dearrw": 3,
            "xt": 10.0,
            "yt": 20.0,
            "dearrw2": 7,
        },
    )
    assert data["form"] == 1
    assert data["xt"] == pytest.approx(10.0)
    assert data["yt"] == pytest.approx(20.0)
    assert data["dearrw2"] == 7


def test_general_symbol_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=228,
        data={
            "denote": 41,
            "n": 2,
            "geometries": [43, 45],
            "l": 2,
            "leaders": [47, 49],
        },
    )
    assert data["denote"] == 41
    assert data["geometries"] == [43, 45]
    assert data["l"] == 2
    assert data["leaders"] == [47, 49]


def test_sectioned_area_multiple_islands_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=230,
        data={
            "bndp": 21,
            "patrn": 5,
            "xt": 10.0,
            "yt": 20.0,
            "zt": 0.0,
            "dist": 3.5,
            "angle": 1.047,
            "n": 2,
            "islands": [23, 25],
        },
    )
    assert data["bndp"] == 21
    assert data["patrn"] == 5
    assert data["dist"] == pytest.approx(3.5)
    assert data["angle"] == pytest.approx(1.047)
    assert data["islands"] == [23, 25]
