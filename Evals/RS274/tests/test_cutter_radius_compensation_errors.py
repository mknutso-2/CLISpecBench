from __future__ import annotations

from pathlib import Path

import pytest

from rs274_support import mapping_field, run_rs274, run_rs274_invalid_input

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 6.0 rougher
"""

# RS274 Appendix B.5.4 explicitly defines an error for a D number larger than
# the number of carousel slots.

CRC_ACTIVE_PREFIX = "G17 G90 G94\nG41 D1\n"

PLANE_CODES_INVALID_WHEN_ENABLING_CRC = [
    ("g18", "G18\n"),
    ("g19", "G19\n"),
]

CRC_ENABLE_CODES = [
    ("g41", "G41 D1\n"),
    ("g42", "G42 D1\n"),
]

COORDINATE_SYSTEM_SELECTION_CODES = [
    ("g54", "G54\n"),
    ("g55", "G55\n"),
    ("g56", "G56\n"),
    ("g57", "G57\n"),
    ("g58", "G58\n"),
    ("g59", "G59\n"),
    ("g59-1", "G59.1\n"),
    ("g59-2", "G59.2\n"),
    ("g59-3", "G59.3\n"),
]

GCODE_BODIES_INVALID_WHILE_CRC_IS_ACTIVE = [
    # RS274 Appendix B.5 errors 8 and 9: XZ/YZ plane selection may not be used
    # while cutter radius compensation is on.
    ("g18", "G18\n"),
    ("g19", "G19\n"),
    # RS274 Appendix B.5: unit changes may not be used while cutter radius
    # compensation is on.
    ("g20", "G20\n"),
    ("g21", "G21\n"),
    # RS274 section 3.5.12: G53 may not be used while cutter radius
    # compensation is on.
    ("g53", "G53 G0 X1.0\n"),
    # RS274 Appendix B.5 error 6: G28/G30 may not be used while cutter radius
    # compensation is on.
    ("g28", "G28\n"),
    ("g30", "G30\n"),
    # RS274 Appendix B.5 error 3: probing is not allowed while cutter radius
    # compensation is on.
    ("g38-2", "F10.0\nG38.2 X1.0\n"),
    # RS274 section 3.5.16 explicitly says canned cycles are invalid while
    # cutter radius compensation is active. G81 is used here as a
    # representative supported canned cycle.
    ("g81", "F10.0\nG81 X1.0 Y1.0 Z-1.0 R0.5\n"),
    # RS274 Appendix B.5 error 1 says axis offsets may not be changed while
    # cutter compensation is on. In the implemented RS274 subset, the explicit
    # axis-offset commands are G92, G92.1, G92.2, and G92.3; section 3.5.18
    # refers to these directly as axis offsets. G10 may also be disallowed by
    # implication because it changes coordinate-system data, but the RS274 text
    # does not state that explicitly and unambiguously, so it is intentionally
    # excluded from this matrix.
    ("g92", "G92 X1.0\n"),
    # Removed in RS274 v1.0.1: replaced by CRC_AXIS_OFFSET_WHILE_ACTIVE_CASES
    # below, which establish nonzero G92 offsets before enabling CRC to make
    # the test intent unambiguous.
    # ("g92-1", "G92.1\n"),
    # ("g92-2", "G92.2\n"),
    # ("g92-3", "G92.3\n"),
    # RS274 section 3.5.13: coordinate-system selection codes may not be used
    # while cutter radius compensation is on.
    *COORDINATE_SYSTEM_SELECTION_CODES,
]


# Added in RS274 v1.0.1: replaces the g92-1/g92-2/g92-3 entries above.
# Appendix B.5 error 1: "Cannot change axis offsets with cutter radius comp."
# Section 3.5.18 defines G92.1/G92.2/G92.3 as axis-offset commands. G92.1 is
# the representative CRC precondition case here; G92.2 and G92.3 behavior is
# covered independently by the G92 tests.
CRC_AXIS_OFFSET_WHILE_ACTIVE_INPUT = "G17 G90 G94\nG92 X5.0\nG41 D1\nG92.1\n"


CRC_ERROR_CASES: list[tuple[str, str, int | None]] = [
    # RS274 section 3.5.10: the D number may not be larger than the number of
    # carousel slots.
    (
        "g41-rejects-d-larger-than-carousel-slots",
        "G17 G90 G94\nG41 D7\n",
        6,
    ),
    # RS274 Appendix B.5.4: the D number may not be negative.
    (
        "g41-rejects-negative-d-number",
        "G17 G90 G94\nG41 D-1\n",
        None,
    ),
    # RS274 Appendix B.5 error 12: a D word may not appear without G41 or G42.
    (
        "d-word-without-g41-or-g42",
        "D1\n",
        None,
    ),
    # RS274 section 3.5.10 and Appendix B.5 error 5: compensation may not be
    # turned on when it is already on.
    (
        "g42-when-compensation-is-already-on",
        "G17\nG41 D1\nG42 D1\n",
        None,
    ),
    # Same-direction re-enable is the same Appendix B.5 error 5.
    (
        "g41-when-g41-is-already-on",
        "G17\nG41 D1\nG41 D1\n",
        None,
    ),
    (
        "g42-when-g42-is-already-on",
        "G17\nG42 D1\nG42 D1\n",
        None,
    ),
    # RS274 Appendix B.5.3: the first move is an error if the programmed point
    # is inside the initial cross section of the tool.
    (
        "first-move-gouging-error",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X2.0 Y0.0\n",
        None,
    ),
    # RS274 Appendix B.5.1 and Figure 6: a concave corner into which the tool
    # circle will not fit is an error. After establishing a compensated
    # horizontal path with G42, the turn from (10, 0) to (14, -3) places the
    # tool on the inside of the acute corner, so the interpreter must reject
    # it as a concave-corner error.
    (
        "concave-corner-after-entry-with-g42",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X14.0 Y-3.0\n",
        None,
    ),
    # Mirror-image oblique concave corner for G41. After the compensated
    # horizontal path is established, the turn from (10, 0) to (14, 3) places
    # the tool on the inside of the acute corner, so it must also be rejected.
    (
        "concave-corner-after-entry-with-g41",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X14.0 Y3.0\n",
        None,
    ),
    # Simpler 90-degree concave corner for G41: from +X to +Y while keeping
    # the tool on the left side of the contour.
    (
        "concave-90-degree-corner-with-g41",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X10.0 Y4.0\n",
        None,
    ),
    # Simpler 90-degree concave corner for G42: from +X to -Y while keeping
    # the tool on the right side of the contour.
    (
        "concave-90-degree-corner-with-g42",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG1 X10.0 Y0.0\nG1 X10.0 Y-4.0\n",
        None,
    ),
    # RS274 Appendix B.5.1 error 16: if the tool radius is not less than the
    # programmed arc radius on an inward compensated arc, the tool cannot stay
    # tangent to the contour. For G41 on a CCW arc, the tool is on the inside
    # of the arc, so a radius-3 tool on a radius-3 arc must be rejected.
    (
        "g41-tool-radius-not-less-than-arc-radius-with-comp",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG3 X2.0 Y3.0 I-3.0 J0.0\n",
        None,
    ),
    # Mirror-image inward arc for G42 on a CW move.
    (
        "g42-tool-radius-not-less-than-arc-radius-with-comp",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG2 X2.0 Y-3.0 I-3.0 J0.0\n",
        None,
    ),
    # The same Appendix B.5.1 error also applies when the programmed arc
    # radius is strictly smaller than the tool radius.
    (
        "g41-tool-radius-greater-than-arc-radius-with-comp",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG3 X3.0 Y2.0 I-2.0 J0.0\n",
        None,
    ),
    # Mirror-image inward arc for G42 with programmed radius 2.0.
    (
        "g42-tool-radius-greater-than-arc-radius-with-comp",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG2 X3.0 Y-2.0 I-2.0 J0.0\n",
        None,
    ),
    # Radius-format border-tangent case under the Clarifications.md path-arc
    # reading: tool-tip at (5, 3), programmed end (2, 3), inside-tangent G41
    # CCW gives aux_r = path_r + tool_r = 6 with path_r = R = 3, and the
    # chord between tool-tip and programmed end is 3 = |aux_r - path_r|.
    # The two-circle intersection is internally tangent — the resulting
    # path arc has zero length (tool-tip start = end), the analog of
    # §3.5.3.1's "end point of the arc is the same as the current point."
    (
        "g41-degenerate-radius-format-crc-arc-zero-length",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG3 X2.0 Y3.0 R3.0\n",
        None,
    ),
    # Mirror-image border-tangent radius-format case for G42 CW.
    (
        "g42-degenerate-radius-format-crc-arc-zero-length",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG2 X2.0 Y-3.0 R3.0\n",
        None,
    ),
    # Radius-format geometrically-impossible case under the path-arc reading:
    # path_r = R = 2, aux_r = 5 (inside-tangent), chord between tool-tip
    # (5, 3) and programmed end (3, 2) is sqrt(5) ≈ 2.24, which is strictly
    # less than |aux_r - path_r| = 3. No path-arc center exists that places
    # tool-tip on the path arc and programmed end on the aux arc, so the
    # input must be rejected.
    (
        "g41-impossible-radius-format-crc-arc-chord-too-short",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG41 D1 G1 X5.0 Y0.0\nG3 X3.0 Y2.0 R2.0\n",
        None,
    ),
    # Mirror-image impossible-chord radius-format case for G42 CW.
    (
        "g42-impossible-radius-format-crc-arc-chord-too-short",
        "G17 G90 G94\nG0 X0.0 Y0.0\nG42 D1 G1 X5.0 Y0.0\nG2 X3.0 Y-2.0 R2.0\n",
        None,
    ),
]


@pytest.mark.parametrize(
    ("input_gcode", "carousel_slots"),
    [(input_gcode, carousel_slots) for _, input_gcode, carousel_slots in CRC_ERROR_CASES],
    ids=[case_id for case_id, _, _ in CRC_ERROR_CASES],
)
def test_application_rejects_invalid_cutter_radius_compensation_usage(
    submission_command: tuple[str, ...],
    input_gcode: str,
    carousel_slots: int | None,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )


@pytest.mark.parametrize(
    ("active_plane_gcode", "crc_enable_gcode"),
    [
        (active_plane_gcode, crc_enable_gcode)
        for _, active_plane_gcode in PLANE_CODES_INVALID_WHEN_ENABLING_CRC
        for _, crc_enable_gcode in CRC_ENABLE_CODES
    ],
    ids=[
        f"enable-{crc_enable_id}-while-{active_plane_id}-is-active"
        for active_plane_id, _ in PLANE_CODES_INVALID_WHEN_ENABLING_CRC
        for crc_enable_id, _ in CRC_ENABLE_CODES
    ],
)
def test_application_rejects_turning_on_cutter_compensation_out_of_xy_plane(
    submission_command: tuple[str, ...],
    active_plane_gcode: str,
    crc_enable_gcode: str,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=active_plane_gcode + crc_enable_gcode,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )


@pytest.mark.parametrize(
    ("plane_code", "expected_active_plane"),
    [
        (plane_code, plane_id.upper())
        for plane_id, plane_code in PLANE_CODES_INVALID_WHEN_ENABLING_CRC
    ],
    ids=[
        f"{plane_id}-is-valid-when-cutter-radius-compensation-is-not-being-enabled"
        for plane_id, _ in PLANE_CODES_INVALID_WHEN_ENABLING_CRC
    ],
)
def test_application_accepts_non_xy_plane_selection_when_cutter_radius_compensation_is_off(
    submission_command: tuple[str, ...],
    plane_code: str,
    expected_active_plane: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=plane_code,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "active_modal_g_codes").get("2") == expected_active_plane


@pytest.mark.parametrize(
    "invalid_gcode_body",
    [invalid_gcode_body for _, invalid_gcode_body in GCODE_BODIES_INVALID_WHILE_CRC_IS_ACTIVE],
    ids=[
        f"{invalid_gcode_id}-with-cutter-radius-compensation-active"
        for invalid_gcode_id, _ in GCODE_BODIES_INVALID_WHILE_CRC_IS_ACTIVE
    ],
)
def test_application_rejects_gcodes_that_are_invalid_while_cutter_compensation_is_active(
    submission_command: tuple[str, ...],
    invalid_gcode_body: str,
    tmp_path: Path,
) -> None:
    """Check the explicit RS274 G-code prohibitions that apply while CRC is active.

    Governing sections: RS274 Appendix B.5 and sections 3.5.10, 3.5.12,
    3.5.13, and 3.5.16.
    """
    run_rs274_invalid_input(
        submission_command,
        input_gcode=CRC_ACTIVE_PREFIX + invalid_gcode_body,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )


def test_application_rejects_axis_offset_changes_while_cutter_compensation_is_active(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Check that a G92.x axis-offset change is rejected while CRC is active.

    Governing section: RS274 Appendix B.5, error 1.
    """
    run_rs274_invalid_input(
        submission_command,
        input_gcode=CRC_AXIS_OFFSET_WHILE_ACTIVE_INPUT,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )
