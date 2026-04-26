from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import (
    GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
    GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION,
    GCODE_MODAL_GROUP_DISTANCE_MODE,
    GCODE_MODAL_GROUP_FEED_RATE_MODE,
    GCODE_MODAL_GROUP_MOTION,
    GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
    GCODE_MODAL_GROUP_PLANE_SELECTION,
    GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
    GCODE_MODAL_GROUP_TOOL_LENGTH_OFFSET,
    GCODE_MODAL_GROUP_UNITS,
)
from rs274_support import mapping_field, run_rs274, with_default_rotary_axes

ActiveGcodeGroupCase = tuple[str, str, str]
CoordinateSystemSelectionCase = tuple[str, str, dict[str, float]]

ACTIVE_GCODE_GROUP_CASES: list[ActiveGcodeGroupCase] = [
    (
        "G94\nG0 X0\nG1 X0\n",
        GCODE_MODAL_GROUP_MOTION,
        "G1",
    ),
    (
        "G17\nG18\n",
        GCODE_MODAL_GROUP_PLANE_SELECTION,
        "G18",
    ),
    (
        "#1=18\nG17\nG#1\n",
        GCODE_MODAL_GROUP_PLANE_SELECTION,
        "G18",
    ),
    (
        "G17\nG[17+2]\n",
        GCODE_MODAL_GROUP_PLANE_SELECTION,
        "G19",
    ),
    (
        "G90\nG91\n",
        GCODE_MODAL_GROUP_DISTANCE_MODE,
        "G91",
    ),
    (
        "#1=91\nG90\nG#1\n",
        GCODE_MODAL_GROUP_DISTANCE_MODE,
        "G91",
    ),
    (
        "G90\nG[45*2]\n",
        GCODE_MODAL_GROUP_DISTANCE_MODE,
        "G90",
    ),
    (
        "G94\nG93\n",
        GCODE_MODAL_GROUP_FEED_RATE_MODE,
        "G93",
    ),
    (
        "#1=93\nG94\nG#1\n",
        GCODE_MODAL_GROUP_FEED_RATE_MODE,
        "G93",
    ),
    (
        "G93\nG[47*2]\n",
        GCODE_MODAL_GROUP_FEED_RATE_MODE,
        "G94",
    ),
    (
        "G20\nG21\n",
        GCODE_MODAL_GROUP_UNITS,
        "G21",
    ),
    (
        "#1=21\nG20\nG#1\n",
        GCODE_MODAL_GROUP_UNITS,
        "G21",
    ),
    (
        "G20\nG[42/2]\n",
        GCODE_MODAL_GROUP_UNITS,
        "G21",
    ),
    (
        "G40\nG41\n",
        GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION,
        "G41",
    ),
    (
        "G49\nG43 H0\n",
        GCODE_MODAL_GROUP_TOOL_LENGTH_OFFSET,
        "G43",
    ),
    (
        "G98\nG99\n",
        GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
        "G99",
    ),
    (
        "G54\nG55\n",
        GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
        "G55",
    ),
    (
        "#1=54\nG55\nG#1\n",
        GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
        "G54",
    ),
    (
        "G55\nG[53+1]\n",
        GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
        "G54",
    ),
    (
        "G61\nG64\n",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G64",
    ),
    (
        "G64\nG61\n",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G61",
    ),
    (
        "G61\nG61.1\n",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G61.1",
    ),
    (
        "#1=61.1\nG64\nG#1\n",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G61.1",
    ),
    (
        "G61.1\nG[32*2]\n",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G64",
    ),
    (
        "G64\nG64\n",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G64",
    ),
]

COORDINATE_SYSTEM_SELECTION_CASES: list[CoordinateSystemSelectionCase] = [
    ("G54", "1", {"x": 10.0, "y": 0.0, "z": 0.0}),
    ("G55", "2", {"x": 20.0, "y": 0.0, "z": 0.0}),
    ("G56", "3", {"x": 30.0, "y": 0.0, "z": 0.0}),
    ("G57", "4", {"x": 40.0, "y": 0.0, "z": 0.0}),
    ("G58", "5", {"x": 50.0, "y": 0.0, "z": 0.0}),
    ("G59", "6", {"x": 60.0, "y": 0.0, "z": 0.0}),
    ("G59.1", "7", {"x": 70.0, "y": 0.0, "z": 0.0}),
    ("G59.2", "8", {"x": 80.0, "y": 0.0, "z": 0.0}),
    ("G59.3", "9", {"x": 90.0, "y": 0.0, "z": 0.0}),
]


# See RS274/prompt/docs/RS274NGC.md section 3.4 "Modal Groups" and Table 4:
# only one member of a modal group may be in force at a time, so the last
# emitted G-code from a group should be the active one reported in the output.
# Section 3.3.2 says G words take real values, and sections 3.3.2.2 and
# 3.3.2.3 define parameter values and expressions as real values, so supported
# G-code selections in the covered modal groups should accept those forms too.
@pytest.mark.parametrize(
    ("input_gcode", "group_number", "expected_active_gcode"),
    ACTIVE_GCODE_GROUP_CASES,
    ids=[
        f"group-{group_number}-{expected_active_gcode.lower()}"
        for _, group_number, expected_active_gcode in ACTIVE_GCODE_GROUP_CASES
    ],
)
def test_application_tracks_active_gcode_groups(
    submission_command: tuple[str, ...],
    input_gcode: str,
    group_number: str,
    expected_active_gcode: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "active_modal_g_codes").get(group_number) == expected_active_gcode


# RS274 section 3.2.2 defines the nine program coordinate systems, and
# section 3.5.13 says G54 through G59.3 select among them. This matrix uses one
# shared setup that assigns a distinct X offset to each system, then verifies
# that each selection code activates the expected modal code and uses the
# corresponding stored offset for motion.
@pytest.mark.parametrize(
    ("selected_gcode", "expected_system_number", "expected_machine_position"),
    COORDINATE_SYSTEM_SELECTION_CASES,
    ids=[selected_gcode.lower() for selected_gcode, _, _ in COORDINATE_SYSTEM_SELECTION_CASES],
)
def test_coordinate_system_selection_codes_activate_the_expected_system(
    submission_command: tuple[str, ...],
    selected_gcode: str,
    expected_system_number: str,
    expected_machine_position: dict[str, float],
    tmp_path: Path,
) -> None:
    coordinate_system_setup = "".join(
        f"G10 L2 P{system_number} X{system_number * 10}.0 Y0.0 Z0.0\n"
        for system_number in range(1, 10)
    )
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            coordinate_system_setup + f"{selected_gcode}\n" + "G90\n" + "G0 X0.0 Y0.0 Z0.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert (
        mapping_field(payload, "active_modal_g_codes").get(
            GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION
        )
        == selected_gcode
    )
    assert mapping_field(payload, "coordinate_system_offsets").get(
        expected_system_number
    ) == with_default_rotary_axes(expected_machine_position)
    assert payload.get("machine_position") == with_default_rotary_axes(expected_machine_position)
