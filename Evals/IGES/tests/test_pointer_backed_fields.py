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


def test_plane_unbounded_pointer_field_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=108,
        data={
            "A": 0.0,
            "B": 0.0,
            "C": 1.0,
            "D": 0.0,
            "ptr": 7,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "size": 1.5,
        },
    )
    assert data["ptr"] == 7
    assert data["size"] == pytest.approx(1.5)


def test_node_ndcsp_pointer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=134,
        data={"x": 1.0, "y": 2.0, "z": 3.0, "ndcsp": 9},
    )
    assert data == {"x": 1.0, "y": 2.0, "z": 3.0, "ndcsp": 9}


def test_nodal_displacement_node_pointer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=138,
        data={
            "nc": 1,
            "gp": [11],
            "nn": 1,
            "nodes": [{
                "node_id": 5,
                "np": 7,
                "cases": [{
                    "x": 0.1,
                    "y": 0.2,
                    "z": 0.3,
                    "rx": 0.01,
                    "ry": 0.02,
                    "rz": 0.03,
                }],
            }],
        },
    )
    assert data["gp"] == [11]
    assert data["nodes"][0]["np"] == 7
    assert data["nodes"][0]["cases"][0]["rz"] == pytest.approx(0.03)


def test_nodal_results_gnote_and_np_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=146,
        data={
            "gnote": 13,
            "scn": 2,
            "time": 1.5,
            "nv": 2,
            "nn": 1,
            "nodes": [{"node_id": 5, "np": 7, "values": [3.14, 2.72]}],
        },
    )
    assert data["gnote"] == 13
    assert data["nodes"][0]["np"] == 7
    assert data["nodes"][0]["values"] == pytest.approx([3.14, 2.72])


def test_element_results_gnote_and_ep_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=148,
        data={
            "gnote": 15,
            "scn": 1,
            "time": 2.0,
            "nv": 2,
            "rrf": 0,
            "ne": 1,
            "elements": [{
                "en": 21,
                "ep": 23,
                "itop": 4,
                "nl": 1,
                "dlf": 0,
                "nrl": 1,
                "rdrl": [1],
                "numv": 2,
                "values": [10.0, 20.0],
            }],
        },
    )
    assert data["gnote"] == 15
    assert data["elements"][0]["ep"] == 23
    assert data["elements"][0]["values"] == pytest.approx([10.0, 20.0])


def test_network_subfigure_definition_display_pointer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=320,
        data={
            "depth": 1,
            "name": "RESISTOR",
            "na": 1,
            "associated": [5],
            "tf": 0,
            "prd": "R1",
            "dptr": 7,
            "nc": 2,
            "connects": [9, 11],
        },
    )
    assert data["dptr"] == 7
    assert data["connects"] == [9, 11]


def test_nodal_load_constraint_node_pointer_roundtrips(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=418,
        data={"nc": 2, "type": 1, "de": 9, "ptrs": [11, 13]},
    )
    assert data == {"nc": 2, "type": 1, "de": 9, "ptrs": [11, 13]}


def test_network_subfigure_instance_definition_and_display_pointers_roundtrip(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    data = _roundtrip_single(
        submission_command,
        tmp_path,
        entity_type=420,
        data={
            "de": 11,
            "x": -5.5,
            "y": 12.3,
            "z": 0.1,
            "xs": 0.5,
            "ys": 0.5,
            "zs": 0.5,
            "tf": 2,
            "prd": "IC3",
            "dptr": 15,
            "nc": 1,
            "cptrs": [17],
        },
    )
    assert data["de"] == 11
    assert data["dptr"] == 15
    assert data["cptrs"] == [17]
