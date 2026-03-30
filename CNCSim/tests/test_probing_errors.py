from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import ProbeBox, run_cncsim_invalid_input

PROBE_TOOL = 2
PROBE_BOX: ProbeBox = (0.0, 10.0, 0.0, 10.0, 2.0, 4.0)
PROBE_TOOL_TABLE = """POCKET FMS TLO DIAMETER COMMENT

2 2 1.5 0.25 probe
"""

ProbeErrorCase = tuple[str, str]

PROBE_ERROR_CASES: list[ProbeErrorCase] = [
    (
        "g38-2-requires-linear-axis-word",
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "F10.0\n"
        "G38.2\n",
    ),
    (
        "g38-2-rejects-inverse-time-feed-rate-mode",
        "G20\n"
        "G90\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z5.0\n"
        "G93\n"
        "F1.0\n"
        "G38.2 Z0.0\n",
    ),
    (
        "g38-2-rejects-programmed-point-that-is-too-close",
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z5.0\n"
        "F10.0\n"
        "G38.2 Z4.995\n",
    ),
]


# RS274 section 3.5.9 explicitly makes these invalid uses of G38.2 errors:
# no X/Y/Z word, inverse-time feed rate mode, and a programmed point closer
# than 0.01 inch or 0.254 millimeter to the current point.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in PROBE_ERROR_CASES],
    ids=[case_id for case_id, _ in PROBE_ERROR_CASES],
)
def test_application_rejects_explicit_invalid_g38_2_uses(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tmp_path=tmp_path,
    )


# RS274 section 3.5.9 says the tool in the spindle must be a probe, and the
# technical requirements prompt defines --probe-tool as the probe designation
# used by the eval harness.
def test_application_requires_the_probe_tool_in_the_spindle(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="G20\nG90 G94\nT1 M6\nG0 X5.0 Y5.0 Z5.0\nF10.0\nG38.2 Z0.0\n",
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tmp_path=tmp_path,
    )


# RS274 section 4.3.6.6 explicitly says the spindle must not be turning when
# STRAIGHT_PROBE starts.
def test_application_rejects_probing_with_the_spindle_turning(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=(
            "G20\n"
            "G90 G94\n"
            "T2 M6\n"
            "G0 X5.0 Y5.0 Z5.0\n"
            "S500.0 M3\n"
            "F10.0\n"
            "G38.2 Z0.0\n"
        ),
        probe_box=PROBE_BOX,
        probe_tool=PROBE_TOOL,
        tmp_path=tmp_path,
    )


# RS274 section 4.3.6.6 explicitly says the probe must not already be tripped
# when STRAIGHT_PROBE starts. With tool length compensation active, the RS274
# controlled point is the compensated probe-tip position, so this case starts
# with the controlled point already inside the probe box.
def test_application_rejects_probing_when_the_probe_is_already_tripped(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=(
            "G20\n"
            "G90 G94\n"
            "T2 M6\n"
            "G0 X5.0 Y5.0 Z3.0\n"
            "G43 H2\n"
            "F10.0\n"
            "G38.2 Z0.0\n"
        ),
        probe_box=(0.0, 10.0, 0.0, 10.0, 0.0, 2.0),
        probe_tool=PROBE_TOOL,
        tool_table_content=PROBE_TOOL_TABLE,
        tmp_path=tmp_path,
    )


NoHitProbeCase = tuple[str, ProbeBox, str]

NO_HIT_PROBE_CASES: list[NoHitProbeCase] = [
    (
        "x-probe-no-hit",
        (0.0, 10.0, 0.0, 10.0, 0.0, 6.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X-5.0 Y5.0 Z3.0\n"
        "F10.0\n"
        "G38.2 X-1.0\n",
    ),
    (
        "y-probe-no-hit",
        (0.0, 10.0, 0.0, 10.0, 0.0, 6.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y-5.0 Z3.0\n"
        "F10.0\n"
        "G38.2 Y-1.0\n",
    ),
    (
        "z-probe-no-hit",
        (0.0, 10.0, 0.0, 10.0, 0.0, 4.0),
        "G20\n"
        "G90 G94\n"
        "T2 M6\n"
        "G0 X5.0 Y5.0 Z8.0\n"
        "F10.0\n"
        "G38.2 Z6.0\n",
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
    built_executable_path: Path,
    probe_box: ProbeBox,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        probe_box=probe_box,
        probe_tool=PROBE_TOOL,
        tmp_path=tmp_path,
    )
