from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim, with_default_rotary_axes

PositionTrackingCase = tuple[str, str, dict[str, float]]

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0 A0.0 B0.0 C0.0\nG54\nG94\n"

POSITION_TRACKING_CASES: list[PositionTrackingCase] = [
    (
        "absolute-xyz",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 X1.0 Y2.0 Z3.0\n",
        {"x": 1.0, "y": 2.0, "z": 3.0},
    ),
    (
        "absolute-abc-does-not-normalize-rotary-values",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 A370.0 B-45.0 C720.0\n",
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 370.0, "b": -45.0, "c": 720.0},
    ),
    (
        "absolute-xyz-from-parameter-values",
        ZERO_OFFSET_P1_SETUP
        +
        "#1=1.5\n"
        "#2=2.5\n"
        "#3=3.5\n"
        "G90\n"
        "G0 X#1 Y#2 Z#3\n",
        {"x": 1.5, "y": 2.5, "z": 3.5},
    ),
    (
        "absolute-xyz-from-expressions",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 X[1+2] Y[8/2] Z[5-2]\n",
        {"x": 3.0, "y": 4.0, "z": 3.0},
    ),
    (
        "absolute-abc-from-parameter-values-and-expressions",
        ZERO_OFFSET_P1_SETUP
        +
        "#1=10.0\n"
        "#2=3.0\n"
        "#3=30.0\n"
        "G90\n"
        "G0 A#1 B[6*7] C##2\n",
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 10.0, "b": 42.0, "c": 30.0},
    ),
    # RS274 sections 2.1.2.10 and 3.5.7: when length units change, the
    # numbers representing current position must be adjusted even without axis
    # motion.
    (
        "g20-converts-current-position-numerically-without-motion",
        "G21\n"
        + ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G0 X25.4 Y50.8 Z76.2\n"
        + "G20\n",
        {"x": 1.0, "y": 2.0, "z": 3.0},
    ),
    # RS274 sections 2.1.2.10 and 3.5.7: the same current-position rescaling
    # requirement applies when switching from inches to millimeters.
    (
        "g21-converts-current-position-numerically-without-motion",
        "G20\n"
        + ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G0 X1.0 Y2.0 Z3.0\n"
        + "G21\n",
        {"x": 25.4, "y": 50.8, "z": 76.2},
    ),
    (
        "g21-converts-xyz-but-leaves-abc-unchanged",
        "G20\n"
        + ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G0 X1.0 Y2.0 Z3.0 A30.0 B45.0 C60.0\n"
        + "G21\n",
        {"x": 25.4, "y": 50.8, "z": 76.2, "a": 30.0, "b": 45.0, "c": 60.0},
    ),
    # RS274 section 4.3.3.2: the effective location of the program origin
    # should not change when units change. The harness contract in
    # technical-requirements-prompt.md says machine_position is serialized in
    # the currently active length units.
    (
        "motion-after-unit-change-preserves-program-origin-location",
        "G21\n"
        "G10 L2 P1 X25.4 Y50.8 Z76.2\n"
        "G54\n"
        "G90\n"
        "G0 X0.0 Y0.0 Z0.0\n"
        "G20\n"
        "G0 X1.5 Y2.5 Z3.5\n",
        {"x": 2.5, "y": 4.5, "z": 6.5},
    ),
    # RS274 section 3.5.12: G53 moves to absolute machine coordinates.
    (
        "g53-uses-machine-coordinates",
        "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
        "G54\n"
        "G90\n"
        "G0 X0.0 Y0.0 Z0.0\n"
        "G92 X5.0 Y6.0 Z7.0\n"
        "G53 G0 X1.0 Y2.0 Z3.0\n",
        {"x": 1.0, "y": 2.0, "z": 3.0},
    ),
    (
        "g53-uses-machine-coordinates-for-rotary-axes",
        "G10 L2 P1 A10.0 B20.0 C30.0\n"
        "G54\n"
        "G90\n"
        "G0 A0.0 B0.0 C0.0\n"
        "G92 A5.0 B6.0 C7.0\n"
        "G53 G0 A1.0 B2.0 C3.0\n",
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 1.0, "b": 2.0, "c": 3.0},
    ),
    # RS274 section 3.5.12: G53 is not modal and must be programmed on each line.
    (
        "g53-is-not-modal",
        "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
        "G54\n"
        "G90\n"
        "G53 G0 X1.0 Y2.0 Z3.0\n"
        "G0 X4.0 Y5.0 Z6.0\n",
        {"x": 14.0, "y": 25.0, "z": 36.0},
    ),
    # RS274 section 3.5.12: G0 or G1 is optional on a G53 line if one is already active.
    (
        "g53-may-omit-g0-or-g1-when-linear-motion-is-active",
        "G10 L2 P1 X10.0 Y20.0 Z30.0\n"
        "G54\n"
        "G90\n"
        "G1 X0.0 Y0.0 Z0.0 F1.0\n"
        "G53 X4.0 Y5.0 Z6.0\n",
        {"x": 4.0, "y": 5.0, "z": 6.0},
    ),
    (
        "absolute-updates-only-programmed-axes",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 X1.0 Y2.0 Z3.0\n"
        "G1 X4.0\n",
        {"x": 4.0, "y": 2.0, "z": 3.0},
    ),
    (
        "incremental-xyz",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 X10.0 Y20.0 Z30.0\n"
        "G91\n"
        "G0 X1.0 Y2.0 Z3.0\n",
        {"x": 11.0, "y": 22.0, "z": 33.0},
    ),
    (
        "incremental-abc",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 A10.0 B20.0 C30.0\n"
        "G91\n"
        "G0 A1.0 B2.0 C3.0\n",
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 11.0, "b": 22.0, "c": 33.0},
    ),
    (
        "g1-updates-rotary-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G1 A45.0 B-30.0 C90.0 F10.0\n",
        {"x": 0.0, "y": 0.0, "z": 0.0, "a": 45.0, "b": -30.0, "c": 90.0},
    ),
    (
        "incremental-accumulates-from-current-position",
        ZERO_OFFSET_P1_SETUP
        +
        "G90\n"
        "G0 X10.0 Y20.0 Z30.0\n"
        "G91\n"
        "G0 X1.0 Y2.0 Z3.0\n"
        "G1 X-0.5 Y1.5 Z2.0\n",
        {"x": 10.5, "y": 23.5, "z": 35.0},
    ),
    (
        "g2-updates-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G2 X0.0 Y-1.0 Z4.0 I-1.0 J0.0\n",
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g2-updates-simultaneous-rotary-endpoints",
        ZERO_OFFSET_P1_SETUP
        +
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0 A10.0 B20.0 C30.0\n"
        "G2 X0.0 Y-1.0 Z4.0 A40.0 B50.0 C60.0 I-1.0 J0.0\n",
        {"x": 0.0, "y": -1.0, "z": 4.0, "a": 40.0, "b": 50.0, "c": 60.0},
    ),
    (
        "g2-accepts-parameter-values-in-i-and-j",
        ZERO_OFFSET_P1_SETUP
        +
        "#1=-1.0\n"
        "#2=0.0\n"
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G2 X0.0 Y-1.0 Z4.0 I#1 J#2\n",
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g2-updates-g18-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G18\n"
        "G90\n"
        "G0 X1.0 Y5.0 Z0.0\n"
        "G2 X0.0 Y4.0 Z-1.0 I-1.0 K0.0\n",
        {"x": 0.0, "y": 4.0, "z": -1.0},
    ),
    (
        "g2-accepts-expressions-in-i-and-k",
        ZERO_OFFSET_P1_SETUP
        +
        "G18\n"
        "G90\n"
        "G0 X1.0 Y5.0 Z0.0\n"
        "G2 X0.0 Y4.0 Z-1.0 I[-2/2] K[0+0]\n",
        {"x": 0.0, "y": 4.0, "z": -1.0},
    ),
    (
        "g3-updates-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G3 X0.0 Y1.0 Z6.0 I-1.0 J0.0\n",
        {"x": 0.0, "y": 1.0, "z": 6.0},
    ),
    (
        "g3-updates-g19-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G19\n"
        "G90\n"
        "G0 X5.0 Y1.0 Z0.0\n"
        "G3 X4.0 Y0.0 Z1.0 J-1.0 K0.0\n",
        {"x": 4.0, "y": 0.0, "z": 1.0},
    ),
    (
        "g3-accepts-parameter-values-in-j-and-k",
        ZERO_OFFSET_P1_SETUP
        +
        "#1=-1.0\n"
        "#2=0.0\n"
        "G19\n"
        "G90\n"
        "G0 X5.0 Y1.0 Z0.0\n"
        "G3 X4.0 Y0.0 Z1.0 J#1 K#2\n",
        {"x": 4.0, "y": 0.0, "z": 1.0},
    ),
    (
        "g2-radius-format-updates-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G2 X0.0 Y-1.0 Z4.0 R1.0\n",
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g2-radius-format-accepts-expressions-in-r",
        ZERO_OFFSET_P1_SETUP
        +
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G2 X0.0 Y-1.0 Z4.0 R[0.5+0.5]\n",
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g2-radius-format-updates-g18-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G18\n"
        "G90\n"
        "G0 X1.0 Y5.0 Z0.0\n"
        "G2 X0.0 Y4.0 Z-1.0 R1.0\n",
        {"x": 0.0, "y": 4.0, "z": -1.0},
    ),
    (
        "g3-radius-format-updates-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G17\n"
        "G90\n"
        "G0 X1.0 Y0.0 Z5.0\n"
        "G3 X0.0 Y1.0 Z6.0 R1.0\n",
        {"x": 0.0, "y": 1.0, "z": 6.0},
    ),
    (
        "g3-radius-format-updates-g19-arc-endpoint",
        ZERO_OFFSET_P1_SETUP
        +
        "G19\n"
        "G90\n"
        "G0 X5.0 Y1.0 Z0.0\n"
        "G3 X4.0 Y0.0 Z1.0 R1.0\n",
        {"x": 4.0, "y": 0.0, "z": 1.0},
    ),
]

POSITION_TRACKING_PARAMS = [
    (input_gcode, expected_machine_position)
    for _, input_gcode, expected_machine_position in POSITION_TRACKING_CASES
]


# See CNCSim/prompt/docs/RS274NGC.md section 2.1.2.10 "Current Position":
# the controller always has a current position, but the spec does not assign a
# fixed startup machine location or startup work-offset values. These cases
# therefore explicitly activate coordinate system 1 with zero offsets and
# explicitly select G94 so the assertions isolate motion tracking rather than
# work-offset behavior or an assumed startup feed-rate mode.
# See sections 3.5.1 and 3.5.2 for linear motion with axis words, section
# 3.5.3 for G2/G3 arc endpoint programming in the selected plane, section
# 3.5.3.1 for radius-format arcs, and section 3.5.17 for how G90/G91 control
# whether axis values are interpreted as absolute positions or incremental
# offsets. RS274 section 2.1.2.2 defines A/B/C as wrapped linear axes measured
# in degrees and unbounded in either direction, so these cases pin the raw
# rotary endpoint values without modulo normalization. Sections 2.1.2.10,
# 3.5.7, and 4.3.3.2 cover the explicit unit-change motion behavior exercised
# here, while the harness contract in technical-requirements-prompt.md defines
# that machine_position is serialized in the currently active length units for
# X/Y/Z and in degrees for A/B/C without G20/G21 conversion. Section 3.5.12
# says G53 moves use absolute machine coordinates, are non-modal, and may omit
# G0/G1 only when one of those linear modes is already active. Section 3.3.2
# says axis words and arc words such as I, J, K, and R take real values, and
# sections 3.3.2.2 and 3.3.2.3 define parameter values and expressions as real
# values, so those forms belong in the motion suite rather than the parameter
# suite.
@pytest.mark.parametrize(
    ("input_gcode", "expected_machine_position"),
    POSITION_TRACKING_PARAMS,
    ids=[case_id for case_id, _, _ in POSITION_TRACKING_CASES],
)
def test_application_tracks_machine_position(
    built_executable_path: Path,
    input_gcode: str,
    expected_machine_position: dict[str, float],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes(expected_machine_position)
