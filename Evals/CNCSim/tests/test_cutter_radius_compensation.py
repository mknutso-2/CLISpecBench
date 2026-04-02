from __future__ import annotations

import math
from pathlib import Path

import pytest

from cncsim_support import run_cncsim

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 6.0 rougher
2 2 0.0 10.0 finisher
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
        # The same Appendix B.6 first-move construction applies to G0 as well
        # as G1, so a rapid first move to the same programmed point reaches
        # the same compensated spindle-center endpoint.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G0 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # RS274 Appendix B.2.4 also allows D0; with zero radius, compensation
        # stays logically on but the spindle center remains on the programmed
        # contour.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D0 G1 X5.0 Y0.0\n"
            "G1 X6.0 Y0.0\n",
            6.0,
            0.0,
            "G41",
            0,
        ),
        # Mirror-image zero-radius case for G42.
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G42 D0 G1 X5.0 Y0.0\n"
            "G1 X6.0 Y0.0\n",
            6.0,
            0.0,
            "G42",
            0,
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
        # RS274 Appendix B.5.2 says that after turning compensation off, the
        # next time it is turned on the following move is treated as a first
        # move again. Starting from the prior compensated point (3.2, 2.4),
        # the right-comp first-move construction to programmed point
        # (8.2, 2.4) gives the shifted endpoint (6.4, 0.0).
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n"
            "G40\n"
            "G42 D1 G1 X8.2 Y2.4\n",
            6.4,
            0.0,
            "G42",
            1,
        ),
        # RS274 Appendix B.6: after G40, no special exit move occurs, and the
        # next move behaves as if the previous move had placed the tool at its
        # current spindle-center position. So this incremental move starts from
        # the compensated point (3.2, 2.4), not from the programmed contour
        # point (5.0, 0.0).
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n"
            "G40\n"
            "G91 G1 X1.0 Y0.0\n",
            4.2,
            2.4,
            "G40",
            None,
        ),
        # RS274 Appendix B says that after the entry moves, the tool remains
        # tangent to the programmed path, and a convex corner inserts an arc of
        # tool radius around the corner. This case first extends the horizontal
        # contour so the tool is already following the compensated line y = 3,
        # then turns onto the segment from (10, 0) to (14, -3). That segment
        # has unit direction (4/5, -3/5), so its left normal is (3/5, 4/5).
        # Offsetting the programmed endpoint by radius 3 along that normal
        # gives the expected spindle-center endpoint:
        #   (14, -3) + 3 * (3/5, 4/5) = (15.8, -0.6)
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n"
            "G1 X10.0 Y0.0\n"
            "G1 X14.0 Y-3.0\n",
            15.8,
            -0.6,
            "G41",
            1,
        ),
        # Same convex-corner rule, but with a 90-degree turn from +X to -Y.
        # Once the tool is established on the compensated horizontal path, the
        # vertical programmed segment from (10, 0) to (10, -4) has left normal
        # (1, 0), so the spindle-center endpoint is simply:
        #   (10, -4) + 3 * (1, 0) = (13, -4)
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 D1 G1 X5.0 Y0.0\n"
            "G1 X10.0 Y0.0\n"
            "G1 X10.0 Y-4.0\n",
            13.0,
            -4.0,
            "G41",
            1,
        ),
        # G42 convex continuation, using the mirror-image diagonal turn from
        # (10, 0) to (14, 3). That segment has unit direction (4/5, 3/5), so
        # its right normal is (3/5, -4/5). Offsetting by radius 3 gives:
        #   (14, 3) + 3 * (3/5, -4/5) = (15.8, 0.6)
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G42 D1 G1 X5.0 Y0.0\n"
            "G1 X10.0 Y0.0\n"
            "G1 X14.0 Y3.0\n",
            15.8,
            0.6,
            "G42",
            1,
        ),
        # Same convex-corner rule for G42, but with a 90-degree turn from +X
        # to +Y. The vertical programmed segment from (10, 0) to (10, 4) has
        # right normal (1, 0), so the spindle-center endpoint is:
        #   (10, 4) + 3 * (1, 0) = (13, 4)
        (
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G42 D1 G1 X5.0 Y0.0\n"
            "G1 X10.0 Y0.0\n"
            "G1 X10.0 Y4.0\n",
            13.0,
            4.0,
            "G42",
            1,
        ),
        # RS274 Appendix B.5 says changing tools while compensation is on is
        # not an error, and the radius in use stays the one from when
        # compensation was turned on until G40. Tool 2 has a different
        # diameter, so if the interpreter incorrectly switched radii here the
        # final Y value would be 5 instead of 3.
        (
            "T1\n"
            "M6\n"
            "G17 G90 G94\n"
            "G0 X0.0 Y0.0\n"
            "G41 G1 X5.0 Y0.0\n"
            "T2\n"
            "M6\n"
            "G1 X6.0 Y0.0\n",
            6.0,
            3.0,
            "G41",
            1,
        ),
    ],
    ids=[
        "g41-first-straight-move-left",
        "g42-first-straight-move-right",
        "g41-omitted-d-uses-tool-in-spindle",
        "g41-first-rapid-move-left",
        "g41-d0-keeps-spindle-center-on-programmed-path",
        "g42-d0-keeps-spindle-center-on-programmed-path",
        "g41-colinear-follow-on-move-left",
        "g42-colinear-follow-on-move-right",
        "g40-on-motion-line-disables-comp-before-motion",
        "g40-then-g42-restarts-with-a-first-move",
        "g40-follow-on-move-starts-from-current-spindle-center",
        "g41-convex-corner-follow-on-move",
        "g41-convex-90-degree-corner-follow-on-move",
        "g42-convex-corner-follow-on-move",
        "g42-convex-90-degree-corner-follow-on-move",
        "tool-change-while-comp-on-keeps-original-radius",
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
    """Check CRC line/rapid endpoint behavior visible in the payload.

    Governing sections: RS274 Appendix B.6, B.2.3, B.2.4, B.5, and B.5.2.
    """
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


# RS274 Appendix B.6 says that if the first move after turning cutter
# compensation on is an arc, the generated tool-center arc is derived from an
# auxiliary programmed arc with the programmed center point and programmed end
# point, while keeping the tool tangent to that auxiliary arc throughout.
#
# These cases pick center-format G17 arcs with center O = (0, 0) and tool
# radius r = 3 so the compensated endpoints are easy to audit:
# - for G42 on a CCW arc or G41 on a CW arc, the tool is on the outside of the
#   programmed arc, so the tool-center radius is 4 + 3 = 7
# - the programmed endpoints are the quarter-circle points (0, 4) and (-4, 0)
# - the compensated tool-center endpoints are therefore (0, 7) and (-7, 0),
#   or the mirrored CW values (0, -7) and (-7, 0)
# The same expected endpoints apply whether that auxiliary arc is programmed in
# center format (I/J) or radius format (R).
CRC_ARC_CASES = [
    (
        "g42-first-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g42-first-radius-format-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G42 D1 G3 X0.0 Y4.0 R4.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g42-subsequent-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\n"
        "G3 X-4.0 Y0.0 I0.0 J-4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g42-subsequent-radius-format-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\n"
        "G3 X-4.0 Y0.0 R4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g41-first-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        "g41-first-radius-format-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G41 D1 G2 X0.0 Y-4.0 R4.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        "g41-subsequent-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\n"
        "G2 X-4.0 Y0.0 I0.0 J4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        "g41-subsequent-radius-format-arc-move",
        "G17 G90 G94\n"
        "G0 X7.0 Y0.0\n"
        "G41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\n"
        "G2 X-4.0 Y0.0 R4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G41",
        1,
    ),
]


@pytest.mark.parametrize(
    ("input_gcode", "expected_machine_position", "expected_crc_mode", "expected_d_number"),
    [
        (
            input_gcode,
            expected_machine_position,
            expected_crc_mode,
            expected_d_number,
        )
        for (
            _,
            input_gcode,
            expected_machine_position,
            expected_crc_mode,
            expected_d_number,
        ) in CRC_ARC_CASES
    ],
    ids=[case_id for case_id, _, _, _, _ in CRC_ARC_CASES],
)
def test_application_tracks_cutter_radius_compensated_arc_endpoints(
    built_executable_path: Path,
    input_gcode: str,
    expected_machine_position: dict[str, float],
    expected_crc_mode: str,
    expected_d_number: int,
    tmp_path: Path,
) -> None:
    """Check the final tool-center endpoints of the compensated arc cases.

    Governing section: RS274 Appendix B.6.
    """
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert math.isclose(
        payload["machine_position"]["x"], expected_machine_position["x"], abs_tol=1e-4
    )
    assert math.isclose(
        payload["machine_position"]["y"], expected_machine_position["y"], abs_tol=1e-4
    )
    assert math.isclose(
        payload["machine_position"]["z"], expected_machine_position["z"], abs_tol=1e-4
    )
    assert payload["active_modal_g_codes"]["7"] == expected_crc_mode
    assert payload["cutter_radius_compensation_number"] == expected_d_number
