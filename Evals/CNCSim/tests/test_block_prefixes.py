from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import (
    run_cncsim,
    run_cncsim_invalid_input,
    with_default_rotary_axes,
)

BlockPrefixCase = tuple[str, str, dict[str, float]]

BLOCK_PREFIX_CASES: list[BlockPrefixCase] = [
    (
        "line-number-prefixes",
        "N10 G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "N20 G54\n"
        "N30 G90\n"
        "N40 G0 X1.0 Y2.0 Z3.0\n",
        {"x": 1.0, "y": 2.0, "z": 3.0},
    ),
    (
        "block-delete-prefixes",
        "/G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "/G54\n"
        "/G90\n"
        "/G0 X4.0 Y5.0 Z6.0\n",
        {"x": 4.0, "y": 5.0, "z": 6.0},
    ),
    (
        "block-delete-and-line-number-prefixes",
        "/N10 G10 L2 P1 X0.0 Y0.0 Z0.0\n"
        "/N20 G54\n"
        "/N30 G90\n"
        "/N40 G0 X7.0 Y8.0 Z9.0\n",
        {"x": 7.0, "y": 8.0, "z": 9.0},
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3 "Format of a Line", items 1
# and 2: a permissible line may begin with an optional block delete character
# "/" followed by an optional line number. Section 3.3.1 "Line Number"
# specifies the N-word syntax. With the block-delete switch off, slash-prefixed
# blocks are still parsed and executed.
@pytest.mark.parametrize(
    ("input_gcode", "expected_machine_position"),
    [
        (input_gcode, expected_machine_position)
        for _, input_gcode, expected_machine_position in BLOCK_PREFIX_CASES
    ],
    ids=[case_id for case_id, _, _ in BLOCK_PREFIX_CASES],
)
def test_application_supports_optional_block_prefixes(
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


# RS274 section 2.2.2 and section 3.3 say that if the block-delete switch is
# on, lines beginning with "/" are skipped entirely.
def test_application_skips_slash_prefixed_blocks_when_block_delete_is_on(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        block_delete=True,
        input_gcode=(
            "G10 L2 P1 X0.0 Y0.0 Z0.0\n"
            "G54\n"
            "G90\n"
            "G0 X1.0 Y2.0 Z3.0\n"
            "/N10 G0 X7.0 Y8.0 Z9.0\n"
        ),
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes({"x": 1.0, "y": 2.0, "z": 3.0})


# RS274 section 3.3 says the block-delete character is an optional prefix
# element at the beginning of a line, not a mid-line token.
def test_application_rejects_block_delete_character_mid_line(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="G0 X1.0 / Y2.0\n",
        tmp_path=tmp_path,
    )


# RS274 section 3.3.1 says line numbers must be integers from 0 to 99999.
def test_application_rejects_out_of_range_line_numbers(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="N100000 G0 X1.0\n",
        tmp_path=tmp_path,
    )
