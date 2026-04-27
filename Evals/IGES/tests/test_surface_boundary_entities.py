"""CLI-level coverage for IGES surface-boundary/reference entities.

These tests lock in the canonical JSON behavior for the remaining
surface-trimming and external-reference entities that were still only
covered indirectly through broader round-trip suites.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from iges_support import make_entity, semantic_roundtrip_json, wrap_entities


def _roundtrip_single(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=entity_type,
                form=form,
                data=data,
            ),
        ]
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
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=141,
        data={
            "type": 1,
            "pref": 2,
            "sptr": 5,
            "n": 2,
            "curves": [
                {"crvpt": 7, "sense": 1, "k": 2, "pscpt": [9, 11]},
                {"crvpt": 13, "sense": 2, "k": 1, "pscpt": [15]},
            ],
        },
    )
    assert data["type"] == 1
    assert data["pref"] == 2
    assert data["sptr"] == 5
    assert data["curves"][0]["pscpt"] == [9, 11]
    assert data["curves"][1]["sense"] == 2


def test_curve_on_parametric_surface_roundtrips_creation_and_preference(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=142,
        data={"crtn": 3, "sptr": 5, "bptr": 7, "cptr": 9, "pref": 3},
    )
    assert data == {"crtn": 3, "sptr": 5, "bptr": 7, "cptr": 9, "pref": 3}


def test_bounded_surface_with_multiple_boundaries_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=143,
        data={"type": 1, "sptr": 3, "n": 3, "bdpt": [5, 7, 9]},
    )
    assert data["type"] == 1
    assert data["sptr"] == 3
    assert data["n"] == 3
    assert data["bdpt"] == [5, 7, 9]


def test_trimmed_surface_with_default_outer_boundary_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=144,
        data={"pts": 1, "n1": 0, "n2": 0, "pto": 0, "pti": []},
    )
    assert data == {"pts": 1, "n1": 0, "n2": 0, "pto": 0, "pti": []}


def test_trimmed_surface_with_inner_boundaries_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=144,
        data={"pts": 5, "n1": 1, "n2": 2, "pto": 7, "pti": [9, 11]},
    )
    assert data["pts"] == 5
    assert data["n1"] == 1
    assert data["pto"] == 7
    assert data["pti"] == [9, 11]


def test_associativity_instance_group_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=402,
        form=1,
        data={"n": 3, "entries": [1, 3, 5]},
    )
    assert data == {"n": 3, "entries": [1, 3, 5]}


def test_associativity_instance_empty_group_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=402,
        form=1,
        data={"n": 0, "entries": []},
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
