from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input

WordRepeatErrorCase = tuple[str, str]

WORD_REPEAT_ERROR_CASES: list[WordRepeatErrorCase] = [
    ("a-word", "G0 A1.0 A2.0\n"),
    ("b-word", "G0 B1.0 B2.0\n"),
    ("c-word", "G0 C1.0 C2.0\n"),
    ("d-word", "G41 D1 D2\n"),
    ("f-word", "G1 F10 F20 X1.0\n"),
    ("h-word", "G43 H1 H2\n"),
    ("i-word", "G17 G2 X1.0 Y0.0 I1.0 I2.0 J0.0\n"),
    ("j-word", "G17 G2 X1.0 Y0.0 I1.0 J0.0 J1.0\n"),
    ("k-word", "G18 G2 X1.0 Z0.0 I1.0 K0.0 K1.0\n"),
    ("l-word", "G10 L2 L2 P1 X0.0\n"),
    ("p-word", "G10 L2 P1 P2 X0.0\n"),
    ("r-word", "G17 G2 X1.0 Y0.0 R1.0 R2.0\n"),
    ("s-word", "S100 S100\n"),
    ("t-word", "T1 T2\n"),
    ("x-word", "G0 X1.0 X2.0\n"),
    ("y-word", "G0 Y1.0 Y1.0\n"),
    ("z-word", "G0 Z1.0 Z2.0\n"),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.5 "Item Repeats": for legal
# letters other than G and M, a line may have only one word beginning with that
# letter. These cases cover each supported non-G/M word letter.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in WORD_REPEAT_ERROR_CASES],
    ids=[case_id for case_id, _ in WORD_REPEAT_ERROR_CASES],
)
def test_application_rejects_repeated_non_modal_word_letters(
    submission_command: tuple[str, ...],
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
