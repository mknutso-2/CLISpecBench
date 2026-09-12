"""Small legal display and coordinate-system records for semantic roundtrips."""

from __future__ import annotations

from math import pi
from typing import Any

from iges_support import make_entity


def context_status(use: str, subordinate: str = "independent") -> dict[str, str]:
    return {
        "blank": "visible",
        "subordinate": subordinate,
        "entity_use": use,
        "hierarchy": "global_defer",
    }


def text_template(index: int) -> dict[str, Any]:
    # §4.74: a predefined font needs no Font Definition pointer.
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
        directory_entry_overrides={"status": context_status("definition", "physically_dependent")},
    )


def context_line(
    index: int, *, use: str = "geometry", subordinate: str = "independent"
) -> dict[str, Any]:
    return make_entity(
        de_index=index,
        entity_type=110,
        data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
        directory_entry_overrides={"status": context_status(use, subordinate)},
    )


def context_matrix(index: int, *, form: int = 0, use: str = "geometry") -> dict[str, Any]:
    # §§4.21/4.27: Form10 is a labeled Cartesian nodal coordinate system.
    return make_entity(
        de_index=index,
        entity_type=124,
        form=form,
        data={
            "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "translation": [0.0, 0.0, 0.0],
        },
        directory_entry_overrides={"entity_label": "GLOBAL", "status": context_status(use)},
    )


def context_note(index: int) -> dict[str, Any]:
    # §4.60: nonempty normal text and a legal nonslant angle.
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
                    "text": "VIEW",
                }
            ],
        },
        directory_entry_overrides={"status": context_status("annotation", "physically_dependent")},
    )
