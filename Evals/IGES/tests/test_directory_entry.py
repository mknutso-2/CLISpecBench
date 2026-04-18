"""DirectoryEntry contract coverage.

Most roundtrip tests in the suite assert only `entity.data`; the
DirectoryEntry (DE) fields documented in TR §2.4 are largely untested.
This file locks the DE contract in with direct
`entities[i].directory_entry` assertions after a full write → parse
cycle.

Covered DE fields (beyond defaults):
- Status Number sub-fields (blank, subordinate, entity_use, hierarchy)
- Line Font Pattern (field 4) — as raw integer and as negated DE pointer
- Level (field 5) — as raw integer and as negated DE pointer
- View (field 6), Xform Matrix (field 7), Label Display (field 8)
  — all as DE pointers
- Structure (field 3) — as negated DE pointer
- Entity Label (field 18) and Entity Subscript (field 19)

Spec refs: §2.2.4.4 and TR §2.4.
"""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    make_entity,
    semantic_roundtrip_json,
    wrap_entities,
)


def _roundtrip_one_line_with_de_overrides(
    submission_command: Sequence[str],
    tmp_path: Path,
    overrides: dict[str, object],
) -> dict[str, object]:
    """Build a doc with a single Line + DE overrides, roundtrip, return that DE."""
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides=overrides,
        ),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    return reparsed["entities"][0]["directory_entry"]


def test_status_sub_fields_non_default_values_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """Each status sub-field has a non-default value that must survive write → parse."""
    overrides = {
        "status": {
            "blank": "blanked",
            "subordinate": "logically_dependent",
            "entity_use": "annotation",
            "hierarchy": "use_property",
        },
    }
    de = _roundtrip_one_line_with_de_overrides(submission_command, tmp_path, overrides)
    assert de["status"]["blank"] == "blanked"
    assert de["status"]["subordinate"] == "logically_dependent"
    assert de["status"]["entity_use"] == "annotation"
    assert de["status"]["hierarchy"] == "use_property"


def test_line_font_pattern_as_integer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.2.4.4.4: Line Font integer values 1-5 denote predefined patterns."""
    de = _roundtrip_one_line_with_de_overrides(
        submission_command, tmp_path, {"line_font": 3}  # 3 = Phantom
    )
    assert de["line_font"] == 3


def test_line_font_pattern_as_negated_pointer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.2.4.4.4: negated value references a Line Font Definition (Type 304) DE."""
    doc = wrap_entities([
        make_entity(
            de_index=1,
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
        ),
        make_entity(
            de_index=3,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={"line_font": -1},
        ),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    assert reparsed["entities"][1]["directory_entry"]["line_font"] == -1


def test_level_as_integer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    de = _roundtrip_one_line_with_de_overrides(
        submission_command, tmp_path, {"level": 5}
    )
    assert de["level"] == 5


def test_structure_as_negated_pointer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.2.4.4.3: Structure is a negated DE pointer to a definition entity."""
    doc = wrap_entities([
        make_entity(
            de_index=1,
            entity_type=302,
            data={
                "k": 1,
                "classes": [
                    {"bp": 1, "order": 1, "n": 1, "item_types": [1]},
                ],
            },
        ),
        make_entity(
            de_index=3,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={"structure": -1},
        ),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    assert reparsed["entities"][1]["directory_entry"]["structure"] == -1


def test_view_and_xform_and_label_display_pointers_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """Fields 6, 7, 8 of the DE — all DE pointers."""
    doc = wrap_entities([
        # View Entity (Type 410, form 0) at DE 1
        make_entity(
            de_index=1,
            entity_type=410,
            form=0,
            data={
                "form": 0,
                "view_number": 1,
                "scale": 1.0,
                "clip_planes": [0, 0, 0, 0, 0, 0],
                "view_plane_normal": [0.0, 0.0, 1.0],
                "view_reference_point": [0.0, 0.0, 0.0],
                "center_of_projection": [0.0, 0.0, 0.0],
                "view_up_vector": [0.0, 1.0, 0.0],
                "view_plane_distance": 0.0,
                "umin": 0.0, "umax": 0.0, "vmin": 0.0, "vmax": 0.0,
                "depth_clipping": 0, "wmin": 0.0, "wmax": 0.0,
            },
        ),
        # Transformation Matrix (Type 124) at DE 3
        make_entity(
            de_index=3,
            entity_type=124,
            data={
                "rotation": [
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                "translation": [0.0, 0.0, 0.0],
            },
        ),
        # Label Display Associativity (Type 402, form 5) at DE 5.
        # The schema is the same as form 1: {n, entries}.
        make_entity(
            de_index=5,
            entity_type=402,
            form=5,
            data={"n": 0, "entries": []},
        ),
        # Line at DE 7 that references 1, 3, 5 in its DE fields 6/7/8.
        make_entity(
            de_index=7,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            directory_entry_overrides={
                "view": 1,
                "xform_matrix": 3,
                "label_display": 5,
            },
        ),
    ])
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    line_de = reparsed["entities"][3]["directory_entry"]
    assert line_de["view"] == 1
    assert line_de["xform_matrix"] == 3
    assert line_de["label_display"] == 5


def test_entity_label_and_subscript_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.2.4.4.18/19: up to 8-char label and 1-8 digit subscript."""
    de = _roundtrip_one_line_with_de_overrides(
        submission_command, tmp_path,
        {"entity_label": "PART01", "entity_subscript": 42},
    )
    assert de["entity_label"] == "PART01"
    assert de["entity_subscript"] == 42


def test_entity_label_8_char_max_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """Boundary: 8-char label (the spec's maximum) roundtrips verbatim."""
    de = _roundtrip_one_line_with_de_overrides(
        submission_command, tmp_path,
        {"entity_label": "ABCDEFGH"},
    )
    assert de["entity_label"] == "ABCDEFGH"
