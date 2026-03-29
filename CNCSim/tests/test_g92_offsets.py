from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.test_support import get_parameter_value, run_cncsim


# See RS274 section 3.5.18 "Coordinate System Offsets -- G92, G92.1, G92.2,
# G92.3". These tests cover only the explicit X/Y/Z behavior the current
# simulator supports.
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
            "#1=#5211\n"
            "G0 X9.0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, 5211) == -3.0
    assert payload["machine_position"] == {"x": 6.0, "y": -3.0, "z": 0.0}


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
    assert get_parameter_value(payload, 5211) == -3.0
    assert payload["machine_position"] == {"x": 4.0, "y": 0.0, "z": 0.0}


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
            "#1=#5211\n"
            "G0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, 5211) == -5.0
    assert payload["machine_position"] == {"x": 4.0, "y": -5.0, "z": 0.0}


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
    assert get_parameter_value(payload, 5211) == -3.0
    assert payload["machine_position"] == {"x": 14.0, "y": 0.0, "z": 0.0}


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
            "#1=#5211\n"
            "G0 X7.0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, 5211) == 0.0
    assert payload["machine_position"] == {"x": 7.0, "y": 0.0, "z": 0.0}


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
            "#1=#5211\n"
            "G0 X7.0 Y#1\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert get_parameter_value(payload, 5211) == -3.0
    assert payload["machine_position"] == {"x": 7.0, "y": -3.0, "z": 0.0}


def test_g92_3_restores_offsets_from_parameters(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#5211=-3.0\n"
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
    assert get_parameter_value(payload, 5211) == -3.0
    assert payload["machine_position"] == {"x": 4.0, "y": 0.0, "z": 0.0}
