from __future__ import annotations

from pathlib import Path

from cncsim_support import run_cncsim_invalid_input


# RS274 section 3.7.2 explicitly says the S number may not be negative.
def test_application_rejects_negative_spindle_speed(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        submission_command,
        input_gcode="S-1\n",
        tmp_path=tmp_path,
    )
