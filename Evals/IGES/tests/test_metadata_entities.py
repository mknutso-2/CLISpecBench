"""Metadata/reference entity tests for remaining non-geometric §4 items."""
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


def test_associativity_definition_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=302,
        data={
            "k": 2,
            "classes": [
                {"bp": 1, "order": 1, "n": 2, "item_types": [1, 2]},
                {"bp": 2, "order": 2, "n": 1, "item_types": [3]},
            ],
        },
    )
    assert data["k"] == 2
    assert data["classes"][0]["item_types"] == [1, 2]
    assert data["classes"][1]["bp"] == 2


def test_line_font_definition_form_one_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=304,
        form=1,
        data={
            "form": 1,
            "m": 0,
            "l1": 5,
            "l2": 2.5,
            "l3": 0.5,
            "segments": [],
            "bitmask": "",
        },
    )
    assert data["form"] == 1
    assert data["l1"] == 5
    assert data["l2"] == pytest.approx(2.5)
    assert data["l3"] == pytest.approx(0.5)


def test_line_font_definition_form_two_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=304,
        form=2,
        data={
            "form": 2,
            "m": 3,
            "l1": 0,
            "l2": 0.0,
            "l3": 0.0,
            "segments": [2.0, 0.5, 0.5],
            "bitmask": "5",
        },
    )
    assert data["form"] == 2
    assert data["segments"] == pytest.approx([2.0, 0.5, 0.5])
    assert data["bitmask"] == "5"


def test_text_font_definition_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=310,
        data={
            "fc": 3,
            "fname": "MYFONT",
            "sf": 0,
            "scale": 12,
            "n": 1,
            "characters": [{
                "ac": 67,
                "nx": 11,
                "ny": 0,
                "nm": 3,
                "motions": [
                    {"pf": 0, "x": 0, "y": 0},
                    {"pf": 0, "x": 5, "y": 10},
                    {"pf": 1, "x": 10, "y": 0},
                ],
            }],
        },
    )
    assert data["fname"] == "MYFONT"
    assert data["characters"][0]["motions"][2]["pf"] == 1
    assert data["characters"][0]["motions"][1]["x"] == 5


def test_text_display_template_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=312,
        data={
            "cbw": 0.25,
            "cbh": 0.35,
            "fc": -7,
            "sl": 1.2,
            "a": 0.785,
            "m": 1,
            "vh": 0,
            "xs": 100.0,
            "ys": 200.0,
            "zs": 50.0,
        },
    )
    assert data["fc"] == -7
    assert data["m"] == 1
    assert data["xs"] == pytest.approx(100.0)


def test_color_definition_optional_name_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=314,
        data={"red": 50.0, "green": 50.0, "blue": 50.0, "name": ""},
    )
    assert data["red"] == pytest.approx(50.0)
    assert data["green"] == pytest.approx(50.0)
    assert data["name"] == ""


def test_units_data_multiple_units_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=316,
        data={
            "np": 3,
            "units": [
                {"typ": "LENGTH", "val": "MM", "sf": 1.0},
                {"typ": "MASS", "val": "G", "sf": 0.001},
                {"typ": "TIME", "val": "S", "sf": 1.0},
            ],
        },
    )
    assert data["np"] == 3
    assert data["units"][1]["val"] == "G"
    assert data["units"][1]["sf"] == pytest.approx(0.001)


def test_attribute_table_definition_form_two_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=322,
        form=2,
        data={
            "name": "RT2",
            "alt": 1,
            "na": 1,
            "attributes": [{
                "at": 1,
                "avdt": 1,
                "avc": 2,
                "values": [
                    {"kind": "int", "value": 10},
                    {"kind": "int", "value": 20},
                ],
                "display_ptrs": [101, 201],
            }],
        },
    )
    assert data["name"] == "RT2"
    assert data["attributes"][0]["values"][0] == {"kind": "int", "value": 10}
    assert data["attributes"][0]["display_ptrs"] == [101, 201]


def test_solid_instance_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=430,
        data={"ptr": 7},
    )
    assert data == {"ptr": 7}
