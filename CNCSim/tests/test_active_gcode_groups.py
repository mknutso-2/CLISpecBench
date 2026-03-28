from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from swe_buildbench.cncsim.modal_groups import GCODE_MODAL_GROUP_DISTANCE_MODE


def test_application_tracks_active_gcode_groups(
    built_executable_path: Path,
    tmp_path: Path,
) -> None:
    _, payload = _run_cncsim(
        built_executable_path,
        input_gcode=(
            "G90\n"
            "G91\n"
        ),
        tmp_path=tmp_path,
    )

    assert payload["active_modal_codes"][GCODE_MODAL_GROUP_DISTANCE_MODE] == "G91"


def _run_cncsim(
    executable_path: Path,
    *,
    input_gcode: str,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    input_path.write_text(input_gcode, encoding="utf-8")

    completed = subprocess.run(
        [str(executable_path), "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert output_path.is_file(), completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return completed, payload
