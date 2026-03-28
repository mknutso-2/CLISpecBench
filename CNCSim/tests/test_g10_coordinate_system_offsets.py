from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

CoordinateSystemOffsetCase = tuple[str, str, dict[str, dict[str, float]]]

COORDINATE_SYSTEM_OFFSET_CASES: list[CoordinateSystemOffsetCase] = [
    (
        "g10-sets-coordinate-system-1-offsets",
        "G10 L2 P1 X3.5 Y17.2 Z-4.0\n",
        {
            "1": {"x": 3.5, "y": 17.2, "z": -4.0},
        },
    ),
    (
        "g10-updates-only-programmed-axes",
        "G10 L2 P2 X1.0 Y2.0 Z3.0\n"
        "G10 L2 P2 X4.5 Z-1.0\n",
        {
            "2": {"x": 4.5, "y": 2.0, "z": -1.0},
        },
    ),
    (
        "g10-keeps-coordinate-systems-independent",
        "G10 L2 P1 X1.0 Y2.0 Z3.0\n"
        "G10 L2 P3 X7.0 Y8.0 Z9.0\n",
        {
            "1": {"x": 1.0, "y": 2.0, "z": 3.0},
            "3": {"x": 7.0, "y": 8.0, "z": 9.0},
        },
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.2.2 for the nine program
# coordinate systems and section 3.5.5 for G10 L2 Pn setting the stored origin
# of a selected coordinate system in absolute coordinates. Axis words omitted
# from a later G10 block keep their previously stored values.
@pytest.mark.parametrize(
    ("input_gcode", "expected_offsets"),
    [
        (input_gcode, expected_offsets)
        for _, input_gcode, expected_offsets in COORDINATE_SYSTEM_OFFSET_CASES
    ],
    ids=[case_id for case_id, _, _ in COORDINATE_SYSTEM_OFFSET_CASES],
)
def test_application_tracks_g10_coordinate_system_offsets(
    built_executable_path: Path,
    input_gcode: str,
    expected_offsets: dict[str, dict[str, float]],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    for system_number, expected_offset in expected_offsets.items():
        assert payload["coordinate_system_offsets"][system_number] == expected_offset
