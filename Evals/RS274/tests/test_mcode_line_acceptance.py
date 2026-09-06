from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import (
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
    MCODE_MODAL_GROUP_STOPPING,
    MCODE_MODAL_GROUP_TOOL_CHANGE,
)
from rs274_support import mapping_field, run_rs274

McodeLineAcceptanceCase = tuple[str, str, dict[str, str]]

MCODE_LINE_ACCEPTANCE_CASES: list[McodeLineAcceptanceCase] = [
    (
        "one-m-word",
        "T0 M6\n",
        {
            MCODE_MODAL_GROUP_TOOL_CHANGE: "M6",
        },
    ),
    (
        "two-m-words",
        "M3 M7\n",
        {
            MCODE_MODAL_GROUP_SPINDLE_TURNING: "M3",
            MCODE_MODAL_GROUP_COOLANT: "M7",
        },
    ),
    (
        "three-m-words",
        "T0 M1 M6 M3\n",
        {
            MCODE_MODAL_GROUP_STOPPING: "M1",
            MCODE_MODAL_GROUP_TOOL_CHANGE: "M6",
            MCODE_MODAL_GROUP_SPINDLE_TURNING: "M3",
        },
    ),
    (
        "four-m-words",
        "T0 M1 M6 M3 M7\n",
        {
            MCODE_MODAL_GROUP_STOPPING: "M1",
            MCODE_MODAL_GROUP_TOOL_CHANGE: "M6",
            MCODE_MODAL_GROUP_SPINDLE_TURNING: "M3",
            MCODE_MODAL_GROUP_COOLANT: "M7",
        },
    ),
]


# See RS274/prompt/docs/RS274NGC.md section 3.3.5 "Item Repeats": a line may
# have zero to four M words. These cases keep the M words in distinct modal
# groups so the test isolates the accepted per-line count.
#
# PASS-RATE NOTE (2026-04-19): the four parametrizations split by which
# groups they probe. `two-m-words` (M3 M7 → groups 7, 8) passes at 34%,
# while `one-m-word` (M6 → group 6), `three-m-words` (M1 M6 M3), and
# `four-m-words` (M1 M6 M3 M7) pass at 13–20%. Every low-pass case
# requires reporting group 6 (tool-change, M6) or group 4 (stopping,
# M1) as persistent modal state after the action has executed. The prompt
# now states that expected serialization rule explicitly for every Table 4
# M-code, including stopping codes and M6.
# That historical attribution was incomplete: the three M6 cases also lacked
# a selected tool. Sections 3.6.3/3.7.3 allow an explicit T0 M6 empty-spindle
# change, so supply T0 without altering the M-word count or requiring a table.
@pytest.mark.parametrize(
    ("input_gcode", "expected_active_m_codes"),
    [
        (input_gcode, expected_active_m_codes)
        for _, input_gcode, expected_active_m_codes in MCODE_LINE_ACCEPTANCE_CASES
    ],
    ids=[case_id for case_id, _, _ in MCODE_LINE_ACCEPTANCE_CASES],
)
def test_application_accepts_up_to_four_m_words_on_one_line(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_active_m_codes: dict[str, str],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    for group_number, expected_active_mcode in expected_active_m_codes.items():
        assert (
            mapping_field(payload, "active_modal_m_codes").get(group_number)
            == expected_active_mcode
        )
