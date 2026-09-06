from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from rs274_support import RS274_INVOCATION_TIMEOUT_SECONDS, read_json_object


# RS274 section 3.1 allows blank lines before a percent opener and whitespace
# around each delimiter. A matching second percent terminates useful content;
# an opener without a closer is an error. These are raw complete files, so do
# not use the behavioral-body wrapper in run_rs274. This gate identifies the
# percent parser prerequisite used by the rest of the suite explicitly.
@pytest.mark.parametrize(
    ("program", "expected_returncode"),
    [
        ("\n  %  \nG90\n % \nG999\n", 0),
        ("%\nG90\n", 1),
    ],
    ids=["second-percent-ends-useful-content", "percent-opener-requires-closer"],
)
def test_application_handles_percent_delimited_files(
    submission_command: tuple[str, ...],
    program: str,
    expected_returncode: int,
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    input_path.write_text(program, encoding="utf-8")
    completed = subprocess.run(
        [*submission_command, "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        check=False,
        text=True,
        timeout=RS274_INVOCATION_TIMEOUT_SECONDS,
    )
    assert completed.returncode == expected_returncode, completed.stderr
    assert read_json_object(output_path), "Interpreter completion must produce a JSON result"
