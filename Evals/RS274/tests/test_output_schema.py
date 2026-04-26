from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from rs274_support import run_rs274, run_rs274_trace

AXES = {"x", "y", "z", "a", "b", "c"}
REQUIRED_OUTPUT_KEYS = {
    "machine_position",
    "feed_rate",
    "spindle_speed",
    "spindle_direction",
    "cutter_radius_compensation_number",
    "tool_length_offset_index",
    "selected_tool",
    "tool_in_spindle",
    "active_modal_g_codes",
    "active_modal_m_codes",
    "coordinate_system_offsets",
    "parameters",
    "error",
}
REQUIRED_TRACE_KEYS = {
    "initial_state",
    "entries",
    "error_line_number",
    "error_block_segment_index",
}
TRACE_STATE_KEYS = REQUIRED_OUTPUT_KEYS - {"error"}
TRACE_ENTRY_KEYS = TRACE_STATE_KEYS | {
    "line_number",
    "time",
    "motion_kind",
    "nonmodal_g_codes",
}
NULLABLE_SCALARS = {
    "cutter_radius_compensation_number",
    "tool_length_offset_index",
    "selected_tool",
    "tool_in_spindle",
}


def assert_number(value: object) -> None:
    assert isinstance(value, int | float)
    assert not isinstance(value, bool)


def assert_axis_mapping(value: object, *, complete: bool) -> None:
    assert isinstance(value, dict)
    typed_value = cast(dict[str, object], value)
    if complete:
        assert set(typed_value) == AXES
    else:
        assert set(typed_value) <= AXES
        assert typed_value
    for axis_value in typed_value.values():
        assert_number(axis_value)


def assert_string_mapping(value: object) -> None:
    assert isinstance(value, dict)
    typed_value = cast(dict[str, object], value)
    for key, item in typed_value.items():
        assert isinstance(key, str)
        assert isinstance(item, str)
        assert item


def assert_parameters(value: object) -> None:
    assert isinstance(value, dict)
    typed_value = cast(dict[str, object], value)
    for key, item in typed_value.items():
        assert isinstance(key, str)
        assert key.isdecimal()
        assert_number(item)


def assert_coordinate_system_offsets(value: object, *, complete: bool) -> None:
    assert isinstance(value, dict)
    typed_value = cast(dict[str, object], value)
    if complete:
        assert set(typed_value) == {str(index) for index in range(1, 10)}
    for system_number, offsets in typed_value.items():
        assert isinstance(system_number, str)
        assert system_number.isdecimal()
        assert_axis_mapping(offsets, complete=complete)


def assert_nullable_scalar(value: object) -> None:
    if value is not None:
        assert isinstance(value, int)
        assert not isinstance(value, bool)


def assert_output_payload_schema(payload: dict[str, Any], *, expect_error: bool) -> None:
    typed_payload = cast(dict[str, object], payload)
    assert set(typed_payload) == REQUIRED_OUTPUT_KEYS
    if expect_error:
        assert isinstance(typed_payload["error"], str)
        assert typed_payload["error"]
        return

    assert_axis_mapping(typed_payload["machine_position"], complete=True)
    assert_number(typed_payload["feed_rate"])
    assert_number(typed_payload["spindle_speed"])
    assert typed_payload["spindle_direction"] in {"CW", "CCW", "OFF"}
    for field in NULLABLE_SCALARS:
        assert_nullable_scalar(typed_payload[field])
    assert_string_mapping(typed_payload["active_modal_g_codes"])
    assert_string_mapping(typed_payload["active_modal_m_codes"])
    assert_coordinate_system_offsets(typed_payload["coordinate_system_offsets"], complete=True)
    assert_parameters(typed_payload["parameters"])
    assert typed_payload["error"] is None


def assert_trace_initial_state_schema(value: object) -> None:
    assert isinstance(value, dict)
    typed_value = cast(dict[str, object], value)
    assert set(typed_value) == TRACE_STATE_KEYS
    assert_axis_mapping(typed_value["machine_position"], complete=True)
    assert_number(typed_value["feed_rate"])
    assert_number(typed_value["spindle_speed"])
    assert typed_value["spindle_direction"] in {"CW", "CCW", "OFF"}
    for field in NULLABLE_SCALARS:
        assert_nullable_scalar(typed_value[field])
    assert_string_mapping(typed_value["active_modal_g_codes"])
    assert_string_mapping(typed_value["active_modal_m_codes"])
    assert_coordinate_system_offsets(typed_value["coordinate_system_offsets"], complete=True)
    assert_parameters(typed_value["parameters"])


def assert_trace_entry_schema(entry: object) -> None:
    assert isinstance(entry, dict)
    typed_entry = cast(dict[str, object], entry)
    assert set(typed_entry) <= TRACE_ENTRY_KEYS
    assert isinstance(typed_entry["line_number"], int)
    assert_number(typed_entry["time"])
    assert "error" not in typed_entry

    if "machine_position" in typed_entry:
        assert_axis_mapping(typed_entry["machine_position"], complete=False)
    if "feed_rate" in typed_entry:
        assert_number(typed_entry["feed_rate"])
    if "spindle_speed" in typed_entry:
        assert_number(typed_entry["spindle_speed"])
    if "spindle_direction" in typed_entry:
        assert typed_entry["spindle_direction"] in {"CW", "CCW", "OFF"}
    for field in NULLABLE_SCALARS:
        if field in typed_entry:
            assert_nullable_scalar(typed_entry[field])
    if "active_modal_g_codes" in typed_entry:
        assert_string_mapping(typed_entry["active_modal_g_codes"])
    if "active_modal_m_codes" in typed_entry:
        assert_string_mapping(typed_entry["active_modal_m_codes"])
    if "coordinate_system_offsets" in typed_entry:
        assert_coordinate_system_offsets(typed_entry["coordinate_system_offsets"], complete=False)
    if "parameters" in typed_entry:
        assert_parameters(typed_entry["parameters"])
    if "motion_kind" in typed_entry:
        assert typed_entry["motion_kind"] in {"rapid", "feed"}
    if "nonmodal_g_codes" in typed_entry:
        nonmodal_g_codes = typed_entry["nonmodal_g_codes"]
        assert isinstance(nonmodal_g_codes, list)
        typed_codes = cast(list[object], nonmodal_g_codes)
        assert all(isinstance(code, str) and code for code in typed_codes)


def assert_trace_payload_schema(trace: dict[str, Any], *, expect_error: bool) -> None:
    typed_trace = cast(dict[str, object], trace)
    assert set(typed_trace) == REQUIRED_TRACE_KEYS
    assert_trace_initial_state_schema(typed_trace["initial_state"])
    assert isinstance(typed_trace["entries"], list)
    entries = cast(list[object], typed_trace["entries"])
    for entry in entries:
        assert_trace_entry_schema(entry)

    if expect_error:
        assert isinstance(typed_trace["error_line_number"], int)
    else:
        assert typed_trace["error_line_number"] is None
    assert typed_trace["error_block_segment_index"] is None or isinstance(
        typed_trace["error_block_segment_index"],
        int,
    )


def test_success_output_payload_has_required_schema(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode="G17 G20 G90 G94\nG1 X1.0 F60\n",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert_output_payload_schema(payload, expect_error=False)


def test_error_output_payload_has_required_schema(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode="G1 X1.0 F60\nG2 X2.0\n",
        tmp_path=tmp_path,
    )

    assert completed.returncode == 1, completed.stderr
    assert_output_payload_schema(payload, expect_error=True)


@pytest.mark.trace
def test_success_trace_payload_has_required_schema(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload, trace = run_rs274_trace(
        submission_command,
        input_gcode="G17 G20 G90 G94\nG1 X1.0 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert_output_payload_schema(payload, expect_error=False)
    assert_trace_payload_schema(trace, expect_error=False)
    assert trace["entries"]


@pytest.mark.trace
def test_error_trace_payload_has_required_schema(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    completed, payload, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1.0 F60\nG2 X2.0\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 1, completed.stderr
    assert_output_payload_schema(payload, expect_error=True)
    assert_trace_payload_schema(trace, expect_error=True)
    assert trace["error_line_number"] == 2
