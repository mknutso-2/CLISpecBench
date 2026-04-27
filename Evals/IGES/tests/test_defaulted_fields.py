"""Regression tests for three entity parsers whose optional fields were
previously read with strict tokenizers and rejected when defaulted.

Fixed 2026-04-14 (Evals/IGES/PLAN.md → Known Issues). ex1.iges is the
original repro; these targeted tests lock in the fix per entity so a
future rewrite that re-introduces strict reads fails loudly.

Each test builds a minimal document containing the entity with its
defaulted fields at their spec-defined defaults, writes + reparses
through the CLI, and asserts the values round-trip cleanly.

Spec references:
  §4.26 Connect Point (132)        — CID / CFN default to "" (string default)
  §4.22 Network Subfigure Def (320) — PRD defaults to "" (string default)
  §4.41 Rectangular Array (412)    — DDF defaults to 0 (integer default)
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from iges_support import make_entity, semantic_roundtrip_json, wrap_entities


def test_connect_point_with_defaulted_cid_and_cfn_roundtrips(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§4.26: CID (field 7) and CFN (field 9) default to empty string."""
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=132,
                data={
                    "location": [0.0, 0.0, 0.0],
                    "display_symbol": 0,
                    "tf": 0,
                    "ff": 0,
                    "cid": "",  # defaulted
                    "pttcid": 0,
                    "cfn": "",  # defaulted
                    "pttcfn": 0,
                    "cpid": 0,
                    "fc": 0,
                    "sf": 0,
                    "psfi": 0,
                },
            ),
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    data = reparsed["entities"][0]["entity"]["data"]
    assert data["cid"] == ""
    assert data["cfn"] == ""
    assert data["location"] == [0.0, 0.0, 0.0]


def test_network_subfigure_definition_with_defaulted_prd_roundtrips(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§4.22: PRD (Primary Reference Designator) defaults to empty string."""
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=320,
                data={
                    "depth": 1,
                    "name": "NET",
                    "na": 0,
                    "associated": [],
                    "tf": 0,
                    "prd": "",  # defaulted
                    "dptr": 0,
                    "nc": 0,
                    "connects": [],
                },
            ),
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    data = reparsed["entities"][0]["entity"]["data"]
    assert data["prd"] == ""
    assert data["dptr"] == 0
    assert data["name"] == "NET"


def test_rectangular_array_with_defaulted_ddf_roundtrips(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§4.41: DDF (Do-Don't Flag) defaults to 0 when omitted from the PD."""
    doc = wrap_entities(
        [
            # A base entity to point at. Using a Line (110) as the simplest
            # thing the Rectangular Array can reference.
            make_entity(
                de_index=1,
                entity_type=110,
                data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            ),
            make_entity(
                de_index=3,
                entity_type=412,
                data={
                    "de": 1,  # DE pointer to Line above
                    "s": 1.0,
                    "position": [0.0, 0.0, 0.0],
                    "nc": 2,
                    "nr": 2,
                    "dx": 1.0,
                    "dy": 1.0,
                    "ax": 0.0,
                    "lc": 0,
                    "ddf": 0,  # defaulted
                    "positions": [],
                },
            ),
        ]
    )
    reparsed = semantic_roundtrip_json(submission_command, doc, tmp_path)
    array_entity = reparsed["entities"][1]["entity"]
    assert array_entity["type"] == 412
    data = array_entity["data"]
    assert data["ddf"] == 0
    assert data["nc"] == 2
    assert data["nr"] == 2
