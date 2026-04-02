from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input

ParameterErrorCase = tuple[str, str]

PARAMETER_ERROR_CASES: list[ParameterErrorCase] = [
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting must evaluate to an integer in 1..5399.
    (
        "parameter-setting-index-too-low",
        "#0=1\n",
    ),
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting must evaluate to an integer in 1..5399.
    (
        "parameter-setting-index-too-high",
        "#5400=1\n",
    ),
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting must evaluate to an integer in 1..5399.
    (
        "parameter-setting-index-non-integer",
        "#1.5=1\n",
    ),
    # RS274 section 3.3.3 "Parameter Setting":
    # the parameter index in a setting is a real value, but it must still
    # evaluate to an integer in 1..5399.
    (
        "parameter-setting-expression-index-too-low",
        "#[1-1]=1\n",
    ),
    # RS274 section 3.3.2.2 "Parameter Value":
    # the parameter index in a read must evaluate to an integer in 1..5399.
    (
        "parameter-read-index-too-low",
        "G0 X#0\n",
    ),
    # RS274 section 3.3.2.2 "Parameter Value":
    # the parameter index in a read must evaluate to an integer in 1..5399.
    (
        "parameter-read-index-too-high",
        "G0 X#5400\n",
    ),
    # RS274 section 3.3.2.2 "Parameter Value":
    # the parameter index in a read must evaluate to an integer in 1..5399.
    (
        "parameter-read-index-non-integer",
        "G0 X#1.5\n",
    ),
    # RS274 section 3.3.2.3 "Expressions and Binary Operations":
    # an expression must end with a balancing right bracket.
    (
        "expression-missing-closing-bracket",
        "G0 X[1+2\n",
    ),
    # RS274 section 3.3.2.3 "Expressions and Binary Operations":
    # binary operations appear only inside expressions.
    (
        "binary-operation-outside-expression",
        "G0 X1+2\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # ATAN requires one expression divided by another expression.
    (
        "atan-missing-second-expression",
        "G0 XATAN[1]\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # unary operation names other than ATAN must be followed by an expression.
    (
        "unary-operation-missing-expression",
        "G0 XSIN30\n",
    ),
    # RS274 section 3.3.2.2 "Parameter Value":
    # repeated # indirection is allowed, but the resulting index must still
    # evaluate to an integer in 1..5399.
    (
        "parameter-read-indirection-index-non-integer",
        "#1=1.5\n"
        "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "G54\n"
        "G90\n"
        "G0 X##1\n",
    ),
    # RS274 section 3.3.2.1 "Number":
    # indexes are only considered close enough if within 0.0001 of an integer.
    (
        "parameter-setting-index-not-close-enough-to-integer",
        "#1.0002=1\n",
    ),
    # RS274 section 3.3.2.1 "Number":
    # G codes multiplied by ten are only considered close enough if within
    # 0.0001 of an integer.
    (
        "g-code-not-close-enough-to-supported-value",
        "G53.99998\n",
    ),
    # RS274 section 3.3.2.1 "Number":
    # M codes are only considered close enough if within 0.0001 of an integer.
    (
        "m-code-not-close-enough-to-integer",
        "M2.9998\n",
    ),
    # RS274 section 3.3.2.3 "Expressions and Binary Operations":
    # division by zero is not a valid expression result.
    (
        "expression-division-by-zero",
        "G0 X[1/0]\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # ACOS is only defined for inputs in [-1, 1].
    (
        "acos-argument-out-of-range",
        "G0 XACOS[2]\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # ASIN is only defined for inputs in [-1, 1].
    (
        "asin-argument-out-of-range",
        "G0 XASIN[-2]\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # LN is only defined for positive inputs.
    (
        "ln-zero",
        "G0 XLN[0]\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # LN is only defined for positive inputs.
    (
        "ln-negative",
        "G0 XLN[-1]\n",
    ),
    # RS274 section 3.3.2.4 "Unary Operation Value":
    # SQRT is only defined for non-negative inputs.
    (
        "sqrt-negative",
        "G0 XSQRT[-1]\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md sections 3.3.2.2 "Parameter Value",
# 3.3.3 "Parameter Setting", and Appendix E. This file covers only
# spec-defined invalid parameter usage. Expressions such as X[1+2], parameter
# settings like #1=[2+3], and repeated # indirection like ##2 are spec-valid
# and therefore are intentionally not asserted as failures here.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in PARAMETER_ERROR_CASES],
    ids=[case_id for case_id, _ in PARAMETER_ERROR_CASES],
)
def test_application_rejects_invalid_parameter_usage(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
