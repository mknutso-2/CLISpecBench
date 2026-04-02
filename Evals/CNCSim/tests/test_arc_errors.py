from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0 A0.0 B0.0 C0.0\nG54\n"

ArcErrorCase = tuple[str, str]

ARC_ERROR_CASES: list[ArcErrorCase] = [
    (
        "g17-radius-format-omits-selected-plane-axes",
        ZERO_OFFSET_P1_SETUP
        + "G17\n"
        + "G90\n"
        + "G0 X1.0 Y0.0 Z5.0\n"
        + "G2 Z4.0 R1.0\n",  # missing X or Y axis in G17 plane
    ),
    (
        "g18-center-format-omits-center-offsets",
        ZERO_OFFSET_P1_SETUP
        + "G18\n"
        + "G90\n"
        + "G0 X1.0 Y5.0 Z0.0\n"
        + "G2 X0.0 Y4.0 Z-1.0\n",  # missing I or K axis in G18 plane
    ),
    # Radius-format arcs may not end at the current point.
    (
        "g19-radius-format-reuses-current-endpoint",
        ZERO_OFFSET_P1_SETUP
        + "G19\n"
        + "G90\n"
        + "G0 X5.0 Y1.0 Z0.0\n"
        + "G3 X5.0 Y1.0 Z0.0 R1.0\n",
    ),
    # RS274 section 3.5.19: inverse-time feed mode requires F on every G2 line.
    (
        "g2-inverse-time-motion-missing-f",
        ZERO_OFFSET_P1_SETUP
        + "G17\n"
        + "G90\n"
        + "G0 X1.0 Y0.0 Z5.0\n"
        + "G93\n"
        + "G2 X0.0 Y-1.0 Z4.0 I-1.0 J0.0\n",
    ),
    # RS274 section 3.5.19: the same inverse-time rule applies to implicit G3 motion.
    (
        "implicit-g3-inverse-time-motion-missing-f",
        ZERO_OFFSET_P1_SETUP
        + "G17\n"
        + "G90\n"
        + "G0 X1.0 Y0.0 Z5.0\n"
        + "G93\n"
        + "G3 X0.0 Y1.0 Z6.0 I-1.0 J0.0 F2.0\n"
        + "X-1.0 Y0.0 I0.0 J-1.0\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.5.3.1 for radius-format arc
# errors and section 3.5.3.2 for center-format arc errors in the selected
# plane. Section 3.5.19 adds the inverse-time feed requirement for every G2/G3
# line when G93 is active.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in ARC_ERROR_CASES],
    ids=[case_id for case_id, _ in ARC_ERROR_CASES],
)
def test_application_rejects_invalid_arc_commands(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
