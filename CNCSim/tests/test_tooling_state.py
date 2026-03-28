from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

ToolingStateCase = tuple[str, str, int | None, int | None, int | None]

TOOLING_STATE_CASES: list[ToolingStateCase] = [
    (
        "tracks-cutter-radius-compensation-number",
        "G41 D7\n",
        7,
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
    ),
    (
        "tracks-tool-length-offset-index",
        "G43 H12\n",
        None,
        12,
        None,
    ),
    (
        "clears-tool-length-offset-index-on-g49",
        "G43 H4\n"
        "G49\n",
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
    ),
    (
        "tracks-latest-selected-tool",
        "T2\n"
        "T9\n"
        "M6\n",
        None,
        None,
        9,
    ),
    (
        "tracks-all-tooling-state-together",
        "T5\n"
        "G41 D6\n"
        "G43 H7\n",
        6,
        7,
        5,
    ),
]


@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_cutter_radius_compensation_number",
        "expected_tool_length_offset_index",
        "expected_selected_tool",
    ),
    [
        (
            input_gcode,
            expected_cutter_radius_compensation_number,
            expected_tool_length_offset_index,
            expected_selected_tool,
        )
        for (
            _,
            input_gcode,
            expected_cutter_radius_compensation_number,
            expected_tool_length_offset_index,
            expected_selected_tool,
        ) in TOOLING_STATE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _ in TOOLING_STATE_CASES],
)
def test_application_tracks_tooling_state(
    built_executable_path: Path,
    input_gcode: str,
    expected_cutter_radius_compensation_number: int | None,
    expected_tool_length_offset_index: int | None,
    expected_selected_tool: int | None,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
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
