from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import MCODE_MODAL_GROUP_COOLANT
from rs274_support import mapping_field, run_rs274

ToolingStateCase = tuple[
    str,
    str,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
    str,
]

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

4 4 0.5 0.25 finisher
6 6 1.0 0.375 slotdrill
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
        None,
        "OFF",
    ),
    (
        "clears-cutter-radius-compensation-number-on-g40",
        "G41 D3\nG40\n",
        None,
        None,
        None,
        None,
        None,
        "OFF",
    ),
    (
        "tracks-tool-length-offset-index",
        "G43 H12\n",
        None,
        12,
        None,
        None,
        None,
        "OFF",
    ),
    (
        "clears-tool-length-offset-index-on-g49",
        "G43 H4\nG49\n",
        None,
        None,
        None,
        None,
        None,
        "OFF",
    ),
    (
        "tracks-selected-tool",
        "T8\n",
        None,
        None,
        8,
        None,
        None,
        "OFF",
    ),
    (
        "tracks-tool-in-spindle-after-m6",
        "T2\nT9\nM6\n",
        None,
        None,
        9,
        9,
        None,
        "OFF",
    ),
    (
        "tracks-selected-tool-separately-from-tool-in-spindle",
        "T4\nM6\nT7\n",
        None,
        None,
        7,
        4,
        None,
        "OFF",
    ),
    (
        "tracks-empty-spindle-after-t0-m6",
        "T5\nM6\nT0\nM6\n",
        None,
        None,
        0,
        None,
        None,
        "OFF",
    ),
    (
        "accepts-d-h-and-t-equal-to-carousel-slot-count",
        "T6\nM6\nG43 H6\nG41 D6\n",
        6,
        6,
        6,
        6,
        6,
        "OFF",
    ),
    (
        "m6-stops-the-spindle",
        "S1200\nM3\nT4\nM6\n",
        None,
        None,
        4,
        4,
        None,
        "OFF",
    ),
    (
        "tracks-all-tooling-state-together",
        "T5\nG41 D6\nG43 H7\n",
        6,
        7,
        5,
        None,
        None,
        "OFF",
    ),
    (
        "tracks-tooling-state-from-parameter-values",
        "#1=6\n#2=7\n#3=4\nT#1\nG43 H#2\nG41 D#3\n",
        4,
        7,
        6,
        None,
        None,
        "OFF",
    ),
    (
        "tracks-tooling-state-from-expressions",
        "T[3+3]\nG43 H[3+4]\nG41 D[2+2]\n",
        4,
        7,
        6,
        None,
        None,
        "OFF",
    ),
    (
        "tracks-tooling-state-from-repeated-parameters-and-unary-ops",
        "#1=2\n#2=6\nT##1\nG43 HABS[-7]\nG41 DABS[-4]\n",
        4,
        7,
        6,
        None,
        None,
        "OFF",
    ),
]


#
# See RS274/prompt/docs/RS274NGC.md section 3.3.2 "Words": a word is a
# letter followed by a real value. Sections 3.3.2.2 and 3.3.2.3 define
# parameter values and expressions as real values, so the supported T, H, and
# D words should accept those forms as well as numeric literals. Section
# 3.3.2.2 also explicitly allows repeated `#`, and section 3.3.2.4 defines
# unary-operation values as real values. RS274 section 3.7.3 says a T word
# selects the next tool but does not change the spindle until M6, and section
# 3.6.3 says that after M6 the selected tool is the tool in the spindle, with
# T0 leaving the spindle empty after the tool change, and that the spindle will
# be stopped. Sections 3.5.10, 3.5.11,
# and 3.7.3 all make the carousel-slot-count check a strict `>` comparison, so
# a D/H/T number equal to the slot count remains valid.
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_cutter_radius_compensation_number",
        "expected_tool_length_offset_index",
        "expected_selected_tool",
        "expected_tool_in_spindle",
        "carousel_slots",
        "expected_spindle_direction",
    ),
    [
        (
            input_gcode,
            expected_cutter_radius_compensation_number,
            expected_tool_length_offset_index,
            expected_selected_tool,
            expected_tool_in_spindle,
            carousel_slots,
            expected_spindle_direction,
        )
        for (
            _,
            input_gcode,
            expected_cutter_radius_compensation_number,
            expected_tool_length_offset_index,
            expected_selected_tool,
            expected_tool_in_spindle,
            carousel_slots,
            expected_spindle_direction,
        ) in TOOLING_STATE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _, _, _, _ in TOOLING_STATE_CASES],
)
def test_application_tracks_tooling_state(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_cutter_radius_compensation_number: int | None,
    expected_tool_length_offset_index: int | None,
    expected_selected_tool: int | None,
    expected_tool_in_spindle: int | None,
    carousel_slots: int | None,
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert (
        payload.get("cutter_radius_compensation_number")
        == expected_cutter_radius_compensation_number
    )
    assert payload.get("tool_length_offset_index") == expected_tool_length_offset_index
    assert payload.get("selected_tool") == expected_selected_tool
    assert payload.get("tool_in_spindle") == expected_tool_in_spindle
    assert payload.get("spindle_direction") == expected_spindle_direction


def test_m6_stops_spindle_without_clearing_unrelated_observable_state(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("F12.5\nM8\nS1200\nM3\nT4\nM6\n"),
        tool_table_content=TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("feed_rate") == 12.5
    assert payload.get("spindle_speed") == 1200.0
    assert payload.get("spindle_direction") == "OFF"
    assert mapping_field(payload, "active_modal_m_codes").get(MCODE_MODAL_GROUP_COOLANT) == "M8"
