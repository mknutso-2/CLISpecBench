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


def _definition(
    de_index: int,
    entity_type: int,
    data: Mapping[str, Any],
    *,
    form: int = 0,
    dependent: bool = False,
) -> dict[str, Any]:
    # §2.2.4.4.9: all 300-series entities have Definition entity use.
    overrides: dict[str, Any] = {
        "status": {
            "blank": "visible",
            "subordinate": "physically_dependent" if dependent else "independent",
            "entity_use": "definition",
            "hierarchy": "global_top_down",
        },
    }
    # §§4.70/4.76 also require a fallback font/color for simpler receivers.
    if entity_type == 304:
        overrides["line_font"] = 1
    elif entity_type == 314:
        overrides["color"] = 8
    return make_entity(
        de_index=de_index,
        entity_type=entity_type,
        form=form,
        data=data,
        directory_entry_overrides=overrides,
    )


def _text_font(de_index: int) -> dict[str, Any]:
    return _definition(
        de_index,
        310,
        {
            "fc": 3,
            "fname": "MYFONT",
            "sf": 0,
            "scale": 12,
            "n": 1,
            "characters": [
                {
                    "ac": 67,
                    "nx": 11,
                    "ny": 0,
                    "nm": 3,
                    "motions": [
                        {"pf": 0, "x": 0, "y": 0},
                        {"pf": 0, "x": 5, "y": 10},
                        {"pf": 1, "x": 10, "y": 0},
                    ],
                }
            ],
        },
    )


def _text_display(de_index: int) -> dict[str, Any]:
    return _definition(
        de_index,
        312,
        {
            "cbw": 0.25,
            "cbh": 0.35,
            "fc": 1,
            "sl": 1.5707963267948966,
            "a": 0.0,
            "m": 0,
            "vh": 0,
            "xs": 0.0,
            "ys": 0.0,
            "zs": 0.0,
        },
    )


def _roundtrip_single(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
    support: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    target = (
        _definition(1, entity_type, data, form=form)
        if 300 <= entity_type < 400
        else make_entity(de_index=1, entity_type=entity_type, form=form, data=data)
    )
    doc = wrap_entities([target, *support])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    # Support makes every pointer resolvable, but only the named target is
    # compared; an unrelated support entity's serialization cannot fail this.
    entity = next(record for record in reparsed["entities"] if record["de_index"] == 1)["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def test_associativity_definition_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=302,
        # §4.69 reserves 5001–9999 for implementor-defined associativities.
        form=5001,
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
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=304,
        form=1,
        data={
            "form": 1,
            "m": 0,
            "l1": 3,
            "l2": 2.5,
            "l3": 0.5,
            "segments": [],
            "bitmask": "",
        },
        support=[
            # §4.70 L1 references a real §4.73 subfigure and its geometry.
            _definition(
                3,
                308,
                {"depth": 0, "name": "TEMPLATE", "n": 1, "entities": [5]},
                dependent=True,
            ),
            make_entity(
                de_index=5,
                entity_type=110,
                data={"start": [0.0, 0.0, 0.0], "terminate": [0.0, 1.0, 0.0]},
                directory_entry_overrides={
                    "status": {
                        "blank": "visible",
                        "subordinate": "physically_dependent",
                        "entity_use": "definition",
                        "hierarchy": "global_defer",
                    }
                },
            ),
        ],
    )
    assert data["form"] == 1
    assert data["l1"] == 3
    assert data["l2"] == pytest.approx(2.5, rel=1e-12, abs=1e-15)
    assert data["l3"] == pytest.approx(0.5, rel=1e-12, abs=1e-15)


def test_line_font_definition_form_two_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
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
    assert data["segments"] == pytest.approx([2.0, 0.5, 0.5], rel=1e-12, abs=1e-15)
    assert data["bitmask"] == "5"


def test_text_font_definition_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
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
            "characters": [
                {
                    "ac": 67,
                    "nx": 11,
                    "ny": 0,
                    "nm": 3,
                    "motions": [
                        {"pf": 0, "x": 0, "y": 0},
                        {"pf": 0, "x": 5, "y": 10},
                        {"pf": 1, "x": 10, "y": 0},
                    ],
                }
            ],
        },
    )
    assert data["fname"] == "MYFONT"
    assert data["characters"][0]["motions"][2]["pf"] == 1
    assert data["characters"][0]["motions"][1]["x"] == 5


def test_text_display_template_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=312,
        data={
            "cbw": 0.25,
            "cbh": 0.35,
            "fc": -3,
            "sl": 1.2,
            "a": 0.785,
            "m": 1,
            "vh": 0,
            "xs": 100.0,
            "ys": 200.0,
            "zs": 50.0,
        },
        # TR Type312 defines negative FC as a pointer to a Type310 font.
        support=[_text_font(3)],
    )
    assert data["fc"] == -3
    assert data["m"] == 1
    assert data["xs"] == pytest.approx(100.0, rel=1e-12, abs=1e-15)


def test_color_definition_optional_name_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=314,
        data={"red": 50.0, "green": 50.0, "blue": 50.0, "name": ""},
    )
    assert data["red"] == pytest.approx(50.0, rel=1e-12, abs=1e-15)
    assert data["green"] == pytest.approx(50.0, rel=1e-12, abs=1e-15)
    assert data["name"] == ""


def test_units_data_multiple_units_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=316,
        data={
            "np": 3,
            "units": [
                # §4.77 lists M and KG; scale expresses millimetres/grams.
                # This avoids the TR's illustrative MM spelling, which the
                # normative unit table does not list.
                {"typ": "LENGTH", "val": "M", "sf": 0.001},
                {"typ": "MASS", "val": "KG", "sf": 0.001},
                {"typ": "TIME", "val": "S", "sf": 1.0},
            ],
        },
    )
    assert data["np"] == 3
    assert data["units"][1]["val"] == "KG"
    assert data["units"][1]["sf"] == pytest.approx(0.001, rel=1e-12, abs=1e-15)


def test_attribute_table_definition_form_two_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
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
            "attributes": [
                {
                    "at": 1,
                    "avdt": 1,
                    "avc": 2,
                    "values": [
                        {"kind": "int", "value": 10},
                        {"kind": "int", "value": 20},
                    ],
                    "display_ptrs": [3, 5],
                }
            ],
        },
        # TR Type322 Form2 requires one actual display-template pointer per value.
        support=[_text_display(3), _text_display(5)],
    )
    assert data["name"] == "RT2"
    assert data["attributes"][0]["values"][0] == {"kind": "int", "value": 10}
    assert data["attributes"][0]["display_ptrs"] == [3, 5]


def test_solid_instance_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=430,
        data={"ptr": 3},
        # §4.142 Form0 permits a pointer to a solid primitive (§4.41 sphere).
        support=[
            make_entity(
                de_index=3,
                entity_type=158,
                data={"radius": 1.0, "center": [0.0, 0.0, 0.0]},
            ),
        ],
    )
    assert data == {"ptr": 3}
