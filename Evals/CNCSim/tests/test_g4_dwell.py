from __future__ import annotations

from pathlib import Path

from cncsim_support import run_cncsim, with_default_rotary_axes


# See CNCSim/prompt/docs/RS274NGC.md section 3.5.4 "Dwell -- G4": G4 P...
# dwells for the specified time, but the final-state payload exposes no dwell
# duration, so this test only verifies that a valid dwell line is accepted and
# does not disturb the rest of program execution.
def test_application_accepts_g4_dwell(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode="G90\nG0 X1.0 Y2.0 Z3.0\nG4 P0.5\nG0 X4.0 Y5.0 Z6.0\n",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["machine_position"] == with_default_rotary_axes({"x": 4.0, "y": 5.0, "z": 6.0})
