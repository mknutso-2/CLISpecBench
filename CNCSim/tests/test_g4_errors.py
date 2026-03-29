from __future__ import annotations

from pathlib import Path

from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input


# See CNCSim/prompt/docs/RS274NGC.md section 3.5.4 "Dwell -- G4": it is an
# error if the P number is negative.
def test_application_rejects_negative_g4_p(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode="G4 P-0.5\n",
        tmp_path=tmp_path,
    )
