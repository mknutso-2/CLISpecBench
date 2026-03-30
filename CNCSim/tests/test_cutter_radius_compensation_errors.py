from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim, run_cncsim_invalid_input

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 6.0 rougher
"""

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
    # RS274 Appendix B.5 error 1 says axis offsets may not be changed while
    # cutter compensation is on. In the implemented RS274 subset, the explicit
    # axis-offset commands are G92, G92.1, G92.2, and G92.3; section 3.5.18
    # refers to these directly as axis offsets. G10 may also be disallowed by
    # implication because it changes coordinate-system data, but the RS274 text
    # does not state that explicitly and unambiguously, so it is intentionally
    # excluded from this matrix.
    ("g92", "G92 X1.0\n"),
    ("g92-1", "G92.1\n"),
    ("g92-2", "G92.2\n"),
    ("g92-3", "G92.3\n"),
    # RS274 section 3.5.13: coordinate-system selection codes may not be used
    # while cutter radius compensation is on.
    *COORDINATE_SYSTEM_SELECTION_CODES,
]


CRC_ERROR_CASES: list[tuple[str, str]] = [
    # RS274 Appendix B.5 error 12: a D word may not appear without G41 or G42.
    (
        "d-word-without-g41-or-g42",
        "D1\n",
    ),
    # RS274 section 3.5.10 and Appendix B.5 error 5: compensation may not be
    # turned on when it is already on.
    (
        "g42-when-compensation-is-already-on",
        "G17\n"
        "G41 D1\n"
        "G42 D1\n",
    ),
    # RS274 Appendix B.5.3: the first move is an error if the programmed point
    # is inside the initial cross section of the tool.
    (
        "first-move-gouging-error",
        "G17 G90 G94\n"
        "G0 X0.0 Y0.0\n"
        "G41 D1 G1 X2.0 Y0.0\n",
    ),
    # RS274 Appendix B.5.1 and Figure 6: a concave corner into which the tool
    # circle will not fit is an error. After establishing a compensated
    # horizontal path with G42, the turn from (10, 0) to (14, -3) places the
    # tool on the inside of the acute corner, so the interpreter must reject
    # it as a concave-corner error.
    (
        "concave-corner-after-entry-with-g42",
        "G17 G90 G94\n"
        "G0 X0.0 Y0.0\n"
        "G42 D1 G1 X5.0 Y0.0\n"
        "G1 X10.0 Y0.0\n"
        "G1 X14.0 Y-3.0\n",
    ),
    # Mirror-image oblique concave corner for G41. After the compensated
    # horizontal path is established, the turn from (10, 0) to (14, 3) places
    # the tool on the inside of the acute corner, so it must also be rejected.
    (
        "concave-corner-after-entry-with-g41",
        "G17 G90 G94\n"
        "G0 X0.0 Y0.0\n"
        "G41 D1 G1 X5.0 Y0.0\n"
        "G1 X10.0 Y0.0\n"
        "G1 X14.0 Y3.0\n",
    ),
    # Simpler 90-degree concave corner for G41: from +X to +Y while keeping
    # the tool on the left side of the contour.
    (
        "concave-90-degree-corner-with-g41",
        "G17 G90 G94\n"
        "G0 X0.0 Y0.0\n"
        "G41 D1 G1 X5.0 Y0.0\n"
        "G1 X10.0 Y0.0\n"
        "G1 X10.0 Y4.0\n",
    ),
    # Simpler 90-degree concave corner for G42: from +X to -Y while keeping
    # the tool on the right side of the contour.
    (
        "concave-90-degree-corner-with-g42",
        "G17 G90 G94\n"
        "G0 X0.0 Y0.0\n"
        "G42 D1 G1 X5.0 Y0.0\n"
        "G1 X10.0 Y0.0\n"
        "G1 X10.0 Y-4.0\n",
    ),
]


@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in CRC_ERROR_CASES],
    ids=[case_id for case_id, _ in CRC_ERROR_CASES],
)
def test_application_rejects_invalid_cutter_radius_compensation_usage(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
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
    built_executable_path: Path,
    active_plane_gcode: str,
    crc_enable_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
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
    built_executable_path: Path,
    plane_code: str,
    expected_active_plane: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=plane_code,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["active_modal_g_codes"]["2"] == expected_active_plane


@pytest.mark.parametrize(
    "invalid_gcode_body",
    [invalid_gcode_body for _, invalid_gcode_body in GCODE_BODIES_INVALID_WHILE_CRC_IS_ACTIVE],
    ids=[
        f"{invalid_gcode_id}-with-cutter-radius-compensation-active"
        for invalid_gcode_id, _ in GCODE_BODIES_INVALID_WHILE_CRC_IS_ACTIVE
    ],
)
def test_application_rejects_gcodes_that_are_invalid_while_cutter_compensation_is_active(
    built_executable_path: Path,
    invalid_gcode_body: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=CRC_ACTIVE_PREFIX + invalid_gcode_body,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )
