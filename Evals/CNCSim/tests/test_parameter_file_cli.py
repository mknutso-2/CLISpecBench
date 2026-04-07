from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import (
    build_parameter_file,
    get_parameter_value,
    run_cncsim,
    run_cncsim_invalid_input,
    with_default_rotary_axes,
)
from rs274_parameters import (
    G92_A_OFFSET_PARAMETER,
    G92_B_OFFSET_PARAMETER,
    G92_C_OFFSET_PARAMETER,
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
    coordinate_system_xyz_parameter_indices,
    coordinate_system_xyzabc_parameter_indices,
)

CLI_CASES: list[tuple[str, str | None, bool]] = [
    ("parameter-input-only", build_parameter_file(), False),
    ("parameter-output-only", None, True),
    ("parameter-input-and-output", build_parameter_file(), True),
]


# This keeps the narrow CLI-surface check for the optional parameter-file
# arguments. Startup parameter semantics are covered by the tests below.
@pytest.mark.parametrize(
    ("parameter_input_content", "pass_parameter_output"),
    [
        (parameter_input_content, pass_parameter_output)
        for _, parameter_input_content, pass_parameter_output in CLI_CASES
    ],
    ids=[case_id for case_id, _, _ in CLI_CASES],
)
def test_application_accepts_parameter_file_cli_arguments(
    submission_command: tuple[str, ...],
    parameter_input_content: str | None,
    pass_parameter_output: bool,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode="G90\nG0 X1.0 Y2.0 Z3.0\n",
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes({"x": 1.0, "y": 2.0, "z": 3.0})


# RS274 section 3.2.1 says the interpreter reads the parameter file when it
# starts up, and section 3.3.2.2 says parameter values are read from the
# numbered parameter slots.
def test_application_uses_parameter_values_loaded_from_input_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode="G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X#1\n",
        parameter_input_content=build_parameter_file({1: 4.25}),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes({"x": 4.25, "y": 0.0, "z": 0.0})
    assert get_parameter_value(payload, 1) == 4.25


# RS274 section 3.2.2 says startup selects the active coordinate system from
# parameter 5220.
def test_application_uses_selected_coordinate_system_loaded_from_input_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode="",
        parameter_input_content=build_parameter_file({SELECTED_COORDINATE_SYSTEM_PARAMETER: 2.0}),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    active_modal_g_codes = payload["active_modal_g_codes"]
    assert isinstance(active_modal_g_codes, dict)
    assert active_modal_g_codes["12"] == "G55"
    assert get_parameter_value(payload, SELECTED_COORDINATE_SYSTEM_PARAMETER) == 2.0


# RS274 section 3.2.1 says the coordinate-system origin parameters in Table 2
# are required startup state, and section 3.2.2 says the selected coordinate
# system is defined by those stored parameters.
def test_application_initializes_coordinate_system_offsets_from_input_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    cs2_x_parameter, cs2_y_parameter, cs2_z_parameter = coordinate_system_xyz_parameter_indices(2)
    (_, _, _, cs2_a_parameter, cs2_b_parameter, cs2_c_parameter) = (
        coordinate_system_xyzabc_parameter_indices(2)
    )
    completed, payload = run_cncsim(
        submission_command,
        input_gcode="G55\nG90\nG0 X1.0 Y2.0 Z3.0 A4.0 B5.0 C6.0\n",
        parameter_input_content=build_parameter_file(
            {
                cs2_x_parameter: 10.0,
                cs2_y_parameter: 20.0,
                cs2_z_parameter: 30.0,
                cs2_a_parameter: 40.0,
                cs2_b_parameter: 50.0,
                cs2_c_parameter: 60.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["coordinate_system_offsets"]["2"] == with_default_rotary_axes(
        {"x": 10.0, "y": 20.0, "z": 30.0, "a": 40.0, "b": 50.0, "c": 60.0}
    )
    assert payload["machine_position"] == with_default_rotary_axes(
        {"x": 11.0, "y": 22.0, "z": 33.0, "a": 44.0, "b": 55.0, "c": 66.0}
    )


# RS274 section 3.2.1 says parameters 5211-5216 are part of the required
# startup parameter state, and section 3.5.18 says those values define the
# axis offsets used by G92.3.
def test_application_initializes_g92_offsets_from_input_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0 A0.0 B0.0 C0.0\n"
            "G54\n"
            "G92.3\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0 A4.0 B5.0 C6.0\n"
        ),
        parameter_input_content=build_parameter_file(
            {
                G92_X_OFFSET_PARAMETER: 10.0,
                G92_Y_OFFSET_PARAMETER: 20.0,
                G92_Z_OFFSET_PARAMETER: 30.0,
                G92_A_OFFSET_PARAMETER: 40.0,
                G92_B_OFFSET_PARAMETER: 50.0,
                G92_C_OFFSET_PARAMETER: 60.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes(
        {"x": 11.0, "y": 22.0, "z": 33.0, "a": 44.0, "b": 55.0, "c": 66.0}
    )


PARAMETER_FILE_ERROR_CASES: list[tuple[str, str]] = [
    (
        "parameter-file-rejects-non-ascending-indices",
        "RS274 parameter file\n\n5162 0.0\n5161 0.0\n",
    ),
    # In preliminary testing, no model passes this test.
    # Section 3.2.1: "A parameter file may include any other parameter, as
    # long as its number is in the range 1 to 5400." Changed in v1.0.1 from
    # 5400 to 5401 because 5400 is the inclusive upper bound per the spec.
    (
        "parameter-file-rejects-out-of-range-index",
        "RS274 parameter file\n\n5401 1.0\n",
    ),
    (
        "parameter-file-rejects-invalid-5220",
        build_parameter_file({SELECTED_COORDINATE_SYSTEM_PARAMETER: 10.0}),
    ),
]


# RS274 section 3.2.1 requires ascending parameter numbers in range, and
# section 3.2.2 says startup parameter 5220 must be a whole number from 1 to 9.
@pytest.mark.parametrize(
    "parameter_input_content",
    [parameter_input_content for _, parameter_input_content in PARAMETER_FILE_ERROR_CASES],
    ids=[case_id for case_id, _ in PARAMETER_FILE_ERROR_CASES],
)
def test_application_rejects_invalid_parameter_input_files(
    submission_command: tuple[str, ...],
    parameter_input_content: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        submission_command,
        input_gcode="",
        parameter_input_content=parameter_input_content,
        tmp_path=tmp_path,
    )
