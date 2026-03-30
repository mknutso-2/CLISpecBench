from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 6.0 rougher
"""


CRC_ERROR_CASES: list[tuple[str, str]] = [
    # RS274 Appendix B.5 error 12: a D word may not appear without G41 or G42.
    (
        "d-word-without-g41-or-g42",
        "D1\n",
    ),
    # RS274 section 3.5.10: cutter compensation may be performed only in the XY plane.
    (
        "g41-out-of-xy-plane",
        "G18\n"
        "G41 D1\n",
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
