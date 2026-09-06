"""Tests for trace stepping mode edge cases (time, distance, tolerance)."""

# pyright: reportUnknownMemberType=none
from __future__ import annotations

import math
from pathlib import Path

import pytest

from rs274_support import (
    input_line,
    reconstruct_state,
    run_rs274_trace,
    trace_entries,
    trace_initial_state,
)

pytestmark = pytest.mark.trace


# ---------------------------------------------------------------------------
# Time stepping
# ---------------------------------------------------------------------------


def test_time_step_correct_number_of_entries(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X2 F60 → 2.0s. --trace-time-step 0.5 → 3 interior + 1 final = 4 entries."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X2 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 4
    expected_times = [0.5, 1.0, 1.5, 2.0]
    for e, t in zip(entries, expected_times, strict=True):
        assert e["time"] == pytest.approx(t, abs=1e-6)


def test_time_step_positions_are_linearly_interpolated(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Linear G1 X2 F60: positions at t=0.5,1.0,1.5,2.0 → X=0.5,1.0,1.5,2.0."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X2 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    expected_x = [0.5, 1.0, 1.5, 2.0]
    for e, x in zip(entries, expected_x, strict=True):
        assert e["machine_position"]["x"] == pytest.approx(x, abs=1e-6)


def test_time_step_larger_than_motion_only_final_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Step dt=100 on a 1s motion: no interior sample fits, only final entry."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    assert entries[0]["time"] == pytest.approx(1.0)
    assert entries[0]["machine_position"]["x"] == pytest.approx(1.0)


def test_time_step_exactly_divides_duration(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X1 F60 → 1.0s. dt=0.5 → interior at 0.5 + final at 1.0 = 2 entries.

    When dt exactly divides L_time, the sample at L_time is NOT an interior
    sample (it's not strictly less than L_time), it's the mandatory final entry.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 2
    assert entries[0]["time"] == pytest.approx(0.5)
    assert entries[1]["time"] == pytest.approx(1.0)


def test_time_step_last_interior_not_duplicated_with_final(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """If the last interior sample would land at L_time, it should be merged
    with (or replaced by) the final entry, not produce a duplicate."""
    # G1 X1 F120 → 0.5s. dt=0.25 → interior at 0.25, final at 0.5.
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F120\n",
        trace_time_step=0.25,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 2
    assert entries[0]["time"] == pytest.approx(0.25)
    assert entries[1]["time"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Distance stepping
# ---------------------------------------------------------------------------


def test_distance_step_correct_number_of_entries(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X4 F60 → 4-inch path. ds=1.0 → 3 interior + 1 final = 4 entries."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X4 F60\n",
        trace_distance_step=1.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 4


def test_distance_step_positions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X4 F60 with ds=1.0: positions at 1,2,3,4."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X4 F60\n",
        trace_distance_step=1.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    expected_x = [1.0, 2.0, 3.0, 4.0]
    for e, x in zip(entries, expected_x, strict=True):
        assert e["machine_position"]["x"] == pytest.approx(x, abs=1e-6)


def test_distance_step_larger_than_path_only_final(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """ds=1000 on a 1-inch path: only the final entry."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    assert entries[0]["machine_position"]["x"] == pytest.approx(1.0)


def test_distance_step_diagonal_move(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G1 X3 Y4 F60 → path_length = 5.0. ds=2.5 → 1 interior + 1 final = 2."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X3 Y4 F60\n",
        trace_distance_step=2.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 2
    # At ds=2.5 → frac=0.5, position = (1.5, 2.0)
    assert entries[0]["machine_position"]["x"] == pytest.approx(1.5, abs=1e-4)
    assert entries[0]["machine_position"]["y"] == pytest.approx(2.0, abs=1e-4)
    # Final at (3.0, 4.0)
    assert entries[1]["machine_position"]["x"] == pytest.approx(3.0, abs=1e-4)
    assert entries[1]["machine_position"]["y"] == pytest.approx(4.0, abs=1e-4)


# ---------------------------------------------------------------------------
# Rapid motion uses 1000 ipm rate
# ---------------------------------------------------------------------------


def test_rapid_duration_at_1000_ipm(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G0 X1 at 1000 ipm = 1/16.667 min = 0.06s. Large step → one final entry."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    expected_dur = 1.0 / (1000.0 / 60.0)  # = 0.06s
    assert entries[0]["time"] == pytest.approx(expected_dur, abs=1e-4)


# ---------------------------------------------------------------------------
# Multi-line cumulative time resets per line
# ---------------------------------------------------------------------------


def test_time_resets_per_line(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Each source line's time starts at 0 (not cumulative across lines)."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG1 Y1\n",
        trace_time_step=100.0,  # Only final entries.
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    # Line 1: final at 1.0s, Line 2: final at 1.0s (not 2.0).
    line1_entries = [e for e in entries if e["line_number"] == input_line(1)]
    line2_entries = [e for e in entries if e["line_number"] == input_line(2)]
    assert len(line1_entries) == 1
    assert len(line2_entries) == 1
    assert line1_entries[0]["time"] == pytest.approx(1.0)
    assert line2_entries[0]["time"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Arc stepping
# ---------------------------------------------------------------------------


def test_arc_g2_produces_entries(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G2 X1 Y0 I0.5 J0 (half-circle, r=0.5). Should produce arc entries."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G17\nG1 X0 Y0 F60\nG2 X1 Y0 I0.5 J0 F60\n",
        trace_time_step=0.1,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(arc_entries) >= 2  # At least one interior + final.
    # Final position should be at (1, 0).
    last = arc_entries[-1]
    assert last["machine_position"]["x"] == pytest.approx(1.0, abs=1e-4)
    # Y should return to 0 at the end.
    if "y" in last["machine_position"]:
        assert last["machine_position"]["y"] == pytest.approx(0.0, abs=1e-4)


def test_arc_positions_stay_on_circle(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Arc-stepped entries should lie on the true circle path."""
    _, _, trace = run_rs274_trace(
        submission_command,
        # Full semicircle in XY plane: center at (0.5, 0), radius 0.5.
        input_gcode="G17\nG1 X0 Y0 F60\nG2 X1 Y0 I0.5 J0 F60\n",
        trace_time_step=0.05,
        tmp_path=tmp_path,
    )
    # Reconstruct full positions for the arc line.
    initial_pos = trace_initial_state(trace)["machine_position"]
    cx, cy = 0.5, 0.0
    r = 0.5
    # Track running position through all entries to check arc entries.
    cur_x = initial_pos["x"]
    cur_y = initial_pos["y"]
    for e in trace_entries(trace):
        if "machine_position" in e:
            mp = e["machine_position"]
            if "x" in mp:
                cur_x = mp["x"]
            if "y" in mp:
                cur_y = mp["y"]
        if e["line_number"] == input_line(3):
            dist = math.sqrt((cur_x - cx) ** 2 + (cur_y - cy) ** 2)
            assert dist == pytest.approx(r, abs=0.01), (
                f"Point ({cur_x}, {cur_y}) is {dist} from center, expected {r}"
            )


# ---------------------------------------------------------------------------
# Canned cycle stepping
# ---------------------------------------------------------------------------


def test_canned_cycle_sub_motions_stepped_independently(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G81 with small time step: sub-motions have independent stepping."""
    setup = "G90\nG98\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G81 X5 Y0 Z-3 R0 F60\n",
        trace_time_step=0.1,
        tmp_path=tmp_path,
    )
    g81_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    assert len(g81_entries) > 4  # Multiple stepped entries per sub-motion.

    # Verify times are monotonically increasing.
    times = [e["time"] for e in g81_entries]
    for i in range(1, len(times)):
        assert times[i] > times[i - 1], f"Times not monotonic: {times}"

    # The final entry's time should match the total duration.
    total_dur = 0.3 + 0.12 + 3.0 + 0.3  # SM1+SM2+SM3+SM4
    assert times[-1] == pytest.approx(total_dur, abs=0.02)


def test_canned_cycle_motion_kind_only_on_first_entry_per_sm(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """motion_kind appears only on the first emitted entry of each canned-cycle sub-motion."""
    setup = "G90\nG98\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G81 X5 Y0 Z-3 R0 F60\n",
        trace_time_step=0.01,  # Lots of entries.
        tmp_path=tmp_path,
    )
    g81_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    # Count entries with motion_kind set.
    mk_entries = [e for e in g81_entries if "motion_kind" in e]
    # Should be exactly 4 (one per sub-motion): rapid, rapid, feed, rapid.
    assert len(mk_entries) == 4
    assert mk_entries[0]["motion_kind"] == "rapid"
    assert mk_entries[1]["motion_kind"] == "rapid"
    assert mk_entries[2]["motion_kind"] == "feed"
    assert mk_entries[3]["motion_kind"] == "rapid"


# ---------------------------------------------------------------------------
# Zero-duration sub-motions in canned cycles
# ---------------------------------------------------------------------------


def test_canned_cycle_zero_duration_sm_skipped(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G81 where SM1 (rapid XY) is zero-length (already at target XY).

    Machine already at (5, 0, 2). G81 X5 Y0 Z-3 R0 F60:
    SM1 rapid (5,0,2)→(5,0,2): zero, skipped.
    SM2 rapid Z2→0: 2 inches, dur=0.12s.
    SM3 feed Z0→-3: 3 inches, dur=3.0s.
    SM4 rapid Z-3→2: 5 inches, dur=0.3s.
    """
    setup = "G90\nG98\nG0 X5 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G81 X5 Y0 Z-3 R0 F60\n",
        trace_distance_step=1000.0,  # Only final entries.
        tmp_path=tmp_path,
    )
    g81_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    # Only 3 sub-motions produce entries (SM1 skipped).
    assert len(g81_entries) == 3
    # First entry should be SM2 (rapid), at time=0.12.
    assert g81_entries[0]["motion_kind"] == "rapid"
    assert g81_entries[0]["time"] == pytest.approx(0.12, abs=0.01)
    # G81 modal delta must ride the first emitted entry (SM2, since SM1 was
    # zero-length and skipped).
    assert g81_entries[0].get("active_modal_g_codes", {}).get("1") == "G81"
    # SM3 feed.
    assert g81_entries[1]["motion_kind"] == "feed"
    # SM4 rapid.
    assert g81_entries[2]["motion_kind"] == "rapid"


# ---------------------------------------------------------------------------
# Dwell
# ---------------------------------------------------------------------------


def test_dwell_entry_at_time_p(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G4 P2 produces a single entry at time=2.0."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G4 P2\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    assert entries[0]["time"] == pytest.approx(2.0)
    assert entries[0]["line_number"] == input_line(1)


def test_dwell_p_zero_no_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G4 P0 produces no entry."""
    completed, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G4 P0\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    assert completed.returncode == 0
    # An absent trace cannot establish that an error field or entry is absent.
    assert trace, "The interpreter must produce an observable trace object"
    entries = trace_entries(trace)
    # G4 P0 is a no-change block -> no entry.
    assert len(entries) == 0


# ---------------------------------------------------------------------------
# G93 inverse-time feed duration
# ---------------------------------------------------------------------------


def test_g93_inverse_time_duration(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Under G93, F is inverse minutes so duration is 60/F seconds.

    G93 G1 X2 F120 -> duration = 60/120 = 0.5s. Large step -> single final entry.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G93\nG1 X2 F120\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    g1_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(g1_entries) == 1
    assert g1_entries[0]["time"] == pytest.approx(0.5, abs=1e-6)
    assert g1_entries[0]["machine_position"]["x"] == pytest.approx(2.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G21 mm mode: trace coordinates in active units
# ---------------------------------------------------------------------------


def test_g21_mm_mode_trace_coordinates(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Under G21, trace machine_position should be in mm.

    G21 G1 X25.4 F1524 -> 25.4mm = 1 inch. F1524 mm/min = 60 ipm -> 1s.
    Final position should be 25.4 (mm).
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G21\nG1 X25.4 F1524\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    g1_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(g1_entries) == 1
    assert g1_entries[0]["machine_position"]["x"] == pytest.approx(25.4, abs=0.01)


# ---------------------------------------------------------------------------
# Multi-repeat canned cycle (L>1)
# ---------------------------------------------------------------------------


def test_canned_cycle_l2_produces_double_sub_motions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G81 with L2 at two different XY positions.

    G81 X5 Y0 Z-1 R0 L2 X10: first repeat at (5,0), second at (10,0).
    Each repeat has 4 sub-motions. Large step -> 4 entries per repeat.
    """
    setup = "G90\nG98\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G81 X5 Y0 Z-1 R0 F60 L2\nX10\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    # Line 4 (G81 L2): should produce sub-motions for 2 repeats.
    g81_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    # 2 repeats x 4 sub-motions each = 8 entries (some may be zero-length).
    assert len(g81_entries) >= 6  # At least 3 non-zero SMs per repeat.

    # The second repeat (line 5: X10) is a separate G-code line.
    repeat2_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(5)]
    assert len(repeat2_entries) >= 3  # At least rapid-XY + rapid-R + feed-Z.


# ---------------------------------------------------------------------------
# Helical arcs: path length includes axial component
# ---------------------------------------------------------------------------


def test_helical_arc_duration_includes_axial(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G2 arc with Z movement: duration uses sqrt(arc_len^2 + dz^2).

    Half-circle from (1,0) to (-1,0) with center (0,0), radius=1 in XY.
    In-plane arc length = pi (half-circumference).  Axial Z moves 0→1 (1 inch).
    Helical path length = sqrt(pi^2 + 1^2) ≈ 3.297.
    At F60 (1 ipm) → duration ≈ 3.297 s.  Time step 1.0 → 3 interior + 1 final.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\nG2 X-1 Z1 I-1 J0 F60\n",
        trace_time_step=1.0,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    expected_path = math.sqrt(math.pi**2 + 1.0**2)  # ≈ 3.297
    expected_duration = expected_path  # F60 = 1 inch/s
    # Final entry's time == total duration.
    assert arc_entries[-1]["time"] == pytest.approx(expected_duration, rel=1e-3)
    # Should have interior samples + final.
    assert len(arc_entries) >= 3


def test_helical_arc_z_varies_during_arc(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Helical arc: Z should change linearly as the arc progresses."""
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\nG2 X-1 Z2 I-1 J0 F60\n",
        trace_time_step=0.5,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    # Z should increase through the arc entries (from 0 → 2).
    z_values: list[float] = []
    z = 0.0  # initial Z
    for e in arc_entries:
        if "machine_position" in e and "z" in e["machine_position"]:
            z = e["machine_position"]["z"]
        z_values.append(z)
    # Should be monotonically increasing.
    for i in range(1, len(z_values)):
        assert z_values[i] >= z_values[i - 1] - 1e-9
    # Final Z should be 2.0.
    assert z_values[-1] == pytest.approx(2.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Full circle arc: start == end → path length = 2*pi*r
# ---------------------------------------------------------------------------


def test_full_circle_arc_duration(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G2 full circle (start==end): path = 2*pi*r.

    Start at (1,0), center at (0,0), radius=1. Full circle in XY.
    Endpoint X1 Y0 equals start → full circle.
    Path = 2*pi*1 ≈ 6.283. At F60 (1 ips) → duration ≈ 6.283 s.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\nG2 X1 Y0 I-1 J0 F60\n",
        trace_time_step=2.0,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    expected_duration = 2.0 * math.pi  # ≈ 6.283 s
    assert arc_entries[-1]["time"] == pytest.approx(expected_duration, rel=1e-3)
    # 3 interior (at 2.0, 4.0, 6.0) + 1 final (at 6.283) = 4.
    assert len(arc_entries) == 4


def test_full_circle_arc_with_explicit_axis_words_returns_to_start(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Center-format arc with endpoint equal to current point → full circle.

    RS274 §3.5.3.2 permits the endpoint to equal the current point, but
    G17 center-format arcs still require at least one in-plane axis word.
    This input names the return point explicitly with X1 Y0.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\nG2 X1 Y0 I-1 J0 F60\n",
        trace_time_step=2.0,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    expected_duration = 2.0 * math.pi  # ≈ 6.283 s
    assert arc_entries[-1]["time"] == pytest.approx(expected_duration, rel=1e-3)
    assert len(arc_entries) == 4

    # End position should equal start position (full circle returns home).
    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["x"] == pytest.approx(1.0, abs=1e-6)
    assert final["machine_position"]["y"] == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Position tolerance stepping (adaptive)
# ---------------------------------------------------------------------------


def test_tolerance_stepping_linear_single_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """For a straight line, any tolerance produces exactly 1 (final) entry.

    Linear interpolation between start and end is exact on a straight line,
    so no intermediate samples are needed regardless of tolerance.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\n",
        trace_position_tolerance=0.001,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    assert len(entries) == 1
    assert entries[0]["time"] == pytest.approx(1.0)
    assert entries[0]["machine_position"]["x"] == pytest.approx(1.0)


def test_tolerance_stepping_arc_produces_intermediate_samples(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Arc with tight tolerance must produce interior samples.

    G2 full circle, radius=1, tight tolerance → many samples to track curvature.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X1\nG2 X1 Y0 I-1 J0 F60\n",
        trace_position_tolerance=0.01,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    # Must have multiple interior samples to stay within 0.01" of the arc.
    assert len(arc_entries) >= 5
    # Final entry returns to start: x≈1, y≈0.
    # Reconstruct final position.
    x, y = 0.0, 0.0
    for e in trace_entries(trace):
        if "machine_position" in e:
            if "x" in e["machine_position"]:
                x = e["machine_position"]["x"]
            if "y" in e["machine_position"]:
                y = e["machine_position"]["y"]
    assert x == pytest.approx(1.0, abs=0.02)
    assert y == pytest.approx(0.0, abs=0.02)


def test_tolerance_stepping_arc_deviation_within_tolerance(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Verify that arc samples under tolerance stepping actually stay within eps.

    G3 half-circle, radius=2, tolerance=0.1. Check that every midpoint between
    consecutive entries is within 0.1 of the true arc.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G0 X2\nG3 X-2 I-2 J0 F60\n",
        trace_position_tolerance=0.1,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert arc_entries, "The programmed half-circle must produce arc samples"
    # Reconstruct XY positions through the arc.
    positions: list[tuple[float, float]] = [(2.0, 0.0)]  # start
    x, y = 2.0, 0.0
    for e in arc_entries:
        if "machine_position" in e:
            if "x" in e["machine_position"]:
                x = e["machine_position"]["x"]
            if "y" in e["machine_position"]:
                y = e["machine_position"]["y"]
        positions.append((x, y))
    # Require the complete arc; a partial or unchanged point sequence could
    # otherwise satisfy every tested chord while omitting the actual motion.
    assert positions[-1] == pytest.approx((-2.0, 0.0), abs=1e-6)
    # For each consecutive pair, check that the midpoint is near the arc
    # (center at origin, radius=2).
    for i in range(len(positions) - 1):
        mid_x = (positions[i][0] + positions[i + 1][0]) / 2
        mid_y = (positions[i][1] + positions[i + 1][1]) / 2
        dist_from_center = math.hypot(mid_x, mid_y)
        deviation = abs(dist_from_center - 2.0)
        assert deviation <= 0.1 + 1e-6, (
            f"Midpoint ({mid_x:.4f}, {mid_y:.4f}) deviates {deviation:.4f} from radius 2 arc"
        )


# ---------------------------------------------------------------------------
# G38.2 probing in trace
# ---------------------------------------------------------------------------


def test_probe_trip_point_in_trace(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G38.2 probe: final entry position should be the trip point, not the commanded endpoint.

    Move to X=-1, probe toward X=5 with a box at X=[2,3].
    Trip at X=2 (first entry into box). Final entry should have X≈2.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="T1\nM6\nG0 X-1\nG38.2 X5 F60\n",
        trace_time_step=100.0,  # Large step → only final entry.
        tmp_path=tmp_path,
        tool_table_content="POCKET FMS TLO DIAMETER\n\n1 1 0.0 0.0\n",
        probe_box=(2.0, 3.0, -1.0, 1.0, -1.0, 1.0),
        probe_tool=1,
    )
    probe_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    assert len(probe_entries) == 1
    # Trip point: X=2 (left edge of probe box).
    assert probe_entries[0]["machine_position"]["x"] == pytest.approx(2.0, abs=0.01)


# ---------------------------------------------------------------------------
# G84 tapping: spindle_direction flips twice on one source line
# ---------------------------------------------------------------------------


def test_g84_tap_spindle_reversal_in_trace(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G84 tapping cycle flips spindle_direction CW→CCW→CW within one line.

    Setup: M3 (spindle CW), then G84 cycle.
    Feed-to-Z sub-motion: spindle CW.
    Feed-retract sub-motion: spindle CCW (reversal).
    After cycle: spindle restored to CW.
    """
    setup = "M3\nG90\nG98\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G84 X0 Y0 Z-1 R0 F60\n",
        trace_distance_step=1000.0,  # Large step → 1 entry per SM.
        tmp_path=tmp_path,
    )
    g84_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(5)]
    # Should have at least 3 entries (rapid-XY may be zero if already at 0,0):
    # rapid-to-R, feed-to-Z, feed-retract, maybe rapid-retract.
    assert len(g84_entries) >= 2

    # Find the feed-retract entry: it should carry spindle_direction = "CCW".
    found_ccw = False
    for e in g84_entries:
        if e.get("spindle_direction") == "CCW":
            found_ccw = True
            break
    assert found_ccw, "G84 retract should flip spindle to CCW"

    # After the cycle, spindle should be restored to CW.
    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["spindle_direction"] == "CW"


def test_g84_g99_spindle_reversal_visible(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G84 with G99 (return-to-R): both spindle flips must be visible.

    With G99, clear == R so no rapid retract SM exists after the feed
    retract.  The CW→CCW flip (for retract) and the CCW→CW restore must
    both appear in the trace even when the retract SM has only one entry.
    """
    setup = "M3\nG90\nG99\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G84 X0 Y0 Z-1 R0 F60\n",
        trace_distance_step=1000.0,  # Large step → 1 entry per SM.
        tmp_path=tmp_path,
    )
    g84_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(5)]

    # Both spindle transitions must be visible in the entries.
    found_ccw = any(e.get("spindle_direction") == "CCW" for e in g84_entries)
    assert found_ccw, "G84 G99 retract should show spindle_direction CCW"

    found_cw_restore = False
    for e in g84_entries:
        if e.get("spindle_direction") == "CW":
            found_cw_restore = True
            break
    assert found_cw_restore, "G84 G99 should show spindle restored to CW"

    # Spec: trailing entry rule — the CW restore must be a separate entry at
    # the same time as the preceding CCW entry (not folded/overwritten).
    ccw_idx = next(i for i, e in enumerate(g84_entries) if e.get("spindle_direction") == "CCW")
    cw_idx = next(i for i, e in enumerate(g84_entries) if e.get("spindle_direction") == "CW")
    assert cw_idx > ccw_idx, "CW restore must follow CCW entry"
    assert g84_entries[cw_idx]["time"] == pytest.approx(g84_entries[ccw_idx]["time"]), (
        "Trailing entry must share time with the preceding entry"
    )

    # Reconstructed final state must be CW.
    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["spindle_direction"] == "CW"


# ---------------------------------------------------------------------------
# G83 peck drill: multiple feed+retract sub-motions
# ---------------------------------------------------------------------------


def test_g83_peck_drill_decomposition(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G83 with Q=0.5, depth 1.5: produces 3 pecks, each with retract cycles.

    Peck 1: R=0 → Z=-0.5 (feed), retract to R (rapid), re-approach (rapid)
    Peck 2: Z=-0.5 → Z=-1.0 (feed), retract to R (rapid), re-approach (rapid)
    Peck 3: Z=-1.0 → Z=-1.5 (feed) — no retract mid-peck since this is last
    Final retract to clear height (rapid).
    """
    setup = "G90\nG98\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G83 X0 Y0 Z-1.5 R0 Q0.5 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g83_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    # SM1: rapid XY (zero — already at 0,0)
    # SM2: rapid to R (0→0 — may be zero if already at Z=0... actually Z=2→0)
    # Peck 1: feed 0→-0.5, rapid -0.5→0, rapid 0→-0.5
    # Peck 2: feed -0.5→-1.0, rapid -1.0→0, rapid 0→-1.0
    # Peck 3: feed -1.0→-1.5
    # Final retract: rapid -1.5→2
    # At least 8-10 non-zero sub-motions.
    assert len(g83_entries) >= 8

    # Verify motion_kind labels alternate between rapid and feed.
    kinds = [e.get("motion_kind") for e in g83_entries if "motion_kind" in e]
    assert "rapid" in kinds
    assert "feed" in kinds


# ---------------------------------------------------------------------------
# G93 inverse-time with G81 canned cycle (single feed SM)
# ---------------------------------------------------------------------------


def test_g93_inverse_time_multi_line(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G93 inverse-time: each G1 block has its own F word determining duration.

    G93 F120 G1 X1 → duration = 60/120 = 0.5 s.
    G1 X2 F240     → duration = 60/240 = 0.25 s.
    Line 2 time resets, so entry times are local to each line.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G93 G1 X1 F120\nG1 X2 F240\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    line1 = [e for e in trace_entries(trace) if e["line_number"] == input_line(1)]
    line2 = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(line1) == 1
    assert len(line2) == 1
    assert line1[0]["time"] == pytest.approx(0.5, rel=1e-3)
    assert line2[0]["time"] == pytest.approx(0.25, rel=1e-3)


# ---------------------------------------------------------------------------
# Distance step is always in inches, regardless of G21 mode
# ---------------------------------------------------------------------------


def test_distance_step_in_inches_under_g21(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """--trace-distance-step is in inches even when G21 (mm) is active.

    G21 G1 X25.4 F1524 → 25.4mm = 1 inch.
    --trace-distance-step 0.5 (inches) → 1 interior + 1 final = 2 entries.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G21\nG1 X25.4 F1524\n",
        trace_distance_step=0.5,
        tmp_path=tmp_path,
    )
    g1_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    # 1 inch path, 0.5 inch step → 1 interior (at 0.5") + 1 final (at 1") = 2.
    assert len(g1_entries) == 2
    # Positions should be in mm (active units).
    assert g1_entries[0]["machine_position"]["x"] == pytest.approx(12.7, abs=0.1)
    assert g1_entries[1]["machine_position"]["x"] == pytest.approx(25.4, abs=0.1)


# ---------------------------------------------------------------------------
# Pending deltas ride the line's first emitted entry
# ---------------------------------------------------------------------------


def test_pending_modal_deltas_ride_first_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Feed rate change on a motion line merges into the first emitted entry.

    G1 X2 F120 changes both position and feed_rate. The feed_rate delta
    must appear on the first (and possibly only) entry, not as a separate
    time=0.0 entry.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG1 X2 F120\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    line2_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(line2_entries) == 1  # Large step → only final.
    e = line2_entries[0]
    # The feed rate change should ride this entry.
    assert e.get("feed_rate") == pytest.approx(120.0)
    # No entry at time == 0.0 should exist for this line.
    for ent in line2_entries:
        assert ent["time"] > 0.0


# ---------------------------------------------------------------------------
# G93 inverse-time arc duration
# ---------------------------------------------------------------------------


def test_g93_inverse_time_arc_duration(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Under G93 inverse-time, arc duration must be 60/F regardless of geometry.

    G2 X0 Y0 I-1 J0 at F120 should have duration 60/120 = 0.5 seconds.
    Arc starts at (2, 0), circles via center (1, 0) back to (2, 0).
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X2 F60\nG93\nG2 X2 Y0 I-1 J0 F120\n",
        trace_time_step=100.0,  # Large step → only final entry.
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(arc_entries) >= 1
    # G93 F120 → duration = 60/F = 0.5 seconds, regardless of arc geometry.
    # "time" is per-line (seconds since start of the source line).
    assert arc_entries[-1]["time"] == pytest.approx(0.5, abs=1e-6)


# ---------------------------------------------------------------------------
# Tolerance stepping on helical arc
# ---------------------------------------------------------------------------


def test_tolerance_stepping_helical_arc(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Tolerance stepping on a helical arc must produce correct intermediate positions.

    Quarter-circle arc in XY from (1,0) to (0,1) center (0,0) with helical Z.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG2 X0 Y1 Z-1 I-1 J0 F60\n",
        trace_position_tolerance=0.001,  # Tight tolerance → many samples.
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(arc_entries) >= 3, "Tight tolerance should produce multiple arc samples"
    # Verify Z progresses monotonically from 0 toward -1.
    states = [reconstruct_state(trace, i) for i in range(len(trace_entries(trace)))]
    arc_states = [
        s for i, s in enumerate(states) if trace_entries(trace)[i]["line_number"] == input_line(2)
    ]
    z_values = [s["machine_position"]["z"] for s in arc_states]
    for i in range(1, len(z_values)):
        assert z_values[i] <= z_values[i - 1] + 1e-9, (
            f"Z should decrease monotonically in helical arc: {z_values}"
        )
    assert z_values[-1] == pytest.approx(-1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G18 and G19 plane arcs in trace
# ---------------------------------------------------------------------------


def test_g18_xz_plane_arc_trace(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G18 (XZ plane) arc must produce correct trace positions.

    Quarter-circle from (1,0,0) to (0,0,1) center (0,0,0) in XZ.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G18\nG1 X1 F60\nG3 X0 Z1 I-1 K0 F60\n",
        trace_time_step=100.0,  # Only final entry.
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(arc_entries) >= 1
    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["x"] == pytest.approx(0.0, abs=1e-6)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)
    assert final["machine_position"]["y"] == pytest.approx(0.0, abs=1e-6)


def test_g19_yz_plane_arc_trace(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G19 (YZ plane) arc must produce correct trace positions.

    Quarter-circle from (0,1,0) to (0,0,1) center (0,0,0) in YZ.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G19\nG1 Y1 F60\nG3 Y0 Z1 J-1 K0 F60\n",
        trace_time_step=100.0,  # Only final entry.
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(arc_entries) >= 1
    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["y"] == pytest.approx(0.0, abs=1e-6)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)
    assert final["machine_position"]["x"] == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G82 drill with dwell — canned cycle dwell timing
# ---------------------------------------------------------------------------


def test_g82_drill_with_dwell_trace(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G82 drill with dwell at bottom: trace has sub-motions for the motion
    parts (rapid to XY, rapid to R, feed to Z, rapid retract).

    The dwell at bottom (P) is an internal cycle behavior, not a sub-motion.
    Trace time reflects sub-motion durations only.
    """
    setup = "G90\nG0 X0 Y0 Z1\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G82 X1 Z-1 R0 P0.5 F60\n",
        trace_distance_step=1000.0,  # Only final entries per SM.
        tmp_path=tmp_path,
    )
    g82_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    # SM1: rapid X0→X1 (1 inch)
    # SM2: rapid Z1→Z0 (R height)
    # SM3: feed Z0→Z-1 (1 inch)
    # (dwell — no trace entry)
    # SM4: rapid Z-1→Z1 (retract to initial Z under G98)
    assert len(g82_entries) >= 3  # At least 3 non-zero SMs.

    kinds = [e.get("motion_kind") for e in g82_entries if "motion_kind" in e]
    assert "rapid" in kinds
    assert "feed" in kinds

    # Verify final Z position is back at initial (G98 return mode).
    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G85 boring cycle: feed to Z, feed retract (both sub-motions are "feed")
# ---------------------------------------------------------------------------


def test_g85_boring_feed_retract(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G85 boring: feed to Z, feed retract to clear height.

    Both the plunge and retract are feed-rate moves (not rapid).
    """
    setup = "G90\nG0 X0 Y0 Z1\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G85 X1 Z-1 R0 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g85_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(g85_entries) >= 3  # rapid-XY, rapid-to-R, feed-to-Z, feed-retract

    kinds = [e.get("motion_kind") for e in g85_entries if "motion_kind" in e]
    # G85 retract is feed, not rapid.  Both plunge and retract are "feed".
    feed_count = sum(1 for k in kinds if k == "feed")
    assert feed_count >= 2, "G85 plunge and retract should both be feed"

    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G86 boring cycle: feed to Z, rapid retract (spindle must be on)
# ---------------------------------------------------------------------------


def test_g86_boring_rapid_retract(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G86 boring: feed to Z, rapid retract.  Requires spindle on."""
    setup = "M3\nG90\nG0 X0 Y0 Z1\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G86 X1 Z-1 R0 P0.5 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g86_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    assert len(g86_entries) >= 3

    kinds = [e.get("motion_kind") for e in g86_entries if "motion_kind" in e]
    assert "rapid" in kinds
    assert "feed" in kinds

    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G87 back boring: rapid to Z, feed to R, rapid retract
# ---------------------------------------------------------------------------


def test_g87_back_boring_sub_motions(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G87 with omitted I/J/K uses zero defaults and returns to clear Z.

    Clarifications.md defines omitted G87 I/J/K as zero. In this setup,
    G90 makes defaulted K equivalent to absolute Z0, so the feed-up move
    from Z-1 to Z0 is observable. G98 then retracts to the pre-cycle Z
    value.
    """
    # Section 3.5.16.8 restarts the spindle in its prior direction. Establish
    # that direction so this test only measures the defaulted I/J/K path.
    setup = "G90 M3 S100\nG98\nG0 X0 Y0 Z2\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G87 X1 Z-1 R0 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g87_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(4)]
    assert len(g87_entries) >= 3

    kinds = [e.get("motion_kind") for e in g87_entries if "motion_kind" in e]
    # G87: first depth move is rapid, then feed up to defaulted K0.
    assert kinds[0] == "rapid" or kinds[1] == "rapid", "G87 should have rapid move to depth"
    assert "feed" in kinds, "G87 should have a feed move to K"

    # Section 3.5.16.8 steps 6 and 7 feed to K and back to Z. With omitted
    # K in G90, Clarifications.md resolves K to absolute Z0, not retract R
    # in general. The separate explicit-I/J/K test distinguishes those levels.
    feed_z = [
        reconstruct_state(trace, i)["machine_position"]["z"]
        for i, entry in enumerate(trace_entries(trace))
        if entry["line_number"] == input_line(4) and entry.get("motion_kind") == "feed"
    ]
    assert feed_z == pytest.approx([0.0, -1.0], abs=1e-6)

    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["z"] == pytest.approx(2.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G89 boring with dwell: feed to Z, (dwell), feed retract
# ---------------------------------------------------------------------------


def test_g89_boring_dwell_feed_retract(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G89 boring with dwell: feed to Z, dwell, feed retract.

    Like G85 (both moves are feed), but with a dwell at bottom.
    The dwell is internal to the cycle and does not appear in the trace.
    """
    setup = "G90\nG0 X0 Y0 Z1\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G89 X1 Z-1 R0 P0.5 F60\n",
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    g89_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(g89_entries) >= 3

    kinds = [e.get("motion_kind") for e in g89_entries if "motion_kind" in e]
    # G89 retract is feed (same as G85).
    feed_count = sum(1 for k in kinds if k == "feed")
    assert feed_count >= 2, "G89 plunge and retract should both be feed"

    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Unit switch mid-program (G20 → G21)
# ---------------------------------------------------------------------------


def test_unit_switch_mid_program_trace_coordinates(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Entries before G21 use inches; entries after G21 use mm.

    Line 1: G1 X1 F60   (G20 default — inches, 1 inch in 1 s)
    Line 2: G21          (switch to mm)
    Line 3: G1 X50.8 F1524  (mm, 50.8 mm = 2 inches, F1524 mm/min = ~1 s)

    Large step so each motion has exactly 1 entry (the final).
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 F60\nG21\nG1 X50.8 F1524\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    # Line 1 (inches): final position X = 1.0 inch
    l1_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(1)]
    assert len(l1_entries) == 1
    assert l1_entries[0]["machine_position"]["x"] == pytest.approx(1.0, abs=0.01)

    # Line 3 (mm): final position X = 50.8 mm
    l3_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    assert len(l3_entries) == 1
    assert l3_entries[0]["machine_position"]["x"] == pytest.approx(50.8, abs=0.1)


def test_g21_arc_distance_stepping(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """Distance stepping for an arc under G21 uses inches, coordinates in mm.

    G21 G2 X0 Y0 I-25.4 F1524  (full circle, radius 25.4 mm = 1 inch,
    circumference = 2*pi inches ~= 6.283 inches).
    --trace-distance-step 2.0 (inches) -> 3 interior + 1 final = 4 entries.
    All positions should be in mm.
    """
    # Start at (25.4, 0) mm = (1, 0) inches so arc center is at origin.
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G21\nG0 X25.4 Y0\nG2 X25.4 Y0 I-25.4 F1524\n",
        trace_distance_step=2.0,
        tmp_path=tmp_path,
    )
    arc_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(3)]
    # Circumference ~= 6.283 inches / 2.0 step -> 3 interior + 1 final = 4.
    assert len(arc_entries) >= 3, (
        f"Expected >=3 arc entries for full circle with 2-inch step, got {len(arc_entries)}"
    )

    # All positions should be in mm (radius 25.4 mm from origin).
    for entry in arc_entries:
        state = reconstruct_state(trace, trace_entries(trace).index(entry))
        x = state["machine_position"]["x"]
        y = state["machine_position"]["y"]
        r = math.sqrt(x**2 + y**2)
        assert r == pytest.approx(25.4, abs=0.5), (
            f"Arc point ({x}, {y}) should be ~25.4 mm from origin, got r={r}"
        )

    # Final entry returns to start (25.4, 0) mm.
    final_state = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final_state["machine_position"]["x"] == pytest.approx(25.4, abs=0.1)
    assert final_state["machine_position"]["y"] == pytest.approx(0.0, abs=0.1)


# ---------------------------------------------------------------------------
# RS274 §2.1.2.5 Case A: linear + rotary path length uses XYZ only
# ---------------------------------------------------------------------------


def test_linear_plus_rotary_duration_uses_xyz_path_only(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """RS274 §2.1.2.5 Case A: path length excludes rotary axes.

    G1 X1 A90 F60: XYZ path = 1 inch, duration = 1.0 s.
    If rotary axes are incorrectly included, path ~= 90, duration ~= 90 s.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G1 X1 A90 F60\n",
        trace_time_step=100.0,
        tmp_path=tmp_path,
    )
    entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(1)]
    assert len(entries) == 1
    # Duration should be ~1.0 s (1 inch at 60 ipm), NOT ~90 s.
    assert entries[0]["time"] == pytest.approx(1.0, abs=0.05)


def test_rotary_only_g21_feed_rate_not_converted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """RS274 §2.1.2.5 Case B: rotary-only feed rate is deg/min, not mm/min.

    G21 G1 A90 F90: path = 90 degrees, rate = 90 deg/min, duration = 60 s.
    Bug: G21 would convert 90 "mm/min" to ~3.54 in/min, giving ~1524 s.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="G21\nG1 A90 F90\n",
        trace_time_step=1000.0,
        tmp_path=tmp_path,
    )
    entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    assert len(entries) == 1
    # 90 degrees at 90 deg/min = 60 seconds, NOT ~1524 seconds.
    assert entries[0]["time"] == pytest.approx(60.0, abs=0.5)


# ---------------------------------------------------------------------------
# G88 boring cycle trace coverage
# ---------------------------------------------------------------------------


def test_g88_boring_rapid_retract(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G88 uses the non-interactive manual-retract convention.

    Clarifications.md maps G88's manual operator retract to an automatic
    rapid retract to the canned-cycle clear level. Under G98 here, clear
    Z is the pre-cycle Z value because it is above R0.
    """
    tool_table = "POCKET FMS TLO DIAMETER\n\n1 1 0.0 0.0\n"
    setup = "T1\nM6\nM3\nG90\nG98\nG0 X0 Y0 Z1\n"
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=setup + "G88 X1 Z-1 R0 P0.5 F60\n",
        trace_distance_step=1000.0,
        tool_table_content=tool_table,
        tmp_path=tmp_path,
    )
    g88_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(7)]
    assert len(g88_entries) >= 3

    kinds = [e.get("motion_kind") for e in g88_entries if "motion_kind" in e]
    assert "rapid" in kinds, "G88 should have rapid sub-motions"
    assert "feed" in kinds, "G88 should have feed sub-motions"

    final = reconstruct_state(trace, len(trace_entries(trace)) - 1)
    assert final["machine_position"]["z"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# G28 per-sub-motion stepping
# ---------------------------------------------------------------------------


def test_g28_stepping_applied_per_sub_motion(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """G28 stepping is applied to each sub-motion independently.

    G28 from (0,0,0) via intermediate (3,0,0) to home (6,0,0).
    SM1: rapid (0,0,0)→(3,0,0), 3 inches.
    SM2: rapid (3,0,0)→(6,0,0), 3 inches.
    With --trace-distance-step 2.0: each SM gets 1 interior + 1 final = 2 entries.
    Total G28 entries = 4 (not 3, which would mean stepping across the whole move).
    """
    # Section 3.5.8 uses the home parameters; file parsing is tested elsewhere.
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode="#5161=6 #5162=0 #5163=0\nG28 X3\n",
        trace_distance_step=2.0,
        tmp_path=tmp_path,
    )
    g28_entries = [e for e in trace_entries(trace) if e["line_number"] == input_line(2)]
    # Per-SM stepping: each 3-inch SM with 2-inch step → 1 interior + 1 final = 2.
    # Total = 4 entries. Treating the whole six-inch move as one would instead
    # emit samples at X2, X4, X6 and miss the mandatory X3 sub-motion endpoint.
    assert len(g28_entries) == 4

    # Times accumulate across sub-motions within the same source block.
    sm1_final_time = g28_entries[1]["time"]
    sm2_first_time = g28_entries[2]["time"]
    assert sm2_first_time > sm1_final_time, (
        "SM2 entries should have cumulative time greater than SM1"
    )

    # Verify positions at SM boundaries.
    sm1_final = reconstruct_state(trace, trace_entries(trace).index(g28_entries[1]))
    assert sm1_final["machine_position"]["x"] == pytest.approx(3.0, abs=0.01)
    sm2_final = reconstruct_state(trace, trace_entries(trace).index(g28_entries[3]))
    assert sm2_final["machine_position"]["x"] == pytest.approx(6.0, abs=0.01)
