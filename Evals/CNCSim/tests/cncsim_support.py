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
CNCSIM_INVOCATION_TIMEOUT_SECONDS = 5


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
        timeout=CNCSIM_INVOCATION_TIMEOUT_SECONDS,
    )

    assert output_path.is_file(), completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    parameter_output: str | None = None
    if parameter_output_path is not None:
        assert parameter_output_path.is_file(), completed.stderr
        parameter_output = parameter_output_path.read_text(encoding="utf-8")

    return completed, payload, parameter_output


# v3.0 candidate: the behavioral tests that call run_cncsim then do
# `assert payload["error"] is None` (~180 sites across ~40 files) should move
# the schema check into a single gate test and use `payload.get("error") is
# None` in the behavioral assertions. Today a single conditional-emit bug in an
# agent's JSON writer (missing `"error": null` on success) fails every one of
# those tests with `KeyError: 'error'`, drowning the real behavioral signal —
# e.g. sonnet-4-6 cpp eval2/run3 lost 259 tests to this single cascade
# (see `official-results/CNCSIM/results-2_1_1.md` and `Eval-Design.md` §7.4).
# Intentionally not changed before V3.0 to avoid mid-version test-suite churn.
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


def _build_cncsim_trace_command(
    submission_command: Sequence[str],
    *,
    block_delete: bool,
    carousel_slots: int | None,
    input_gcode: str,
    parameter_input_content: str | None,
    probe_box: ProbeBox | None,
    probe_tool: int | None,
    tool_table_content: str | None,
    trace_time_step: float | None,
    trace_distance_step: float | None,
    trace_position_tolerance: float | None,
    tmp_path: Path,
) -> tuple[list[str], Path, Path, Path | None]:
    """Build a command that includes --trace-output.

    Returns (command, output_path, trace_path, parameter_output_path).
    """
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    trace_path = tmp_path / "trace.json"
    input_path.write_text(input_gcode, encoding="utf-8")

    command = [
        *submission_command,
        "--input", str(input_path),
        "--output", str(output_path),
        "--trace-output", str(trace_path),
    ]

    if trace_time_step is not None:
        command.extend(["--trace-time-step", str(trace_time_step)])
    if trace_distance_step is not None:
        command.extend(["--trace-distance-step", str(trace_distance_step)])
    if trace_position_tolerance is not None:
        command.extend(["--trace-position-tolerance", str(trace_position_tolerance)])

    if block_delete:
        command.append("--block-delete")
    if carousel_slots is not None:
        command.extend(["--carousel-slots", str(carousel_slots)])
    if parameter_input_content is not None:
        parameter_input_path = tmp_path / "parameters-in.var"
        parameter_input_path.write_text(parameter_input_content, encoding="utf-8")
        command.extend(["--parameter-input", str(parameter_input_path)])
    if probe_box is not None:
        command.append("--probe-box")
        command.extend(str(value) for value in probe_box)
    if probe_tool is not None:
        command.extend(["--probe-tool", str(probe_tool)])
    if tool_table_content is not None:
        tool_table_path = tmp_path / "tool.tbl"
        tool_table_path.write_text(tool_table_content, encoding="utf-8")
        command.extend(["--tool-table", str(tool_table_path)])

    return command, output_path, trace_path, None


def run_cncsim_trace(
    submission_command: Sequence[str],
    *,
    block_delete: bool = False,
    carousel_slots: int | None = None,
    input_gcode: str,
    parameter_input_content: str | None = None,
    probe_box: ProbeBox | None = None,
    probe_tool: int | None = None,
    tool_table_content: str | None = None,
    trace_time_step: float | None = None,
    trace_distance_step: float | None = None,
    trace_position_tolerance: float | None = None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], dict[str, Any]]:
    """Run cncsim with --trace-output and return (process, output_payload, trace_payload)."""
    command, output_path, trace_path, _ = _build_cncsim_trace_command(
        submission_command,
        block_delete=block_delete,
        carousel_slots=carousel_slots,
        input_gcode=input_gcode,
        parameter_input_content=parameter_input_content,
        probe_box=probe_box,
        probe_tool=probe_tool,
        tool_table_content=tool_table_content,
        trace_time_step=trace_time_step,
        trace_distance_step=trace_distance_step,
        trace_position_tolerance=trace_position_tolerance,
        tmp_path=tmp_path,
    )

    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        timeout=CNCSIM_INVOCATION_TIMEOUT_SECONDS,
    )

    assert output_path.is_file(), f"--output not written. stderr: {completed.stderr}"
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert trace_path.is_file(), f"--trace-output not written. stderr: {completed.stderr}"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))

    return completed, payload, trace


def reconstruct_state(trace: dict[str, Any], entry_index: int) -> dict[str, Any]:
    """Fold initial_state + deltas[0..entry_index] to get full state at that entry.

    Returns a dict with the same shape as the --output payload (minus "error").
    Useful for verifying that delta encoding correctly represents machine state.
    """
    state: dict[str, Any] = json.loads(json.dumps(trace["initial_state"]))
    for i in range(entry_index + 1):
        entry = trace["entries"][i]
        for key, value in entry.items():
            if key in ("line_number", "time", "motion_kind", "nonmodal_g_codes"):
                continue  # Trace-specific fields, not part of state.
            if key in ("machine_position", "coordinate_system_offsets",
                       "active_modal_g_codes", "active_modal_m_codes", "parameters"):
                if key not in state:
                    state[key] = {}
                if key == "coordinate_system_offsets":
                    for cs_key, cs_val in value.items():
                        if cs_key not in state[key]:
                            state[key][cs_key] = {}
                        state[key][cs_key].update(cs_val)
                else:
                    state[key].update(value)
            else:
                state[key] = value
    return state
