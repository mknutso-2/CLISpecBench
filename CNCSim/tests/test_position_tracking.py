from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

PositionTrackingCase = tuple[str, str, dict[str, float]]

POSITION_TRACKING_CASES: list[PositionTrackingCase] = [
    (
        "absolute-xyz",
        "G90\n"
        "G0 X1.0 Y2.0 Z3.0\n",
        {"x": 1.0, "y": 2.0, "z": 3.0},
    ),
    (
        "absolute-updates-only-programmed-axes",
        "G90\n"
        "G0 X1.0 Y2.0 Z3.0\n"
        "G1 X4.0\n",
        {"x": 4.0, "y": 2.0, "z": 3.0},
    ),
    (
        "incremental-xyz",
        "G90\n"
        "G0 X10.0 Y20.0 Z30.0\n"
        "G91\n"
        "G0 X1.0 Y2.0 Z3.0\n",
        {"x": 11.0, "y": 22.0, "z": 33.0},
    ),
    (
        "incremental-accumulates-from-current-position",
        "G90\n"
        "G0 X10.0 Y20.0 Z30.0\n"
        "G91\n"
        "G0 X1.0 Y2.0 Z3.0\n"
        "G1 X-0.5 Y1.5 Z2.0\n",
        {"x": 10.5, "y": 23.5, "z": 35.0},
    ),
    (
        "g2-updates-arc-endpoint",
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G2 X0.0 Y-1.0 Z4.0 I-1.0 J0.0\n",
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g3-updates-arc-endpoint",
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G3 X0.0 Y1.0 Z6.0 I-1.0 J0.0\n",
        {"x": 0.0, "y": 1.0, "z": 6.0},
    ),
    (
        "g2-radius-format-updates-arc-endpoint",
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G2 X0.0 Y-1.0 Z4.0 R1.0\n",
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g3-radius-format-updates-arc-endpoint",
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G3 X0.0 Y1.0 Z6.0 R1.0\n",
        {"x": 0.0, "y": 1.0, "z": 6.0},
    ),
]

POSITION_TRACKING_PARAMS = [
    (input_gcode, expected_final_position)
    for _, input_gcode, expected_final_position in POSITION_TRACKING_CASES
]


# See CNCSim/prompt/docs/RS274NGC.md section 2.1.2.10 "Current Position":
# the controller always has a current position, but this section does not assign
# a fixed startup X/Y/Z location. The incremental cases therefore establish a
# known position first before asserting relative motion.
# See sections 3.5.1 and 3.5.2 for linear motion with axis words, section
# 3.5.3 for G2/G3 arc endpoint programming, section 3.5.3.1 for radius-format
# arcs, and section 3.5.17 for how G90/G91 control whether X/Y/Z values are
# interpreted as absolute positions or incremental offsets.
@pytest.mark.parametrize(
    ("input_gcode", "expected_final_position"),
    POSITION_TRACKING_PARAMS,
    ids=[case_id for case_id, _, _ in POSITION_TRACKING_CASES],
)
def test_application_tracks_final_position(
    built_executable_path: Path,
    input_gcode: str,
    expected_final_position: dict[str, float],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["final_position"] == expected_final_position
