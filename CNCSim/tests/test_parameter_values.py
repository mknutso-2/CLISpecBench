from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.test_support import run_cncsim


# See CNCSim/prompt/docs/RS274NGC.md sections 3.2.1 "Parameters",
# 3.3.2.2 "Parameter Value", 3.3.3 "Parameter Setting", and D.8.4
# "Parameter Buffering". These tests stay indirect: they verify parameter
# behavior through existing motion and state outputs rather than adding a
# parameter dump to the harness schema.
def test_application_reads_parameters_in_axis_words(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#1=1.5\n"
            "#2=2.5\n"
            "#3=3.5\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X#1 Y#2 Z#3\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 1.5, "y": 2.5, "z": 3.5}


def test_application_reads_parameters_in_feed_spindle_and_tooling_words(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#1=250.0\n"
            "#2=1200.0\n"
            "#3=6\n"
            "#4=7\n"
            "#5=4\n"
            "#6=3\n"
            "F#1\n"
            "S#2 M#6\n"
            "T#3\n"
            "G43 H#4\n"
            "G41 D#5\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["feed_rate"] == 250.0
    assert payload["spindle_speed"] == 1200.0
    assert payload["spindle_direction"] == "CW"
    assert payload["selected_tool"] == 6
    assert payload["tool_length_offset_index"] == 7
    assert payload["cutter_radius_compensation_number"] == 4


def test_application_reads_parameters_in_g_l_p_and_m_words(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#100=10\n"
            "#101=2\n"
            "#102=1\n"
            "#103=54\n"
            "#104=3\n"
            "G#100 L#101 P#102 X3.5 Y0.0 Z0.0\n"
            "G#103\n"
            "G90\n"
            "M#104\n"
            "G0 X1.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 4.5, "y": 0.0, "z": 0.0}
    assert payload["spindle_direction"] == "CW"


def test_parameter_settings_are_buffered_until_after_line_execution(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#3=15\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "#3=6 G0 X#3\n"
            "G0 Y#3\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 15.0, "y": 6.0, "z": 0.0}


def test_repeated_parameter_setting_uses_the_last_value(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#3=15\n"
            "#3=6 #3=8\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X#3\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 8.0, "y": 0.0, "z": 0.0}

def test_startup_uses_the_default_selected_coordinate_system_parameter(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    # RS274 section 3.2.1 Table 2 gives the default value 5220=1.0, and
    # section 3.2.2 says startup selects the active coordinate system from 5220.
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#1=#5220\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G90\n"
            "G0 X#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 1.0, "y": 0.0, "z": 0.0}
