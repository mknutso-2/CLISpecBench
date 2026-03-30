from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

ToolingStateCase = tuple[str, str, int | None, int | None, int | None, int | None]

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

4 4 0.5 0.25 finisher
7 7 1.5 0.5 endmill
12 12 2.0 0.75 drill
"""

TOOLING_STATE_CASES: list[ToolingStateCase] = [
    (
        "tracks-cutter-radius-compensation-number",
        "G41 D7\n",
        7,
        None,
        None,
        None,
    ),
    (
        "clears-cutter-radius-compensation-number-on-g40",
        "G41 D3\n"
        "G40\n",
        None,
        None,
        None,
        None,
    ),
    (
        "tracks-tool-length-offset-index",
        "G43 H12\n",
        None,
        12,
        None,
        None,
    ),
    (
        "clears-tool-length-offset-index-on-g49",
        "G43 H4\n"
        "G49\n",
        None,
        None,
        None,
        None,
    ),
    (
        "tracks-selected-tool",
        "T8\n",
        None,
        None,
        8,
        None,
    ),
    (
        "tracks-tool-in-spindle-after-m6",
        "T2\n"
        "T9\n"
        "M6\n",
        None,
        None,
        9,
        9,
    ),
    (
        "tracks-selected-tool-separately-from-tool-in-spindle",
        "T4\n"
        "M6\n"
        "T7\n",
        None,
        None,
        7,
        4,
    ),
    (
        "tracks-empty-spindle-after-t0-m6",
        "T5\n"
        "M6\n"
        "T0\n"
        "M6\n",
        None,
        None,
        0,
        None,
    ),
    (
        "tracks-all-tooling-state-together",
        "T5\n"
        "G41 D6\n"
        "G43 H7\n",
        6,
        7,
        5,
        None,
    ),
    (
        "tracks-tooling-state-from-parameter-values",
        "#1=6\n"
        "#2=7\n"
        "#3=4\n"
        "T#1\n"
        "G43 H#2\n"
        "G41 D#3\n",
        4,
        7,
        6,
        None,
    ),
    (
        "tracks-tooling-state-from-expressions",
        "T[3+3]\n"
        "G43 H[3+4]\n"
        "G41 D[2+2]\n",
        4,
        7,
        6,
        None,
    ),
    (
        "tracks-tooling-state-from-repeated-parameters-and-unary-ops",
        "#1=2\n"
        "#2=6\n"
        "T##1\n"
        "G43 HABS[-7]\n"
        "G41 DABS[-4]\n",
        4,
        7,
        6,
        None,
    ),
]


#
# See CNCSim/prompt/docs/RS274NGC.md section 3.3.2 "Words": a word is a
# letter followed by a real value. Sections 3.3.2.2 and 3.3.2.3 define
# parameter values and expressions as real values, so the supported T, H, and
# D words should accept those forms as well as numeric literals. Section
# 3.3.2.2 also explicitly allows repeated `#`, and section 3.3.2.4 defines
# unary-operation values as real values. RS274 section 3.7.3 says a T word
# selects the next tool but does not change the spindle until M6, and section
# 3.6.3 says that after M6 the selected tool is the tool in the spindle, with
# T0 leaving the spindle empty after the tool change.
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_cutter_radius_compensation_number",
        "expected_tool_length_offset_index",
        "expected_selected_tool",
        "expected_tool_in_spindle",
    ),
    [
        (
            input_gcode,
            expected_cutter_radius_compensation_number,
            expected_tool_length_offset_index,
            expected_selected_tool,
            expected_tool_in_spindle,
        )
        for (
            _,
            input_gcode,
            expected_cutter_radius_compensation_number,
            expected_tool_length_offset_index,
            expected_selected_tool,
            expected_tool_in_spindle,
        ) in TOOLING_STATE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _, _ in TOOLING_STATE_CASES],
)
def test_application_tracks_tooling_state(
    built_executable_path: Path,
    input_gcode: str,
    expected_cutter_radius_compensation_number: int | None,
    expected_tool_length_offset_index: int | None,
    expected_selected_tool: int | None,
    expected_tool_in_spindle: int | None,
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
    assert (
        payload["cutter_radius_compensation_number"]
        == expected_cutter_radius_compensation_number
    )
    assert payload["tool_length_offset_index"] == expected_tool_length_offset_index
    assert payload["selected_tool"] == expected_selected_tool
    assert payload["tool_in_spindle"] == expected_tool_in_spindle
