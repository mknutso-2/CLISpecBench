from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import (
    GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION,
    GCODE_MODAL_GROUP_DISTANCE_MODE,
    GCODE_MODAL_GROUP_FEED_RATE_MODE,
    GCODE_MODAL_GROUP_MOTION,
    GCODE_MODAL_GROUP_PLANE_SELECTION,
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
)
from rs274_parameters import (
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
)
from rs274_support import (
    get_parameter_value,
    mapping_field,
    run_rs274,
    with_default_rotary_axes,
)

PROGRAM_END_CODES = ("M2", "M30")

ZERO_RADIUS_CRC_TOOL_TABLE = """POCKET FMS TLO DIAMETER

1 1 0.0 0.0
"""


# RS274 section 3.6.1 says M2 and M30 have the following effects:
# - "Selected plane is set to CANON_PLANE_XY (like G17)."
# - "Distance mode is set to MODE_ABSOLUTE (like G90)."
# - "Feed rate mode is set to UNITS_PER_MINUTE (like G94)."
# - "Feed and speed overrides are set to ON (like M48)."
# - "Cutter compensation is turned off (like G40)."
# - "The spindle is stopped (like M5)."
# - "The current motion mode is set to G_1 (like G1)."
# - "Coolant is turned off (like M9)."
# It also says no more lines are executed after M2/M30.
# The separate clause "origin offsets are set to the default (like G54)" is
# intentionally not asserted here, because RS274 does not map that clause
# unambiguously onto RS274's serialized fields. Assertions such as "active
# coordinate system is G54" or "parameter 5220 is 1" would be stronger than
# the spec text itself.
@pytest.mark.parametrize("program_end_code", PROGRAM_END_CODES)
def test_application_resets_explicit_modal_state_on_m2_and_m30_and_ignores_invalid_trailing_lines(
    submission_command: tuple[str, ...],
    program_end_code: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            "G10 L2 P2 X0.0 Y0.0 Z0.0\n"
            "G55\n"
            "G18\n"
            "G91\n"
            "G93\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "M49\n"
            "S1200 M3\n"
            "M7\n"
            f"{program_end_code}\n"
            "G59.3\n"
            "G19\n"
            "G91\n"
            "G93\n"
            "M49\n"
            "M3\n"
            "M7\n"
            "G5\n"
            "G0 X[\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 1.0, "y": 2.0, "z": 3.0}
    )
    assert (
        mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_PLANE_SELECTION)
        == "G17"
    )
    assert (
        mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_DISTANCE_MODE) == "G90"
    )
    assert (
        mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_FEED_RATE_MODE)
        == "G94"
    )
    assert (
        mapping_field(payload, "active_modal_g_codes").get(
            GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION
        )
        == "G40"
    )
    assert mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_MOTION) == "G1"
    assert (
        mapping_field(payload, "active_modal_m_codes").get(MCODE_MODAL_GROUP_OVERRIDE_SWITCHES)
        == "M48"
    )
    assert (
        mapping_field(payload, "active_modal_m_codes").get(MCODE_MODAL_GROUP_SPINDLE_TURNING)
        == "M5"
    )
    assert mapping_field(payload, "active_modal_m_codes").get(MCODE_MODAL_GROUP_COOLANT) == "M9"
    assert payload.get("spindle_direction") == "OFF"


# RS274 section 3.6.1 explicitly says M2 and M30 turn cutter compensation off.
# This setup uses a zero-radius D1 tool-table entry, not D0, so the test is
# about the program-end reset rather than D0 serialization.
@pytest.mark.parametrize("program_end_code", PROGRAM_END_CODES)
def test_application_turns_cutter_compensation_off_on_m2_and_m30(
    submission_command: tuple[str, ...],
    program_end_code: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            f"G17 G90 G94 F60\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\n{program_end_code}\nG42 D1\n"
        ),
        tool_table_content=ZERO_RADIUS_CRC_TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 5.0, "y": 0.0, "z": 0.0}
    )
    assert (
        mapping_field(payload, "active_modal_g_codes").get(
            GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION
        )
        == "G40"
    )
    assert payload.get("cutter_radius_compensation_number") is None


# RS274 section 3.6.1 says axis offsets are set to zero like G92.2, which
# cancels the active offsets without resetting parameters 5211..5216. The
# current payload exposes the parameter-preservation half of that behavior
# directly, even though it does not expose the canceled active offset layer.
@pytest.mark.parametrize("program_end_code", PROGRAM_END_CODES)
def test_application_preserves_g92_parameters_on_m2_and_m30_like_g92_2(
    submission_command: tuple[str, ...],
    program_end_code: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X10.0 Y20.0 Z30.0\n"
            "G92 X1.0 Y2.0 Z3.0\n"
            f"{program_end_code}\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == 9.0
    assert get_parameter_value(payload, G92_Y_OFFSET_PARAMETER) == 18.0
    assert get_parameter_value(payload, G92_Z_OFFSET_PARAMETER) == 27.0
