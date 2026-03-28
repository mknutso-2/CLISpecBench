from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from swe_buildbench.cncsim.modal_groups import (
    GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
    GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION,
    GCODE_MODAL_GROUP_DISTANCE_MODE,
    GCODE_MODAL_GROUP_FEED_RATE_MODE,
    GCODE_MODAL_GROUP_MOTION,
    GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
    GCODE_MODAL_GROUP_PLANE_SELECTION,
    GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
    GCODE_MODAL_GROUP_TOOL_LENGTH_OFFSET,
    GCODE_MODAL_GROUP_UNITS,
)


def _active_gcode_group_case(input_gcode: str, expected_active_modal_codes: dict[str, str]) -> Any:
    group_number, active_gcode = next(iter(expected_active_modal_codes.items()))
    return pytest.param(
        input_gcode,
        expected_active_modal_codes,
        id=f"group-{group_number}-{active_gcode.lower()}",
    )


@pytest.mark.parametrize(
    ("input_gcode", "expected_active_modal_codes"),
    [
        _active_gcode_group_case(
            "G0 X0\n"
            "G1 X0\n",
            {GCODE_MODAL_GROUP_MOTION: "G1"},
        ),
        _active_gcode_group_case(
            "G17\n"
            "G18\n",
            {GCODE_MODAL_GROUP_PLANE_SELECTION: "G18"},
        ),
        _active_gcode_group_case(
            "G90\n"
            "G91\n",
            {GCODE_MODAL_GROUP_DISTANCE_MODE: "G91"},
        ),
        _active_gcode_group_case(
            "G94\n"
            "G93\n",
            {GCODE_MODAL_GROUP_FEED_RATE_MODE: "G93"},
        ),
        _active_gcode_group_case(
            "G20\n"
            "G21\n",
            {GCODE_MODAL_GROUP_UNITS: "G21"},
        ),
        _active_gcode_group_case(
            "G40\n"
            "G41\n",
            {GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION: "G41"},
        ),
        _active_gcode_group_case(
            "G49\n"
            "G43 H0\n",
            {GCODE_MODAL_GROUP_TOOL_LENGTH_OFFSET: "G43"},
        ),
        _active_gcode_group_case(
            "G98\n"
            "G99\n",
            {GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES: "G99"},
        ),
        _active_gcode_group_case(
            "G54\n"
            "G55\n",
            {GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION: "G55"},
        ),
        _active_gcode_group_case(
            "G61\n"
            "G64\n",
            {GCODE_MODAL_GROUP_PATH_CONTROL_MODE: "G64"},
        ),
    ],
)
def test_application_tracks_active_gcode_groups(
    built_executable_path: Path,
    input_gcode: str,
    expected_active_modal_codes: dict[str, str],
    tmp_path: Path,
) -> None:
    completed, payload = _run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None

    for group_number, active_gcode in expected_active_modal_codes.items():
        assert payload["active_modal_codes"][group_number] == active_gcode


def _run_cncsim(
    executable_path: Path,
    *,
    input_gcode: str,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    input_path.write_text(input_gcode, encoding="utf-8")

    completed = subprocess.run(
        [str(executable_path), "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert output_path.is_file(), completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return completed, payload
