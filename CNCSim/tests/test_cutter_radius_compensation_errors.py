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
