from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

CoordinateSystemSelectionErrorCase = tuple[str, str]

COORDINATE_SYSTEM_SELECTION_ERROR_CASES: list[CoordinateSystemSelectionErrorCase] = [
    ("g54-with-cutter-radius-compensation-active", "G41 D1\nG54\n"),
    ("g55-with-cutter-radius-compensation-active", "G41 D1\nG55\n"),
    ("g56-with-cutter-radius-compensation-active", "G41 D1\nG56\n"),
    ("g57-with-cutter-radius-compensation-active", "G41 D1\nG57\n"),
    ("g58-with-cutter-radius-compensation-active", "G41 D1\nG58\n"),
    ("g59-with-cutter-radius-compensation-active", "G41 D1\nG59\n"),
    ("g59-1-with-cutter-radius-compensation-active", "G41 D1\nG59.1\n"),
    ("g59-2-with-cutter-radius-compensation-active", "G41 D1\nG59.2\n"),
    ("g59-3-with-cutter-radius-compensation-active", "G41 D1\nG59.3\n"),
]


# RS274 section 3.5.13 says it is an error if one of G54 through G59.3 is used
# while cutter radius compensation is on.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in COORDINATE_SYSTEM_SELECTION_ERROR_CASES],
    ids=[case_id for case_id, _ in COORDINATE_SYSTEM_SELECTION_ERROR_CASES],
)
def test_application_rejects_coordinate_system_selection_with_cutter_compensation_active(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
