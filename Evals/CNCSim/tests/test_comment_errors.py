from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim_invalid_input

CommentErrorCase = tuple[str, str]

COMMENT_ERROR_CASES: list[CommentErrorCase] = [
    (
        "non-printable-comment-character",
        "G0 X1.0 (\x07)\n",
    ),
    (
        "nested-parenthetical-comment",
        "G0 X1.0 (outer (inner))\n",
    ),
    (
        "unterminated-parenthetical-comment",
        "G0 X1.0 (missing close\n",
    ),
    (
        "unmatched-right-parenthesis",
        "G0 X1.0 )\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.4 "Comments and Messages"
# and Appendix E: comments may contain only comment_character values, comments
# may not be nested, and a left parenthesis must be matched by a right
# parenthesis before the end of the line. Input not explicitly allowed by the
# line grammar is illegal, so an unmatched right parenthesis is rejected.
@pytest.mark.parametrize(
    "input_gcode",
    [input_gcode for _, input_gcode in COMMENT_ERROR_CASES],
    ids=[case_id for case_id, _ in COMMENT_ERROR_CASES],
)
def test_application_rejects_invalid_parenthetical_comments(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
