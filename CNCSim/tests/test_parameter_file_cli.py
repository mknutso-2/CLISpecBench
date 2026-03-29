from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import (
    get_parameter_value,
    run_cncsim,
    run_cncsim_invalid_input,
)


def build_parameter_file(overrides: dict[int, float] | None = None) -> str:
    entries: dict[int, float] = {
        5161: 0.0,
        5162: 0.0,
        5163: 0.0,
        5181: 0.0,
        5182: 0.0,
        5183: 0.0,
        5211: 0.0,
        5212: 0.0,
        5213: 0.0,
        5220: 1.0,
    }
    for system_number in range(1, 10):
        base = 5221 + ((system_number - 1) * 20)
        entries[base] = 0.0
        entries[base + 1] = 0.0
        entries[base + 2] = 0.0

    if overrides is not None:
        entries.update(overrides)

    lines = ["RS274 parameter file", ""]
    lines.extend(
        f"{parameter_index} {entries[parameter_index]}"
        for parameter_index in sorted(entries)
    )
    return "\n".join(lines) + "\n"


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
    built_executable_path: Path,
    parameter_input_content: str | None,
    pass_parameter_output: bool,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="G90\nG0 X1.0 Y2.0 Z3.0\n",
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 1.0, "y": 2.0, "z": 3.0}


# RS274 section 3.2.1 says the interpreter reads the parameter file when it
# starts up, and section 3.3.2.2 says parameter values are read from the
# numbered parameter slots.
def test_application_uses_parameter_values_loaded_from_input_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X#1\n",
        parameter_input_content=build_parameter_file({1: 4.25}),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 4.25, "y": 0.0, "z": 0.0}
    assert get_parameter_value(payload, 1) == 4.25


# RS274 section 3.2.2 says startup selects the active coordinate system from
# parameter 5220.
def test_application_uses_selected_coordinate_system_loaded_from_input_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="",
        parameter_input_content=build_parameter_file({5220: 2.0}),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    active_modal_g_codes = payload["active_modal_g_codes"]
    assert isinstance(active_modal_g_codes, dict)
    assert active_modal_g_codes["12"] == "G55"
    assert get_parameter_value(payload, 5220) == 2.0


# RS274 section 3.2.1 says the coordinate-system origin parameters in Table 2
# are required startup state, and section 3.2.2 says the selected coordinate
# system is defined by those stored parameters.
def test_application_initializes_coordinate_system_offsets_from_input_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="G55\nG90\nG0 X1.0 Y2.0 Z3.0\n",
        parameter_input_content=build_parameter_file(
            {
                5241: 10.0,
                5242: 20.0,
                5243: 30.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["coordinate_system_offsets"]["2"] == {"x": 10.0, "y": 20.0, "z": 30.0}
    assert payload["machine_position"] == {"x": 11.0, "y": 22.0, "z": 33.0}


# RS274 section 3.2.1 says parameters 5211-5216 are part of the required
# startup parameter state, and section 3.5.18 says those values define the
# axis offsets used by G92.3.
def test_application_initializes_g92_offsets_from_input_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG92.3\nG90\nG0 X1.0 Y2.0 Z3.0\n",
        parameter_input_content=build_parameter_file(
            {
                5211: 10.0,
                5212: 20.0,
                5213: 30.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 11.0, "y": 22.0, "z": 33.0}


PARAMETER_FILE_ERROR_CASES: list[tuple[str, str]] = [
    (
        "parameter-file-rejects-non-ascending-indices",
        "RS274 parameter file\n\n5162 0.0\n5161 0.0\n",
    ),
    (
        "parameter-file-rejects-out-of-range-index",
        "RS274 parameter file\n\n5400 1.0\n",
    ),
    (
        "parameter-file-rejects-invalid-5220",
        build_parameter_file({5220: 10.0}),
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
    built_executable_path: Path,
    parameter_input_content: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="",
        parameter_input_content=parameter_input_content,
        tmp_path=tmp_path,
    )
