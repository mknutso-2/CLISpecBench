from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

ParameterErrorCase = tuple[str, str]

PARAMETER_ERROR_CASES: list[ParameterErrorCase] = [
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting must evaluate to an integer in 1..5399.
    (
        "parameter-setting-index-too-low",
        "#0=1\n",
    ),
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting must evaluate to an integer in 1..5399.
    (
        "parameter-setting-index-too-high",
        "#5400=1\n",
    ),
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting must evaluate to an integer in 1..5399.
    (
        "parameter-setting-index-non-integer",
        "#1.5=1\n",
    ),
    # RS274 section 3.3.2.2 "Parameter Value":
    # the parameter index in a read must evaluate to an integer in 1..5399.
    (
        "parameter-read-index-too-low",
        "G0 X#0\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md sections 3.3.2.2 "Parameter Value",
# 3.3.3 "Parameter Setting", and Appendix E. This file covers only
# spec-defined invalid parameter usage. Expressions such as X[1+2], parameter
# settings like #1=[2+3], and repeated # indirection like ##2 are spec-valid
# and therefore are intentionally not asserted as failures here.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in PARAMETER_ERROR_CASES],
    ids=[case_id for case_id, _ in PARAMETER_ERROR_CASES],
)
def test_application_rejects_invalid_parameter_usage(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
