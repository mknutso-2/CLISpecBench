from __future__ import annotations

from pathlib import Path

import pytest

from rs274_support import run_rs274_invalid_input

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
    (
        "t-rejects-slot-number-larger-than-carousel-slots",
        "T7\n",
    ),
]


# RS274 section 3.7.3 says the T number gives the changer slot of the tool,
# and section 3.6.3 likewise describes it as an integer slot number. The same
# section also makes it an error to use a T number larger than the number of
# carousel slots.
@pytest.mark.parametrize(
    ("input_gcode", "carousel_slots"),
    [
        (input_gcode, 6 if case_id == "t-rejects-slot-number-larger-than-carousel-slots" else None)
        for case_id, input_gcode in TOOL_SELECTION_ERROR_CASES
    ],
    ids=[case_id for case_id, _ in TOOL_SELECTION_ERROR_CASES],
)
def test_application_rejects_invalid_tool_selection_words(
    submission_command: tuple[str, ...],
    input_gcode: str,
    carousel_slots: int | None,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
