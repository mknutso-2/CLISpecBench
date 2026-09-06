from __future__ import annotations

from pathlib import Path

import pytest

from modal_groups import (
    GCODE_MODAL_GROUP_MOTION,
    GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
)
from rs274_support import (
    mapping_field,
    run_rs274,
    with_default_rotary_axes,
)

CannedCycleCase = tuple[str, str, str, str, dict[str, float], str]
RepeatedCannedCycleCase = tuple[str, str, str, dict[str, float], str]

# Sections 3.6.2 and 3.7.2 permit M3/M4 at S0 without actual rotation.
# Cases below that require or restore a turning spindle set S100 explicitly;
# the other cycle cases keep their intentionally stopped spindle state.
ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0 A0.0 B0.0 C0.0\nG54\nG17\nG94\n"

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
        "g81-allows-stationary-rotary-words",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "G0 X1.0 Y2.0 Z3.0 A10.0 B20.0 C30.0\n"
        + "G81 X4.0 Y5.0 Z1.5 R2.8 A10.0 B20.0 C30.0 F7.0\n",
        "G81",
        "G98",
        {"x": 4.0, "y": 5.0, "z": 3.0, "a": 10.0, "b": 20.0, "c": 30.0},
        "OFF",
    ),
    (
        "g83-allows-stationary-rotary-words",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "G0 X1.0 Y2.0 Z3.0 A10.0 B20.0 C30.0\n"
        + "G83 X4.0 Y5.0 Z1.5 R2.8 Q0.25 A10.0 B20.0 C30.0 F7.0\n",
        "G83",
        "G99",
        {"x": 4.0, "y": 5.0, "z": 2.8, "a": 10.0, "b": 20.0, "c": 30.0},
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
        + "S100 M3\n"
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
        + "S100 M4\n"
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
        + "S100 M3\n"
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
        + "S100 M4\n"
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

REPEATED_CANNED_CYCLE_CASES: list[RepeatedCannedCycleCase] = [
    (
        "g84-reuses-sticky-r-and-z-on-following-line",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G98\n"
        + "S100 M3\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G84 X4.0 Y5.0 Z1.5 R2.8 F7.0\n"
        + "X6.0 Y7.0\n",
        "G98",
        {"x": 6.0, "y": 7.0, "z": 3.0},
        "CW",
    ),
    (
        "g85-reuses-sticky-r-and-z-on-following-line",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G99\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G85 X4.0 Y5.0 Z1.5 R2.8 F7.0\n"
        + "X6.0 Y7.0\n",
        "G99",
        {"x": 6.0, "y": 7.0, "z": 2.8},
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
# - G98/G99 remain modal while a cycle stays active, so changing return mode on
#   a later line changes that later line's clear-Z result
#
# An earlier low-pass-rate audit grouped the spindle-restoration cases by
# their shared behavior, but omitted S setup also allowed an already-stopped
# spindle. Positive speed now establishes an actual direction to restore.
# Cases stay separate because each cycle has its own motion/spindle sequence.
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
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_active_motion: str,
    expected_return_mode: str,
    expected_machine_position: dict[str, float],
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert (
        mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_MOTION)
        == expected_active_motion
    )
    assert (
        mapping_field(payload, "active_modal_g_codes").get(
            GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES
        )
        == expected_return_mode
    )
    assert payload.get("machine_position") == with_default_rotary_axes(expected_machine_position)
    assert payload.get("spindle_direction") == expected_spindle_direction


# RS274 section 3.5.16 says sticky R and depth-word behavior applies to canned
# cycles generally, not only to G81. These two cases extend the repeat
# coverage to supported cycles with no extra non-sticky arguments. G88 has
# separate success-path coverage below for its non-interactive manual-retract
# convention and observable spindle restart behavior.
@pytest.mark.parametrize(
    (
        "input_gcode",
        "expected_return_mode",
        "expected_machine_position",
        "expected_spindle_direction",
    ),
    [
        (
            input_gcode,
            expected_return_mode,
            expected_machine_position,
            expected_spindle_direction,
        )
        for (
            _,
            input_gcode,
            expected_return_mode,
            expected_machine_position,
            expected_spindle_direction,
        ) in REPEATED_CANNED_CYCLE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _ in REPEATED_CANNED_CYCLE_CASES],
)
# PASS-RATE NOTE (2026-04-19): the g84 and g85 parametrizations each pass
# at ~20%, and `test_application_tracks_initial_canned_cycle_behavior
# [g81-reuses-sticky-r-and-z-on-following-line]` (56/255, 22%) is the
# third member of the same cluster. Three test IDs for one behavior:
# "retain R and the selected-plane depth word across consecutive blocks
# of the same cycle." The duplicated precondition is intentional because each
# cycle still has separate endpoint and spindle expectations.
def test_supported_canned_cycles_reuse_sticky_r_and_depth_words_on_later_lines(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_return_mode: str,
    expected_machine_position: dict[str, float],
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_MOTION) in {
        "G84",
        "G85",
    }
    assert (
        mapping_field(payload, "active_modal_g_codes").get(
            GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES
        )
        == expected_return_mode
    )
    assert payload.get("machine_position") == with_default_rotary_axes(expected_machine_position)
    assert payload.get("spindle_direction") == expected_spindle_direction


# RS274 section 3.5.16.9 defines G88's operator stop and spindle restart.
# Clarifications.md maps the manual retract to an automatic rapid retract for
# this non-interactive simulator; these cases check the observable final
# spindle direction after that stop/retract sequence.
@pytest.mark.parametrize(
    ("input_gcode", "expected_spindle_direction"),
    [
        (
            ZERO_OFFSET_P1_SETUP
            + "G90\n"
            + "G98\n"
            + "S100 M3\n"
            + "G0 X1.0 Y2.0 Z3.0\n"
            + "G88 X4.0 Y5.0 Z1.5 R2.8 P0.5 F7.0\n",
            "CW",
        ),
        (
            ZERO_OFFSET_P1_SETUP
            + "G90\n"
            + "G99\n"
            + "S100 M4\n"
            + "G0 X1.0 Y2.0 Z3.0\n"
            + "G88 X4.0 Y5.0 Z1.5 R2.8 P0.5 F7.0\n",
            "CCW",
        ),
    ],
    ids=[
        "g88-restores-clockwise-spindle-in-the-observable-success-path",
        "g88-restores-counterclockwise-spindle-in-the-observable-success-path",
    ],
)
def test_g88_restores_the_prior_spindle_direction_after_the_cycle(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_MOTION) == "G88"
    assert payload.get("spindle_direction") == expected_spindle_direction


# RS274 section 3.5.15 says axis words are an error when G80 is active unless
# a modal-group-0 G-code using axis words is programmed. G10 and G92 are both
# supported group-0 axis-using commands, so they should still execute while
# G80 is the current motion mode.
def test_g80_allows_axis_words_when_supported_group_zero_gcodes_use_them(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("G80\nG10 L2 P2 X4.0 Y5.0 Z6.0\nG92 X7.0\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    # This case owns group-zero acceptance while G80 remains active. Numeric
    # G10/G92 behavior has dedicated cases; the public offset-map contract
    # does not choose between raw G10 and effective G10+G92 serialization.
    assert mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_MOTION) == "G80"


# RS274 section 3.5.16 says the clear-Z height at the end of each repeat is
# determined by the current retract mode, so changing from G98 to G99 between
# later lines of the same active canned cycle should change the later line's
# final retract level.
def test_return_mode_change_affects_later_repeats_of_an_active_canned_cycle(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(
            ZERO_OFFSET_P1_SETUP
            + "G90\n"
            + "G98\n"
            + "G0 X1.0 Y2.0 Z3.0\n"
            + "G81 X4.0 Y5.0 Z1.5 R2.8 F7.0\n"
            + "G99\n"
            + "X6.0 Y7.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "active_modal_g_codes").get(GCODE_MODAL_GROUP_MOTION) == "G81"
    assert (
        mapping_field(payload, "active_modal_g_codes").get(
            GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES
        )
        == "G99"
    )
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 6.0, "y": 7.0, "z": 2.8}
    )
