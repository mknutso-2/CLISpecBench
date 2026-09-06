from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import MCODE_MODAL_GROUP_COOLANT
from rs274_support import mapping_field, run_rs274

ToolingStateCase = tuple[str, str, dict[str, int | str | None], int | None]

TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

3 3 0.0 0.0 spare
4 4 0.5 0.25 finisher
5 5 0.0 0.0 spare
6 6 1.0 0.375 slotdrill
7 7 1.5 0.5 endmill
9 9 0.0 0.0 spare
12 12 2.0 0.75 drill
"""

# The boundary case supplies only an occupied slot within its six-slot
# carousel. An out-of-range table would fail parsing before D/H/T validation.
SIX_SLOT_TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

6 6 1.0 0.375 slotdrill
"""

# Each row asserts the fields it changes, avoiding default selected-tool or
# spindle values as prerequisites for unrelated D/H checks. Only the named
# integration row establishes and checks every tooling field together.
# Appendix B.2.4 and Clarifications.md also define explicit D0 serialization.
TOOLING_STATE_CASES: list[ToolingStateCase] = [
    (
        "tracks-explicit-zero-cutter-radius-compensation-number",
        "G17\nG41 D0\n",
        {"cutter_radius_compensation_number": 0},
        None,
    ),
    (
        "tracks-cutter-radius-compensation-number",
        "G17\nG41 D7\n",
        {"cutter_radius_compensation_number": 7},
        None,
    ),
    (
        "clears-cutter-radius-compensation-number-on-g40",
        "G17\nG41 D3\nG40\n",
        {"cutter_radius_compensation_number": None},
        None,
    ),
    (
        "tracks-tool-length-offset-index",
        "G43 H12\n",
        {"tool_length_offset_index": 12},
        None,
    ),
    (
        "clears-tool-length-offset-index-on-g49",
        "G43 H4\nG49\n",
        {"tool_length_offset_index": None},
        None,
    ),
    (
        "tracks-selected-tool",
        "T8\n",
        {"selected_tool": 8},
        None,
    ),
    (
        "tracks-tool-in-spindle-after-m6",
        "T2\nT9\nM6\n",
        {"tool_in_spindle": 9},
        None,
    ),
    (
        "tracks-selected-tool-separately-from-tool-in-spindle",
        "T4\nM6\nT7\n",
        {"selected_tool": 7, "tool_in_spindle": 4},
        None,
    ),
    (
        "tracks-empty-spindle-after-t0-m6",
        "T5\nM6\nT0\nM6\n",
        {"tool_in_spindle": None},
        None,
    ),
    (
        "accepts-d-h-and-t-equal-to-carousel-slot-count",
        "G17\nT6\nM6\nG43 H6\nG41 D6\n",
        {
            "cutter_radius_compensation_number": 6,
            "tool_length_offset_index": 6,
            "selected_tool": 6,
            "tool_in_spindle": 6,
        },
        6,
    ),
    (
        "m6-stops-the-spindle",
        "S1200\nM3\nT4\nM6\n",
        {"spindle_direction": "OFF"},
        None,
    ),
    (
        "tracks-all-tooling-state-together",
        "G17\nT4\nM6\nT5\nG41 D6\nG43 H7\nS1200 M3\n",
        {
            "cutter_radius_compensation_number": 6,
            "tool_length_offset_index": 7,
            "selected_tool": 5,
            "tool_in_spindle": 4,
            "spindle_direction": "CW",
        },
        None,
    ),
    (
        "tracks-tooling-state-from-parameter-values",
        "G17\n#1=6\n#2=7\n#3=4\nT#1\nG43 H#2\nG41 D#3\n",
        {"cutter_radius_compensation_number": 4, "tool_length_offset_index": 7, "selected_tool": 6},
        None,
    ),
    (
        "tracks-tooling-state-from-expressions",
        "G17\nT[3+3]\nG43 H[3+4]\nG41 D[2+2]\n",
        {"cutter_radius_compensation_number": 4, "tool_length_offset_index": 7, "selected_tool": 6},
        None,
    ),
    (
        "tracks-tooling-state-from-repeated-parameters-and-unary-ops",
        "G17\n#1=2\n#2=6\nT##1\nG43 HABS[-7]\nG41 DABS[-4]\n",
        {"cutter_radius_compensation_number": 4, "tool_length_offset_index": 7, "selected_tool": 6},
        None,
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
# be stopped. Slots used for tool changes and D/H lookups are explicitly
# populated: section 3.7.3 permits empty slots, so absence from a tool table
# cannot stand in for an occupied tool. In particular, the T0 case first loads
# the occupied slot 5 to test an actual transition to an empty spindle.
# Sections 3.5.10, 3.5.11,
# and 3.7.3 all make the carousel-slot-count check a strict `>` comparison, so
# a D/H/T number equal to the slot count remains valid.
@pytest.mark.parametrize(
    ("input_gcode", "expected_fields", "carousel_slots"),
    [(program, expected, slots) for _, program, expected, slots in TOOLING_STATE_CASES],
    ids=[case_id for case_id, _, _, _ in TOOLING_STATE_CASES],
)
def test_application_tracks_tooling_state(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_fields: dict[str, int | str | None],
    carousel_slots: int | None,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        tool_table_content=SIX_SLOT_TOOL_TABLE if carousel_slots == 6 else TOOL_TABLE,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    for field, expected in expected_fields.items():
        assert payload.get(field) == expected, field


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
