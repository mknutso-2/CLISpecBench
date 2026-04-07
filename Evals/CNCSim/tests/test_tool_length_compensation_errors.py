from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input

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
    # RS274 section 3.5.11: the H number may not be larger than the number of
    # carousel slots.
    (
        "g43-rejects-h-larger-than-carousel-slots",
        "G43 H7\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.5.11 "Tool Length Offsets --
# G43 and G49" for the explicit H-number error conditions covered here.
@pytest.mark.parametrize(
    ("input_gcode", "carousel_slots"),
    [
        (input_gcode, 6 if case_id == "g43-rejects-h-larger-than-carousel-slots" else None)
        for case_id, input_gcode in TOOL_LENGTH_COMPENSATION_ERROR_CASES
    ],
    ids=[case_id for case_id, _ in TOOL_LENGTH_COMPENSATION_ERROR_CASES],
)
def test_application_rejects_invalid_tool_length_compensation_usage(
    submission_command: tuple[str, ...],
    input_gcode: str,
    carousel_slots: int | None,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        submission_command,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
