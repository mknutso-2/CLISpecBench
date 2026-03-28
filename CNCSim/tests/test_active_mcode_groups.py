from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.modal_groups import (
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
    MCODE_MODAL_GROUP_STOPPING,
    MCODE_MODAL_GROUP_TOOL_CHANGE,
)
from swe_buildbench.cncsim.test_support import run_cncsim

ActiveMcodeGroupCase = tuple[str, str, str]

ACTIVE_MCODE_GROUP_CASES: list[ActiveMcodeGroupCase] = [
    (
        "M0\n"
        "M1\n",
        MCODE_MODAL_GROUP_STOPPING,
        "M1",
    ),
    (
        "M6\n",
        MCODE_MODAL_GROUP_TOOL_CHANGE,
        "M6",
    ),
    (
        "M3\n"
        "M5\n",
        MCODE_MODAL_GROUP_SPINDLE_TURNING,
        "M5",
    ),
    (
        "M7\n"
        "M9\n",
        MCODE_MODAL_GROUP_COOLANT,
        "M9",
    ),
    (
        "M48\n"
        "M49\n",
        MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
        "M49",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.4 "Modal Groups" and Table 4:
# only one member of a modal group may be in force at a time, so the last
# emitted M-code from a group should be the active one reported in the output.
@pytest.mark.parametrize(
    ("input_gcode", "group_number", "expected_active_mcode"),
    ACTIVE_MCODE_GROUP_CASES,
    ids=[
        f"group-{group_number}-{expected_active_mcode.lower()}"
        for _, group_number, expected_active_mcode in ACTIVE_MCODE_GROUP_CASES
    ],
)
def test_application_tracks_active_mcode_groups(
    built_executable_path: Path,
    input_gcode: str,
    group_number: str,
    expected_active_mcode: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["active_modal_m_codes"][group_number] == expected_active_mcode
