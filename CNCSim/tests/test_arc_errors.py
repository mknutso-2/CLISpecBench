from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\n"

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
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.5.3.1 for radius-format arc
# errors and section 3.5.3.2 for center-format arc errors in the selected
# plane.
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
