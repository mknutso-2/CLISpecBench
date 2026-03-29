from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim


def build_parameter_file() -> str:
    entries: list[tuple[int, float]] = [
        (5161, 0.0),
        (5162, 0.0),
        (5163, 0.0),
        (5181, 0.0),
        (5182, 0.0),
        (5183, 0.0),
        (5211, 0.0),
        (5212, 0.0),
        (5213, 0.0),
        (5220, 1.0),
    ]
    for system_number in range(1, 10):
        base = 5221 + ((system_number - 1) * 20)
        entries.extend(
            [
                (base, 0.0),
                (base + 1, 0.0),
                (base + 2, 0.0),
            ]
        )

    lines = ["RS274 parameter file", ""]
    lines.extend(f"{parameter_index} {value}" for parameter_index, value in entries)
    return "\n".join(lines) + "\n"


CLI_CASES: list[tuple[str, str | None, bool]] = [
    ("parameter-input-only", build_parameter_file(), False),
    ("parameter-output-only", None, True),
    ("parameter-input-and-output", build_parameter_file(), True),
]


# These flags are currently a harness-contract surface only. This test checks
# only that the executable accepts the optional parameter-file CLI arguments and
# still runs successfully; it does not yet assert parameter-file read/write
# semantics.
@pytest.mark.parametrize(
    ("parameter_input_content", "pass_parameter_output"),
    [
        (parameter_input_content, pass_parameter_output)
        for _, parameter_input_content, pass_parameter_output in CLI_CASES
    ],
    ids=[case_id for case_id, _, _ in CLI_CASES],
)
def test_application_accepts_parameter_file_cli_arguments(
    built_executable_path: Path,
    parameter_input_content: str | None,
    pass_parameter_output: bool,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="G90\nG0 X1.0 Y2.0 Z3.0\n",
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == {"x": 1.0, "y": 2.0, "z": 3.0}
