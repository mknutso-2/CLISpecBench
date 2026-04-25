from __future__ import annotations

from pathlib import Path

import pytest

from rs274_parameters import (
    G92_A_OFFSET_PARAMETER,
    G92_B_OFFSET_PARAMETER,
    G92_C_OFFSET_PARAMETER,
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
    coordinate_system_xyzabc_parameter_indices,
)
from rs274_support import (
    build_parameter_file,
    get_parameter_value,
    run_rs274,
    run_rs274_invalid_input,
    with_default_rotary_axes,
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
    completed, payload = run_rs274(
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
# starts up, Table 2 defines coordinate-system and G92 stored parameters, and
# section 3.2.2 says parameter 5220 selects the active startup coordinate
# system. Keep these loaded-state checks together so a single parameter-file
# parser defect does not create several independent-looking failures.
def test_application_initializes_startup_state_from_parameter_input_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    (
        cs2_x_parameter,
        cs2_y_parameter,
        cs2_z_parameter,
        cs2_a_parameter,
        cs2_b_parameter,
        cs2_c_parameter,
    ) = coordinate_system_xyzabc_parameter_indices(2)
    completed, payload = run_rs274(
        submission_command,
        input_gcode="G92.3\nG90\nG0 X#1 Y2.0 Z3.0 A4.0 B5.0 C6.0\n",
        parameter_input_content=build_parameter_file(
            {
                1: 4.25,
                SELECTED_COORDINATE_SYSTEM_PARAMETER: 2.0,
                cs2_x_parameter: 10.0,
                cs2_y_parameter: 20.0,
                cs2_z_parameter: 30.0,
                cs2_a_parameter: 40.0,
                cs2_b_parameter: 50.0,
                cs2_c_parameter: 60.0,
                G92_X_OFFSET_PARAMETER: 1.0,
                G92_Y_OFFSET_PARAMETER: 2.0,
                G92_Z_OFFSET_PARAMETER: 3.0,
                G92_A_OFFSET_PARAMETER: 4.0,
                G92_B_OFFSET_PARAMETER: 5.0,
                G92_C_OFFSET_PARAMETER: 6.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    active_modal_g_codes = payload["active_modal_g_codes"]
    assert isinstance(active_modal_g_codes, dict)
    assert active_modal_g_codes["12"] == "G55"
    assert get_parameter_value(payload, 1) == 4.25
    assert get_parameter_value(payload, SELECTED_COORDINATE_SYSTEM_PARAMETER) == 2.0
    assert payload["coordinate_system_offsets"]["2"] == with_default_rotary_axes(
        {"x": 10.0, "y": 20.0, "z": 30.0, "a": 40.0, "b": 50.0, "c": 60.0}
    )
    assert payload["machine_position"] == with_default_rotary_axes(
        {"x": 15.25, "y": 24.0, "z": 36.0, "a": 48.0, "b": 60.0, "c": 72.0}
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
    run_rs274_invalid_input(
        submission_command,
        input_gcode="",
        parameter_input_content=parameter_input_content,
        tmp_path=tmp_path,
    )
