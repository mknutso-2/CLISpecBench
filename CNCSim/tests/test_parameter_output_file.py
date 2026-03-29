from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.rs274_parameters import (
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
    REQUIRED_NON_ROTATIONAL_PARAMETER_INDICES,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
    coordinate_system_xyz_parameter_indices,
)
from swe_buildbench.cncsim.test_support import (
    build_parameter_file,
    run_cncsim_with_parameter_output,
)


def required_non_rotational_parameter_indices() -> set[int]:
    return set(REQUIRED_NON_ROTATIONAL_PARAMETER_INDICES)


def parse_parameter_output_file(parameter_output: str) -> dict[int, float]:
    lines = parameter_output.splitlines()
    blank_line_indices = [index for index, line in enumerate(lines) if line == ""]
    assert len(blank_line_indices) == 1
    blank_line_index = blank_line_indices[0]
    assert blank_line_index >= 1

    data_lines = lines[blank_line_index + 1 :]
    assert data_lines

    parsed_entries: list[tuple[int, float]] = []
    for line in data_lines:
        parts = line.split()
        assert len(parts) == 2
        parsed_entries.append((int(parts[0]), float(parts[1])))

    indices = [parameter_index for parameter_index, _ in parsed_entries]
    assert indices == sorted(indices)
    return dict(parsed_entries)


# RS274 section 3.2.1 says the interpreter writes a parameter file when it
# exits. The file must contain the required non-rotational Table 2 parameters
# and parameter numbers must be arranged in ascending order.
def test_application_writes_required_parameter_output_file_entries(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload, parameter_output = run_cncsim_with_parameter_output(
        built_executable_path,
        input_gcode="",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None

    parsed_entries = parse_parameter_output_file(parameter_output)
    assert required_non_rotational_parameter_indices() <= set(parsed_entries)
    assert parsed_entries[SELECTED_COORDINATE_SYSTEM_PARAMETER] == 1.0


# RS274 section 3.2.1 explicitly says any parameter included in the file read
# by the interpreter will be included in the file it writes when it exits.
def test_application_preserves_input_parameters_in_output_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload, parameter_output = run_cncsim_with_parameter_output(
        built_executable_path,
        input_gcode="",
        parameter_input_content=build_parameter_file({1: 4.25, 150: 7.5}),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None

    parsed_entries = parse_parameter_output_file(parameter_output)
    assert parsed_entries[1] == 4.25
    assert parsed_entries[150] == 7.5


# technical-requirements-prompt.md requires the written parameter file to
# include parameters set during execution. This checks both a direct parameter
# setting and parameter-backed state changes such as selected coordinate
# system, coordinate-system offsets, and G92 offsets.
def test_application_writes_execution_updates_to_output_parameter_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    cs2_x_parameter, cs2_y_parameter, cs2_z_parameter = coordinate_system_xyz_parameter_indices(2)
    completed, payload, parameter_output = run_cncsim_with_parameter_output(
        built_executable_path,
        input_gcode=(
            "#1=5.5\n"
            "G55\n"
            "G10 L2 P2 X10.0 Y20.0 Z30.0\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "G92 X4.0 Y5.0 Z6.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None

    parsed_entries = parse_parameter_output_file(parameter_output)
    assert parsed_entries[1] == 5.5
    assert parsed_entries[SELECTED_COORDINATE_SYSTEM_PARAMETER] == 2.0
    assert parsed_entries[cs2_x_parameter] == 10.0
    assert parsed_entries[cs2_y_parameter] == 20.0
    assert parsed_entries[cs2_z_parameter] == 30.0
    assert parsed_entries[G92_X_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_Y_OFFSET_PARAMETER] == -3.0
    assert parsed_entries[G92_Z_OFFSET_PARAMETER] == -3.0
