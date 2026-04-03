from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import (
    get_parameter_value,
    run_cncsim,
    with_default_rotary_axes,
)
from rs274_parameters import (
    coordinate_system_xyz_parameter_indices,
    coordinate_system_xyzabc_parameter_indices,
)

CoordinateSystemOffsetCase = tuple[str, str, dict[str, dict[str, float]]]

COORDINATE_SYSTEM_OFFSET_CASES: list[CoordinateSystemOffsetCase] = [
    (
        "g10-sets-coordinate-system-1-offsets",
        "G10 L2 P1 X3.5 Y17.2 Z-4.0\n",
        {
            "1": {"x": 3.5, "y": 17.2, "z": -4.0},
        },
    ),
    (
        "g10-sets-coordinate-system-1-rotary-offsets",
        "G10 L2 P1 A10.0 B20.0 C30.0\n",
        {
            "1": {"x": 0.0, "y": 0.0, "z": 0.0, "a": 10.0, "b": 20.0, "c": 30.0},
        },
    ),
    (
        "g10-accepts-parameter-values-in-g-l-p-and-axis-words",
        "#100=10\n"
        "#101=2\n"
        "#102=1\n"
        "#103=3.5\n"
        "#104=17.2\n"
        "#105=-4.0\n"
        "G#100 L#101 P#102 X#103 Y#104 Z#105\n",
        {
            "1": {"x": 3.5, "y": 17.2, "z": -4.0},
        },
    ),
    (
        "g10-accepts-expressions-in-g-l-p-and-axis-words",
        "G[5*2] L[1+1] P[1] X[7/2] Y[86/5] Z[-2-2]\n",
        {
            "1": {"x": 3.5, "y": 17.2, "z": -4.0},
        },
    ),
    (
        "offsets-serialize-in-the-currently-active-length-units",
        "G21\nG10 L2 P1 X25.4 Y50.8 Z76.2\nG20\n",
        {
            "1": {"x": 1.0, "y": 2.0, "z": 3.0},
        },
    ),
    (
        "g10-updates-only-programmed-axes",
        "G10 L2 P2 X1.0 Y2.0 Z3.0\nG10 L2 P2 X4.5 Z-1.0\n",
        {
            "2": {"x": 4.5, "y": 2.0, "z": -1.0},
        },
    ),
    (
        "g10-keeps-coordinate-systems-independent",
        "G10 L2 P1 X1.0 Y2.0 Z3.0\nG10 L2 P3 X7.0 Y8.0 Z9.0\n",
        {
            "1": {"x": 1.0, "y": 2.0, "z": 3.0},
            "3": {"x": 7.0, "y": 8.0, "z": 9.0},
        },
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.2.2 for the nine program
# coordinate systems and section 3.5.5 for G10 L2 Pn setting the stored origin
# of a selected coordinate system in absolute coordinates. Section 3.3.2 says
# words take real values, and sections 3.3.2.2 and 3.3.2.3 define parameter
# values and expressions as real values, so the supported G, L, P, and axis
# words on a G10 block should accept those forms. Section 4.3.3.2 says the
# effective program-origin location should not change when units change, and
# the harness contract in technical-requirements-prompt.md says
# coordinate_system_offsets are serialized in the currently active length
# units. Axis words omitted from a later G10 block keep their previously stored
# values.
@pytest.mark.parametrize(
    ("input_gcode", "expected_offsets"),
    [
        (input_gcode, expected_offsets)
        for _, input_gcode, expected_offsets in COORDINATE_SYSTEM_OFFSET_CASES
    ],
    ids=[case_id for case_id, _, _ in COORDINATE_SYSTEM_OFFSET_CASES],
)
def test_application_tracks_g10_coordinate_system_offsets(
    built_executable_path: Path,
    input_gcode: str,
    expected_offsets: dict[str, dict[str, float]],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    for system_number, expected_offset in expected_offsets.items():
        assert payload["coordinate_system_offsets"][system_number] == with_default_rotary_axes(
            expected_offset
        )


@pytest.mark.parametrize(
    ("input_gcode", "expected_offset", "expected_parameter_values"),
    [
        (
            # In preliminary testing, no model passes this test.
            # Section 4.3.3.3: "All other stored values which involve length
            # units are not changed, including: coordinate system offsets."
            # Section 4.3.3.2: "The effective location of the program origin
            # should not change when units change."
            # The serialization expectation (25.4/50.8/76.2 after G21) comes
            # from the harness contract ("Serialize coordinate_system_offsets
            # in the currently active RS274 length units"), not RS274 alone.
            # This is intentional: the benchmark tests the full prompt, not
            # just the spec in isolation.
            "G20\nG10 L2 P1 X1.0 Y2.0 Z3.0 A10.0 B20.0 C30.0\nG21\n",
            {"x": 25.4, "y": 50.8, "z": 76.2, "a": 10.0, "b": 20.0, "c": 30.0},
            {"x": 1.0, "y": 2.0, "z": 3.0, "a": 10.0, "b": 20.0, "c": 30.0},
        ),
        (
            "G21\nG10 L2 P1 X25.4 Y50.8 Z76.2 A10.0 B20.0 C30.0\nG20\n",
            {"x": 1.0, "y": 2.0, "z": 3.0, "a": 10.0, "b": 20.0, "c": 30.0},
            {"x": 25.4, "y": 50.8, "z": 76.2, "a": 10.0, "b": 20.0, "c": 30.0},
        ),
    ],
    ids=["g20-to-g21", "g21-to-g20"],
)
def test_coordinate_system_offset_parameters_remain_raw_across_unit_changes(
    built_executable_path: Path,
    input_gcode: str,
    expected_offset: dict[str, float],
    expected_parameter_values: dict[str, float],
    tmp_path: Path,
) -> None:
    # RS274 section 4.3.3.2 says the effective program-origin location should
    # not change when units change, while section 4.3.3.3 says stored
    # coordinate-system offsets are not numerically changed by a unit switch.
    # The harness contract in technical-requirements-prompt.md serializes
    # coordinate_system_offsets in the currently active length units, while the
    # backing parameters remain at their raw stored values from RS274.
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    cs1_x_parameter, cs1_y_parameter, cs1_z_parameter = coordinate_system_xyz_parameter_indices(1)
    (_, _, _, cs1_a_parameter, cs1_b_parameter, cs1_c_parameter) = (
        coordinate_system_xyzabc_parameter_indices(1)
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["coordinate_system_offsets"]["1"] == with_default_rotary_axes(expected_offset)
    assert get_parameter_value(payload, cs1_x_parameter) == expected_parameter_values["x"]
    assert get_parameter_value(payload, cs1_y_parameter) == expected_parameter_values["y"]
    assert get_parameter_value(payload, cs1_z_parameter) == expected_parameter_values["z"]
    assert get_parameter_value(payload, cs1_a_parameter) == expected_parameter_values["a"]
    assert get_parameter_value(payload, cs1_b_parameter) == expected_parameter_values["b"]
    assert get_parameter_value(payload, cs1_c_parameter) == expected_parameter_values["c"]
