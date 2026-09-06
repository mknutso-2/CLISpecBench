from __future__ import annotations

from pathlib import Path

from rs274_parameters import (
    G28_HOME_A_PARAMETER,
    G28_HOME_B_PARAMETER,
    G28_HOME_C_PARAMETER,
    G28_HOME_X_PARAMETER,
    G28_HOME_Y_PARAMETER,
    G28_HOME_Z_PARAMETER,
    G30_HOME_A_PARAMETER,
    G30_HOME_B_PARAMETER,
    G30_HOME_C_PARAMETER,
    G30_HOME_X_PARAMETER,
    G30_HOME_Y_PARAMETER,
    G30_HOME_Z_PARAMETER,
)
from rs274_support import (
    run_rs274,
    with_default_rotary_axes,
)


def parameter_assignment_lines(values: dict[int, float]) -> str:
    return "".join(f"#{parameter_index}={value}\n" for parameter_index, value in values.items())


# RS274 section 3.5.8 says G28 and G30 use home positions defined by
# parameters 5161-5166 and 5181-5186, that those parameter values are in the
# absolute coordinate system, and that all axis words on the G28/G30 line are
# optional. Home parameters are set by in-program parameter assignments here so
# these tests do not depend on the parameter-file parser. The payload exposes
# only the final controlled-point position, so these tests assert the final home
# endpoint rather than the intermediate traverse segment.
# Final snapshot parameters may be sparse (technical requirements). Observe
# backing values through parameter reads and required machine positions,
# rather than requiring optional JSON entries in every behavioral case.
def test_application_returns_to_g28_home_set_by_parameters(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G28_HOME_X_PARAMETER: 40.0,
                    G28_HOME_Y_PARAMETER: 50.0,
                    G28_HOME_Z_PARAMETER: 60.0,
                }
            )
            + "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "G28\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 40.0, "y": 50.0, "z": 60.0}
    )


def test_application_returns_to_g28_home_after_intermediate_programmed_position(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G28_HOME_X_PARAMETER: 40.0,
                    G28_HOME_Y_PARAMETER: 50.0,
                    G28_HOME_Z_PARAMETER: 60.0,
                }
            )
            + "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0 Y5.0 Z6.0\n"
            "G28 X1.0 Y2.0 Z3.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 40.0, "y": 50.0, "z": 60.0}
    )


def test_application_returns_to_g30_secondary_home_set_by_parameters(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G30_HOME_X_PARAMETER: 70.0,
                    G30_HOME_Y_PARAMETER: 80.0,
                    G30_HOME_Z_PARAMETER: 90.0,
                }
            )
            + "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0 Y5.0 Z6.0\n"
            "G30 X1.0 Y2.0 Z3.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 70.0, "y": 80.0, "z": 90.0}
    )


def test_application_returns_to_g30_secondary_home_without_axis_words(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G30_HOME_X_PARAMETER: 70.0,
                    G30_HOME_Y_PARAMETER: 80.0,
                    G30_HOME_Z_PARAMETER: 90.0,
                }
            )
            + "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
            "G54\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "G30\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 70.0, "y": 80.0, "z": 90.0}
    )


def test_application_returns_to_g28_rotary_home_set_by_parameters(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G28_HOME_A_PARAMETER: 40.0,
                    G28_HOME_B_PARAMETER: 50.0,
                    G28_HOME_C_PARAMETER: 60.0,
                }
            )
            + "G90\n"
            "G0 A1.0 B2.0 C3.0\n"
            "G28 A4.0 B5.0 C6.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 40.0, "b": 50.0, "c": 60.0}
    )


def test_application_returns_to_g28_rotary_home_without_axis_words(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G28_HOME_A_PARAMETER: 40.0,
                    G28_HOME_B_PARAMETER: 50.0,
                    G28_HOME_C_PARAMETER: 60.0,
                }
            )
            + "G90\n"
            "G0 A1.0 B2.0 C3.0\n"
            "G28\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 40.0, "b": 50.0, "c": 60.0}
    )


def test_application_returns_to_g30_rotary_home_without_axis_words(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G30_HOME_A_PARAMETER: 70.0,
                    G30_HOME_B_PARAMETER: 80.0,
                    G30_HOME_C_PARAMETER: 90.0,
                }
            )
            + "G90\n"
            "G0 A1.0 B2.0 C3.0\n"
            "G30\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 70.0, "b": 80.0, "c": 90.0}
    )


def test_application_returns_to_g30_rotary_home_after_intermediate_programmed_position(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            parameter_assignment_lines(
                {
                    G30_HOME_A_PARAMETER: 70.0,
                    G30_HOME_B_PARAMETER: 80.0,
                    G30_HOME_C_PARAMETER: 90.0,
                }
            )
            + "G90\n"
            "G0 A1.0 B2.0 C3.0\n"
            "G30 A4.0 B5.0 C6.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 70.0, "b": 80.0, "c": 90.0}
    )
