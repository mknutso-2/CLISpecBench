from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

ToolSelectionErrorCase = tuple[str, str]

TOOL_SELECTION_ERROR_CASES: list[ToolSelectionErrorCase] = [
    (
        "t-rejects-non-integer-tool-number",
        "T1.5\n",
    ),
    (
        "t-rejects-negative-tool-number",
        "T-1\n",
    ),
]


# RS274 section 3.7.3 says the T number gives the changer slot of the tool,
# and section 3.6.3 likewise describes it as an integer slot number. The same
# section also makes it an error to use a T number larger than the number of
# carousel slots, but CNCSim does not currently define that slot-count value in
# the harness contract, so this file only covers the explicit integer and
# non-negative requirements.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in TOOL_SELECTION_ERROR_CASES],
    ids=[case_id for case_id, _ in TOOL_SELECTION_ERROR_CASES],
)
def test_application_rejects_invalid_tool_selection_words(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
