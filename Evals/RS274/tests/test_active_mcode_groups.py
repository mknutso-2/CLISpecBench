from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import (
    MCODE_MODAL_GROUP_COOLANT,
    MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
    MCODE_MODAL_GROUP_SPINDLE_TURNING,
    MCODE_MODAL_GROUP_STOPPING,
    MCODE_MODAL_GROUP_TOOL_CHANGE,
)
from rs274_support import mapping_field, run_rs274

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
        "M0\nM1\n",
        MCODE_MODAL_GROUP_STOPPING,
        "M1",
    ),
    (
        "M6\n",
        MCODE_MODAL_GROUP_TOOL_CHANGE,
        "M6",
    ),
    (
        "M3\nM5\n",
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
        "M7\nM9\n",
        MCODE_MODAL_GROUP_COOLANT,
        "M9",
    ),
    (
        "M48\nM49\n",
        MCODE_MODAL_GROUP_OVERRIDE_SWITCHES,
        "M49",
    ),
]


# See RS274/prompt/docs/RS274NGC.md section 3.4 "Modal Groups" and Table 4:
# only one member of a modal group may be in force at a time, so the last
# emitted M-code from a group should be the active one reported in the output.
# For stopping-group codes such as M0, M1, and M60, the current harness can
# only observe acceptance and modal-state tracking, not the full stop/resume or
# pallet-shuttle behavior from section 3.6.1.
#
# PASS-RATE NOTE (2026-04-19): these 10 parametrizations split sharply by
# which modal group they probe (see CHANGELOG "Proposed"):
#   - group 4 (stopping, M0/M1/M60): 18–22%
#   - group 6 (tool-change, M6):     20%
#   - group 7 (spindle, M5):         42%
#   - group 8 (coolant, M7/M8/M9):   34–41%
#   - group 9 (override, M49):       36%
# Two separate issues are in play:
#   1. Typo in technical-requirements-prompt.md Example 1 (line 292):
#      `{"4": "M5", ...}`. M5 is in group 7 per RS274 Table 4, not
#      group 4. Real but small — if this were the driver, `group-7-m5`
#      would have the lowest pass rate; it has the highest.
#   2. Genuine spec ambiguity — "modal group" in RS274 Table 4 strictly
#      means "at most one member per line." For continuous states
#      (spindle, coolant, override) it also reads naturally as
#      persistent across lines. For instantaneous actions (M0/M1/M2/
#      M30/M60 stop codes and M6 tool-change), the spec never says
#      whether the code remains the "active" member of its group after
#      the action completes. The tests assume yes; models reasonably
#      disagree, and treat these codes as events without a persistent
#      modal slot. This is the ~20 pp driver of the gap.
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
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "active_modal_m_codes").get(group_number) == expected_active_mcode
