"""Tests for trace file structure, initial_state shape, error cases, and CLI validation."""
# pyright: reportUnknownMemberType=none
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cncsim_support import (
    build_parameter_file,
    reconstruct_state,
    run_cncsim_trace,
)

pytestmark = pytest.mark.trace

# ---------------------------------------------------------------------------
# Top-level structure
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL_KEYS = {
    "initial_state", "entries", "error_line_number", "error_block_segment_index",
}
REQUIRED_OUTPUT_FIELDS = {
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
}


def test_trace_has_required_top_level_keys(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert set(trace.keys()) == REQUIRED_TOP_LEVEL_KEYS


def test_initial_state_matches_output_payload_shape(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """initial_state has the same fields as --output, minus 'error'."""
    _, _payload, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    initial = trace["initial_state"]
    # Must have all output fields except "error".
    assert "error" not in initial
    for field in REQUIRED_OUTPUT_FIELDS:
        assert field in initial, f"initial_state missing '{field}'"


def test_initial_state_has_all_nine_coordinate_systems(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    cs = trace["initial_state"]["coordinate_system_offsets"]
    for i in range(1, 10):
        assert str(i) in cs, f"coordinate_system_offsets missing system '{i}'"


def test_initial_state_machine_position_has_six_axes(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    pos = trace["initial_state"]["machine_position"]
    for axis in ("x", "y", "z", "a", "b", "c"):
        assert axis in pos, f"machine_position missing axis '{axis}'"


def test_success_trace_has_null_error_fields(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert trace["error_line_number"] is None
    assert trace["error_block_segment_index"] is None


# ---------------------------------------------------------------------------
# Empty/minimal programs
# ---------------------------------------------------------------------------


def test_m2_only_produces_state_only_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """M2 alone is a state-only block: one entry at time=0.0001 with resets."""
    completed, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="M2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 0
    entries = trace["entries"]
    assert len(entries) == 1
    e = entries[0]
    assert e["line_number"] == 1
    assert e["time"] == pytest.approx(0.0001)


def test_comment_only_produces_no_entries(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """A comment followed by M2 produces only the M2 entry."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="(comment)\nM2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace["entries"]
    # Only the M2 entry (line 2), not the comment (line 1).
    assert len(entries) == 1
    assert entries[0]["line_number"] == 2


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_error_trace_sets_error_line_number(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """On error, entries are truncated and error_line_number is set.

    G2 X2 (without I/J/R center) is an arc error on line 2.
    """
    completed, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG2 X2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 1
    assert trace["error_line_number"] == 2
    # Entries from line 1 should still be present.
    assert len(trace["entries"]) >= 1
    for e in trace["entries"]:
        assert e["line_number"] == 1  # Only line 1 completed.


def test_error_trace_has_correct_entries_from_completed_blocks(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X1 F60 (ok), G2 X2 (arc error). Line 1's entries survive."""
    completed, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG2 X2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 1
    entries = trace["entries"]
    assert len(entries) == 2  # Stepped at t=0.5, final at t=1.0.
    assert entries[0]["time"] == pytest.approx(0.5)
    assert entries[1]["time"] == pytest.approx(1.0)
    assert entries[0]["machine_position"]["x"] == pytest.approx(0.5)
    assert entries[1]["machine_position"]["x"] == pytest.approx(1.0)


def test_error_block_segment_index_null_for_simple_block(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Non-multi-sub-motion errors have null error_block_segment_index."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG2 X2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert trace["error_block_segment_index"] is None


# ---------------------------------------------------------------------------
# Entries field: no time==0.0, no "error"
# ---------------------------------------------------------------------------


def test_no_entry_at_time_zero(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Spec: no entry is emitted at time == 0.0."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    for entry in trace["entries"]:
        assert entry["time"] != 0.0


def test_entries_do_not_contain_error_field(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    for entry in trace["entries"]:
        assert "error" not in entry


# ---------------------------------------------------------------------------
# Delta encoding correctness
# ---------------------------------------------------------------------------


def test_reconstructed_final_state_matches_output_payload(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Folding initial_state + all deltas should reproduce the --output payload (minus error)."""
    _, payload, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG1 Y2\n",
        trace_time_step=100.0,  # Large step: only final entries.
        tmp_path=tmp_path,
    )
    last_idx = len(trace["entries"]) - 1
    reconstructed = reconstruct_state(trace, last_idx)
    # Compare key fields.
    assert reconstructed["machine_position"] == pytest.approx(payload["machine_position"])
    assert reconstructed["feed_rate"] == pytest.approx(payload["feed_rate"])
    assert reconstructed["active_modal_g_codes"] == payload["active_modal_g_codes"]


def test_delta_encoding_omits_unchanged_fields(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Second entry on same line should not repeat feed_rate.

    G0 X1 changes motion mode from default (G1) to G0, and sets feed_rate
    implicitly via rapid. The second stepped entry should not re-emit
    feed_rate since it hasn't changed since the first entry.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X2 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace["entries"]
    assert len(entries) >= 2
    # First entry carries feed_rate delta.
    assert "feed_rate" in entries[0]
    # Second entry should NOT re-emit feed_rate (unchanged).
    assert "feed_rate" not in entries[1]


def test_machine_position_is_sparse_in_delta(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """machine_position in entries includes only axes that changed."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=100.0,  # One final entry.
        tmp_path=tmp_path,
    )
    entries = trace["entries"]
    assert len(entries) >= 1
    # Only X moved; Y, Z, A, B, C should not be present in the delta.
    pos = entries[-1]["machine_position"]
    assert "x" in pos
    for axis in ("y", "z", "a", "b", "c"):
        assert axis not in pos, f"Unchanged axis '{axis}' should not appear in delta"


# ---------------------------------------------------------------------------
# CLI validation
# ---------------------------------------------------------------------------


def test_trace_output_without_stepping_flag_exits_1(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """--trace-output without any stepping flag is invalid."""
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    trace_path = tmp_path / "trace.json"
    input_path.write_text("G1 X1 F60\n", encoding="utf-8")

    import subprocess
    completed = subprocess.run(
        [*submission_command, "--input", str(input_path), "--output", str(output_path),
         "--trace-output", str(trace_path)],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_stepping_flag_without_trace_output_exits_1(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """--trace-time-step without --trace-output is invalid."""
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    input_path.write_text("G1 X1 F60\n", encoding="utf-8")

    import subprocess
    completed = subprocess.run(
        [*submission_command, "--input", str(input_path), "--output", str(output_path),
         "--trace-time-step", "0.5"],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


def test_multiple_stepping_flags_exits_1(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Providing two stepping flags is invalid."""
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    trace_path = tmp_path / "trace.json"
    input_path.write_text("G1 X1 F60\n", encoding="utf-8")

    import subprocess
    completed = subprocess.run(
        [*submission_command, "--input", str(input_path), "--output", str(output_path),
         "--trace-output", str(trace_path),
         "--trace-time-step", "0.5", "--trace-distance-step", "0.5"],
        capture_output=True, check=False, text=True, timeout=30,
    )
    assert completed.returncode == 1


# ---------------------------------------------------------------------------
# Spec Example 1 -- full structure match
# ---------------------------------------------------------------------------


def test_spec_example_1_linear_motion_time_stepping(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Example 1 structure: G0 X0 / G1 X1 F60 with --trace-time-step 0.5.

    G0 first to ensure G1 produces a modal delta. F60 = 1 unit/s, 1-unit
    move → 1.0s. Interior at 0.5, final at 1.0.
    """
    completed, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G0 X0\nG1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 0
    g1_entries = [e for e in trace["entries"] if e["line_number"] == 2]
    assert len(g1_entries) == 2

    e0, e1 = g1_entries[0], g1_entries[1]
    assert e0["line_number"] == 2
    assert e0["time"] == pytest.approx(0.5)
    assert e0["feed_rate"] == pytest.approx(60.0)
    assert e0["active_modal_g_codes"]["1"] == "G1"
    assert e0["machine_position"]["x"] == pytest.approx(0.5)

    assert e1["line_number"] == 2
    assert e1["time"] == pytest.approx(1.0)
    assert e1["machine_position"]["x"] == pytest.approx(1.0)
    # Second entry should not repeat modal or feed_rate.
    assert "feed_rate" not in e1
    assert "active_modal_g_codes" not in e1


# ---------------------------------------------------------------------------
# Spec Example 2 -- G81 canned cycle sub-motion expansion
# ---------------------------------------------------------------------------


def test_spec_example_2_g81_canned_cycle_distance_stepping(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Example 2 from spec: G81 X5 Y0 Z-3 R0 F60 with --trace-distance-step 1000.

    Precondition: machine at (0, 0, 2), feed_rate 60, G98 retract mode.
    Large distance step → only final entries per sub-motion.
    SM1: rapid (0,0,2) → (5,0,2), t=0.3
    SM2: rapid (5,0,2) → (5,0,0), t=0.42
    SM3: feed  (5,0,0) → (5,0,-3), t=3.42
    SM4: rapid (5,0,-3)→ (5,0,2), t=3.72
    """
    setup = (
        "G90\n"
        "G98\n"
        "G0 X0 Y0 Z2\n"
    )
    completed, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode=setup + "G81 X5 Y0 Z-3 R0 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 0

    # Filter to entries from the G81 line (the last source line).
    g81_line = 4  # Line 4: G81 ...
    g81_entries = [e for e in trace["entries"] if e["line_number"] == g81_line]
    assert len(g81_entries) == 4

    sm1, sm2, sm3, sm4 = g81_entries
    assert sm1["time"] == pytest.approx(0.3, abs=0.01)
    assert sm1["motion_kind"] == "rapid"
    assert sm1["active_modal_g_codes"]["1"] == "G81"
    assert sm1["machine_position"]["x"] == pytest.approx(5.0)

    assert sm2["time"] == pytest.approx(0.42, abs=0.01)
    assert sm2["motion_kind"] == "rapid"
    assert sm2["machine_position"]["z"] == pytest.approx(0.0)

    assert sm3["time"] == pytest.approx(3.42, abs=0.01)
    assert sm3["motion_kind"] == "feed"
    assert sm3["machine_position"]["z"] == pytest.approx(-3.0)

    assert sm4["time"] == pytest.approx(3.72, abs=0.01)
    assert sm4["motion_kind"] == "rapid"
    assert sm4["machine_position"]["z"] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Spec Example 3 -- error case
# ---------------------------------------------------------------------------


def test_spec_example_3_error_case(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Error case: G1 X1 F60 / G2 X2 (arc without center) / G1 X3.

    Line 2 errors because G2 requires I/J/R. Entries from line 1 survive.
    """
    completed, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG2 X2\nG1 X3\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 1
    assert trace["error_line_number"] == 2
    assert trace["error_block_segment_index"] is None
    entries = trace["entries"]
    assert len(entries) == 2
    assert entries[0]["time"] == pytest.approx(0.5)
    assert entries[0]["feed_rate"] == pytest.approx(60.0)
    assert entries[0]["machine_position"]["x"] == pytest.approx(0.5)
    assert entries[1]["time"] == pytest.approx(1.0)
    assert entries[1]["machine_position"]["x"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# State-only blocks produce time=0.0001 entries
# ---------------------------------------------------------------------------


def test_modal_only_line_produces_state_only_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """A line that only changes modal state (G90) produces time=0.0001 entry."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G91\nG90\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    # G91 on line 1 is a state change, G90 on line 2 is another.
    entries = trace["entries"]
    for e in entries:
        assert e["time"] == pytest.approx(0.0001)


def test_feed_rate_only_line_produces_state_only_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """F100 on its own line is a state-only change."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="F100\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace["entries"]
    assert len(entries) == 1
    assert entries[0]["time"] == pytest.approx(0.0001)
    assert entries[0]["feed_rate"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# Nullable scalar fields
# ---------------------------------------------------------------------------


def test_nullable_fields_can_be_explicit_null_in_delta(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """M2 resets cutter_radius_compensation_number to null.

    Activate CRC (G41 D1), then M2 turns it off (G40) and sets
    cutter_radius_compensation_number to null. The delta must include
    the field with an explicit null value (spec: "write its new value
    verbatim (including null when the new value is null)").
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="T1\nM6\nG41 D1 G1 X1 F60\nG1 X2\nM2\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
        tool_table_content="POCKET FMS TLO DIAMETER\n\n1 1 0.0 0.5\n",
    )
    # Verify CRC set a non-null cutter_radius_compensation_number before M2.
    pre_m2 = reconstruct_state(trace, len(trace["entries"]) - 2)
    assert pre_m2["cutter_radius_compensation_number"] is not None, \
        "G41 D1 should set cutter_radius_compensation_number"
    # Find the M2 entry.
    m2_entries = [e for e in trace["entries"] if e["line_number"] == 5]
    assert len(m2_entries) >= 1
    m2_delta = m2_entries[-1]
    # M2 resets CRC — cutter_radius_compensation_number transitions to null.
    assert "cutter_radius_compensation_number" in m2_delta, \
        "M2 must include explicit null for cutter_radius_compensation_number"
    assert m2_delta["cutter_radius_compensation_number"] is None


# ---------------------------------------------------------------------------
# Motion + M2 on same line — post-motion delta folds into final motion entry
# ---------------------------------------------------------------------------


def test_motion_plus_m2_same_line_final_entry_time(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X1 F60 M2 on a single line: the final entry's time must equal the
    motion's total duration (1 inch at 60 ipm = 1 s), not total_duration + epsilon.
    The M2 state deltas are folded into that final entry.

    PASS-RATE NOTE (2026-04-18): 2 passes / 243 attempts across all models
    (see CHANGELOG "Proposed"). technical-requirements-prompt.md describes
    state-only-block entries (time == 0.0001) and motion-block stepping as
    separate cases; the behavior when a state-only transition (M2) shares a
    line with a motion block is a legitimately underspecified interaction.
    Models reasonably emit either a folded final entry or a trailing
    0.0001s epsilon entry; only the folded form passes here.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60 M2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace["entries"]
    # 1 inch at 60 ipm = 1.0 s.  Time step 0.5 → entries at 0.5 and 1.0.
    assert len(entries) == 2
    assert entries[-1]["time"] == pytest.approx(1.0)
    # The final entry must carry the M2 modal reset (e.g. spindle_direction).
    assert "active_modal_m_codes" in entries[-1]
    assert entries[-1]["active_modal_m_codes"].get("4") == "M2"


# ---------------------------------------------------------------------------
# Coordinate system offsets: two-level sparse delta encoding
# ---------------------------------------------------------------------------


def test_cs_offsets_sparse_two_level_delta(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G10 L2 P1 X1.0 changes only CS 1's X offset.

    The entry's coordinate_system_offsets should include only key "1",
    and that object should include only key "x".
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G10 L2 P1 X1.0\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace["entries"]
    assert len(entries) == 1
    cs_delta = entries[0].get("coordinate_system_offsets", {})
    # Only CS "1" should appear.
    assert set(cs_delta.keys()) == {"1"}
    # Only axis "x" within CS "1".
    assert set(cs_delta["1"].keys()) == {"x"}
    assert cs_delta["1"]["x"] == pytest.approx(1.0)


def test_cs_offset_delta_uses_active_units(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G10 L2 under G21 should report CS offset delta in mm, not inches."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G21\nG10 L2 P1 X25.4\n",  # 25.4 mm = 1 inch
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    g10_entries = [e for e in trace["entries"] if e["line_number"] == 2]
    assert len(g10_entries) == 1
    cs_delta = g10_entries[0]["coordinate_system_offsets"]["1"]
    # Value should be 25.4 (mm), not 1.0 (inches).
    assert cs_delta["x"] == pytest.approx(25.4, abs=0.1)


# ---------------------------------------------------------------------------
# Coordinates in G53 space with offsets active
# ---------------------------------------------------------------------------


def test_trace_coordinates_are_absolute_machine_coordinates(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """With G54 offset and G92 offset active, trace machine_position should
    report the absolute (G53) machine coordinate, not the programmed position.

    Setup: G10 L2 P1 X10 sets CS1 X offset to 10.
    G54 is default CS.  G92 X100 sets G92 offset so programmed X=100.
    Then G1 X101 F60 moves +1 in programmed space = +1 in machine space.
    Machine X should be: programmed_in_CS - G92_offset + CS_offset.
    Before motion: machine X = 10 + (100 - 100) ... let me think through this.

    Actually: G92 X100 means "make the current position read as X=100."
    If machine is at X=10 (CS1 offset=10, programmed=0), G92 X100 makes
    programmed=100, so G92 offset = 100 - 0 = 100 ... no.

    Simpler: Start at origin.  G10 L2 P1 X5 → CS1 X offset = 5.
    G54 active (CS1).  Machine stays at X=0 (G10 doesn't move).
    G1 X2 F60 → programmed X = 2, machine X = 2 + 5 = 7.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G10 L2 P1 X5.0\nG1 X2 F60\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    # G10 changes the CS offset but does NOT move the machine.
    g10_entries = [e for e in trace["entries"] if e["line_number"] == 1]
    assert len(g10_entries) == 1
    g10 = g10_entries[0]
    # The CS offset should appear in the delta.
    assert g10["coordinate_system_offsets"]["1"]["x"] == pytest.approx(5.0, abs=1e-6)
    # machine_position should NOT change (machine didn't move).
    assert "machine_position" not in g10
    # Check the G1 motion entry:
    g1_entries = [e for e in trace["entries"] if e["line_number"] == 2]
    assert len(g1_entries) == 1
    # Reconstruct X after the G1: should be 7.0 (programmed 2 + CS offset 5).
    final = reconstruct_state(trace, len(trace["entries"]) - 1)
    assert final["machine_position"]["x"] == pytest.approx(7.0, abs=1e-6)


# ---------------------------------------------------------------------------
# M2/M30 parameter resets reported in delta
# ---------------------------------------------------------------------------


def test_m2_resets_produce_correct_delta(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """M2 after modal/spindle changes produces a delta reverting that state.

    Set spindle on (M3), non-default plane (G18), then M2 resets both.
    The M2 entry should carry deltas for the modal resets.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="M3\nG18\nM2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    m2_entries = [e for e in trace["entries"] if e["line_number"] == 3]
    assert len(m2_entries) == 1
    m2_entry = m2_entries[0]
    assert m2_entry["time"] == pytest.approx(0.0001)
    # M2 resets spindle (M5), plane (G17), and sets M-code group 4 to M2.
    assert "active_modal_m_codes" in m2_entry
    assert m2_entry["active_modal_m_codes"].get("4") == "M2"
    # Spindle should be reset to OFF.
    assert m2_entry.get("spindle_direction") == "OFF"
    # Verify reconstructed final state has correct modal resets.
    final = reconstruct_state(trace, len(trace["entries"]) - 1)
    assert final["spindle_direction"] == "OFF"
    assert final["active_modal_g_codes"]["2"] == "G17"  # plane reset


def test_m2_parameter_delta_includes_selected_cs_reset(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """M2 resets selected_cs to 1 (parameter 5220); the delta must report it.

    Select G55 (CS 2), then M2. Parameter 5220 changes from 2.0 → 1.0.
    The M2 entry's parameters delta must include this change.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G55\nM2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    m2_entries = [e for e in trace["entries"] if e["line_number"] == 2]
    assert len(m2_entries) == 1
    m2_entry = m2_entries[0]
    assert m2_entry["time"] == pytest.approx(0.0001)
    # Parameter 5220 (selected coordinate system) must appear in the delta.
    assert "parameters" in m2_entry, \
        "M2 entry must carry a parameters delta when selected_cs resets"
    assert m2_entry["parameters"]["5220"] == pytest.approx(1.0)
    # Verify reconstructed final state.
    final = reconstruct_state(trace, len(trace["entries"]) - 1)
    assert final["parameters"]["5220"] == pytest.approx(1.0)
    assert final["active_modal_g_codes"]["12"] == "G54"  # CS 1


# ---------------------------------------------------------------------------
# initial_state reflects --parameter-input and --tool-table
# ---------------------------------------------------------------------------


def test_initial_state_includes_loaded_parameters(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """initial_state should reflect parameters loaded from --parameter-input."""
    params = build_parameter_file({100: 42.0, 200: -3.14})
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="M2\n",
        trace_time_step=0.5,
        parameter_input_content=params,
        tmp_path=tmp_path,
    )
    init = trace["initial_state"]
    assert init["parameters"]["100"] == pytest.approx(42.0)
    assert init["parameters"]["200"] == pytest.approx(-3.14)


def test_initial_state_includes_tool_table(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """initial_state is captured before the first block. With a tool table
    loaded, tool data is available but selected_tool is still null (no T/M6).
    After T1 M6, the trace entry should carry tool_in_spindle=1.
    """
    tool_table = "POCKET FMS TLO DIAMETER\n\n1 1 1.5 0.25\n2 2 0.0 0.5\n"
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="T1\nM6\nM2\n",
        trace_time_step=0.5,
        tool_table_content=tool_table,
        tmp_path=tmp_path,
    )
    init = trace["initial_state"]
    # Before any T/M6, selected_tool and tool_in_spindle are null.
    assert init["selected_tool"] is None
    assert init["tool_in_spindle"] is None
    # After T1 M6, the trace entries should reflect tool selection.
    t1_entries = [e for e in trace["entries"] if e["line_number"] == 1]
    assert len(t1_entries) == 1
    assert t1_entries[0].get("selected_tool") == 1
    # M6 loads the tool into the spindle — verify tool_in_spindle delta.
    m6_entries = [e for e in trace["entries"] if e["line_number"] == 2]
    assert len(m6_entries) == 1
    assert m6_entries[0].get("tool_in_spindle") == 1


# ---------------------------------------------------------------------------
# Block-delete: deleted lines produce no entries
# ---------------------------------------------------------------------------


def test_block_deleted_line_produces_no_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Lines prefixed with '/' when --block-delete is active produce no entry."""
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G1 X1 F60\n/G1 X2\nG1 X3\n",
        trace_time_step=100.0,
        block_delete=True,
        tmp_path=tmp_path,
    )
    line_numbers = {e["line_number"] for e in trace["entries"]}
    assert 2 not in line_numbers  # Block-deleted line 2.
    assert 1 in line_numbers
    assert 3 in line_numbers
    # Line 3 moves from X=1 (skipping deleted line 2) to X=3.
    final = reconstruct_state(trace, len(trace["entries"]) - 1)
    assert final["machine_position"]["x"] == pytest.approx(3.0, abs=1e-6)
    # Duration: 2 inches at 60 ipm = 2.0 s (not 1.0 s if line 2 executed).
    l3_entries = [e for e in trace["entries"] if e["line_number"] == 3]
    assert l3_entries[-1]["time"] == pytest.approx(2.0, abs=0.05)


# ---------------------------------------------------------------------------
# CRC: trace machine_position describes the compensated (tool-tip) path
# ---------------------------------------------------------------------------


def test_crc_trace_reports_compensated_path(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """With G41 active, trace machine_position should be offset from the
    programmed contour by the cutter radius.

    Tool slot 1 diameter=6.0 (radius=3.0). G41 first move + follow-on along +X.
    After the follow-on move to X6, the spindle center should be at (6, 3):
    fully offset LEFT of the programmed +X path by radius 3.
    """
    tool_table = "POCKET FMS TLO DIAMETER\n\n1 1 0.0 6.0\n"
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="T1\nM6\nG41 D1 G1 X5 Y0 F60\nG1 X6 Y0\n",
        trace_time_step=100.0,
        tool_table_content=tool_table,
        tmp_path=tmp_path,
    )
    # Line 4: the follow-on compensated motion to X6.
    line4 = [e for e in trace["entries"] if e["line_number"] == 4]
    assert len(line4) >= 1
    # Reconstruct final position from initial_state + all deltas.
    final = reconstruct_state(trace, len(trace["entries"]) - 1)
    # G41 follow-on on a +X colinear path → spindle center at (6, 3).
    assert final["machine_position"]["y"] == pytest.approx(3.0, abs=0.01)
    assert final["machine_position"]["x"] == pytest.approx(6.0, abs=0.01)


# ---------------------------------------------------------------------------
# Error in canned cycle: completed sub-motions are preserved
# ---------------------------------------------------------------------------


def test_error_in_canned_cycle_preserves_completed_sms(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """If a canned cycle errors during the second repeat (new line), the
    first repeat's sub-motions should appear in the trace.

    G81 at X=5, then second call on next line with an error-inducing condition.
    Actually, canned cycle errors happen at validation time (before SMs execute),
    so test that a valid cycle's entries are present alongside an error on a later
    line.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        # Line 4: valid G81.  Line 5: G2 with no center words → error.
        input_gcode="G90\nG98\nG0 X0 Y0 Z2\nG81 X0 Y0 Z-1 R0 F60\nG2 X2\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    assert trace["error_line_number"] == 5
    # Line 4 (G81) entries should be present (completed before error).
    g81_entries = [e for e in trace["entries"] if e["line_number"] == 4]
    assert len(g81_entries) >= 2  # At least rapid-to-R + feed-to-Z.


# ---------------------------------------------------------------------------
# active_modal_g_codes sparse delta
# ---------------------------------------------------------------------------


def test_modal_g_codes_sparse_in_delta(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Changing plane (G18) should only include group 2 in the delta, not all
    modal G-code groups.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G18\nM2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    g18_entries = [e for e in trace["entries"] if e["line_number"] == 1]
    assert len(g18_entries) == 1
    g_delta = g18_entries[0].get("active_modal_g_codes", {})
    # Only group "2" (plane) should appear.
    assert "2" in g_delta
    assert g_delta["2"] == "G18"
    # Other groups (like "1" for motion mode) should NOT appear.
    assert "1" not in g_delta


# ---------------------------------------------------------------------------
# parameters sparse delta
# ---------------------------------------------------------------------------


def test_parameters_sparse_in_delta(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Assigning one parameter via #100=42 should only include that parameter
    in the delta, not all parameters.
    """
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="#100=42.0\nM2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    line1_entries = [e for e in trace["entries"] if e["line_number"] == 1]
    assert len(line1_entries) == 1
    p_delta = line1_entries[0].get("parameters", {})
    assert "100" in p_delta
    assert p_delta["100"] == pytest.approx(42.0)
    # Should be sparse — not include ALL parameters.
    assert len(p_delta) == 1


# ---------------------------------------------------------------------------
# Bug fix: --parameter-output must not be written on error path (spec: success-only)
# ---------------------------------------------------------------------------


def test_parameter_output_not_written_on_error(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Spec: --parameter-output is success-only and must not be written on error."""
    input_path = tmp_path / "program.nc"
    output_path = tmp_path / "result.json"
    trace_path = tmp_path / "trace.json"
    param_out_path = tmp_path / "parameters-out.var"
    input_path.write_text("G1 X1 F60\nG2 X2\n", encoding="utf-8")  # Arc error

    command = [
        *submission_command,
        "--input", str(input_path),
        "--output", str(output_path),
        "--trace-output", str(trace_path),
        "--trace-time-step", "0.5",
        "--parameter-output", str(param_out_path),
    ]

    completed = subprocess.run(command, capture_output=True, check=False, text=True, timeout=30)
    assert completed.returncode == 1
    assert output_path.is_file()
    assert trace_path.is_file()
    # --parameter-output must NOT exist on the error path.
    assert not param_out_path.exists(), \
        "--parameter-output should not be written on error"


# ---------------------------------------------------------------------------
# Bug fix: probe no-trip records commanded endpoint in trace before erroring
# ---------------------------------------------------------------------------


def test_probe_no_trip_records_commanded_endpoint(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Spec: on probe no-trip, final entry reflects the commanded endpoint."""
    # Probe box at X=5..6, but we probe to X=3 (won't trip).
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="T1 M6\nG43 H1\nS0 M5\nG38.2 X3 F60\n",
        trace_time_step=10.0,
        probe_box=(5.0, 6.0, -1.0, 1.0, -1.0, 1.0),
        probe_tool=1,
        tool_table_content="POCKET FMS TLO DIAMETER\n\n1 1 0.0 0.0\n",
        tmp_path=tmp_path,
    )
    assert trace["error_line_number"] == 4
    # The probe motion to the commanded endpoint should appear in entries.
    probe_entries = [e for e in trace["entries"] if e["line_number"] == 4]
    assert len(probe_entries) >= 1, "Probe motion should produce at least one trace entry"
    # The final entry should show the commanded endpoint (X=3).
    final = reconstruct_state(trace, len(trace["entries"]) - 1)
    assert final["machine_position"]["x"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Bug fix: all-zero-length SMs suppress nonmodal label (spec: label does not appear)
# ---------------------------------------------------------------------------


def test_zero_length_g28_suppresses_nonmodal_label(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Spec: zero-duration sub-motions produce no entries and their labels don't appear."""
    # G28 from the home position (all zeros) with no axis words → both SMs
    # are zero-length. The nonmodal label should not appear.
    _, _, trace = run_cncsim_trace(
        submission_command,
        input_gcode="G28\nM2\n",
        trace_time_step=0.5,
        parameter_input_content=build_parameter_file({5161: 0.0, 5162: 0.0, 5163: 0.0}),
        tmp_path=tmp_path,
    )
    g28_entries = [e for e in trace["entries"] if e["line_number"] == 1]
    # No entries should exist for the G28 line (all SMs zero-length).
    for e in g28_entries:
        assert "nonmodal_g_codes" not in e, \
            "Zero-length G28 should not emit nonmodal_g_codes label"
