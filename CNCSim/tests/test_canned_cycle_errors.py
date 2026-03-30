from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG17\nG94\n"

CANNNED_CYCLE_ERROR_CASES: list[tuple[str, str]] = [
    (
        "g80-rejects-axis-words-without-a-group-0-axis-gcode",
        ZERO_OFFSET_P1_SETUP + "G80 X1.0\n",
    ),
    (
        "g81-requires-r-on-first-use",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 F7.0\n",
    ),
    (
        "g81-requires-the-depth-word-on-first-use",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 R2.8 F7.0\n",
    ),
    (
        "g81-rejects-r-below-depth",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z2.8 R1.5 F7.0\n",
    ),
    (
        "active-g81-rejects-a-following-line-without-x-y-or-z",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n"
        + "R3.0\n",
    ),
    (
        "canned-cycles-reject-inverse-time-mode",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G93\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n",
    ),
    (
        "canned-cycles-reject-cutter-radius-compensation",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G0 X0.0 Y0.0 Z0.0\n"
        + "G41 D0 G1 X1.0 Y0.0 F1.0\n"
        + "G81 X4.0 Y5.0 Z-1.0 R1.0 F7.0\n",
    ),
    (
        "canned-cycle-l-must-be-positive",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 L0 F7.0\n",
    ),
    (
        "canned-cycle-l-must-be-an-integer",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 L1.5 F7.0\n",
    ),
    (
        "g82-requires-nonnegative-p",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G82 X4.0 Y5.0 Z1.5 R2.8 P-0.5 F7.0\n",
    ),
    (
        "g83-requires-positive-q",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G83 X4.0 Y5.0 Z1.5 R2.8 Q0.0 F7.0\n",
    ),
]


# RS274 section 3.5.15 makes axis words an error when G80 is active unless a
# modal-group-0 G-code using axis words is programmed. Section 3.5.16 adds the
# canned-cycle-specific errors checked here:
# - X/Y/Z may not all be omitted during a canned cycle
# - R is sticky and must therefore be programmed on first use
# - the selected-plane depth word is sticky and must therefore be programmed on
#   first use of a given cycle
# - L must be a positive integer
# - inverse time feed and cutter radius compensation are invalid with canned
#   cycles
# - in the XY plane, R may not be less than Z
# Section 3.5.16.3 requires non-negative P for G82, and section 3.5.16.4
# requires positive Q for G83.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in CANNNED_CYCLE_ERROR_CASES],
    ids=[case_id for case_id, _ in CANNNED_CYCLE_ERROR_CASES],
)
def test_application_rejects_invalid_canned_cycle_usage(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
