from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.modal_groups import (
    GCODE_MODAL_GROUP_MOTION,
    GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
)
from swe_buildbench.cncsim.test_support import run_cncsim

CannedCycleCase = tuple[str, str, str, str, dict[str, float], str]

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG17\nG94\n"

CANNED_CYCLE_CASES: list[CannedCycleCase] = [
    (
        "g81-g98-returns-to-old-z",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n",
        "G81",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0},
        "OFF",
    ),
    (
        "g81-g99-returns-to-r",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n",
        "G81",
        "G99",
        {"x": 4.0, "y": 5.0, "z": 2.8},
        "OFF",
    ),
    (
        "g81-reuses-sticky-r-and-z-on-following-line",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n"
        + "X6.0 Y7.0\n",
        "G81",
        "G98",
        {"x": 6.0, "y": 7.0, "z": 3.0},
        "OFF",
    ),
    (
        "g81-g91-l-repeats-advance-xy",
        ZERO_OFFSET_P1_SETUP
        + "G91\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z-0.6 R1.8 L3 F7.0\n",
        "G81",
        "G98",
        {"x": 13.0, "y": 17.0, "z": 4.8},
        "OFF",
    ),
    (
        "g82-accepts-p-and-retracts-like-g81",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G82 X4.0 Y5.0 Z1.5 R2.8 P0.5 F7.0\n",
        "G82",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0},
        "OFF",
    ),
    (
        "g83-accepts-q-and-retracts-to-r-under-g99",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G83 X4.0 Y5.0 Z1.5 R2.8 Q0.25 F7.0\n",
        "G83",
        "G99",
        {"x": 4.0, "y": 5.0, "z": 2.8},
        "OFF",
    ),
    (
        "g81-g18-uses-y-as-the-depth-axis",
        "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "G54\n"
        "G18\n"
        "G94\n"
        "G90\n"
        "G99\n"
        "G0 X1.0 Y3.0 Z2.0\n"
        "G81 X4.0 Y1.5 Z5.0 R2.8 F7.0\n",
        "G81",
        "G99",
        {"x": 4.0, "y": 2.8, "z": 5.0},
        "OFF",
    ),
    (
        "g81-g19-uses-x-as-the-depth-axis",
        "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "G54\n"
        "G19\n"
        "G94\n"
        "G90\n"
        "G99\n"
        "G0 X3.0 Y1.0 Z2.0\n"
        "G81 X1.5 Y4.0 Z5.0 R2.8 F7.0\n",
        "G81",
        "G99",
        {"x": 2.8, "y": 4.0, "z": 5.0},
        "OFF",
    ),
    (
        "g84-restores-clockwise-spindle-after-the-cycle",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "M3\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G84 X4.0 Y5.0 Z1.5 R2.8 F7.0\n",
        "G84",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0},
        "CW",
    ),
    (
        "g85-retracts-like-g81-at-line-end",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G85 X4.0 Y5.0 Z1.5 R2.8 F7.0\n",
        "G85",
        "G99",
        {"x": 4.0, "y": 5.0, "z": 2.8},
        "OFF",
    ),
    (
        "g86-restores-the-prior-spindle-direction",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "M4\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G86 X4.0 Y5.0 Z1.5 R2.8 P0.5 F7.0\n",
        "G86",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0},
        "CCW",
    ),
    (
        "g87-restores-clockwise-spindle-and-returns-to-r-under-g99",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "M3\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G87 X4.0 Y5.0 Z1.5 R2.8 I-0.5 J-0.5 K2.25 F7.0\n",
        "G87",
        "G99",
        {"x": 4.0, "y": 5.0, "z": 2.8},
        "CW",
    ),
    (
        "g87-restores-counterclockwise-spindle-and-returns-to-old-z-under-g98",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "M4\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G87 X4.0 Y5.0 Z1.5 R2.8 I-0.5 J-0.5 K2.25 F7.0\n",
        "G87",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0},
        "CCW",
    ),
    (
        "g89-retracts-like-g82-at-line-end",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G89 X4.0 Y5.0 Z1.5 R2.8 P0.5 F7.0\n",
        "G89",
        "G99",
        {"x": 4.0, "y": 5.0, "z": 2.8},
        "OFF",
    ),
    (
        "g80-cancels-canned-cycle-motion",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n"
        + "G80\n",
        "G80",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0},
        "OFF",
    ),
]


# RS274 section 3.5.16 defines the observable end-of-line effects we can check
# with the current payload:
# - G81 retracts to clear Z
# - G82 adds dwell but otherwise retracts like G81
# - G83 pecks internally but still ends at clear Z
# - G84/G86/G87 have spindle side effects, which are observable through the
#   final spindle direction
# - G85 and G89 differ from G81/G82 in feed-vs-traverse retract details, but
#   the current payload can still confirm their final retract level
# - G98 retracts to OLD_Z when it is above R; G99 retracts to R
# - R is always sticky, and the selected-plane depth word is sticky when the
#   same canned cycle remains active on following lines
# - L repeats in incremental mode advance the in-plane axes while R and depth
#   positions remain fixed for the repeats
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_active_motion",
        "expected_return_mode",
        "expected_machine_position",
        "expected_spindle_direction",
    ),
    [
        (
            input_gcode,
            expected_active_motion,
            expected_return_mode,
            expected_machine_position,
            expected_spindle_direction,
        )
        for (
            _,
            input_gcode,
            expected_active_motion,
            expected_return_mode,
            expected_machine_position,
            expected_spindle_direction,
        ) in CANNED_CYCLE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _, _ in CANNED_CYCLE_CASES],
)
def test_application_tracks_initial_canned_cycle_behavior(
    built_executable_path: Path,
    input_gcode: str,
    expected_active_motion: str,
    expected_return_mode: str,
    expected_machine_position: dict[str, float],
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["active_modal_g_codes"][GCODE_MODAL_GROUP_MOTION] == expected_active_motion
    assert (
        payload["active_modal_g_codes"][GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES]
        == expected_return_mode
    )
    assert payload["machine_position"] == expected_machine_position
    assert payload["spindle_direction"] == expected_spindle_direction
