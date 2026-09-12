"""Type 114 physical patch ordering, independently of submission roundtrips."""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from iges_support import (
    evaluate_entity,
    fixture_iges_from_json,
    make_entity,
    wrap_entities,
    write_iges_from_json,
)
from raw_iges_support import physical_lines_by_section


def two_patch_surface_document() -> dict[str, Any]:
    """Two adjoining quadratic patches: X=u, Y=v, Z=max(u-1, 0)^2."""
    patches: list[dict[str, list[float]]] = []
    for row in range(2):
        x, y, z = [0.0] * 16, [0.0] * 16, [0.0] * 16
        x[0], x[1], y[4] = float(row), 1.0, 1.0
        z[2] = float(row)
        patches.append({"coeff_x": x, "coeff_y": y, "coeff_z": z})
    return wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=114,
                data={
                    "ctype": 2,
                    "ptype": 1,
                    "M": 2,
                    "N": 1,
                    "tu": [0.0, 1.0, 2.0],
                    "tv": [0.0, 1.0],
                    "patches": patches,
                },
            )
        ]
    )


def test_eval_second_spline_surface_row_skips_boundary_placeholders(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # §4.15 inserts 48 ignored coefficients after EACH row. Nonzero arbitrary
    # values in the frozen fixture ensure a contiguous M*N reader is detected.
    path = fixture_iges_from_json(submission_command, two_patch_surface_document(), tmp_path)
    _, payload = evaluate_entity(submission_command, path, 1, 1.5, tmp_path, s=0.25)
    point: list[float] = payload["point"]
    assert len(point) == 3
    assert all(
        math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
        for a, b in zip(point, [1.5, 0.25, 0.25], strict=True)
    )


def test_write_spline_surface_includes_boundary_patch_slots(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    document = two_patch_surface_document()
    path = write_iges_from_json(submission_command, document, tmp_path)
    fields = "".join(line[:64] for line in physical_lines_by_section(path)["P"])
    tokens = fields.split(";", 1)[0].split(",")
    # §4.15 places a 48-slot ignored boundary column between the real rows.
    # §2.2.3 allows record termination to default trailing parameters, so do
    # not require a writer to spell out wholly trailing zero/ignored slots.
    prefix = 1 + 4 + 3 + 2
    patches = document["entities"][0]["entity"]["data"]["patches"]
    for row, patch in enumerate(patches):
        begin = prefix + row * 2 * 48
        actual = [
            float(tokens[i].strip().replace("D", "E").replace("d", "e") or "0")
            if i < len(tokens)
            else 0.0
            for i in range(begin, begin + 48)
        ]
        expected = [*patch["coeff_x"], *patch["coeff_y"], *patch["coeff_z"]]
        assert all(
            math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)
            for a, b in zip(actual, expected, strict=True)
        )
