from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

CommentParsingCase = tuple[str, str, dict[str, float]]

COMMENT_PARSING_CASES: list[CommentParsingCase] = [
    (
        "empty-parenthetical-comments",
        "G10 L2 P1 X0.0 Y0.0 Z0.0 ()\n"
        "G54 ()\n"
        "G90 ()\n"
        "G0 X0.5 Y1.5 Z2.5 ()\n",
        {"x": 0.5, "y": 1.5, "z": 2.5},
    ),
    (
        "end-of-line-parenthetical-comments",
        "G10 L2 P1 X0.0 Y0.0 Z0.0 (set coordinate system 1)\n"
        "G54 (activate coordinate system 1)\n"
        "G90 (absolute distance mode)\n"
        "G0 X1.0 Y2.0 Z3.0 (rapid move)\n",
        {"x": 1.0, "y": 2.0, "z": 3.0},
    ),
    (
        "leading-comments-before-words",
        "(set coordinate system 1) G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "(activate it) G54\n"
        "(absolute mode) G90\n"
        "(move) G0 X4.0 Y5.0 Z6.0\n",
        {"x": 4.0, "y": 5.0, "z": 6.0},
    ),
    (
        "multiple-comments-on-one-line",
        "(first comment) G10 L2 P1 X0.0 Y0.0 Z0.0 (second comment)\n"
        "G54 (activate) (still activate)\n"
        "G90 (absolute) (message ignored)\n"
        "G0 X7.0 Y8.0 Z9.0 (move) (final comment)\n",
        {"x": 7.0, "y": 8.0, "z": 9.0},
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.4 "Comments and Messages"
# and Appendix E: ordinary_comment is "(" + {comment_character} + ")", and
# comment_character is any printable character plus space and tab except "("
# and ")". That makes empty comments legal. Section 3.3.5 says multiple
# comments on a line are legal if each comment is well-formed, and section
# 3.3.6 allows comments and words to be interleaved without changing the
# meaning of the line.
@pytest.mark.parametrize(
    ("input_gcode", "expected_machine_position"),
    [
        (input_gcode, expected_machine_position)
        for _, input_gcode, expected_machine_position in COMMENT_PARSING_CASES
    ],
    ids=[case_id for case_id, _, _ in COMMENT_PARSING_CASES],
)
def test_application_accepts_well_formed_parenthetical_comments(
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
    assert payload["machine_position"] == expected_machine_position
