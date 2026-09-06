from __future__ import annotations

import math
from pathlib import Path

from rs274_parameters import (
    G92_A_OFFSET_PARAMETER,
    G92_B_OFFSET_PARAMETER,
    G92_C_OFFSET_PARAMETER,
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
    REQUIRED_PARAMETER_INDICES,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
    coordinate_system_xyz_parameter_indices,
    coordinate_system_xyzabc_parameter_indices,
)
from rs274_support import (
    build_parameter_file,
    parameter_output_entries,
    run_rs274_with_parameter_output,
)


# RS274 section 3.2.1 says the interpreter writes a parameter file when it
# exits. The file must contain all Table 2 parameters for the six supported
# axes, including A/B/C, in strictly ascending order (no duplicate indices).
def test_application_writes_required_parameter_output_file_entries(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload, parameter_output = run_rs274_with_parameter_output(
        submission_command,
        input_gcode="",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None

    # Section 3.2.1: zero or more header lines, one blank separator,
    # ordered unique indices in 1..5400, and optional comment columns.
    lines = parameter_output.splitlines()
    separators = [index for index, line in enumerate(lines) if not line.strip()]
    assert len(separators) == 1
    assert lines[separators[0]] == ""  # Section 3.2.1 excludes spaces/tabs here.
    data_lines = lines[separators[0] + 1 :]
    assert data_lines and all(len(line.split()) >= 2 for line in data_lines)
    entries = parameter_output_entries(parameter_output)
    indices = [index for index, _ in entries]
    assert indices == sorted(set(indices))
    assert all(1 <= index <= 5400 for index in indices)
    assert all(math.isfinite(value) for _, value in entries)
    parsed_entries = dict(entries)
    assert set(REQUIRED_PARAMETER_INDICES) <= set(parsed_entries)
    assert parsed_entries[SELECTED_COORDINATE_SYSTEM_PARAMETER] == 1.0


# RS274 section 3.2.1 explicitly says any parameter included in the file read
# by the interpreter will be included in the file it writes when it exits.
def test_application_preserves_input_parameters_in_output_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload, parameter_output = run_rs274_with_parameter_output(
        submission_command,
        input_gcode="",
        parameter_input_content=build_parameter_file({1: 4.25, 150: 7.5}),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None

    parsed_entries = dict(parameter_output_entries(parameter_output))
    assert parsed_entries[1] == 4.25
    assert parsed_entries[150] == 7.5


# technical-requirements-prompt.md requires the written parameter file to
# include parameters set during execution. This checks both a direct parameter
# setting and parameter-backed state changes such as selected coordinate
# system, coordinate-system offsets, and G92 offsets.
def test_application_writes_execution_updates_to_output_parameter_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    cs2_x_parameter, cs2_y_parameter, cs2_z_parameter = coordinate_system_xyz_parameter_indices(2)
    (_, _, _, cs2_a_parameter, cs2_b_parameter, cs2_c_parameter) = (
        coordinate_system_xyzabc_parameter_indices(2)
    )
    completed, payload, parameter_output = run_rs274_with_parameter_output(
        submission_command,
        input_gcode=(
            "#1=5.5\n"
            "G55\n"
            "G10 L2 P2 X10.0 Y20.0 Z30.0 A40.0 B50.0 C60.0\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0 A4.0 B5.0 C6.0\n"
            "G92 X4.0 Y5.0 Z6.0 A7.0 B8.0 C9.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None

    parsed_entries = dict(parameter_output_entries(parameter_output))
    assert parsed_entries[1] == 5.5
    assert parsed_entries[SELECTED_COORDINATE_SYSTEM_PARAMETER] == 2.0
    assert parsed_entries[cs2_x_parameter] == 10.0
    assert parsed_entries[cs2_y_parameter] == 20.0
    assert parsed_entries[cs2_z_parameter] == 30.0
    assert parsed_entries[cs2_a_parameter] == 40.0
    assert parsed_entries[cs2_b_parameter] == 50.0
    assert parsed_entries[cs2_c_parameter] == 60.0
    assert parsed_entries[G92_X_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_Y_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_Z_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_A_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_B_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_C_OFFSET_PARAMETER] == -3.0
