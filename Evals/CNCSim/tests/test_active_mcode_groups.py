from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim
from modal_groups import (
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
    MCODE_MODAL_GROUP_STOPPING,
    MCODE_MODAL_GROUP_TOOL_CHANGE,
)

ActiveMcodeGroupCase = tuple[str, str, str]

ACTIVE_MCODE_GROUP_CASES: list[ActiveMcodeGroupCase] = [
    (
        "M0\n",
        MCODE_MODAL_GROUP_STOPPING,
        "M0",
    ),
    (
        "M1\n",
        MCODE_MODAL_GROUP_STOPPING,
        "M1",
    ),
    (
        "M60\n",
        MCODE_MODAL_GROUP_STOPPING,
        "M60",
    ),
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
        "M7\n",
        MCODE_MODAL_GROUP_COOLANT,
        "M7",
    ),
    (
        "M8\n",
        MCODE_MODAL_GROUP_COOLANT,
        "M8",
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
# For stopping-group codes such as M0, M1, and M60, the current harness can
# only observe acceptance and modal-state tracking, not the full stop/resume or
# pallet-shuttle behavior from section 3.6.1.
@pytest.mark.parametrize(
    ("input_gcode", "group_number", "expected_active_mcode"),
    ACTIVE_MCODE_GROUP_CASES,
    ids=[
        f"group-{group_number}-{expected_active_mcode.lower()}"
        for _, group_number, expected_active_mcode in ACTIVE_MCODE_GROUP_CASES
    ],
)
def test_application_tracks_active_mcode_groups(
    submission_command: tuple[str, ...],
    input_gcode: str,
    group_number: str,
    expected_active_mcode: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["active_modal_m_codes"][group_number] == expected_active_mcode
