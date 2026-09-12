"""Dedicated CLI coverage for structure and view entities."""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from context_support import context_line, context_matrix, context_note, context_status
from iges_support import make_entity, semantic_roundtrip_json, wrap_entities


def _roundtrip_single(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
    supporting: Sequence[dict[str, Any]] = (),
    directory_entry_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=entity_type,
                form=form,
                data=data,
                directory_entry_overrides=directory_entry_overrides,
            ),
            *supporting,
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    entity = next(record for record in reparsed["entities"] if record["de_index"] == 1)["entity"]
    assert entity["type"] == entity_type
    assert entity["form"] == form
    return entity["data"]


def test_subfigure_definition_roundtrips_empty_member_list(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=308,
        data={"depth": 0, "name": "EMPTY", "n": 0, "entities": []},
    )
    assert data == {"depth": 0, "name": "EMPTY", "n": 0, "entities": []}


def test_drawing_form_one_roundtrips_angles_and_annotations(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=404,
        form=1,
        # §4.96: real Views are logically dependent; drawing-space annotation
        # is physically dependent. Keep the observation on the Drawing data.
        supporting=[
            *[
                make_entity(
                    de_index=index,
                    entity_type=410,
                    data={"form": 0, "view_number": number, "scale": 1.0, "clip_planes": [0] * 6},
                    directory_entry_overrides={
                        "xform_matrix": 9,
                        "status": context_status("annotation", "logically_dependent"),
                    },
                )
                for index, number in [(3, 1), (5, 2)]
            ],
            context_note(7),
            context_matrix(9, use="annotation"),
        ],
        directory_entry_overrides={"status": context_status("annotation")},
        data={
            "n": 2,
            "views": [
                {"view": 3, "x_origin": 0.0, "y_origin": 0.0, "angle": 0.0},
                {"view": 5, "x_origin": 5.0, "y_origin": 10.0, "angle": 1.5708},
            ],
            "m": 1,
            "annotations": [7],
        },
    )
    assert data["views"][1]["view"] == 5
    assert data["views"][1]["angle"] == pytest.approx(1.5708, rel=1e-12, abs=1e-15)
    assert data["annotations"] == [7]


def test_view_form_one_roundtrips_perspective_fields(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=410,
        form=1,
        # §2.2.4.4.9.3 explicitly assigns View entities to annotation use.
        directory_entry_overrides={"status": context_status("annotation")},
        data={
            "form": 1,
            "view_number": 2,
            "scale": 0.5,
            "clip_planes": [],
            "view_plane_normal": [0.0, 0.0, 1.0],
            "view_reference_point": [1.0, 2.0, 3.0],
            "center_of_projection": [0.0, 0.0, 100.0],
            "view_up_vector": [0.0, 1.0, 0.0],
            "view_plane_distance": 50.0,
            "umin": -10.0,
            "umax": 10.0,
            "vmin": -5.0,
            "vmax": 5.0,
            "depth_clipping": 1,
            "wmin": -200.0,
            "wmax": 200.0,
        },
    )
    assert data["view_number"] == 2
    assert data["center_of_projection"][2] == pytest.approx(100.0, rel=1e-12, abs=1e-15)
    assert data["view_plane_distance"] == pytest.approx(50.0, rel=1e-12, abs=1e-15)
    assert data["wmax"] == pytest.approx(200.0, rel=1e-12, abs=1e-15)


def test_rectangular_array_roundtrips_do_dont_list(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=412,
        # §4.136 permits a Line as the base entity; the list selects 2/12 copies.
        supporting=[context_line(3)],
        data={
            "de": 3,
            "s": 2.0,
            "position": [1.0, 2.0, 0.0],
            "nc": 3,
            "nr": 4,
            "dx": 10.0,
            "dy": 15.0,
            "ax": 0.5,
            "lc": 2,
            "ddf": 0,
            "positions": [1, 4],
        },
    )
    assert data["nc"] == 3
    assert data["nr"] == 4
    assert data["ddf"] == 0
    assert data["positions"] == [1, 4]
