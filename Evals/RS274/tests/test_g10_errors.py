from __future__ import annotations

from pathlib import Path

import pytest

from rs274_support import run_rs274_invalid_input

G10ErrorCase = tuple[str, str]

G10_ERROR_CASES: list[G10ErrorCase] = [
    # G10 L2 P requires a coordinate-system number in the range 1 to 9.
    (
        "g10-rejects-out-of-range-p",
        "G10 L2 P10 X1.0\n",
    ),
    # G10 L2 P requires an integer coordinate-system number.
    (
        "g10-rejects-non-integer-p",
        "G10 L2 P1.5 X1.0\n",
    ),
]


# See RS274/prompt/docs/RS274NGC.md section 3.5.5: G10 L2 P requires an
# integer P number in the range 1 to 9.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in G10_ERROR_CASES],
    ids=[case_id for case_id, _ in G10_ERROR_CASES],
)
def test_application_rejects_invalid_g10_commands(
    submission_command: tuple[str, ...],
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
