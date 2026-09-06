from __future__ import annotations

from pathlib import Path

import pytest

from rs274_support import ProbeBox, run_rs274_invalid_input

PROBE_TOOL = 2
PROBE_BOX: ProbeBox = (0.0, 10.0, 0.0, 10.0, 2.0, 4.0)
PROBE_TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

1 1 0.0 0.0 non-probe
2 2 0.0 0.0 probe
"""

ProbeErrorCase = tuple[str, str]

PROBE_ERROR_CASES: list[ProbeErrorCase] = [
    (
        "g38-2-requires-linear-axis-word",
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2\n",
    ),
    (
        "g38-2-rejects-inverse-time-feed-rate-mode",
        "G20\nG90\nT2 M6\nG0 X5.0 Y5.0 Z5.0\nG93\nF1.0\nG38.2 Z0.0\n",
    ),
    (
        "g38-2-rejects-programmed-point-that-is-too-close",
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z4.005\nF10.0\nG38.2 Z4.0\n",
    ),
    (
        "g38-2-rejects-a-axis-motion",
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0 A10.0\nF10.0\nG38.2 Z0.0 A11.0\n",
    ),
    (
        "g38-2-rejects-b-axis-motion",
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0 B20.0\nF10.0\nG38.2 Z0.0 B21.0\n",
    ),
    (
        "g38-2-rejects-c-axis-motion",
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0 C30.0\nF10.0\nG38.2 Z0.0 C31.0\n",
    ),
]


# RS274 section 3.5.9 explicitly makes these invalid uses of G38.2 errors:
# no X/Y/Z word, inverse-time feed rate mode, and a programmed point closer
# than 0.01 inch or 0.254 millimeter to the current point. The same section
# also says rotational axes may appear only if they are not commanded to move.
# All cases load an occupied probe slot and establish a positive feed. The
# too-close move crosses the box boundary, so it cannot pass merely because
# a probe that ignores the minimum distance later reports a no-hit error.
# Successful probe cases in test_probing.py control the valid setup separately.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in PROBE_ERROR_CASES],
    ids=[case_id for case_id, _ in PROBE_ERROR_CASES],
)
def test_application_rejects_explicit_invalid_g38_2_uses(
    submission_command: tuple[str, ...],
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=input_gcode,
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )


# RS274 section 3.5.9 says the tool in the spindle must be a probe, and the
# technical requirements prompt defines --probe-tool as the probe designation
# used by the eval harness.
def test_application_requires_the_probe_tool_in_the_spindle(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode="G20\nG90 G94\nT1 M6\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2 Z0.0\n",
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )


# RS274 section 3.7.3 says a T word only selects a tool, and section 3.6.3
# says the tool in the spindle changes only when M6 is programmed. So merely
# selecting the designated probe tool is not enough for G38.2.
def test_application_requires_the_probe_tool_to_be_loaded_not_just_selected(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode="G20\nG90 G94\nT1 M6\nT2\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2 Z0.0\n",
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )


# RS274 section 4.3.6.6 explicitly says the spindle must not be turning when
# STRAIGHT_PROBE starts.
def test_application_rejects_probing_with_the_spindle_turning(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=("G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z5.0\nS500.0 M3\nF10.0\nG38.2 Z0.0\n"),
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )


# RS274 section 4.3.6.6 explicitly says the probe must not already be tripped
# when STRAIGHT_PROBE starts. Put the controlled point directly inside the
# probe box, without coupling this rejection to tool-length compensation.
def test_application_rejects_probing_when_the_probe_is_already_tripped(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=("G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z3.0\nF10.0\nG38.2 Z0.0\n"),
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )


NoHitProbeCase = tuple[str, ProbeBox, str]

NO_HIT_PROBE_CASES: list[NoHitProbeCase] = [
    (
        "x-probe-no-hit",
        (0.0, 10.0, 0.0, 10.0, 0.0, 6.0),
        "G20\nG90 G94\nT2 M6\nG0 X-5.0 Y5.0 Z3.0\nF10.0\nG38.2 X-1.0\n",
    ),
    (
        "y-probe-no-hit",
        (0.0, 10.0, 0.0, 10.0, 0.0, 6.0),
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y-5.0 Z3.0\nF10.0\nG38.2 Y-1.0\n",
    ),
    (
        "z-probe-no-hit",
        (0.0, 10.0, 0.0, 10.0, 0.0, 4.0),
        "G20\nG90 G94\nT2 M6\nG0 X5.0 Y5.0 Z8.0\nF10.0\nG38.2 Z6.0\n",
    ),
]


# RS274 section 3.5.9 says it is an error if the probe does not trip even
# after overshooting the programmed point slightly. Each of these cases keeps
# the whole commanded segment outside the probe box for one of the X, Y, or Z
# probing directions, so no trip can occur before the programmed point.
@pytest.mark.parametrize(
    ("probe_box", "input_gcode"),
    [(probe_box, input_gcode) for _, probe_box, input_gcode in NO_HIT_PROBE_CASES],
    ids=[case_id for case_id, _, _ in NO_HIT_PROBE_CASES],
)
def test_application_rejects_probing_when_no_trip_occurs(
    submission_command: tuple[str, ...],
    probe_box: ProbeBox,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_rs274_invalid_input(
        submission_command,
        input_gcode=input_gcode,
        probe_box=probe_box,
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )
