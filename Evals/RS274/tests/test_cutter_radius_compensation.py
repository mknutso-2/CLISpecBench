from __future__ import annotations

import math
from pathlib import Path

import pytest

from rs274_support import run_rs274

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
#
# PASS-RATE NOTE (2026-04-18): across ~255 runs spanning every model, the
# "first-move" cases (g41/g42-first-straight-move-*, g41-omitted-d-uses-
# tool-in-spindle, g41-first-rapid-move-left) and the continuation cases
# (colinear-follow-on, convex-corner, convex-90-degree, g40-then-g42-restarts,
# g40-follow-on-move-starts-from-current-spindle-center,
# tool-change-while-comp-on-keeps-original-radius) each passed ≤5 times. Two
# related causes (see CHANGELOG "Proposed"):
#   - Entry-move ambiguity: §B.6 describes the tangent-circle construction
#     in prose and Figure 7, but G41/G42 side selection ("on the appropriate
#     side") and G0-as-first-move (not called out in §B.6) both require
#     inference. g41-first-rapid-move-left additionally requires applying
#     the B.6 construction to G0, which §B.6 does not explicitly cover.
#   - Cascade: the continuation and G40-transition cases are behaviorally
#     straightforward given §B.6's "keeps the tool tangent to the programmed
#     path on the appropriate side" rule, but every one of them depends on
#     first computing the entry-move endpoint correctly. A model that flips
#     the side-selection convention once fails every dependent test, making
#     these tests score the single entry-move mistake N times — the cascade
#     pattern warned against in skills/eval-authoring/SKILL.md.
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_x",
        "expected_y",
        "expected_crc_mode",
        "expected_d_number",
    ),
    [
        # In preliminary testing, no model passes this test.
        # Appendix B.6 defines the first-move tangent-circle construction for
        # cutter radius compensation.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.6 first straight move, mirrored for right compensation.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\n",
            3.2,
            -2.4,
            "G42",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.2.4: if D is omitted, the slot number of the tool
        # currently in the spindle is used as the D number.
        (
            "T1\nM6\nG17 G90 G94\nG0 X0.0 Y0.0\nG41 G1 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.6 first-move construction applies to G0 as well as G1.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G0 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # RS274 Appendix B.2.4 also allows D0; with zero radius, compensation
        # stays logically on but the spindle center remains on the programmed
        # contour.
        #
        # PASS-RATE NOTE (2026-04-18): the two D0 cases below each passed
        # 33 / 255 times across all models, and they cascade into
        # test_program_end_reset.py::test_application_turns_cutter_compensation_off_on_m2_and_m30
        # (26 / 255 each, M2 and M30). The expected_d_number here is 0
        # (explicit zero), but technical-requirements-prompt.md says the
        # serialized field is "the active D number, or null if no explicit
        # cutter radius compensation number is active." D0 fits both
        # readings — "D=0 is explicit" and "D0 deactivates the CRC
        # number" — and the prompt does not disambiguate. See CHANGELOG
        # "Proposed".
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D0 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            0.0,
            "G41",
            0,
        ),
        # Mirror-image zero-radius case for G42.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D0 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            0.0,
            "G42",
            0,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.6: after the entry move, the tool stays tangent to the
        # programmed path. Colinear follow-on from X5 to X6 puts the tool
        # center at (6, 3).
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            3.0,
            "G41",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Same colinear continuation case, mirrored for right compensation.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            -3.0,
            "G42",
            1,
        ),
        # Appendix B.2.3: G40 on the same line as motion turns compensation
        # off before the move is made.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG40 G1 X7.0 Y0.0\n",
            7.0,
            0.0,
            "G40",
            None,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.5.2: after G40, re-enabling compensation treats the
        # next move as a first move again.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG40\nG42 D1 G1 X8.2 Y2.4\n",
            6.4,
            0.0,
            "G42",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.6: after G40, subsequent motion starts from the
        # compensated spindle-center position, not the programmed contour
        # point.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG40\nG91 G1 X1.0 Y0.0\n",
            4.2,
            2.4,
            "G40",
            None,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B: convex corner inserts an arc of tool radius around the
        # corner. This case first extends the horizontal contour so the tool
        # is already following the compensated line y = 3,
        # then turns onto the segment from (10, 0) to (14, -3). That segment
        # has unit direction (4/5, -3/5), so its left normal is (3/5, 4/5).
        # Offsetting the programmed endpoint by radius 3 along that normal
        # gives the expected spindle-center endpoint:
        #   (14, -3) + 3 * (3/5, 4/5) = (15.8, -0.6)
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X14.0 Y-3.0\n",
            15.8,
            -0.6,
            "G41",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Same convex-corner rule, 90-degree turn from +X to -Y.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X10.0 Y-4.0\n",
            13.0,
            -4.0,
            "G41",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # G42 convex continuation, using the mirror-image diagonal turn from
        # (10, 0) to (14, 3). That segment has unit direction (4/5, 3/5), so
        # its right normal is (3/5, -4/5). Offsetting by radius 3 gives:
        #   (14, 3) + 3 * (3/5, -4/5) = (15.8, 0.6)
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X14.0 Y3.0\n",
            15.8,
            0.6,
            "G42",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Same convex-corner rule for G42, 90-degree turn from +X to +Y.
        (
            "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X10.0 Y4.0\n",
            13.0,
            4.0,
            "G42",
            1,
        ),
        # In preliminary testing, no model passes this test.
        # Appendix B.5: changing tools while CRC is on keeps the original
        # radius until G40.
        (
            "T1\nM6\nG17 G90 G94\nG0 X0.0 Y0.0\nG41 G1 X5.0 Y0.0\nT2\nM6\nG1 X6.0 Y0.0\n",
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
    submission_command: tuple[str, ...],
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
    completed, payload = run_rs274(
        submission_command,
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
#
# PASS-RATE NOTE (2026-04-18): across ~255 runs spanning every model, each of
# these 8 cases had 0 or 1 passes. A review of the spec vs. the test inputs
# identified four interpretive leaps required to reach the expected answers
# that are not stated in the prose spec (see CHANGELOG "Proposed"):
#   1. §B.6's auxiliary-arc rule must silently override §3.5.3.2's
#      "distance from current point to center differs from distance to end
#      point" error check. Inputs below have current-point (7,0) at radius 7
#      and programmed endpoint (0,±4) at radius 4 — a 3-unit mismatch that
#      §3.5.3.2 normally rejects.
#   2. For the radius-format cases the programmed arc is geometrically
#      impossible under the normal R rule (chord √65 ≈ 8.06 > 2r = 8). The
#      tests assume R becomes the auxiliary-arc radius, but §B.6 never
#      states this and §3.5.3.1 says nothing about CRC.
#   3. Under CRC, I/J offset from the programmed contour point, not from
#      the compensated tool center. §3.5.3.2 only says "the current
#      location"; under CRC the two diverge.
#   4. G41/G42 side selection on a CCW arc (G42 CCW ⇒ outside) must be
#      inferred from the tangent-direction convention; §B.6 only says "on
#      the appropriate side."
# These are defensible choices the reference implementation encodes, but a
# model working only from the prose docs cannot uniquely recover them.
CRC_ARC_CASES = [
    # In preliminary testing, no model passes any of the 8 arc CRC cases below.
    # Appendix B.6 defines compensated arc geometry: the tool-center arc radius
    # is the programmed arc radius +/- the tool radius depending on which side
    # of the contour the tool is on.
    (
        "g42-first-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g42-first-radius-format-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 R4.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g42-subsequent-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\nG3 X-4.0 Y0.0 I0.0 J-4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g42-subsequent-radius-format-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\nG3 X-4.0 Y0.0 R4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        "g41-first-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        "g41-first-radius-format-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 R4.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        "g41-subsequent-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\nG2 X-4.0 Y0.0 I0.0 J4.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        "g41-subsequent-radius-format-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\nG2 X-4.0 Y0.0 R4.0\n",
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
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_machine_position: dict[str, float],
    expected_crc_mode: str,
    expected_d_number: int,
    tmp_path: Path,
) -> None:
    """Check the final tool-center endpoints of the compensated arc cases.

    Governing section: RS274 Appendix B.6.
    """
    completed, payload = run_rs274(
        submission_command,
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
