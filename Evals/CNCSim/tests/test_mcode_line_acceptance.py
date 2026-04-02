from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim
from modal_groups import (
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
    MCODE_MODAL_GROUP_STOPPING,
    MCODE_MODAL_GROUP_TOOL_CHANGE,
)

McodeLineAcceptanceCase = tuple[str, str, dict[str, str]]

MCODE_LINE_ACCEPTANCE_CASES: list[McodeLineAcceptanceCase] = [
    (
        "one-m-word",
        "M6\n",
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
        "M1 M6 M3\n",
        {
            MCODE_MODAL_GROUP_STOPPING: "M1",
            MCODE_MODAL_GROUP_TOOL_CHANGE: "M6",
            MCODE_MODAL_GROUP_SPINDLE_TURNING: "M3",
        },
    ),
    (
        "four-m-words",
        "M1 M6 M3 M7\n",
        {
            MCODE_MODAL_GROUP_STOPPING: "M1",
            MCODE_MODAL_GROUP_TOOL_CHANGE: "M6",
            MCODE_MODAL_GROUP_SPINDLE_TURNING: "M3",
            MCODE_MODAL_GROUP_COOLANT: "M7",
        },
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.5 "Item Repeats": a line may
# have zero to four M words. These cases keep the M words in distinct modal
# groups so the test isolates the accepted per-line count.
@pytest.mark.parametrize(
    ("input_gcode", "expected_active_m_codes"),
    [
        (input_gcode, expected_active_m_codes)
        for _, input_gcode, expected_active_m_codes in MCODE_LINE_ACCEPTANCE_CASES
    ],
    ids=[case_id for case_id, _, _ in MCODE_LINE_ACCEPTANCE_CASES],
)
def test_application_accepts_up_to_four_m_words_on_one_line(
    built_executable_path: Path,
    input_gcode: str,
    expected_active_m_codes: dict[str, str],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    for group_number, expected_active_mcode in expected_active_m_codes.items():
        assert payload["active_modal_m_codes"][group_number] == expected_active_mcode
