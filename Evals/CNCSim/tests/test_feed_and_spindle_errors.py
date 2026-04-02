from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input


# RS274 section 3.7.2 explicitly says the S number may not be negative.
def test_application_rejects_negative_spindle_speed(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="S-1\n",
        tmp_path=tmp_path,
    )
