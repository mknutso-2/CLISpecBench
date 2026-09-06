from __future__ import annotations

import math
from pathlib import Path

import pytest

from rs274_support import (
    mapping_field,
    run_rs274,
    with_default_rotary_axes,
)

BinaryExpressionCase = tuple[str, str, float]
UnaryOperationCase = tuple[str, str, float]


def assert_close(value: object, expected: float, *, abs_tol: float) -> None:
    assert isinstance(value, int | float)
    assert math.isclose(float(value), expected, abs_tol=abs_tol)


# RS274 section 3.3.2.3 "Expressions and Binary Operations" explicitly allows
# expressions as real values and defines the supported binary operators and
# their precedence.
BINARY_EXPRESSION_CASES: list[BinaryExpressionCase] = [
    ("precedence", "[1+2*3-4/5]", 6.2),
    ("power", "[2**3.0]", 8.0),
    ("modulo", "[15MOD4.0]", 3.0),
    ("modulo-real", "[5.5MOD2.0]", 1.5),
    ("logical-or", "[0OR1]", 1.0),
    ("logical-and", "[2AND2]", 1.0),
    ("logical-xor", "[2XOR2]", 0.0),
    ("logical-reals", "[0.25AND2.5]", 1.0),
    ("nested", "[2+[3*4]]", 14.0),
    ("left-to-right-group1", "[2**3**2]", 64.0),
    ("left-to-right-group2", "[8/4/2]", 1.0),
    ("left-to-right-group3", "[9-3-2]", 4.0),
    ("spec-example-precedence", "[2.0/3*1.5-5.5/11.0]", 0.5),
    ("power-before-group2", "[2*3**2]", 18.0),
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
    ("fix-positive", "FIX[2.8]", 2.0),
    ("fix", "FIX[-2.8]", -3.0),
    ("fup-positive", "FUP[2.8]", 3.0),
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
    submission_command: tuple[str, ...],
    expression: str,
    expected_x: float,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(f"G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X{expression}\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert_close(mapping_field(payload, "machine_position").get("x"), expected_x, abs_tol=1e-6)


@pytest.mark.parametrize(
    ("unary_value", "expected_x"),
    [(unary_value, expected_x) for _, unary_value, expected_x in UNARY_OPERATION_CASES],
    ids=[case_id for case_id, _, _ in UNARY_OPERATION_CASES],
)
def test_application_evaluates_unary_operation_values(
    submission_command: tuple[str, ...],
    unary_value: str,
    expected_x: float,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=(f"G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X{unary_value}\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert_close(mapping_field(payload, "machine_position").get("x"), expected_x, abs_tol=1e-5)


# The technical requirements allow any final parameter value to be omitted.
# Observe expression-based writes through the required machine position after
# the existing G0 read, rather than depending on optional parameter reporting.
def test_application_supports_expression_based_parameter_indices(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 sections 3.3.2.2 and 3.3.3 define parameter_index as a real value,
    # and Appendix E makes that grammar explicit.
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#[1+2]=7\nG10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X#3\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "machine_position").get("x") == 7.0


def test_application_supports_expression_valued_parameter_settings(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.3 defines the right-hand side of a parameter setting as
    # a real value, and section 3.3.2.3 says a real value may be an expression.
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#1=[2+3]\nG10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X#1\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "machine_position").get("x") == 5.0


def test_application_supports_bracketed_parameter_reads(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2.2 explicitly distinguishes #1+2 from #[1+2].
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#1=5\n#3=9\nG10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X[#1+2] Y#[1+2]\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 7.0, "y": 9.0, "z": 0.0}
    )


def test_application_supports_repeated_parameter_indirection(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2.2 explicitly says the # character may be repeated.
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#1=2\n##1=0.375\nG10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X#2\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "machine_position").get("x") == 0.375


def test_application_evaluates_expressions_before_parameter_settings_take_effect(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 sections 3.3.2.3 and 3.3.3 say expressions on a line are evaluated
    # when the line is read, and parameter settings do not take effect until
    # after all parameter values on that line have been found.
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#3=15\nG10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\n#3=[2+4] G0 X[#3+1]\nG0 Y#3\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 16.0, "y": 6.0, "z": 0.0}
    )


def test_application_accepts_close_to_integer_parameter_indices(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2.1 says values that are supposed to be close to an
    # integer are acceptable if they are within 0.0001 of one.
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("#1.00005=[2+3]\nG10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X#1.00005\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert mapping_field(payload, "machine_position").get("x") == 5.0


def test_application_accepts_close_to_integer_g_and_m_codes_from_expressions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # RS274 section 3.3.2.1 says M codes and G codes multiplied by ten are
    # considered close enough if within 0.0001 of an integer.
    # Set positive speed on the M-code line so the CW assertion tests the
    # parsed M3, not an unspecified startup S (sections 3.6.2 and 3.7.2).
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("G10 L2 P2 X3.0 Y0.0 Z0.0\nG[54.999995]\nG90\nS100 M[2.99995]\nG0 X1.0\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("machine_position") == with_default_rotary_axes(
        {"x": 4.0, "y": 0.0, "z": 0.0}
    )
    assert payload.get("spindle_direction") == "CW"


def test_application_evaluates_unary_values_inside_expressions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # Appendix E makes unary_combo a real_value, and expressions are built from
    # real_value terms, so unary operations must be usable inside expressions.
    completed, payload = run_rs274(
        submission_command,
        input_gcode=("G10 L2 P1 X0.0 Y0.0 Z0.0\nG54\nG90\nG0 X[1+SIN[30]]\n"),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert_close(mapping_field(payload, "machine_position").get("x"), 1.5, abs_tol=1e-6)
