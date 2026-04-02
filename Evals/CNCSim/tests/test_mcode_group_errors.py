from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input
from modal_groups import (
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
    MCODE_MODAL_GROUP_STOPPING,
    MCODE_MODAL_GROUP_TOOL_CHANGE,
)

McodeGroupErrorCase = tuple[str, str, str]

MCODE_GROUP_ERROR_CASES: list[McodeGroupErrorCase] = [
    (
        "stopping-group",
        MCODE_MODAL_GROUP_STOPPING,
        "M0 M1\n",
    ),
    (
        "tool-change-group",
        MCODE_MODAL_GROUP_TOOL_CHANGE,
        "M6 M6\n",
    ),
    (
        "spindle-turning-group",
        MCODE_MODAL_GROUP_SPINDLE_TURNING,
        "M3 M4\n",
    ),
    (
        "coolant-group",
        MCODE_MODAL_GROUP_COOLANT,
        "M7 M8\n",
    ),
    (
        "override-switches-group",
        MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
        "M48 M49\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.5 "Item Repeats": a line may
# have zero to four M words, and two M words from the same modal group may not
# appear on the same line. These cases cover each supported M-code group.
@pytest.mark.parametrize(
    "input_gcode",
    [
        input_gcode
        for _, _group_number, input_gcode in MCODE_GROUP_ERROR_CASES
    ],
    ids=[
        f"group-{group_number}-{case_id}"
        for case_id, group_number, _ in MCODE_GROUP_ERROR_CASES
    ],
)
def test_application_rejects_multiple_m_words_from_the_same_group(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.5 "Item Repeats": a line may
# have at most four M words.
def test_application_rejects_more_than_four_m_words_on_one_line(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="M1 M6 M3 M7 M48\n",
        tmp_path=tmp_path,
    )
