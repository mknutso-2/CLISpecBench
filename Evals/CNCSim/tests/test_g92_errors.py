from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input

G92ErrorCase = tuple[str, str]

G92_ERROR_CASES: list[G92ErrorCase] = [
    # RS274 section 3.5.18 says at least one axis word must be used with G92.
    (
        "g92-without-axis-words",
        "G92\n",
    ),
]


@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in G92_ERROR_CASES],
    ids=[case_id for case_id, _ in G92_ERROR_CASES],
)
def test_application_rejects_invalid_g92_usage(
    submission_command: tuple[str, ...],
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
