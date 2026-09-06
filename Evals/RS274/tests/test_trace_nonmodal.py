"""Tests for nonmodal_g_codes labeling in trace entries."""

# pyright: reportUnknownMemberType=none
from __future__ import annotations

from pathlib import Path

import pytest

from rs274_parameters import (
    G28_HOME_X_PARAMETER,
    G28_HOME_Y_PARAMETER,
    G28_HOME_Z_PARAMETER,
    G30_HOME_X_PARAMETER,
    G30_HOME_Y_PARAMETER,
    G30_HOME_Z_PARAMETER,
)
from rs274_support import input_line, run_rs274_trace, trace_entries

pytestmark = pytest.mark.trace

# ---------------------------------------------------------------------------
# G53 -- nonmodal absolute machine coordinate
# ---------------------------------------------------------------------------


def test_g53_label_on_first_entry_of_motion(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G53 applied to G1: nonmodal_g_codes on first emitted entry only."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X0 F60\nG53 G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    g53_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(g53_entries) >= 1
    # First entry should carry the nonmodal label.
    assert "nonmodal_g_codes" in g53_entries[0]
    assert "G53" in g53_entries[0]["nonmodal_g_codes"]
    # Subsequent entries should NOT have the label.
    for e in g53_entries[1:]:
        assert "nonmodal_g_codes" not in e


# ---------------------------------------------------------------------------
# G28 -- two sub-motions
# ---------------------------------------------------------------------------


def test_g28_label_on_both_sub_motions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G28 expands into two sub-motions. Both should carry nonmodal_g_codes."""
    # Section 3.5.8 takes home coordinates from parameters. Set them in the
    # program so this label test does not also grade parameter-file loading.
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=(
            f"#{G28_HOME_X_PARAMETER}=10 #{G28_HOME_Y_PARAMETER}=10 "
            f"#{G28_HOME_Z_PARAMETER}=10\n"
            "G0 X1 Y1 Z1\nG28 X5 Y5 Z5\n"
        ),
        trace_distance_step=1000.0,  # Only final entries.
        tmp_path=tmp_path,
    )
    g28_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    # Two sub-motions: (1,1,1)→(5,5,5) then (5,5,5)→(10,10,10).
    assert len(g28_entries) == 2
    # Both should carry the G28 label.
    for e in g28_entries:
        assert "nonmodal_g_codes" in e
        assert "G28" in e["nonmodal_g_codes"]


def test_g28_zero_intermediate_no_label_on_zero_sm(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G28 with no axis words: intermediate == current pos → SM1 is zero-length.

    Zero-duration SM produces no entries, so its label is NOT rolled forward.
    Only SM2 (to home) emits entries and carries the label.
    """
    # In-program assignments isolate zero-sub-motion labeling from file I/O.
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=(
            f"#{G28_HOME_X_PARAMETER}=10 #{G28_HOME_Y_PARAMETER}=0 #{G28_HOME_Z_PARAMETER}=0\nG28\n"
        ),
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g28_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    # SM1 is zero-length (current pos = (0,0,0), intermediate = (0,0,0)).
    # SM2 is (0,0,0) → (10,0,0).
    assert len(g28_entries) == 1  # Only SM2.
    assert "nonmodal_g_codes" in g28_entries[0]
    assert "G28" in g28_entries[0]["nonmodal_g_codes"]


# ---------------------------------------------------------------------------
# G30 -- same two-sub-motion pattern
# ---------------------------------------------------------------------------


def test_g30_label_on_both_sub_motions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    # Section 3.5.8 permits these assignments independently of parameter files.
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=(
            f"#{G30_HOME_X_PARAMETER}=20 #{G30_HOME_Y_PARAMETER}=20 "
            f"#{G30_HOME_Z_PARAMETER}=20\n"
            "G0 X1 Y1 Z1\nG30 X5 Y5 Z5\n"
        ),
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g30_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(g30_entries) == 2
    for e in g30_entries:
        assert "nonmodal_g_codes" in e
        assert "G30" in e["nonmodal_g_codes"]


# ---------------------------------------------------------------------------
# G10 -- state-only nonmodal
# ---------------------------------------------------------------------------


def test_g10_label_on_state_only_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G10 L2 P1 X1 sets coordinate system 1's X offset. State-only at t=0.0001."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G10 L2 P1 X1.0\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    e = entries[0]
    assert e["time"] == pytest.approx(0.0001)
    assert "nonmodal_g_codes" in e
    assert "G10" in e["nonmodal_g_codes"]
    # Should carry the coordinate system offset delta.
    assert "coordinate_system_offsets" in e


# ---------------------------------------------------------------------------
# G92 family -- state-only nonmodal
# ---------------------------------------------------------------------------


def test_g92_label_on_state_only_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G92 X10 sets origin offset. State-only at t=0.0001 with G92 label."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G92 X10\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    e = entries[0]
    assert e["time"] == pytest.approx(0.0001)
    assert "nonmodal_g_codes" in e
    assert "G92" in e["nonmodal_g_codes"]


def test_g92_1_label(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G92.1 resets and deactivates origin offsets."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G92 X10\nG92.1\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    g921_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(g921_entries) == 1
    assert "nonmodal_g_codes" in g921_entries[0]
    assert "G92.1" in g921_entries[0]["nonmodal_g_codes"]


def test_g92_2_label(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G92.2 deactivates origin offsets (without zeroing parameters).

    Move to X=5 first, then G92 X10, then G92.2. After G92 X10 the
    machine_position changes; after G92.2 it changes back.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X5\nG92 X10\nG92.2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    g922_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(g922_entries) == 1
    assert "nonmodal_g_codes" in g922_entries[0]
    assert "G92.2" in g922_entries[0]["nonmodal_g_codes"]


def test_g92_3_label(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G92.3 reactivates origin offsets from saved parameters.

    Move to X=5, G92 X10, G92.2 (deactivate), G92.3 (reactivate).
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X5\nG92 X10\nG92.2\nG92.3\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    g923_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    assert len(g923_entries) == 1
    assert "nonmodal_g_codes" in g923_entries[0]
    assert "G92.3" in g923_entries[0]["nonmodal_g_codes"]


# ---------------------------------------------------------------------------
# G4 dwell -- nonmodal label on dwell entry
# ---------------------------------------------------------------------------


def test_g4_dwell_carries_nonmodal_label(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G4 P2 dwell entry at t=2.0 should carry nonmodal_g_codes: ["G4"]."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G4 P2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    e = entries[0]
    assert "nonmodal_g_codes" in e
    assert e["nonmodal_g_codes"] == ["G4"]
    assert e["time"] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# nonmodal_g_codes field: omitted when empty, sorted alphabetically
# ---------------------------------------------------------------------------


def test_nonmodal_g_codes_omitted_when_none_fired(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Plain G1 motion: no nonmodal → field should be absent, not [] or null."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    # The predicate must examine emitted entries, not an empty iteration.
    assert entries, "This motion program must produce trace entries"
    for e in entries:
        assert "nonmodal_g_codes" not in e


def test_nonmodal_g_codes_alphabetically_sorted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """If multiple nonmodals fire on one block, they are alphabetically sorted.

    G10 L2 P1 X1 combined with G4 P0 on the same line would be unusual,
    so we just test that single-code blocks are a one-element sorted list.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G10 L2 P1 X1.0\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    codes = entries[0]["nonmodal_g_codes"]
    assert codes == sorted(codes)


# ---------------------------------------------------------------------------
# motion_kind only in canned cycles
# ---------------------------------------------------------------------------


def test_motion_kind_absent_outside_canned_cycles(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Plain G0 and G1 do not carry motion_kind."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\nG1 X2 F60\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    # The predicate must examine emitted entries, not an empty iteration.
    assert entries, "This motion program must produce trace entries"
    for e in entries:
        assert "motion_kind" not in e


# ---------------------------------------------------------------------------
# G4 P0 combined with other nonmodal on the same line
# ---------------------------------------------------------------------------


def test_g4_p0_with_modal_change_emits_state_only(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G4 P0 is a no-op that suppresses its G4 label.

    A modal change on the same line (G91) should still produce a state-only
    entry without the G4 label. Note: G4 + another group-0 nonmodal on the
    same line is illegal (both are group 0), so only modal changes coexist.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G91 G4 P0\nG1 X1 F60\nM2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    line1_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(1)]
    assert len(line1_entries) == 1, "G91 modal change should produce state-only entry"
    e = line1_entries[0]
    # G4 P0 label should be suppressed; G91 is a modal, not a nonmodal.
    assert "nonmodal_g_codes" not in e, "G4 P0 label should be suppressed"
    # The G91 modal change should be in the delta.
    assert e.get("active_modal_g_codes", {}).get("3") == "G91"
