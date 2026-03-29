from __future__ import annotations

import math
from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 6.0 rougher
"""


# RS274 Appendix B.1.1 says the world model tracks the center of the tool tip
# while cutter compensation is active. Appendix B.6 defines the first straight
# compensated move by constructing a line through the programmed endpoint that
# is tangent to the initial tool circle.
#
# These cases use:
# - current tool center C = (0, 0)
# - programmed contour endpoint P = (5, 0)
# - tool radius r = 3
#
# Let D = (x, y) be the compensated destination of the tool center. Appendix
# B.6 says the destination point of the tool tip is found as the center of a
# circle of the same radius tangent to the tangent line at the programmed
# point. In this case, that means:
# - the destination tool circle has center D and radius 3
# - the programmed point P = (5, 0) lies on that destination tool circle
# - so the distance from D to P is exactly 3
#
# Writing that with the distance formula gives:
# - sqrt((x - 5)^2 + (y - 0)^2) = 3
# - (x - 5)^2 + y^2 = 9
#
# For this specific geometry, the same tangent construction also implies that
# the tool-center move length is:
# - |CD| = sqrt(5^2 - 3^2) = 4
# so:
# - x^2 + y^2 = 16
#
# Solving the two equations gives x = 3.2 and |y| = 2.4, so the two possible
# compensated endpoints are (3.2, 2.4) and (3.2, -2.4). G41 selects the upper
# one and G42 selects the lower one for this left-to-right move.
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_x",
        "expected_y",
        "expected_crc_mode",
        "expected_d_number",
    ),
    [
        # Appendix B.6 first straight move, with the tool kept left of the
        # programmed path.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # Appendix B.6 first straight move, mirrored for right compensation.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G42 D1 G1 X5.0 Y0.0\n",
            3.2,
            -2.4,
            "G42",
            1,
        ),
        # RS274 Appendix B.2.4: if D is omitted, the slot number of the tool
        # currently in the spindle is used as the D number.
        (
            "T1\n"
            "M6\n"
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 G1 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # RS274 Appendix B.6: after the entry move, the tool stays tangent to
        # the programmed path on the selected side. Extending the same
        # left-to-right contour from X5 to X6 puts the tool center at (6, 3).
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n"
            "G1 X6.0 Y0.0\n",
            6.0,
            3.0,
            "G41",
            1,
        ),
        # Same colinear continuation case, mirrored for right compensation.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G42 D1 G1 X5.0 Y0.0\n"
            "G1 X6.0 Y0.0\n",
            6.0,
            -3.0,
            "G42",
            1,
        ),
        # Appendix B.2.3: G40 on the same line as motion turns compensation
        # off before the move is made.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n"
            "G40 G1 X7.0 Y0.0\n",
            7.0,
            0.0,
            "G40",
            None,
        ),
    ],
    ids=[
        "g41-first-straight-move-left",
        "g42-first-straight-move-right",
        "g41-omitted-d-uses-tool-in-spindle",
        "g41-colinear-follow-on-move-left",
        "g42-colinear-follow-on-move-right",
        "g40-on-motion-line-disables-comp-before-motion",
    ],
)
def test_application_tracks_cutter_radius_compensated_spindle_center(
    built_executable_path: Path,
    input_gcode: str,
    expected_x: float,
    expected_y: float,
    expected_crc_mode: str,
    expected_d_number: int | None,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert math.isclose(payload["machine_position"]["x"], expected_x, abs_tol=1e-4)
    assert math.isclose(payload["machine_position"]["y"], expected_y, abs_tol=1e-4)
    assert math.isclose(payload["machine_position"]["z"], 0.0, abs_tol=1e-4)
    assert payload["active_modal_g_codes"]["7"] == expected_crc_mode
    assert payload["cutter_radius_compensation_number"] == expected_d_number
