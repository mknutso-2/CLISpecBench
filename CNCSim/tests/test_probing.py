from __future__ import annotations

import math
from pathlib import Path

import pytest

from swe_buildbench.cncsim.rs274_parameters import (
    PROBE_TRIP_A_PARAMETER,
    PROBE_TRIP_B_PARAMETER,
    PROBE_TRIP_C_PARAMETER,
    PROBE_TRIP_X_PARAMETER,
    PROBE_TRIP_Y_PARAMETER,
    PROBE_TRIP_Z_PARAMETER,
)
from swe_buildbench.cncsim.test_support import ProbeBox, get_parameter_value, run_cncsim

PROBE_TOOL = 2
PROBE_TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

2 2 1.5 0.25 probe
"""

ProbeSuccessCase = tuple[str, ProbeBox, str, dict[int, float], str | None]

PROBE_SUCCESS_CASES: list[ProbeSuccessCase] = [
    (
        "x-probe-without-tlc",
        (12.0, 20.0, 0.0, 10.0, 0.0, 10.0),
        "G20\n"
        "G10 L2 P1 X10.0 Y0.0 Z0.0\n"
        "G54\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X0.0 Y5.0 Z5.0\n"
        "F10.0\n"
        "G38.2 X10.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 12.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 5.0,
        },
        None,
    ),
    (
        "y-probe-without-tlc",
        (0.0, 10.0, 12.0, 20.0, 0.0, 10.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z5.0\n"
        "F10.0\n"
        "G38.2 Y15.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 12.0,
            PROBE_TRIP_Z_PARAMETER: 5.0,
        },
        None,
    ),
    (
        "x-probe-without-tlc-in-g21-converts-inch-box-extents",
        (1.0, 2.0, 0.0, 10.0, 0.0, 10.0),
        "G21\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X0.0 Y127.0 Z127.0\n"
        "F254.0\n"
        "G38.2 X50.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 25.4,
            PROBE_TRIP_Y_PARAMETER: 127.0,
            PROBE_TRIP_Z_PARAMETER: 127.0,
        },
        None,
    ),
    (
        "z-probe-without-tlc",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z5.0\n"
        "F10.0\n"
        "G38.2 Z0.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
        },
        None,
    ),
    (
        "selected-tool-does-not-change-the-probe-in-spindle-until-m6",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "T1\n"
        "G0 X5.0 Y5.0 Z5.0\n"
        "F10.0\n"
        "G38.2 Z0.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
        },
        None,
    ),
    (
        "x-probe-with-tlc",
        (12.0, 20.0, 0.0, 10.0, 0.0, 1.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X0.0 Y5.0 Z2.5\n"
        "G43 H2\n"
        "F10.0\n"
        "G38.2 X15.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 12.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 1.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "y-probe-with-tlc",
        (0.0, 10.0, 12.0, 20.0, 0.0, 1.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z2.5\n"
        "G43 H2\n"
        "F10.0\n"
        "G38.2 Y15.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 12.0,
            PROBE_TRIP_Z_PARAMETER: 1.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "z-probe-with-tlc",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z6.0\n"
        "G43 H2\n"
        "F10.0\n"
        "G38.2 Z0.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
        },
        PROBE_TOOL_TABLE,
    ),
]


# RS274 section 3.5.9 says G38.2 moves the controlled point toward the
# programmed point and, after a successful trip, sets parameters 5061 to 5066
# to the controlled-point location at the trip time. The technical
# requirements prompt defines the eval-specific probing environment: the
# harness may pass --probe-box for an axis-aligned absolute machine-coordinate
# box and --probe-tool for the tool number that should be treated as a probe.
# These cases pin exact XYZ trip coordinates and also verify that 5064 through
# 5066 are reported numerically on success. The "selected tool" case also
# relies on RS274 section 3.7.3 and section 3.6.3: a T word only changes the
# selected tool, and the tool in the spindle does not change until M6.
@pytest.mark.parametrize(
    ("probe_box", "input_gcode", "expected_trip_parameters", "tool_table_content"),
    [
        (probe_box, input_gcode, expected_trip_parameters, tool_table_content)
        for (
            _,
            probe_box,
            input_gcode,
            expected_trip_parameters,
            tool_table_content,
        ) in PROBE_SUCCESS_CASES
    ],
    ids=[case_id for case_id, _, _, _, _ in PROBE_SUCCESS_CASES],
)
def test_application_reports_probe_trip_parameters(
    built_executable_path: Path,
    probe_box: ProbeBox,
    input_gcode: str,
    expected_trip_parameters: dict[int, float],
    tool_table_content: str | None,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        probe_box=probe_box,
        probe_tool=PROBE_TOOL,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    for parameter_index, expected_value in expected_trip_parameters.items():
        assert get_parameter_value(payload, parameter_index) == expected_value
    for parameter_index in (
        PROBE_TRIP_A_PARAMETER,
        PROBE_TRIP_B_PARAMETER,
        PROBE_TRIP_C_PARAMETER,
    ):
        assert math.isfinite(get_parameter_value(payload, parameter_index))
