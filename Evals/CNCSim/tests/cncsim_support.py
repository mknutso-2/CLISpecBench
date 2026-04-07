from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from rs274_parameters import (
    REQUIRED_NON_ROTATIONAL_PARAMETER_INDICES,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
)

ProbeBox = tuple[float, float, float, float, float, float]


def build_parameter_file(overrides: dict[int, float] | None = None) -> str:
    entries = {
        parameter_index: 0.0 for parameter_index in REQUIRED_NON_ROTATIONAL_PARAMETER_INDICES
    }
    entries[SELECTED_COORDINATE_SYSTEM_PARAMETER] = 1.0

    if overrides is not None:
        entries.update(overrides)

    lines = ["RS274 parameter file", ""]
    lines.extend(
        f"{parameter_index} {entries[parameter_index]}"
        for parameter_index in sorted(entries)
    )
    return "\n".join(lines) + "\n"


def _build_cncsim_command(
    submission_command: Sequence[str],
    *,
    block_delete: bool,
    carousel_slots: int | None,
    input_gcode: str,
    parameter_input_content: str | None,
    pass_parameter_output: bool,
    probe_box: ProbeBox | None,
    probe_tool: int | None,
    tool_table_content: str | None,
    tmp_path: Path,
) -> tuple[list[str], Path, Path | None]:
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    input_path.write_text(input_gcode, encoding="utf-8")

    command = [*submission_command, "--input", str(input_path), "--output", str(output_path)]

    if block_delete:
        command.append("--block-delete")

    if carousel_slots is not None:
        command.extend(["--carousel-slots", str(carousel_slots)])

    if parameter_input_content is not None:
        parameter_input_path = tmp_path / "parameters-in.var"
        parameter_input_path.write_text(parameter_input_content, encoding="utf-8")
        command.extend(["--parameter-input", str(parameter_input_path)])

    parameter_output_path: Path | None = None
    if pass_parameter_output:
        parameter_output_path = tmp_path / "parameters-out.var"
        command.extend(["--parameter-output", str(parameter_output_path)])

    if probe_box is not None:
        command.append("--probe-box")
        command.extend(str(value) for value in probe_box)

    if probe_tool is not None:
        command.extend(["--probe-tool", str(probe_tool)])

    if tool_table_content is not None:
        tool_table_path = tmp_path / "tool.tbl"
        tool_table_path.write_text(tool_table_content, encoding="utf-8")
        command.extend(["--tool-table", str(tool_table_path)])

    return command, output_path, parameter_output_path


def _run_cncsim_and_read_outputs(
    submission_command: Sequence[str],
    *,
    block_delete: bool,
    carousel_slots: int | None,
    input_gcode: str,
    parameter_input_content: str | None,
    pass_parameter_output: bool,
    probe_box: ProbeBox | None,
    probe_tool: int | None,
    tool_table_content: str | None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], str | None]:
    command, output_path, parameter_output_path = _build_cncsim_command(
        submission_command,
        block_delete=block_delete,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        probe_box=probe_box,
        probe_tool=probe_tool,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )

    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert output_path.is_file(), completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    parameter_output: str | None = None
    if parameter_output_path is not None:
        assert parameter_output_path.is_file(), completed.stderr
        parameter_output = parameter_output_path.read_text(encoding="utf-8")

    return completed, payload, parameter_output


def run_cncsim(
    submission_command: Sequence[str],
    *,
    block_delete: bool = False,
    carousel_slots: int | None = None,
    input_gcode: str,
    parameter_input_content: str | None = None,
    pass_parameter_output: bool = False,
    probe_box: ProbeBox | None = None,
    probe_tool: int | None = None,
    tool_table_content: str | None = None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed, payload, _ = _run_cncsim_and_read_outputs(
        submission_command,
        block_delete=block_delete,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        probe_box=probe_box,
        probe_tool=probe_tool,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )
    return completed, payload


def run_cncsim_invalid_input(
    submission_command: Sequence[str],
    *,
    block_delete: bool = False,
    carousel_slots: int | None = None,
    input_gcode: str,
    parameter_input_content: str | None = None,
    pass_parameter_output: bool = False,
    probe_box: ProbeBox | None = None,
    probe_tool: int | None = None,
    tool_table_content: str | None = None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed, payload = run_cncsim(
        submission_command,
        block_delete=block_delete,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        parameter_input_content=parameter_input_content,
        pass_parameter_output=pass_parameter_output,
        probe_box=probe_box,
        probe_tool=probe_tool,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 1, completed.stderr
    assert isinstance(payload["error"], str)
    assert payload["error"]
    return completed, payload


def run_cncsim_with_parameter_output(
    submission_command: Sequence[str],
    *,
    block_delete: bool = False,
    carousel_slots: int | None = None,
    input_gcode: str,
    parameter_input_content: str | None = None,
    probe_box: ProbeBox | None = None,
    probe_tool: int | None = None,
    tool_table_content: str | None = None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], str]:
    completed, payload, parameter_output = _run_cncsim_and_read_outputs(
        submission_command,
        block_delete=block_delete,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        parameter_input_content=parameter_input_content,
        pass_parameter_output=True,
        probe_box=probe_box,
        probe_tool=probe_tool,
        tool_table_content=tool_table_content,
        tmp_path=tmp_path,
    )
    assert parameter_output is not None
    return completed, payload, parameter_output


def get_parameter_value(payload: dict[str, Any], parameter_index: int) -> float:
    parameters = payload["parameters"]
    assert isinstance(parameters, dict)
    typed_parameters = cast(dict[str, object], parameters)

    value = typed_parameters[str(parameter_index)]
    assert isinstance(value, int | float)
    return float(value)


def with_default_rotary_axes(values: Mapping[str, float]) -> dict[str, float]:
    return {
        "x": float(values["x"]),
        "y": float(values["y"]),
        "z": float(values["z"]),
        "a": float(values.get("a", 0.0)),
        "b": float(values.get("b", 0.0)),
        "c": float(values.get("c", 0.0)),
    }
