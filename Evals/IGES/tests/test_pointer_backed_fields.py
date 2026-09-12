"""Regression tests for brace-defaulted pointer fields in entity schemas.

Several entity structs use brace-default initialization for DE-index
members, for example ``DEIndex dptr{0};``. The JSON/schema generators
previously skipped those fields entirely, which meant:

* the prompt schema omitted contract-visible fields, and
* the ref-impl silently dropped them on ``iges write`` / ``iges parse``.

These tests lock the affected fields back into the CLI-observable JSON
surface by round-tripping representative entities through the full
``iges`` executable.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import pi
from pathlib import Path
from typing import Any

import pytest

from iges_support import assert_semantic_equal, make_entity, semantic_roundtrip_json, wrap_entities


def _roundtrip_supported(
    submission_command: Sequence[str],
    tmp_path: Path,
    *,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
    supporting: Sequence[dict[str, Any]],
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


def _status(use: str, *, dependent: bool = False) -> dict[str, str]:
    return {
        "blank": "visible",
        "subordinate": "physically_dependent" if dependent else "independent",
        "entity_use": use,
        "hierarchy": "global_top_down",
    }


def _coordinate_system() -> dict[str, Any]:
    # §§4.21/4.27: a labeled Cartesian nodal definition/displacement system.
    return make_entity(
        de_index=3,
        entity_type=124,
        form=10,
        data={
            "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "translation": [0.0, 0.0, 0.0],
        },
        directory_entry_overrides={
            "entity_label": "GLOBAL",
            "status": _status("geometry"),
        },
    )


def _node(index: int, number: int, x: float = 0.0) -> dict[str, Any]:
    return make_entity(
        de_index=index,
        entity_type=134,
        data={"x": x, "y": 0.0, "z": 0.0, "ndcsp": 3},
        directory_entry_overrides={
            "xform_matrix": 3,
            "entity_subscript": number,
            "status": _status("logical_positional"),
        },
    )


def _case_note(index: int) -> dict[str, Any]:
    # §4.60: valid simple note, including character count and nonslant angle.
    return make_entity(
        de_index=index,
        entity_type=212,
        data={
            "ns": 1,
            "strings": [
                {
                    "nc": 4,
                    "wc": 4.0,
                    "hc": 1.0,
                    "fc": 1,
                    "slant": pi / 2,
                    "angle": 0.0,
                    "mirror": 0,
                    "vh": 0,
                    "start": [0.0, 0.0, 0.0],
                    "text": "CASE",
                }
            ],
        },
        directory_entry_overrides={"status": _status("annotation", dependent=True)},
    )


def _text_template(index: int) -> dict[str, Any]:
    # Public Appendix Type312: use a predefined font, avoiding another pointer.
    return make_entity(
        de_index=index,
        entity_type=312,
        data={
            "cbw": 1.0,
            "cbh": 1.0,
            "fc": 1,
            "sl": pi / 2,
            "a": 0.0,
            "m": 0,
            "vh": 0,
            "xs": 0.0,
            "ys": 0.0,
            "zs": 0.0,
        },
        directory_entry_overrides={"status": _status("definition")},
    )


def _connection(index: int, owner: int, number: int) -> dict[str, Any]:
    # §4.26: the owner is real; optional display pointers may be null.
    return make_entity(
        de_index=index,
        entity_type=132,
        data={
            "location": [0.0, 0.0, 0.0],
            "display_symbol": 0,
            "tf": 2,
            "ff": 1,
            "cid": str(number),
            "pttcid": 0,
            "cfn": "SIGNAL",
            "pttcfn": 0,
            "cpid": number,
            "fc": 0,
            "sf": 0,
            "psfi": owner,
        },
        directory_entry_overrides={"status": _status("logical_positional", dependent=True)},
    )


def _symbol(index: int) -> dict[str, Any]:
    return make_entity(
        de_index=index,
        entity_type=110,
        data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
        directory_entry_overrides={"status": _status("definition", dependent=True)},
    )


def test_plane_bounded_pointer_field_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §4.12 requires PTR=0 for unbounded Form0. Exercise the nonzero field
    # using Form1 and an actual simple closed circle in the plane instead.
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=108,
        form=1,
        supporting=[
            make_entity(
                de_index=3,
                entity_type=100,
                data={"zt": 0.0, "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 0.0, "x3": 1.0, "y3": 0.0},
            )
        ],
        data={
            "A": 0.0,
            "B": 0.0,
            "C": 1.0,
            "D": 0.0,
            "ptr": 3,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "size": 1.5,
        },
    )
    assert data["ptr"] == 3
    assert data["size"] == pytest.approx(1.5, rel=1e-12, abs=1e-15)


def test_node_ndcsp_pointer_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=134,
        data={"x": 1.0, "y": 2.0, "z": 3.0, "ndcsp": 3},
        supporting=[_coordinate_system()],
        directory_entry_overrides={
            "xform_matrix": 3,
            "entity_subscript": 5,
            "status": _status("logical_positional"),
        },
    )
    assert_semantic_equal(data, {"x": 1.0, "y": 2.0, "z": 3.0, "ndcsp": 3})


def test_nodal_displacement_node_pointer_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §4.29 requires actual notes/nodes and a matching node subscript number.
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=138,
        supporting=[_coordinate_system(), _node(5, 5), _case_note(7)],
        data={
            "nc": 1,
            "gp": [7],
            "nn": 1,
            "nodes": [
                {
                    "node_id": 5,
                    "np": 5,
                    "cases": [
                        {
                            "x": 0.1,
                            "y": 0.2,
                            "z": 0.3,
                            "rx": 0.01,
                            "ry": 0.02,
                            "rz": 0.03,
                        }
                    ],
                }
            ],
        },
    )
    assert data["gp"] == [7]
    assert data["nodes"][0]["np"] == 5
    assert data["nodes"][0]["cases"][0]["rz"] == pytest.approx(0.03, rel=1e-12, abs=1e-15)


def test_nodal_results_gnote_and_np_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §4.35 Form0 permits arbitrary positive NV; use03 is analysis data.
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=146,
        supporting=[_coordinate_system(), _node(5, 5), _case_note(7)],
        directory_entry_overrides={"entity_subscript": 1, "status": _status("other")},
        data={
            "gnote": 7,
            "scn": 2,
            "time": 1.5,
            "nv": 2,
            "nn": 1,
            "nodes": [{"node_id": 5, "np": 5, "values": [3.14, 2.72]}],
        },
    )
    assert data["gnote"] == 7
    assert data["nodes"][0]["np"] == 5
    assert data["nodes"][0]["values"] == pytest.approx([3.14, 2.72], rel=1e-12, abs=1e-15)


def test_element_results_gnote_and_ep_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # §§4.28/4.36: a real two-node BEAM, matching element number/topology,
    # and a result reported at node number1 (RRF0), not a dangling element.
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=148,
        supporting=[
            _coordinate_system(),
            _node(5, 1),
            _node(7, 2, 1.0),
            make_entity(
                de_index=9,
                entity_type=136,
                data={"itop": 1, "n": 2, "nodes": [5, 7], "etyp": "BEAM"},
                directory_entry_overrides={"entity_subscript": 21},
            ),
            _case_note(11),
        ],
        directory_entry_overrides={"entity_subscript": 1, "status": _status("other")},
        data={
            "gnote": 11,
            "scn": 1,
            "time": 2.0,
            "nv": 2,
            "rrf": 0,
            "ne": 1,
            "elements": [
                {
                    "en": 21,
                    "ep": 9,
                    "itop": 1,
                    "nl": 1,
                    "dlf": 0,
                    "nrl": 1,
                    "rdrl": [1],
                    "numv": 2,
                    "values": [10.0, 20.0],
                }
            ],
        },
    )
    assert data["gnote"] == 11
    assert data["elements"][0]["ep"] == 9
    assert data["elements"][0]["values"] == pytest.approx([10.0, 20.0], rel=1e-12, abs=1e-15)


def test_network_subfigure_definition_display_pointer_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # Appendix Types320/312/132: all geometry, display and connection targets
    # exist. Depth is zero because the definition contains no nested instance.
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=320,
        supporting=[_symbol(3), _text_template(5), _connection(7, 1, 1), _connection(9, 1, 2)],
        directory_entry_overrides={"status": _status("definition")},
        data={
            "depth": 0,
            "name": "RESISTOR",
            "na": 1,
            "associated": [3],
            "tf": 0,
            "prd": "R1",
            "dptr": 5,
            "nc": 2,
            "connects": [7, 9],
        },
    )
    assert data["dptr"] == 5
    assert data["connects"] == [7, 9]


def test_nodal_load_constraint_node_pointer_roundtrips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # Appendix Type418 and §§4.107/4.139: PTYPE12 tabular properties carry
    # six constant load components (ND6, NI0), one property per analysis case.
    properties = [
        make_entity(
            de_index=index,
            entity_type=406,
            form=11,
            data={
                "np": 9,
                "values": [{"kind": "int", "value": value} for value in (12, 6, 0)]
                + [{"kind": "real", "value": value} for value in (load, 0.0, 0.0, 0.0, 0.0, 0.0)],
            },
            directory_entry_overrides={"status": _status("definition", dependent=True)},
        )
        for index, load in ((7, 1.0), (9, 2.0))
    ]
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=418,
        data={"nc": 2, "type": 1, "de": 5, "ptrs": [7, 9]},
        supporting=[_coordinate_system(), _node(5, 5), *properties],
    )
    assert data == {"nc": 2, "type": 1, "de": 5, "ptrs": [7, 9]}


def test_network_subfigure_instance_definition_and_display_pointers_roundtrip(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    # Appendix Type420: definition and instance each own their connect point;
    # both lists have NC1 and the displayed reference designator has a template.
    definition = make_entity(
        de_index=3,
        entity_type=320,
        data={
            "depth": 0,
            "name": "IC",
            "na": 1,
            "associated": [5],
            "tf": 2,
            "prd": "IC",
            "dptr": 7,
            "nc": 1,
            "connects": [9],
        },
        directory_entry_overrides={"status": _status("definition")},
    )
    data = _roundtrip_supported(
        submission_command,
        tmp_path,
        entity_type=420,
        supporting=[
            definition,
            _symbol(5),
            _text_template(7),
            _connection(9, 3, 1),
            _connection(11, 1, 1),
        ],
        data={
            "de": 3,
            "x": -5.5,
            "y": 12.3,
            "z": 0.1,
            "xs": 0.5,
            "ys": 0.5,
            "zs": 0.5,
            "tf": 2,
            "prd": "IC3",
            "dptr": 7,
            "nc": 1,
            "cptrs": [11],
        },
    )
    assert data["de"] == 3
    assert data["dptr"] == 7
    assert data["cptrs"] == [11]
