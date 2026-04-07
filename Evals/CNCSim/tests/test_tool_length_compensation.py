from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim, with_default_rotary_axes

ToolLengthCompensationCase = tuple[str, str, dict[str, float], int | None]

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

2 2 1.5 0.25 finish
4 4 0.5 0.125 drill
"""

TOOL_LENGTH_COMPENSATION_CASES: list[ToolLengthCompensationCase] = [
    (
        "g43-adjusts-current-z-without-axis-motion",
        "G20\n"
        "G90\n"
        "G0 Z3.0\n"
        "G43 H2\n",
        {"x": 0.0, "y": 0.0, "z": 1.5},
        2,
    ),
    (
        "changing-g43-offsets-adjusts-current-z-by-the-offset-difference",
        "G20\n"
        "G90\n"
        "G0 Z3.0\n"
        "G43 H2\n"
        "G43 H4\n",
        {"x": 0.0, "y": 0.0, "z": 2.5},
        4,
    ),
    (
        "g49-cancels-tool-length-compensation-without-axis-motion",
        "G20\n"
        "G90\n"
        "G0 Z3.0\n"
        "G43 H2\n"
        "G49\n",
        {"x": 0.0, "y": 0.0, "z": 3.0},
        None,
    ),
    (
        "g43-remains-active-during-ordinary-motion",
        "G20\n"
        "G90\n"
        "G0 Z3.0\n"
        "G43 H2\n"
        "G1 X4.0 Y5.0 F2.0\n",
        {"x": 4.0, "y": 5.0, "z": 1.5},
        2,
    ),
]


# RS274 section 2.3 says the tool file supplies the tool length offset values.
# Section 3.5.11 says G43 H... uses the indexed tool-table entry and G49
# cancels tool length compensation. Section 2.1.2.3 says a positive tool
# length offset moves the controlled point out along the spindle axis, and
# section 2.1.2.10 says the current-position numbers must be adjusted without
# axis motion when the tool length offset changes. The interpreter example at
# RS274NGC.md lines 3938-3949 makes the sign explicit: after
# USE_TOOL_LENGTH_OFFSET(1.0000), a later move with no Z word is emitted at
# Z=-0.5000 rather than Z=0.5000, so in the XYZ machine model used by CNCSim a
# positive tool length offset lowers the reported controlled-point Z by that
# amount.
@pytest.mark.parametrize(
    ("input_gcode", "expected_machine_position", "expected_tool_length_offset_index"),
    [
        (
            input_gcode,
            expected_machine_position,
            expected_tool_length_offset_index,
        )
        for (
            _,
            input_gcode,
            expected_machine_position,
            expected_tool_length_offset_index,
        ) in TOOL_LENGTH_COMPENSATION_CASES
    ],
    ids=[case_id for case_id, _, _, _ in TOOL_LENGTH_COMPENSATION_CASES],
)
def test_application_applies_tool_length_compensation_to_current_position(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_machine_position: dict[str, float],
    expected_tool_length_offset_index: int | None,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode=input_gcode,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes(expected_machine_position)
    assert payload["tool_length_offset_index"] == expected_tool_length_offset_index
