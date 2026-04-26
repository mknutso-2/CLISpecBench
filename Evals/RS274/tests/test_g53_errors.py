from __future__ import annotations

from pathlib import Path

import pytest

from rs274_support import run_rs274_invalid_input

G53ErrorCase = tuple[str, str]

G53_ERROR_CASES: list[G53ErrorCase] = [
    # RS274 section 3.5.12: G53 is an error unless G0 or G1 is active.
    (
        "g53-without-g0-or-g1-active",
        "G17\nG53 X1.0\n",
    ),
    # RS274 section 3.5.12: at least one axis word must be used on a G53 line.
    (
        "g53-omits-all-axis-words",
        "G0 X0.0\nG53\n",
    ),
]


# See RS274/prompt/docs/RS274NGC.md section 3.5.12 "Move in Absolute
# Coordinates -- G53" for the explicit error conditions covered here.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in G53_ERROR_CASES],
    ids=[case_id for case_id, _ in G53_ERROR_CASES],
)
def test_application_rejects_invalid_g53_usage(
    submission_command: tuple[str, ...],
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
