from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.rs274_parameters import (
    G28_HOME_X_PARAMETER,
    G28_HOME_Y_PARAMETER,
    G28_HOME_Z_PARAMETER,
    G30_HOME_X_PARAMETER,
    G30_HOME_Y_PARAMETER,
    G30_HOME_Z_PARAMETER,
)
from swe_buildbench.cncsim.test_support import (
    build_parameter_file,
    get_parameter_value,
    run_cncsim,
)


# RS274 section 3.5.8 says G28 and G30 use home positions defined by
# parameters 5161-5166 and 5181-5186, that those parameter values are in the
# absolute coordinate system, and that all axis words on the G28/G30 line are
# optional. Section 3.2.1 says the interpreter reads the parameter file at
# startup. The payload exposes only the final controlled-point position, so
# these tests assert the final home endpoint rather than the intermediate
# traverse segment.
def test_application_returns_to_g28_home_loaded_from_input_parameter_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "G28\n"
        ),
        parameter_input_content=build_parameter_file(
            {
                G28_HOME_X_PARAMETER: 40.0,
                G28_HOME_Y_PARAMETER: 50.0,
                G28_HOME_Z_PARAMETER: 60.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 40.0, "y": 50.0, "z": 60.0}
    assert get_parameter_value(payload, G28_HOME_X_PARAMETER) == 40.0
    assert get_parameter_value(payload, G28_HOME_Y_PARAMETER) == 50.0
    assert get_parameter_value(payload, G28_HOME_Z_PARAMETER) == 60.0


def test_application_returns_to_g28_home_after_intermediate_programmed_position(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0 Y5.0 Z6.0\n"
            "G28 X1.0 Y2.0 Z3.0\n"
        ),
        parameter_input_content=build_parameter_file(
            {
                G28_HOME_X_PARAMETER: 40.0,
                G28_HOME_Y_PARAMETER: 50.0,
                G28_HOME_Z_PARAMETER: 60.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 40.0, "y": 50.0, "z": 60.0}
    assert get_parameter_value(payload, G28_HOME_X_PARAMETER) == 40.0
    assert get_parameter_value(payload, G28_HOME_Y_PARAMETER) == 50.0
    assert get_parameter_value(payload, G28_HOME_Z_PARAMETER) == 60.0


def test_application_returns_to_g30_secondary_home_loaded_from_input_parameter_file(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0 Y5.0 Z6.0\n"
            "G30 X1.0 Y2.0 Z3.0\n"
        ),
        parameter_input_content=build_parameter_file(
            {
                G30_HOME_X_PARAMETER: 70.0,
                G30_HOME_Y_PARAMETER: 80.0,
                G30_HOME_Z_PARAMETER: 90.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 70.0, "y": 80.0, "z": 90.0}
    assert get_parameter_value(payload, G30_HOME_X_PARAMETER) == 70.0
    assert get_parameter_value(payload, G30_HOME_Y_PARAMETER) == 80.0
    assert get_parameter_value(payload, G30_HOME_Z_PARAMETER) == 90.0


def test_application_returns_to_g30_secondary_home_without_axis_words(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "G30\n"
        ),
        parameter_input_content=build_parameter_file(
            {
                G30_HOME_X_PARAMETER: 70.0,
                G30_HOME_Y_PARAMETER: 80.0,
                G30_HOME_Z_PARAMETER: 90.0,
            }
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 70.0, "y": 80.0, "z": 90.0}
    assert get_parameter_value(payload, G30_HOME_X_PARAMETER) == 70.0
    assert get_parameter_value(payload, G30_HOME_Y_PARAMETER) == 80.0
    assert get_parameter_value(payload, G30_HOME_Z_PARAMETER) == 90.0
