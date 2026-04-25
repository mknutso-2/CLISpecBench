from __future__ import annotations

import math
from pathlib import Path

import pytest

from rs274_support import run_rs274

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 6.0 rougher
2 2 0.0 10.0 finisher
"""


# Spec reading for the first straight cutter-radius-compensation move:
#
# 1. Appendix B.1.1 says current_x/current_y track the center of the
#    tool tip. The payload reports that compensated tool-tip center as
#    machine_position.
# 2. Appendix B.2.3 says G41/G42 on the same line as motion turns
#    compensation on before the motion is made.
# 3. Sections 3.5.1 and 3.5.2 define G0 and G1 as linear motions and both
#    defer CRC motion to Appendix B. Therefore Appendix B.6's first
#    straight-move construction applies to first compensated G0 and G1 moves.
# 4. Appendix B.2.4 says D1 selects tool-table slot 1. Slot 1 has diameter
#    6, so the active cutter radius is r = 3.
# 5. For the explicit first-straight-move cases below, the current tool
#    center is C = (0, 0), and the programmed contour endpoint is P = (5, 0).
#    Appendix B.6 makes the destination tool center D = (x, y) the right-angle
#    vertex of triangle C-D-P, with |DP| = r. Thus:
#      (x - 5)^2 + y^2 = 3^2
#      |CD| = sqrt(5^2 - 3^2) = 4, so x^2 + y^2 = 4^2
#    Solving gives x = 3.2 and y = +/-2.4.
# 6. Sections 3.5.10 and B.2.1 select between those two solutions: G41 keeps
#    the cutter left of the programmed path, and G42 keeps it right. For a
#    left-to-right (+X) programmed path, left is +Y and right is -Y.
#
# Therefore the first straight compensated endpoints are:
# - G41: (3.2, 2.4)
# - G42: (3.2, -2.4)
#
# Independence note: cases that are not primarily about that first-move
# construction use a tangential setup instead:
# - G41 starts at (0, 3) and moves to programmed endpoint (5, 0), landing at
#   compensated center (5, 3).
# - G42 starts at (0, -3) and moves to programmed endpoint (5, 0), landing at
#   compensated center (5, -3).
# This still establishes the required CRC state, but it avoids making every
# follow-on, G40, corner, and tool-change assertion depend on the harder
# (3.2, +/-2.4) entry calculation.
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_x",
        "expected_y",
        "expected_crc_mode",
        "expected_d_number",
    ),
    [
        # Appendix B.6 defines the first-move tangent-circle construction for
        # cutter radius compensation.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\n",
            3.2,
            2.4,
            "G41",
            1,
        ),
        # Appendix B.6 first straight move, mirrored for right compensation.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\n",
            3.2,
            -2.4,
            "G42",
            1,
        ),
        # Appendix B.2.4: if D is omitted, the slot number of the tool
        # currently in the spindle is used as the D number.
        (
            "T1\nM6\nG17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 G1 X5.0 Y0.0\n",
            5.0,
            3.0,
            "G41",
            1,
        ),
        # Appendix B.6 first-move construction applies to G0 as well as G1.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G0 X5.0 Y0.0\n",
            5.0,
            3.0,
            "G41",
            1,
        ),
        # RS274 Appendix B.2.4 allows D0; Clarifications.md defines this as
        # active zero-radius compensation. The D number serializes as explicit
        # 0, and the tool-center path remains on the programmed contour.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y0.0\nG41 D0 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            0.0,
            "G41",
            0,
        ),
        # Mirror-image zero-radius case for G42.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y0.0\nG42 D0 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            0.0,
            "G42",
            0,
        ),
        # Appendix B.6: after the entry move, the tool stays tangent to the
        # programmed path. Colinear follow-on from X5 to X6 puts the tool
        # center at (6, 3).
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            3.0,
            "G41",
            1,
        ),
        # Same colinear continuation case, mirrored for right compensation.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y-3.0\nG42 D1 G1 X5.0 Y0.0\nG1 X6.0 Y0.0\n",
            6.0,
            -3.0,
            "G42",
            1,
        ),
        # Appendix B.2.3: G40 on the same line as motion turns compensation
        # off before the move is made.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G1 X5.0 Y0.0\nG40 G1 X7.0 Y0.0\n",
            7.0,
            0.0,
            "G40",
            None,
        ),
        # Appendix B.5.2: after G40, re-enabling compensation treats the
        # next move as a first move again. From current center (5, 3), the
        # restart move runs right-compensated along the -X tangent, so right is
        # +Y and the compensated center lands at (0, 3).
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G1 X5.0 Y0.0\nG40\nG42 D1 G1 X0.0 Y0.0\n",
            0.0,
            3.0,
            "G42",
            1,
        ),
        # Appendix B.6: after G40, subsequent motion starts from the
        # compensated spindle-center position, not the programmed contour
        # point.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G1 X5.0 Y0.0\nG40\nG91 G1 X1.0 Y0.0\n",
            6.0,
            3.0,
            "G40",
            None,
        ),
        # Appendix B: convex corner inserts an arc of tool radius around the
        # corner. This case first extends the horizontal contour so the tool
        # is already following the compensated line y = 3,
        # then turns onto the segment from (10, 0) to (14, -3). That segment
        # has unit direction (4/5, -3/5), so its left normal is (3/5, 4/5).
        # Offsetting the programmed endpoint by radius 3 along that normal
        # gives the expected spindle-center endpoint:
        #   (14, -3) + 3 * (3/5, 4/5) = (15.8, -0.6)
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X14.0 Y-3.0\n",
            15.8,
            -0.6,
            "G41",
            1,
        ),
        # Same convex-corner rule, 90-degree turn from +X to -Y.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X10.0 Y-4.0\n",
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
            "G17 G90 G94 F60\nG0 X0.0 Y-3.0\nG42 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X14.0 Y3.0\n",
            15.8,
            0.6,
            "G42",
            1,
        ),
        # Same convex-corner rule for G42, 90-degree turn from +X to +Y.
        (
            "G17 G90 G94 F60\nG0 X0.0 Y-3.0\nG42 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X10.0 Y4.0\n",
            13.0,
            4.0,
            "G42",
            1,
        ),
        # Appendix B.5: changing tools while CRC is on keeps the original
        # radius until G40.
        (
            "T1\nM6\nG17 G90 G94 F60\nG0 X0.0 Y3.0\nG41 G1 X5.0 Y0.0\nT2\nM6\nG1 X6.0 Y0.0\n",
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
# These cases pick center-format G17 arcs with auxiliary center O = (0, 0)
# and tool radius r = 3 so the compensated endpoints are easy to audit, and
# they cover both side-selection geometries:
# - Outside-tangent (G42-right CCW or G41-left CW): aux radius 4, tool outside, so the
#   tool-center radius is 4 + 3 = 7. Programmed endpoints are the quarter-
#   circle points (0, ±4).
# - Inside-tangent (G41 CCW or G42 CW): aux radius 10, tool inside, so the
#   tool-center radius is 10 - 3 = 7. Programmed endpoints are (0, ±10).
# In every first-arc case the compensated tool-center endpoint is on the
# radius-7 circle around the origin at (0, ±7); subsequent-arc cases land
# at (-7, 0). The same expected endpoints apply whether the auxiliary arc
# is programmed in center format (I/J) or radius format (R). In radius
# format, R names the path (traveled) arc radius (7), not the auxiliary
# arc radius (4 or 10) — §3.5.3 explicitly defers to Appendix B under CRC,
# so "the arc" of §3.5.3 refers to the path the tool traces.
# Assume you'd like to perform a CCW arc move where the tool tip cuts a
# radius-7 path with a radius-3 tool, starting at (7, 0) and ending at
# (0, 7). With CRC enabled via G42 (tool right of programmed contour),
# §B.6's auxiliary-arc construction places the programmed contour at
# radius 4 around (0, 0), so the spec is clear that the input is
# G42 G3 X0.0 Y4.0 J0.0. What is NOT clear is what value R and I take.
#
# §3.5.3 says: "If cutter radius compensation is active, the motion
# will differ from what is described here. See Appendix B." That
# sentence defers the *motion* to Appendix B but does not redefine
# the *input semantics* of R/I/J under CRC, and Appendix B describes
# the geometric construction without ever explicitly restating what
# R/I/J mean — which is what leaves the following ambiguity open.
#
# Compounding this, every CRC example in the spec (Tables 12 and 13,
# §B.4) enables CRC with a straight (G1) move and only uses arcs
# *after* CRC is already active. §B.6 textually accommodates "if the
# first move after cutter radius compensation has been turned on is
# an arc," but no example demonstrates it — so the very case these
# tests probe (G2/G3 as the entry move under CRC) is described in
# prose but never illustrated, which is part of why the R/I/J
# semantics for it are unsettled.
#
# Three readings are defensible:
#
# - Path-arc reading: R names the radius of the path the tool tip
#   actually traces (R=7), and I names the offset from the current
#   tool-tip location to the path-arc center (I=-7).
#   This is consistent with R and I/J retaining their non-CRC meanings
#   (radius and offset to center of the arc the tool traces), with
#   X/Y reinterpreted as the programmed contour endpoint per §B.6.
#
# - Contour reading with I/J relative to the tool-tip: R names the
#   radius of the programmed/auxiliary arc (R=4 in this outside-tangent
#   case; R=10 in the inside-tangent case where Y=10 is programmed
#   instead), but I still names the offset from the current tool-tip
#   location to the shared center (I=-7 in either case, since at the
#   first move the tool-tip and the contour-current coincide). §B.1.1
#   notes that the world model tracks the tool-tip center under CRC,
#   which makes the tool-tip a natural referent for "current location"
#   here, though it is not explicitly required by §3.5.3.2.
#   This would be consistent with the idea that the arc R is a programmed
#   as though CRC is already active, but the I/J offsets are programmed
#   as though CRC is not active.
#
# - Contour reading with I/J relative to a tangent-point on the aux
#   arc: R is the auxiliary-arc radius as above, and I names the
#   offset from the tangent point on the aux arc to the aux-arc
#   center (I=-4 outside-tangent, I=-10 inside-tangent).
#   This would be consistent with the idea that the programming the arc
#   on CRC enabling is the same as programming the arc once CRC is
#   already active.
#
# §B.6 + §3.5.3 + §B.1.1 do not unambiguously settle which reading
# is intended.
#
# This is why the following text is in prompt/docs/Clarifications.md
# (picking the path-arc reading: R and I/J keep their non-CRC meanings,
# X/Y is reinterpreted per §B.6 as the programmed contour endpoint,
# preserving the simplest semantic continuity with non-CRC arcs):
#
# > Under cutter radius compensation, on a G2/G3 arc move — whether
# > the move is the entry move (first compensated motion after G41 or
# > G42) or a continuation move:
# >  - X, Y name the programmed contour endpoint (the auxiliary-arc
# >    endpoint per §B.6), not the position the tool tip will reach.
# >  - R names the radius of the path the tool tip actually traces
# >    (the "generated arc" per §B.6, which shares its center with
# >    the auxiliary arc).
# >  - I, J are offsets from the current tool-tip location (per
# >    §B.1.1's world-model convention) to that shared center — not
# >    from the previous programmed contour endpoint.

CRC_ARC_CASES = [
    # the side per §3.5.10 + §4.3.11).
    (
        # From §3.5.3.2
        # "In the center format, the coordinates of the end point of the arc in the selected plane
        # are specified along with the offsets of the center of the arc from the current location."
        # Per §B.6, the "auxiliary arc" lies on the circle centered at (0, 0) with radius 4.
        # Thus this command results in the tool traveling CCW from (7, 0) to (0, 7) with the center
        # of the arc at (0, 0).
        "g42-ccw-first-center-format-arc-move-tangent-outside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        # Same as above, but now with G41 to stay "inside" the auxiliary arc which requires changing
        # Y from 4 to 10.
        # The "auxiliary arc" from Appendix B.6 lies on the circle centered at (0, 0) with radius
        # 10.
        "g41-ccw-first-center-format-arc-move-tangent-inside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G3 X0.0 Y10.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        # From §3.5.3.1
        # "In the radius format, the coordinates of the end point of the arc in the selected plane
        # are specified along with the radius of the arc"
        # Per §B.6, the "auxiliary arc" lies on the circle centered at (0, 0) with radius 4. The
        # R value names the radius of the path (traveled) arc the tool tip cuts (7), not the
        # auxiliary arc radius (4).
        # Thus this command results in the tool traveling CCW from (7, 0) to (0, 7) with the center
        # of the arc at (0, 0).
        "g42-ccw-first-radius-format-arc-move-tangent-outside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 R7.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        # Same as above, but now with G41 to stay "inside" the auxiliary arc which requires changing
        # Y from 4 to 10.
        # The "auxiliary arc" from Appendix B.6 lies on the circle centered at (0, 0) with radius
        # 10. The R value still names the path (traveled) arc radius (7), not the auxiliary arc
        # radius (10).
        "g41-ccw-first-radius-format-arc-move-tangent-inside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G3 X0.0 Y10.0 R7.0\n",
        {"x": 0.0, "y": 7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        # An argument could be made that this test should be removed per Writing Tests:
        # Golden Rule 3: Independent tests.
        # However, I'm not sure how else to easily test that the arc move *after* the first
        # behaves properly.
        "g42-subsequent-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\nG3 X-4.0 Y0.0 I0.0 J-7.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        # An argument could be made that this test should be removed per Writing Tests:
        # Golden Rule 3: Independent tests.
        # However, I'm not sure how else to easily test that the arc move *after* the first
        # behaves properly.
        "g42-subsequent-radius-format-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G3 X0.0 Y4.0 I-7.0 J0.0\nG3 X-4.0 Y0.0 R7.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        # CW mirror of g42-ccw-first-center-format-arc-move-tangent-outside-arc.
        # Per §B.6, the "auxiliary arc" lies on the circle centered at (0, 0) with radius 4.
        # Thus this command results in the tool traveling CW from (7, 0) to (0, -7) with the center
        # of the arc at (0, 0).
        "g41-cw-first-center-format-arc-move-tangent-outside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        # CW mirror of g41-ccw-first-center-format-arc-move-tangent-inside-arc. G42 stays "inside"
        # the auxiliary arc which requires changing Y from -4 to -10.
        # The "auxiliary arc" from Appendix B.6 lies on the circle centered at (0, 0) with radius
        # 10.
        "g42-cw-first-center-format-arc-move-tangent-inside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G2 X0.0 Y-10.0 I-7.0 J0.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        # CW mirror of g42-ccw-first-radius-format-arc-move-tangent-outside-arc.
        # Per §B.6, the "auxiliary arc" lies on the circle centered at (0, 0) with radius 4. The
        # R value names the radius of the path (traveled) arc the tool tip cuts (7), not the
        # auxiliary arc radius (4).
        "g41-cw-first-radius-format-arc-move-tangent-outside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 R7.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        # CW mirror of g41-ccw-first-radius-format-arc-move-tangent-inside-arc. G42 stays "inside"
        # the auxiliary arc which requires changing Y from -4 to -10.
        # The "auxiliary arc" from Appendix B.6 lies on the circle centered at (0, 0) with radius
        # 10. The R value still names the path (traveled) arc radius (7), not the auxiliary arc
        # radius (10).
        "g42-cw-first-radius-format-arc-move-tangent-inside-arc",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG42 D1 G2 X0.0 Y-10.0 R7.0\n",
        {"x": 0.0, "y": -7.0, "z": 0.0},
        "G42",
        1,
    ),
    (
        # An argument could be made that this test should be removed per Writing Tests:
        # Golden Rule 3: Independent tests.
        # However, I'm not sure how else to easily test that the arc move *after* the first
        # behaves properly.
        "g41-subsequent-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\nG2 X-4.0 Y0.0 I0.0 J7.0\n",
        {"x": -7.0, "y": 0.0, "z": 0.0},
        "G41",
        1,
    ),
    (
        # An argument could be made that this test should be removed per Writing Tests:
        # Golden Rule 3: Independent tests.
        # However, I'm not sure how else to easily test that the arc move *after* the first
        # behaves properly.
        "g41-subsequent-radius-format-arc-move",
        "G17 G90 G94\nG0 X7.0 Y0.0\nG41 D1 G2 X0.0 Y-4.0 I-7.0 J0.0\nG2 X-4.0 Y0.0 R7.0\n",
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
