from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0 A0.0 B0.0 C0.0\nG54\n"

LinearMotionErrorCase = tuple[str, str]

LINEAR_MOTION_ERROR_CASES: list[LinearMotionErrorCase] = [
    # G0 requires at least one axis word.
    (
        "g0-omits-all-axis-words",
        ZERO_OFFSET_P1_SETUP + "G90\n" + "G0\n",
    ),
    # G1 requires at least one axis word.
    (
        "g1-omits-all-axis-words",
        ZERO_OFFSET_P1_SETUP + "G90\n" + "G1\n",
    ),
    # In inverse time feed mode, every G1 motion line must include F.
    (
        "g1-inverse-time-motion-missing-f",
        ZERO_OFFSET_P1_SETUP + "G93\n" + "G1 X1.0\n",
    ),
    # The same inverse-time rule applies when G1 motion is implicit from modal state.
    (
        "implicit-g1-inverse-time-motion-missing-f",
        ZERO_OFFSET_P1_SETUP + "G93\n" + "G1 X1.0 F2.0\n" + "X2.0\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md sections 3.5.1 and 3.5.2 for the
# requirement that G0/G1 include at least one axis word, and section 3.5.19
# for the inverse-time feed rule requiring F on every G1/G2/G3 motion line.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in LINEAR_MOTION_ERROR_CASES],
    ids=[case_id for case_id, _ in LINEAR_MOTION_ERROR_CASES],
)
def test_application_rejects_invalid_linear_motion_commands(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
