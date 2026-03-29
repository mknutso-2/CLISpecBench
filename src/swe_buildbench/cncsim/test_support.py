from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast


def run_cncsim(
    executable_path: Path,
    *,
    input_gcode: str,
    parameter_input_content: str | None = None,
    pass_parameter_output: bool = False,
    tool_table_content: str | None = None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    input_path.write_text(input_gcode, encoding="utf-8")

    command = [str(executable_path), "--input", str(input_path), "--output", str(output_path)]
    if parameter_input_content is not None:
        parameter_input_path = tmp_path / "parameters-in.var"
        parameter_input_path.write_text(parameter_input_content, encoding="utf-8")
        command.extend(["--parameter-input", str(parameter_input_path)])
    if pass_parameter_output:
        parameter_output_path = tmp_path / "parameters-out.var"
        command.extend(["--parameter-output", str(parameter_output_path)])
    if tool_table_content is not None:
        tool_table_path = tmp_path / "tool.tbl"
        tool_table_path.write_text(tool_table_content, encoding="utf-8")
        command.extend(["--tool-table", str(tool_table_path)])

    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert output_path.is_file(), completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return completed, payload


def run_cncsim_invalid_input(
    executable_path: Path,
    *,
    input_gcode: str,
    parameter_input_content: str | None = None,
    pass_parameter_output: bool = False,
    tool_table_content: str | None = None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed, payload = run_cncsim(
        executable_path,
        input_gcode=input_gcode,
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 1, completed.stderr
    assert isinstance(payload["error"], str)
    assert payload["error"]
    return completed, payload


def get_parameter_value(payload: dict[str, Any], parameter_index: int) -> float:
    parameters = payload["parameters"]
    assert isinstance(parameters, dict)
    typed_parameters = cast(dict[str, object], parameters)

    value = typed_parameters[str(parameter_index)]
    assert isinstance(value, int | float)
    return float(value)
