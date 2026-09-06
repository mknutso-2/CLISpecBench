from __future__ import annotations

from pathlib import Path

import pytest

from rs274_parameters import (
    PROBE_TRIP_A_PARAMETER,
    PROBE_TRIP_B_PARAMETER,
    PROBE_TRIP_C_PARAMETER,
    PROBE_TRIP_X_PARAMETER,
    PROBE_TRIP_Y_PARAMETER,
    PROBE_TRIP_Z_PARAMETER,
)
from rs274_support import ProbeBox, run_rs274, with_default_rotary_axes

PROBE_TOOL = 2
PROBE_TLC_TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

2 2 1.5 0.25 probe
"""

# A probe designation is not a tool-table entry. Section 3.7.3 permits
# empty slots, so successful M6 setup explicitly supplies an occupied slot.
PROBE_TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 0.0 non-probe
2 2 0.0 0.0 probe
"""

ProbeSuccessCase = tuple[str, ProbeBox, str, dict[int, float], str]

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
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "y-probe-without-tlc",
        (0.0, 10.0, 12.0, 20.0, 0.0, 10.0),
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2 Y15.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 12.0,
            PROBE_TRIP_Z_PARAMETER: 5.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "x-probe-without-tlc-in-g21-converts-inch-box-extents",
        (1.0, 2.0, 0.0, 10.0, 0.0, 10.0),
        "G21\nG90 G94\nT2 M6\nG0 X0.0 Y127.0 Z127.0\nF254.0\nG38.2 X50.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 25.4,
            PROBE_TRIP_Y_PARAMETER: 127.0,
            PROBE_TRIP_Z_PARAMETER: 127.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "z-probe-without-tlc",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2 Z0.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "selected-tool-does-not-change-the-probe-in-spindle-until-m6",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\nG90 G94\nT2 M6\nT1\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2 Z0.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        # These TLC/probe integration cases necessarily depend on the
        # controlled-point shift from G43 (sections 2.1.2.10 and 3.5.11).
        # Dedicated tool-length tests diagnose that prerequisite separately;
        # retaining a nonzero offset here verifies that probe-box intersection
        # uses the tool tip rather than the spindle gauge point. A failure in
        # that shared prerequisite may therefore also fail these bounded cases.
        "x-probe-with-tlc",
        (12.0, 20.0, 0.0, 10.0, 0.0, 1.0),
        "G20\nG90 G94\nT2 M6\nG0 X0.0 Y5.0 Z2.5\nG43 H2\nF10.0\nG38.2 X15.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 12.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 1.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TLC_TOOL_TABLE,
    ),
    (
        "y-probe-with-tlc",
        (0.0, 10.0, 12.0, 20.0, 0.0, 1.0),
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z2.5\nG43 H2\nF10.0\nG38.2 Y15.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 12.0,
            PROBE_TRIP_Z_PARAMETER: 1.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TLC_TOOL_TABLE,
    ),
    (
        "z-probe-with-tlc",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z6.0\nG43 H2\nF10.0\nG38.2 Z0.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TLC_TOOL_TABLE,
    ),
    (
        "x-probe-g91-g21-incremental-metric",
        (1.0, 2.0, 0.0, 10.0, 0.0, 10.0),
        "G21\nG91 G94\nT2 M6\nG90 G0 X0.0 Y127.0 Z127.0\nG91\nF254.0\nG38.2 X50.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 25.4,
            PROBE_TRIP_Y_PARAMETER: 127.0,
            PROBE_TRIP_Z_PARAMETER: 127.0,
            PROBE_TRIP_A_PARAMETER: 0.0,
            PROBE_TRIP_B_PARAMETER: 0.0,
            PROBE_TRIP_C_PARAMETER: 0.0,
        },
        PROBE_TOOL_TABLE,
    ),
    (
        "probe-accepts-stationary-rotary-words-and-reports-rotary-trip-parameters",
        (0.0, 10.0, 0.0, 10.0, 2.0, 4.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z5.0 A10.0 B20.0 C30.0\n"
        "F10.0\n"
        "G38.2 Z0.0 A10.0 B20.0 C30.0\n",
        {
            PROBE_TRIP_X_PARAMETER: 5.0,
            PROBE_TRIP_Y_PARAMETER: 5.0,
            PROBE_TRIP_Z_PARAMETER: 4.0,
            PROBE_TRIP_A_PARAMETER: 10.0,
            PROBE_TRIP_B_PARAMETER: 20.0,
            PROBE_TRIP_C_PARAMETER: 30.0,
        },
        PROBE_TOOL_TABLE,
    ),
]

PROBE_TRIP_PARAMETER_CASE = PROBE_SUCCESS_CASES[-1]


def trip_parameters_to_machine_position(
    expected_trip_parameters: dict[int, float],
) -> dict[str, float]:
    return with_default_rotary_axes(
        {
            "x": expected_trip_parameters[PROBE_TRIP_X_PARAMETER],
            "y": expected_trip_parameters[PROBE_TRIP_Y_PARAMETER],
            "z": expected_trip_parameters[PROBE_TRIP_Z_PARAMETER],
            "a": expected_trip_parameters[PROBE_TRIP_A_PARAMETER],
            "b": expected_trip_parameters[PROBE_TRIP_B_PARAMETER],
            "c": expected_trip_parameters[PROBE_TRIP_C_PARAMETER],
        }
    )


# RS274 section 3.5.9 says G38.2 moves the controlled point toward the
# programmed point and, after a successful trip, sets parameters 5061 to 5066
# to the controlled-point location at the trip time. This representative case
# checks the full 5061-5066 write path, including rotary trip values. The
# broader probe matrix below checks trip behavior without depending on the same
# parameter-write plumbing in every row.
def test_application_reports_probe_trip_parameters(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, probe_box, input_gcode, expected_trip_parameters, tool_table_content = (
        PROBE_TRIP_PARAMETER_CASE
    )
    completed, payload = run_rs274(
        submission_command,
        # Section 3.5.9 requires #5061..#5066 writes, but the snapshot map
        # may omit entries. Read all six through a required G53 endpoint.
        input_gcode=input_gcode + "G90 G53 G0 X#5061 Y#5062 Z#5063 A#5064 B#5065 C#5066\n",
        probe_box=probe_box,
        probe_tool=PROBE_TOOL,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == trip_parameters_to_machine_position(
        expected_trip_parameters
    )


# The technical requirements prompt defines the eval-specific probing
# environment: the harness may pass --probe-box for an axis-aligned absolute
# machine-coordinate box and --probe-tool for the tool number that should be
# treated as a probe. The selected-tool case also relies on RS274 sections
# 3.7.3 and 3.6.3: a T word only changes the selected tool, and the tool in
# the spindle does not change until M6.
@pytest.mark.parametrize(
    ("probe_box", "input_gcode", "expected_machine_position", "tool_table_content"),
    [
        (
            probe_box,
            input_gcode,
            trip_parameters_to_machine_position(expected_trip_parameters),
            tool_table_content,
        )
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
def test_application_stops_probe_at_trip_point(
    submission_command: tuple[str, ...],
    probe_box: ProbeBox,
    input_gcode: str,
    expected_machine_position: dict[str, float],
    tool_table_content: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        probe_box=probe_box,
        probe_tool=PROBE_TOOL,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == expected_machine_position
