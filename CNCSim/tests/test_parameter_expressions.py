from __future__ import annotations

import math
from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

BinaryExpressionCase = tuple[str, str, float]
UnaryOperationCase = tuple[str, str, float]


# RS274 section 3.3.2.3 "Expressions and Binary Operations" explicitly allows
# expressions as real values and defines the supported binary operators and
# their precedence.
BINARY_EXPRESSION_CASES: list[BinaryExpressionCase] = [
    ("precedence", "[1+2*3-4/5]", 6.2),
    ("power", "[2**3.0]", 8.0),
    ("modulo", "[15MOD4.0]", 3.0),
    ("logical-or", "[0OR1]", 1.0),
    ("logical-and", "[2AND2]", 1.0),
    ("logical-xor", "[2XOR2]", 0.0),
    ("nested", "[2+[3*4]]", 14.0),
]


# RS274 section 3.3.2.4 "Unary Operation Value" explicitly defines these
# unary operations, including degree-based trig behavior and ATAN's two-
# expression form.
UNARY_OPERATION_CASES: list[UnaryOperationCase] = [
    ("abs", "ABS[-1.23]", 1.23),
    ("acos", "ACOS[0.7071067811865476]", 45.0),
    ("asin", "ASIN[1.0]", 90.0),
    ("atan", "ATAN[1.7320508075688772]/[1.0]", 60.0),
    ("cos", "COS[0.0]", 1.0),
    ("exp", "EXP[2.30258509299]", 10.0),
    ("fix", "FIX[-2.8]", -3.0),
    ("fup", "FUP[-2.8]", -2.0),
    ("ln", "LN[10.0]", 2.302585093),
    ("round", "ROUND[9.975]", 10.0),
    ("sin", "SIN[30]", 0.5),
    ("sqrt", "SQRT[3]", 1.732050808),
    ("tan", "TAN[45]", 1.0),
]


@pytest.mark.parametrize(
    ("expression", "expected_x"),
    [(expression, expected_x) for _, expression, expected_x in BINARY_EXPRESSION_CASES],
    ids=[case_id for case_id, _, _ in BINARY_EXPRESSION_CASES],
)
def test_application_evaluates_binary_expressions_in_axis_words(
    built_executable_path: Path,
    expression: str,
    expected_x: float,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            f"G0 X{expression}\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert math.isclose(
        float(payload["machine_position"]["x"]),
        expected_x,
        abs_tol=1e-6,
    )


@pytest.mark.parametrize(
    ("unary_value", "expected_x"),
    [(unary_value, expected_x) for _, unary_value, expected_x in UNARY_OPERATION_CASES],
    ids=[case_id for case_id, _, _ in UNARY_OPERATION_CASES],
)
def test_application_evaluates_unary_operation_values(
    built_executable_path: Path,
    unary_value: str,
    expected_x: float,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            f"G0 X{unary_value}\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert math.isclose(
        float(payload["machine_position"]["x"]),
        expected_x,
        abs_tol=1e-5,
    )


def test_application_supports_expression_based_parameter_indices(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    # RS274 sections 3.3.2.2 and 3.3.3 define parameter_index as a real value,
    # and Appendix E makes that grammar explicit.
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#[1+2]=7\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X#3\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 7.0, "y": 0.0, "z": 0.0}


def test_application_supports_repeated_parameter_indirection(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2.2 explicitly says the # character may be repeated.
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "#1=2\n"
            "##1=0.375\n"
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X#2\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 0.375, "y": 0.0, "z": 0.0}


def test_application_reads_expressions_in_g_l_p_and_m_words(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2 says a word is a letter followed by a real value, and
    # section 3.3.2.3 says a real value may be an expression.
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "G[5*2] L[1+1] P[1] X[7/2] Y0.0 Z0.0\n"
            "G[53+1]\n"
            "G90\n"
            "M[1+2]\n"
            "G0 X1.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 4.5, "y": 0.0, "z": 0.0}
    assert payload["spindle_direction"] == "CW"


def test_application_reads_expressions_in_feed_spindle_and_tooling_words(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2 says a mid-line word is a legal letter plus a real
    # value, so the currently supported F/S/T/H/D words also accept expressions.
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=(
            "F[500/2]\n"
            "S[600*2] M3\n"
            "T[3+3]\n"
            "G43 H[3+4]\n"
            "G41 D[2+2]\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["feed_rate"] == 250.0
    assert payload["spindle_speed"] == 1200.0
    assert payload["spindle_direction"] == "CW"
    assert payload["selected_tool"] == 6
    assert payload["tool_length_offset_index"] == 7
    assert payload["cutter_radius_compensation_number"] == 4
