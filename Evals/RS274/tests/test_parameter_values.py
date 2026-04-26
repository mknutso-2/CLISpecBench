from __future__ import annotations

from pathlib import Path

from rs274_parameters import SELECTED_COORDINATE_SYSTEM_PARAMETER
from rs274_support import get_parameter_value, mapping_field, run_rs274


# See RS274/prompt/docs/RS274NGC.md sections 3.2.1 "Parameters",
# 3.3.3 "Parameter Setting", and D.8.4 "Parameter Buffering". These tests
# stay focused on directly serialized parameter state and parameter write
# semantics. Feature-specific behavior from passing parameters to words or
# G-codes belongs in the corresponding feature test files.
def test_application_serializes_parameter_settings_in_payload(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#1=1.5\n#2=2.5\n#3=3.5\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert get_parameter_value(payload, 1) == 1.5
    assert get_parameter_value(payload, 2) == 2.5
    assert get_parameter_value(payload, 3) == 3.5


def test_parameter_settings_are_buffered_until_after_line_execution(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#3=15\n#3=6 #4=#3\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert get_parameter_value(payload, 3) == 6.0
    assert get_parameter_value(payload, 4) == 15.0


def test_repeated_parameter_setting_uses_the_last_value(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#3=15\n#3=6 #3=8\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert get_parameter_value(payload, 3) == 8.0


def test_startup_uses_the_default_selected_coordinate_system_parameter(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode="",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    # RS274 section 3.2.1 Table 2 gives the default value 5220=1.0, and
    # section 3.2.2 says startup selects the active coordinate system from 5220.
    assert get_parameter_value(payload, SELECTED_COORDINATE_SYSTEM_PARAMETER) == 1.0


def test_payload_reports_parameters_sparsely(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode="",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    parameters = mapping_field(payload, "parameters")
    assert isinstance(parameters, dict)
    assert str(SELECTED_COORDINATE_SYSTEM_PARAMETER) in parameters
    assert "1" not in parameters
