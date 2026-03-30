from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.rs274_parameters import (
    G92_A_OFFSET_PARAMETER,
    G92_B_OFFSET_PARAMETER,
    G92_C_OFFSET_PARAMETER,
    G92_X_OFFSET_PARAMETER,
)
from swe_buildbench.cncsim.test_support import (
    get_parameter_value,
    run_cncsim,
    with_default_rotary_axes,
)


# See RS274 section 3.5.18 "Coordinate System Offsets -- G92, G92.1, G92.2,
# G92.3". These tests cover the explicitly specified translational and rotary
# axis-offset behavior that CNCSim exposes in the payload.
def test_g92_sets_offsets_and_backing_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0\n"
            "G92 X7.0\n"
            f"#1=#{G92_X_OFFSET_PARAMETER}\n"
            "G0 X9.0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == -3.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 6.0, "y": -3.0, "z": 0.0})


def test_g92_ignores_incremental_distance_mode(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0\n"
            "G91\n"
            "G92 X7.0\n"
            "G90\n"
            "G0 X7.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == -3.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 4.0, "y": 0.0, "z": 0.0})


def test_g92_accumulates_existing_offsets(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0\n"
            "G92 X7.0\n"
            "G92 X9.0\n"
            f"#1=#{G92_X_OFFSET_PARAMETER}\n"
            "G0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == -5.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 4.0, "y": -5.0, "z": 0.0})


def test_g92_affects_all_coordinate_systems(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G10 L2 P2 X10.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0\n"
            "G92 X7.0\n"
            "G55\n"
            "G0 X7.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == -3.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 14.0, "y": 0.0, "z": 0.0})


def test_g92_1_cancels_offsets_and_zeros_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0\n"
            "G92 X7.0\n"
            "G92.1\n"
            f"#1=#{G92_X_OFFSET_PARAMETER}\n"
            "G0 X7.0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == 0.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 7.0, "y": 0.0, "z": 0.0})


def test_g92_2_cancels_offsets_without_zeroing_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X4.0\n"
            "G92 X7.0\n"
            "G92.2\n"
            f"#1=#{G92_X_OFFSET_PARAMETER}\n"
            "G0 X7.0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == -3.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 7.0, "y": -3.0, "z": 0.0})


def test_g92_3_restores_offsets_from_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            f"#{G92_X_OFFSET_PARAMETER}=-3.0\n"
            "G92.3\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X7.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_X_OFFSET_PARAMETER) == -3.0
    assert payload["machine_position"] == with_default_rotary_axes({"x": 4.0, "y": 0.0, "z": 0.0})


def test_g92_sets_rotary_offsets_and_backing_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 A0.0 B0.0 C0.0\n"
            "G54\n"
            "G90\n"
            "G0 A10.0 B20.0 C30.0\n"
            "G92 A1.0 B2.0 C3.0\n"
            f"#1=#{G92_A_OFFSET_PARAMETER}\n"
            f"#2=#{G92_B_OFFSET_PARAMETER}\n"
            f"#3=#{G92_C_OFFSET_PARAMETER}\n"
            "G0 A2.0 B3.0 C4.0 X#1 Y#2 Z#3\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_A_OFFSET_PARAMETER) == 9.0
    assert get_parameter_value(payload, G92_B_OFFSET_PARAMETER) == 18.0
    assert get_parameter_value(payload, G92_C_OFFSET_PARAMETER) == 27.0
    assert payload["machine_position"] == with_default_rotary_axes(
        {"x": 9.0, "y": 18.0, "z": 27.0, "a": 11.0, "b": 21.0, "c": 31.0}
    )


def test_g92_1_cancels_rotary_offsets_and_zeros_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 A0.0 B0.0 C0.0\n"
            "G54\n"
            "G90\n"
            "G0 A10.0 B20.0 C30.0\n"
            "G92 A1.0 B2.0 C3.0\n"
            "G92.1\n"
            "G0 A7.0 B8.0 C9.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, G92_A_OFFSET_PARAMETER) == 0.0
    assert get_parameter_value(payload, G92_B_OFFSET_PARAMETER) == 0.0
    assert get_parameter_value(payload, G92_C_OFFSET_PARAMETER) == 0.0
    assert payload["machine_position"] == with_default_rotary_axes(
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 7.0, "b": 8.0, "c": 9.0}
    )
