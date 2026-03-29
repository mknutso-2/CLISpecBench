from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

UnitsErrorCase = tuple[str, str]

UNITS_ERROR_CASES: list[UnitsErrorCase] = [
    # RS274 Appendix B.5: cannot change units with cutter radius compensation on.
    (
        "g20-with-cutter-radius-compensation-active",
        "G41 D1\n"
        "G20\n",
    ),
    # RS274 Appendix B.5: cannot change units with cutter radius compensation on.
    (
        "g21-with-cutter-radius-compensation-active",
        "G41 D1\n"
        "G21\n",
    ),
]


@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in UNITS_ERROR_CASES],
    ids=[case_id for case_id, _ in UNITS_ERROR_CASES],
)
def test_application_rejects_invalid_unit_changes(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
