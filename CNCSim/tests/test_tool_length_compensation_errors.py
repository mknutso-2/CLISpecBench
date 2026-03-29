from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

ToolLengthCompensationErrorCase = tuple[str, str]

TOOL_LENGTH_COMPENSATION_ERROR_CASES: list[ToolLengthCompensationErrorCase] = [
    # RS274 section 3.5.11: the H number must be an integer.
    (
        "g43-rejects-non-integer-h",
        "G43 H1.5\n",
    ),
    # RS274 section 3.5.11: the H number must be non-negative.
    (
        "g43-rejects-negative-h",
        "G43 H-1\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.5.11 "Tool Length Offsets --
# G43 and G49" for the explicit H-number error conditions covered here. The
# same section also says it is an error for H to be larger than the number of
# carousel slots, but CNCSim does not currently define that slot-count value in
# the harness contract, so this file does not assert that clause yet.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in TOOL_LENGTH_COMPENSATION_ERROR_CASES],
    ids=[case_id for case_id, _ in TOOL_LENGTH_COMPENSATION_ERROR_CASES],
)
def test_application_rejects_invalid_tool_length_compensation_usage(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
