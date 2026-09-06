from __future__ import annotations

from pathlib import Path

from rs274_support import mapping_field, run_rs274


# See RS274/prompt/docs/RS274NGC.md sections 3.2.1 "Parameters",
# 3.3.3 "Parameter Setting", and D.8.4 "Parameter Buffering". These tests
# observe parameter writes through required machine-position output: the
# technical requirements permit any parameter to be omitted from the sparse
# final "parameters" object, so its presence cannot be a behavioral precondition.
def test_application_applies_parameter_settings(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#1=1.5\n#2=2.5\n#3=3.5\nG90 G0 X#1 Y#2 Z#3\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    position = mapping_field(payload, "machine_position")
    assert position.get("x") == 1.5
    assert position.get("y") == 2.5
    assert position.get("z") == 3.5


def test_parameter_settings_are_buffered_until_after_line_execution(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#3=15\n#3=6 #4=#3\nG90 G0 X#3 Y#4\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    position = mapping_field(payload, "machine_position")
    assert position.get("x") == 6.0
    assert position.get("y") == 15.0


def test_repeated_parameter_setting_uses_the_last_value(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#3=15\n#3=6 #3=8\nG90 G0 X#3\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "machine_position").get("x") == 8.0


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
    # Observe the selected system via its required modal field; #5220 itself
    # need not be reported in the final parameters object.
    assert mapping_field(payload, "active_modal_g_codes").get("12") == "G54"
